from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.building import Unit
from app.models.document import Document
from app.models.enums import (
    EntityType,
    LeaseStatus,
    OverdueStatus,
    RepairStatus,
)
from app.models.overdue import OverdueRecord
from app.models.payment import Payment, Receipt, RentPeriod
from app.models.portal import TenantNotice
from app.models.repair import Repair
from app.models.tenant import Lease, Tenant
from app.models.user import User
from app.schemas.portal import (
    TenantLeaseInfo,
    TenantNoticeCreate,
    TenantNoticeSummary,
    TenantPortalDashboard,
    TenantUnitInfo,
)
from app.schemas.repair import RepairCreate
from app.services.message_service import MessageService
from app.services.payment_service import PaymentService
from app.services.repair_service import RepairService

UNIT_TYPE_LABELS = {
    "apartment": "Appartement",
    "shop": "Magasin",
    "office": "Bureau",
}

ACTIVE_REPAIR_STATUSES = (
    RepairStatus.new,
    RepairStatus.under_review,
    RepairStatus.technician_assigned,
    RepairStatus.in_progress,
)


class TenantPortalService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _tenant(self, actor: User) -> Tenant:
        if actor.role.code != "locataire" or actor.tenant_profile is None:
            raise HTTPException(status_code=403, detail="Accès réservé aux locataires")
        return actor.tenant_profile

    def _active_lease(self, tenant: Tenant) -> Lease | None:
        return (
            self.db.query(Lease)
            .options(joinedload(Lease.unit).joinedload(Unit.building))
            .filter(Lease.tenant_id == tenant.id, Lease.status == LeaseStatus.active)
            .first()
        )

    def get_dashboard(self, actor: User) -> TenantPortalDashboard:
        tenant = self._tenant(actor)
        lease = self._active_lease(tenant)
        today = date.today()

        unit_info = None
        lease_info = None
        current_month_paid = False
        total_unpaid = Decimal("0")
        next_due = None

        if lease:
            unit = lease.unit
            unit_info = {
                "code": unit.code,
                "type": UNIT_TYPE_LABELS.get(unit.type.value, unit.type.value),
            }
            lease_info = {
                "rent_amount": float(lease.rent_amount),
                "end_date": lease.end_date.isoformat() if lease.end_date else None,
            }
            period = (
                self.db.query(RentPeriod)
                .filter(
                    RentPeriod.lease_id == lease.id,
                    RentPeriod.period_year == today.year,
                    RentPeriod.period_month == today.month,
                )
                .first()
            )
            if period:
                current_month_paid = period.paid_amount >= period.expected_amount
                next_due = period.due_date.isoformat()

            overdues = (
                self.db.query(OverdueRecord)
                .filter(
                    OverdueRecord.tenant_id == tenant.id,
                    OverdueRecord.status != OverdueStatus.resolved,
                )
                .all()
            )
            total_unpaid = sum((item.amount_remaining for item in overdues), Decimal("0"))

        unread_notices = (
            self.db.query(TenantNotice)
            .filter(TenantNotice.tenant_id == tenant.id, TenantNotice.is_read.is_(False))
            .count()
        )
        active_repairs = (
            self.db.query(func.count(Repair.id))
            .filter(
                Repair.reported_by == actor.id,
                Repair.status.in_(ACTIVE_REPAIR_STATUSES),
            )
            .scalar()
            or 0
        )

        return TenantPortalDashboard(
            tenant={"full_name": f"{tenant.first_name} {tenant.last_name}"},
            unit=unit_info,
            lease=lease_info,
            payment_status={
                "current_month_paid": current_month_paid,
                "total_unpaid": float(total_unpaid),
                "next_due_date": next_due,
            },
            unread_notices=unread_notices,
            active_repairs=active_repairs,
            has_active_lease=lease is not None,
        )

    def get_my_unit(self, actor: User) -> TenantUnitInfo:
        tenant = self._tenant(actor)
        lease = self._active_lease(tenant)
        if lease is None:
            raise HTTPException(status_code=404, detail="Aucun logement associé")
        unit = lease.unit
        building = unit.building
        photos = [{"id": str(p.id), "url": p.url} for p in unit.photos]
        return TenantUnitInfo(
            id=str(unit.id),
            code=unit.code,
            type=UNIT_TYPE_LABELS.get(unit.type.value, unit.type.value),
            number=unit.number,
            rent_amount=float(unit.rent_amount),
            building_name=building.name,
            commune=building.commune,
            quartier=building.quartier,
            description=unit.description,
            photos=photos,
        )

    def get_my_lease(self, actor: User) -> TenantLeaseInfo:
        tenant = self._tenant(actor)
        lease = self._active_lease(tenant)
        if lease is None:
            raise HTTPException(status_code=404, detail="Aucun bail actif")
        return TenantLeaseInfo(
            id=str(lease.id),
            start_date=lease.start_date.isoformat(),
            end_date=lease.end_date.isoformat() if lease.end_date else None,
            rent_amount=float(lease.rent_amount),
            deposit_amount=float(lease.deposit_amount),
            status=lease.status.value,
            contract_document_url=lease.contract_document_url,
        )

    def list_payments(self, actor: User):
        return PaymentService(self.db).list_payments(actor, tenant_id=actor.tenant_profile.id)

    def list_receipts(self, actor: User):
        from app.schemas.receipt import ReceiptListResponse, ReceiptSummary

        tenant = self._tenant(actor)
        receipts = (
            self.db.query(Receipt)
            .join(Payment)
            .options(joinedload(Receipt.payment).joinedload(Payment.tenant))
            .filter(Payment.tenant_id == tenant.id)
            .order_by(Receipt.issued_at.desc())
            .all()
        )
        return ReceiptListResponse(
            items=[
                ReceiptSummary(
                    id=str(r.id),
                    payment_id=str(r.payment_id),
                    receipt_number=r.receipt_number,
                    pdf_url=r.pdf_url,
                    issued_at=r.issued_at,
                    issued_by_name="",
                    tenant_name=f"{tenant.first_name} {tenant.last_name}",
                    unit_code="",
                    amount=str(r.payment.amount),
                    status=r.status,
                    sent_email_at=r.sent_email_at,
                )
                for r in receipts
            ],
            total=len(receipts),
            page=1,
            page_size=max(len(receipts), 1),
            pages=1 if receipts else 0,
        )

    def list_overdues(self, actor: User):
        from app.services.overdue_service import OverdueService

        tenant = self._tenant(actor)
        return OverdueService(self.db).list_overdues(actor, tenant_id=tenant.id, page_size=50)

    def list_repairs(self, actor: User):
        return RepairService(self.db).list_repairs(actor, page_size=50)

    def create_repair(self, actor: User, payload: RepairCreate):
        return RepairService(self.db).create_repair(actor, payload)

    def list_documents(self, actor: User):
        tenant = self._tenant(actor)
        lease = self._active_lease(tenant)
        query = self.db.query(Document).filter(
            (Document.entity_type == EntityType.tenant) & (Document.entity_id == tenant.id)
        )
        if lease:
            lease_docs = self.db.query(Document).filter(
                Document.entity_type == EntityType.lease,
                Document.entity_id == lease.id,
            )
            tenant_docs = query.all()
            lease_doc_list = lease_docs.all()
            docs = tenant_docs + lease_doc_list
        else:
            docs = query.all()
        return {
            "items": [
                {
                    "id": str(d.id),
                    "title": d.title,
                    "file_name": d.file_name,
                    "mime_type": d.mime_type,
                    "uploaded_at": d.uploaded_at.isoformat(),
                }
                for d in docs
            ]
        }

    def list_notices(self, actor: User) -> list[TenantNoticeSummary]:
        tenant = self._tenant(actor)
        notices = (
            self.db.query(TenantNotice)
            .filter(TenantNotice.tenant_id == tenant.id)
            .order_by(TenantNotice.published_at.desc())
            .all()
        )
        return [self._notice_summary(n) for n in notices]

    def mark_notice_read(self, actor: User, notice_id: UUID) -> TenantNoticeSummary:
        tenant = self._tenant(actor)
        notice = (
            self.db.query(TenantNotice)
            .filter(TenantNotice.id == notice_id, TenantNotice.tenant_id == tenant.id)
            .first()
        )
        if notice is None:
            raise HTTPException(status_code=404, detail="Avis introuvable")
        notice.is_read = True
        self.db.commit()
        return self._notice_summary(notice)

    def list_messages(self, actor: User):
        return MessageService(self.db).list_messages(actor)

    def send_message(self, actor: User, payload):
        return MessageService(self.db).send_as_user(actor, payload)

    def publish_notice(self, actor: User, payload: TenantNoticeCreate) -> TenantNoticeSummary:
        if actor.role.code not in ("super_admin", "admin_familial", "gestionnaire"):
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        notice = TenantNotice(
            tenant_id=UUID(payload.tenant_id),
            title=payload.title.strip(),
            content=payload.content,
            notice_type=payload.notice_type,
            document_id=UUID(payload.document_id) if payload.document_id else None,
            published_by=actor.id,
        )
        self.db.add(notice)
        self.db.commit()
        return self._notice_summary(notice)

    def _notice_summary(self, notice: TenantNotice) -> TenantNoticeSummary:
        return TenantNoticeSummary(
            id=str(notice.id),
            title=notice.title,
            content=notice.content,
            notice_type=notice.notice_type,
            published_at=notice.published_at,
            is_read=notice.is_read,
        )
