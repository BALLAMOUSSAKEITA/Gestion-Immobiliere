import logging
from datetime import UTC, datetime
from decimal import Decimal
from math import ceil
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.building import Unit
from app.models.enums import OverdueStatus, ReminderStatus, ReminderType
from app.models.overdue import OverdueRecord, Reminder
from app.models.tenant import Lease, Tenant
from app.models.user import User
from app.schemas.overdue import (
    OverdueItem,
    OverdueListResponse,
    OverdueSummary,
    ReminderCreate,
    ReminderListResponse,
    ReminderResponse,
    TenantBrief,
    TenantOverdueListResponse,
    TenantOverdueSummary,
)
from app.services.building_service import BuildingAccessService
from app.services.overdue_detection_service import OverdueDetectionService
from app.services.tenant_access_service import TenantAccessService
from app.services.user_service import PermissionService

logger = logging.getLogger(__name__)


class OverdueService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_overdues(
        self,
        actor: User,
        page: int = 1,
        page_size: int = 20,
        building_id: UUID | None = None,
        tenant_id: UUID | None = None,
        min_days: int | None = None,
        min_amount: Decimal | None = None,
        sort: str = "days_overdue",
    ) -> OverdueListResponse:
        self._ensure_read_access(actor)
        OverdueDetectionService(self.db).sync_all()

        query = (
            self.db.query(OverdueRecord)
            .join(Unit, OverdueRecord.unit_id == Unit.id)
            .options(
                joinedload(OverdueRecord.tenant),
                joinedload(OverdueRecord.reminders),
            )
            .filter(OverdueRecord.status != OverdueStatus.resolved)
        )

        allowed = BuildingAccessService.accessible_building_ids(self.db, actor)
        if allowed is not None:
            query = query.filter(Unit.building_id.in_(allowed) if allowed else Unit.id.is_(None))

        if actor.role.code == "locataire":
            if actor.tenant_profile is None:
                query = query.filter(OverdueRecord.id.is_(None))
            else:
                query = query.filter(OverdueRecord.tenant_id == actor.tenant_profile.id)

        if building_id:
            BuildingAccessService.ensure_building_access(self.db, actor, building_id)
            query = query.filter(Unit.building_id == building_id)
        if tenant_id:
            TenantAccessService.ensure_tenant_access(self.db, actor, tenant_id)
            query = query.filter(OverdueRecord.tenant_id == tenant_id)
        if min_days is not None:
            query = query.filter(OverdueRecord.days_overdue >= min_days)
        if min_amount is not None:
            query = query.filter(OverdueRecord.amount_remaining >= min_amount)

        if sort == "amount":
            query = query.order_by(OverdueRecord.amount_remaining.desc())
        elif sort == "tenant_name":
            query = query.join(Tenant).order_by(Tenant.last_name, Tenant.first_name)
        else:
            query = query.order_by(OverdueRecord.days_overdue.desc())

        total = query.count()
        records = query.offset((page - 1) * page_size).limit(page_size).all()
        pages = ceil(total / page_size) if total else 0

        tenant_totals = self._compute_tenant_totals(records)
        items = [self._to_item(record, tenant_totals) for record in records]
        summary = self._compute_summary(query)

        return OverdueListResponse(
            items=items,
            summary=summary,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def get_summary(self, actor: User) -> OverdueSummary:
        self._ensure_read_access(actor)
        OverdueDetectionService(self.db).sync_all()
        query = self._base_query(actor)
        return self._compute_summary(query)

    def list_by_tenant(self, actor: User) -> TenantOverdueListResponse:
        self._ensure_read_access(actor)
        OverdueDetectionService(self.db).sync_all()
        query = self._base_query(actor)

        rows = (
            query.with_entities(
                OverdueRecord.tenant_id,
                func.sum(OverdueRecord.amount_remaining),
                func.count(OverdueRecord.id),
                func.max(OverdueRecord.days_overdue),
            )
            .group_by(OverdueRecord.tenant_id)
            .all()
        )

        items: list[TenantOverdueSummary] = []
        for tenant_id, total_amount, count, max_days in rows:
            tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if tenant is None:
                continue
            last_reminder = (
                self.db.query(func.max(Reminder.sent_at))
                .filter(Reminder.tenant_id == tenant_id)
                .scalar()
            )
            items.append(
                TenantOverdueSummary(
                    tenant_id=str(tenant_id),
                    tenant_name=f"{tenant.first_name} {tenant.last_name}",
                    phone=tenant.phone_primary,
                    total_overdue_amount=total_amount or Decimal("0"),
                    overdue_months_count=count or 0,
                    oldest_overdue_days=max_days or 0,
                    last_reminder_at=last_reminder,
                )
            )
        items.sort(key=lambda item: item.total_overdue_amount, reverse=True)
        return TenantOverdueListResponse(items=items)

    def get_overdue(self, actor: User, overdue_id: UUID) -> OverdueItem:
        self._ensure_read_access(actor)
        record = self._get_or_404(overdue_id)
        self._ensure_record_access(actor, record)
        totals = self._compute_tenant_totals([record])
        return self._to_item(record, totals)

    def resolve_overdue(self, actor: User, overdue_id: UUID) -> OverdueItem:
        if actor.role.code not in ("super_admin", "admin_familial"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")
        record = self._get_or_404(overdue_id)
        record.status = OverdueStatus.resolved
        record.amount_remaining = Decimal("0")
        record.resolved_at = datetime.now(UTC)
        self.db.commit()
        totals = self._compute_tenant_totals([record])
        return self._to_item(record, totals)

    def list_tenant_overdues(self, actor: User, tenant_id: UUID) -> OverdueListResponse:
        return self.list_overdues(actor, tenant_id=tenant_id, page_size=100)

    def _base_query(self, actor: User):
        query = (
            self.db.query(OverdueRecord)
            .join(Unit, OverdueRecord.unit_id == Unit.id)
            .filter(OverdueRecord.status != OverdueStatus.resolved)
        )
        allowed = BuildingAccessService.accessible_building_ids(self.db, actor)
        if allowed is not None:
            query = query.filter(Unit.building_id.in_(allowed) if allowed else Unit.id.is_(None))
        if actor.role.code == "locataire" and actor.tenant_profile:
            query = query.filter(OverdueRecord.tenant_id == actor.tenant_profile.id)
        return query

    def _compute_summary(self, query) -> OverdueSummary:
        records = query.all()
        tenant_ids = {record.tenant_id for record in records}
        total_amount = sum((record.amount_remaining for record in records), Decimal("0"))
        return OverdueSummary(
            total_overdue_amount=total_amount,
            total_tenants_affected=len(tenant_ids),
            total_periods_overdue=len(records),
        )

    def _compute_tenant_totals(self, records: list[OverdueRecord]) -> dict[UUID, Decimal]:
        tenant_ids = {record.tenant_id for record in records}
        totals: dict[UUID, Decimal] = {}
        for tenant_id in tenant_ids:
            total = (
                self.db.query(func.sum(OverdueRecord.amount_remaining))
                .filter(
                    OverdueRecord.tenant_id == tenant_id,
                    OverdueRecord.status != OverdueStatus.resolved,
                )
                .scalar()
            )
            totals[tenant_id] = total or Decimal("0")
        return totals

    def _to_item(
        self, record: OverdueRecord, tenant_totals: dict[UUID, Decimal]
    ) -> OverdueItem:
        unit = self.db.query(Unit).options(joinedload(Unit.building)).filter(Unit.id == record.unit_id).first()
        tenant = record.tenant
        reminders = record.reminders or []
        last_reminder = max((r.sent_at for r in reminders), default=None)
        return OverdueItem(
            id=str(record.id),
            tenant=TenantBrief(
                id=str(tenant.id),
                full_name=f"{tenant.first_name} {tenant.last_name}",
                phone=tenant.phone_primary,
            ),
            unit_code=unit.code if unit else "",
            building_name=unit.building.name if unit and unit.building else "",
            period=f"{record.period_year}-{record.period_month:02d}",
            period_year=record.period_year,
            period_month=record.period_month,
            amount_due=record.amount_due,
            amount_paid=record.amount_paid,
            amount_remaining=record.amount_remaining,
            days_overdue=record.days_overdue,
            status=record.status,
            reminders_count=len(reminders),
            last_reminder_at=last_reminder,
            tenant_total_overdue=tenant_totals.get(record.tenant_id, record.amount_remaining),
        )

    def _get_or_404(self, overdue_id: UUID) -> OverdueRecord:
        record = (
            self.db.query(OverdueRecord)
            .options(joinedload(OverdueRecord.tenant), joinedload(OverdueRecord.reminders))
            .filter(OverdueRecord.id == overdue_id)
            .first()
        )
        if record is None:
            raise HTTPException(status_code=404, detail="Impayé introuvable")
        return record

    def _ensure_record_access(self, actor: User, record: OverdueRecord) -> None:
        unit = self.db.query(Unit).filter(Unit.id == record.unit_id).first()
        if unit:
            BuildingAccessService.ensure_building_access(self.db, actor, unit.building_id)
        if actor.role.code == "locataire":
            if actor.tenant_profile is None or record.tenant_id != actor.tenant_profile.id:
                raise HTTPException(status_code=403, detail="Accès non autorisé")

    def _ensure_read_access(self, actor: User) -> None:
        if actor.role.code not in (
            "super_admin",
            "admin_familial",
            "gestionnaire",
            "locataire",
        ):
            raise HTTPException(status_code=403, detail="Accès non autorisé")


class ReminderService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_reminders(
        self,
        actor: User,
        page: int = 1,
        page_size: int = 20,
        tenant_id: UUID | None = None,
    ) -> ReminderListResponse:
        if actor.role.code not in ("super_admin", "admin_familial", "gestionnaire", "locataire"):
            raise HTTPException(status_code=403, detail="Accès non autorisé")

        query = self.db.query(Reminder).options(joinedload(Reminder.tenant), joinedload(Reminder.sender))

        if actor.role.code == "locataire":
            if actor.tenant_profile is None:
                query = query.filter(Reminder.id.is_(None))
            else:
                query = query.filter(Reminder.tenant_id == actor.tenant_profile.id)
        elif tenant_id:
            TenantAccessService.ensure_tenant_access(self.db, actor, tenant_id)
            query = query.filter(Reminder.tenant_id == tenant_id)

        total = query.count()
        reminders = (
            query.order_by(Reminder.sent_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        pages = ceil(total / page_size) if total else 0
        return ReminderListResponse(
            items=[self._to_response(item) for item in reminders],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def send_reminder(self, actor: User, payload: ReminderCreate) -> ReminderResponse:
        if actor.role.code not in ("super_admin", "admin_familial", "gestionnaire"):
            raise HTTPException(status_code=403, detail="Accès non autorisé")

        tenant_id = UUID(payload.tenant_id)
        TenantAccessService.ensure_tenant_access(self.db, actor, tenant_id)

        overdue_id = UUID(payload.overdue_record_ids[0]) if payload.overdue_record_ids else None
        reminder = Reminder(
            tenant_id=tenant_id,
            overdue_record_id=overdue_id,
            reminder_type=payload.reminder_type,
            channel=payload.channel,
            message=payload.message.strip(),
            sent_by=actor.id,
            status=ReminderStatus.sent,
        )
        self.db.add(reminder)
        self.db.commit()
        self.db.refresh(reminder)
        logger.info("Relance manuelle envoyée à locataire %s via %s", tenant_id, payload.channel.value)
        loaded = self._load(reminder.id)
        if loaded is None:
            raise HTTPException(status_code=500, detail="Relance introuvable après création")
        return self._to_response(loaded)

    def list_tenant_reminders(self, actor: User, tenant_id: UUID) -> ReminderListResponse:
        return self.list_reminders(actor, tenant_id=tenant_id, page_size=100)

    def _load(self, reminder_id: UUID) -> Reminder:
        return (
            self.db.query(Reminder)
            .options(joinedload(Reminder.tenant), joinedload(Reminder.sender))
            .filter(Reminder.id == reminder_id)
            .first()
        )

    def _to_response(self, reminder: Reminder) -> ReminderResponse:
        return ReminderResponse(
            id=str(reminder.id),
            tenant_id=str(reminder.tenant_id),
            tenant_name=f"{reminder.tenant.first_name} {reminder.tenant.last_name}",
            overdue_record_id=str(reminder.overdue_record_id) if reminder.overdue_record_id else None,
            reminder_type=reminder.reminder_type,
            channel=reminder.channel,
            message=reminder.message,
            sent_at=reminder.sent_at,
            sent_by_name=(
                f"{reminder.sender.first_name} {reminder.sender.last_name}"
                if reminder.sender
                else None
            ),
            status=reminder.status.value,
        )
