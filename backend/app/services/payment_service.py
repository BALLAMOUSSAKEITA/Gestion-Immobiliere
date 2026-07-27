import shutil
from datetime import date
from decimal import Decimal
from math import ceil
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.models.building import Unit
from app.models.enums import LeaseStatus, PaymentRecordStatus
from app.models.payment import Payment, PaymentAllocation, RentPeriod
from app.models.tenant import Lease
from app.models.user import User
from app.schemas.payment import (
    PaymentAllocationResponse,
    PaymentCreate,
    PaymentDetail,
    PaymentListResponse,
    PaymentSummary,
    PeriodAllocationInput,
    RentPeriodResponse,
)
from app.services.building_service import BuildingAccessService
from app.services.receipt_service import ReceiptService
from app.services.rent_period_service import RentPeriodService
from app.services.tenant_access_service import TenantAccessService
from app.services.user_service import PermissionService


class PaymentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        settings = get_settings()
        self.upload_dir = Path(settings.upload_dir)

    def list_periods(self, actor: User, lease_id: UUID) -> list[RentPeriodResponse]:
        self._ensure_read_access(actor)
        lease = self._get_lease_or_404(lease_id)
        self._ensure_lease_access(actor, lease)

        period_service = RentPeriodService(self.db)
        if not lease.rent_periods:
            period_service.generate_for_lease(lease)
            self.db.commit()
            lease = self._get_lease_or_404(lease_id)

        today = date.today()
        items = []
        for period in sorted(
            lease.rent_periods,
            key=lambda item: (item.period_year, item.period_month),
        ):
            period_service.refresh_period_status(period, today)
            remaining = max(period.expected_amount - period.paid_amount, Decimal("0"))
            items.append(
                RentPeriodResponse(
                    id=str(period.id),
                    period_year=period.period_year,
                    period_month=period.period_month,
                    expected_amount=period.expected_amount,
                    paid_amount=period.paid_amount,
                    remaining_amount=remaining,
                    status=period.status,
                    due_date=period.due_date,
                )
            )
        self.db.commit()
        return items

    def generate_periods(self, actor: User, lease_id: UUID) -> list[RentPeriodResponse]:
        self._ensure_manage_access(actor)
        lease = self._get_lease_or_404(lease_id)
        RentPeriodService(self.db).generate_for_lease(lease)
        self.db.commit()
        return self.list_periods(actor, lease_id)

    def list_payments(
        self,
        actor: User,
        page: int = 1,
        page_size: int = 20,
        tenant_id: UUID | None = None,
        lease_id: UUID | None = None,
        building_id: UUID | None = None,
        payment_method: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        status_filter: PaymentRecordStatus | None = None,
    ) -> PaymentListResponse:
        self._ensure_read_access(actor)
        query = (
            self.db.query(Payment)
            .join(Lease)
            .join(Unit)
            .options(
                joinedload(Payment.tenant),
                joinedload(Payment.lease).joinedload(Lease.unit),
                joinedload(Payment.recorder),
                joinedload(Payment.receipt),
            )
        )

        allowed_buildings = BuildingAccessService.accessible_building_ids(self.db, actor)
        if allowed_buildings is not None:
            query = query.filter(
                Unit.building_id.in_(allowed_buildings)
                if allowed_buildings
                else Unit.id.is_(None)
            )

        if actor.role.code == "locataire":
            if actor.tenant_profile is None:
                query = query.filter(Payment.id.is_(None))
            else:
                query = query.filter(Payment.tenant_id == actor.tenant_profile.id)

        if tenant_id:
            TenantAccessService.ensure_tenant_access(self.db, actor, tenant_id)
            query = query.filter(Payment.tenant_id == tenant_id)
        if lease_id:
            query = query.filter(Payment.lease_id == lease_id)
        if building_id:
            BuildingAccessService.ensure_building_access(self.db, actor, building_id)
            query = query.filter(Unit.building_id == building_id)
        if payment_method:
            query = query.filter(Payment.payment_method == payment_method)
        if date_from:
            query = query.filter(Payment.payment_date >= date_from)
        if date_to:
            query = query.filter(Payment.payment_date <= date_to)
        if status_filter:
            query = query.filter(Payment.status == status_filter)

        total = query.count()
        payments = (
            query.order_by(Payment.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        pages = ceil(total / page_size) if total else 0
        return PaymentListResponse(
            items=[self._to_summary(payment) for payment in payments],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def get_payment(self, actor: User, payment_id: UUID) -> PaymentDetail:
        self._ensure_read_access(actor)
        payment = self._get_or_404(payment_id)
        self._ensure_payment_access(actor, payment)
        return self._to_detail(payment)

    def record_payment(self, actor: User, payload: PaymentCreate) -> PaymentDetail:
        self._ensure_manage_access(actor)
        lease_id = UUID(payload.lease_id)
        lease = self._get_lease_or_404(lease_id)
        self._ensure_lease_access(actor, lease)

        if lease.status != LeaseStatus.active:
            raise HTTPException(status_code=400, detail="Le bail n'est pas actif")

        period_service = RentPeriodService(self.db)
        if not lease.rent_periods:
            period_service.generate_for_lease(lease)
            self.db.flush()

        allocations = payload.allocations
        if not allocations:
            allocations = self._auto_allocate(lease_id, payload.amount)

        total_allocated = sum(item.amount for item in allocations)
        if total_allocated != payload.amount:
            raise HTTPException(
                status_code=400,
                detail="Le total des allocations doit être égal au montant du paiement",
            )

        payment = Payment(
            lease_id=lease_id,
            tenant_id=lease.tenant_id,
            amount=payload.amount,
            payment_method=payload.payment_method,
            payment_date=payload.payment_date,
            reference=payload.reference,
            notes=payload.notes,
            recorded_by=actor.id,
        )
        self.db.add(payment)
        self.db.flush()

        for item in allocations:
            period = period_service.get_period(lease_id, item.period_year, item.period_month)
            if period is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Échéance {item.period_month}/{item.period_year} introuvable",
                )
            remaining = period.expected_amount - period.paid_amount
            if item.amount > remaining:
                raise HTTPException(
                    status_code=400,
                    detail=f"Montant supérieur au reste dû pour {item.period_month}/{item.period_year}",
                )

            self.db.add(
                PaymentAllocation(
                    payment_id=payment.id,
                    rent_period_id=period.id,
                    allocated_amount=item.amount,
                )
            )
            period.paid_amount += item.amount
            period_service.refresh_period_status(period, payload.payment_date)

        ReceiptService(self.db).generate_for_payment(payment, actor.id)
        self.db.commit()
        return self._to_detail(self._get_or_404(payment.id))

    def upload_proof(
        self, actor: User, payment_id: UUID, file: UploadFile
    ) -> PaymentDetail:
        self._ensure_manage_access(actor)
        payment = self._get_or_404(payment_id)
        self._ensure_payment_access(actor, payment)

        extension = Path(file.filename or "proof.jpg").suffix.lower() or ".jpg"
        filename = f"{uuid4()}{extension}"
        target_dir = self.upload_dir / "payments"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename
        with target_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        payment.proof_url = f"/uploads/payments/{filename}"
        self.db.commit()
        return self._to_detail(self._get_or_404(payment_id))

    def validate_payment(self, actor: User, payment_id: UUID) -> PaymentDetail:
        if actor.role.code not in ("super_admin", "admin_familial"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")
        payment = self._get_or_404(payment_id)
        from datetime import UTC, datetime

        payment.status = PaymentRecordStatus.validated
        payment.validated_by = actor.id
        payment.validated_at = datetime.now(UTC)
        self.db.commit()
        return self._to_detail(self._get_or_404(payment_id))

    def _auto_allocate(
        self, lease_id: UUID, amount: Decimal
    ) -> list[PeriodAllocationInput]:
        periods = (
            self.db.query(RentPeriod)
            .filter(RentPeriod.lease_id == lease_id)
            .order_by(RentPeriod.period_year, RentPeriod.period_month)
            .all()
        )
        remaining = amount
        allocations: list[PeriodAllocationInput] = []
        for period in periods:
            if remaining <= 0:
                break
            due = period.expected_amount - period.paid_amount
            if due <= 0:
                continue
            alloc = min(due, remaining)
            allocations.append(
                PeriodAllocationInput(
                    period_year=period.period_year,
                    period_month=period.period_month,
                    amount=alloc,
                )
            )
            remaining -= alloc
        if remaining > 0:
            raise HTTPException(
                status_code=400,
                detail="Montant supérieur au total des échéances impayées",
            )
        return allocations

    def _get_lease_or_404(self, lease_id: UUID) -> Lease:
        lease = (
            self.db.query(Lease)
            .options(
                joinedload(Lease.rent_periods),
                joinedload(Lease.unit),
                joinedload(Lease.tenant),
            )
            .filter(Lease.id == lease_id)
            .first()
        )
        if lease is None:
            raise HTTPException(status_code=404, detail="Bail introuvable")
        return lease

    def _get_or_404(self, payment_id: UUID) -> Payment:
        payment = (
            self.db.query(Payment)
            .options(
                joinedload(Payment.tenant),
                joinedload(Payment.lease).joinedload(Lease.unit),
                joinedload(Payment.recorder),
                joinedload(Payment.receipt),
                joinedload(Payment.allocations).joinedload(PaymentAllocation.rent_period),
            )
            .filter(Payment.id == payment_id)
            .first()
        )
        if payment is None:
            raise HTTPException(status_code=404, detail="Paiement introuvable")
        return payment

    def _ensure_lease_access(self, actor: User, lease: Lease) -> None:
        BuildingAccessService.ensure_building_access(self.db, actor, lease.unit.building_id)
        if actor.role.code == "locataire":
            if actor.tenant_profile is None or lease.tenant_id != actor.tenant_profile.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")

    def _ensure_payment_access(self, actor: User, payment: Payment) -> None:
        self._ensure_lease_access(actor, payment.lease)
        if actor.role.code == "locataire":
            if actor.tenant_profile is None or payment.tenant_id != actor.tenant_profile.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")

    def _ensure_read_access(self, actor: User) -> None:
        if actor.role.code not in (
            "super_admin",
            "admin_familial",
            "gestionnaire",
            "proprietaire",
            "locataire",
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")

    def _ensure_manage_access(self, actor: User) -> None:
        if actor.role.code in ("super_admin", "gestionnaire"):
            return
        if actor.role.code == "admin_familial" and PermissionService.check(
            actor, "payments.manage"
        ):
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")

    def _to_summary(self, payment: Payment) -> PaymentSummary:
        return PaymentSummary(
            id=str(payment.id),
            lease_id=str(payment.lease_id),
            tenant_id=str(payment.tenant_id),
            tenant_name=f"{payment.tenant.first_name} {payment.tenant.last_name}",
            unit_code=payment.lease.unit.code,
            amount=payment.amount,
            payment_method=payment.payment_method,
            payment_date=payment.payment_date,
            reference=payment.reference,
            status=payment.status,
            recorded_by_name=f"{payment.recorder.first_name} {payment.recorder.last_name}",
            created_at=payment.created_at,
            receipt_id=str(payment.receipt.id) if payment.receipt else None,
            receipt_number=payment.receipt.receipt_number if payment.receipt else None,
        )

    def _to_detail(self, payment: Payment) -> PaymentDetail:
        summary = self._to_summary(payment)
        validated_name = None
        if payment.validated_by:
            validator = self.db.query(User).filter(User.id == payment.validated_by).first()
            if validator:
                validated_name = f"{validator.first_name} {validator.last_name}"
        return PaymentDetail(
            **summary.model_dump(),
            proof_url=payment.proof_url,
            notes=payment.notes,
            allocations=[
                PaymentAllocationResponse(
                    period_year=alloc.rent_period.period_year,
                    period_month=alloc.rent_period.period_month,
                    allocated_amount=alloc.allocated_amount,
                )
                for alloc in payment.allocations
            ],
            validated_by_name=validated_name,
            validated_at=payment.validated_at,
            updated_at=payment.updated_at,
        )
