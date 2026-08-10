import logging
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.building import Unit
from app.models.enums import LeaseStatus, OverdueStatus, RentPeriodStatus
from app.models.overdue import OverdueRecord
from app.models.payment import RentPeriod
from app.models.tenant import Lease
from app.services.rent_period_service import RentPeriodService

logger = logging.getLogger(__name__)


class OverdueDetectionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.period_service = RentPeriodService(db)

    def sync_all(self, today: date | None = None) -> int:
        today = today or date.today()
        periods = (
            self.db.query(RentPeriod)
            .join(Lease)
            .filter(Lease.status == LeaseStatus.active)
            .all()
        )
        count = 0
        for period in periods:
            if self._sync_period(period, today):
                count += 1
        self.db.commit()
        return count

    def sync_period(self, period_id: UUID, today: date | None = None) -> None:
        today = today or date.today()
        period = self.db.query(RentPeriod).filter(RentPeriod.id == period_id).first()
        if period:
            self._sync_period(period, today)
            self.db.commit()

    def _sync_period(self, period: RentPeriod, today: date) -> bool:
        lease = (
            self.db.query(Lease)
            .options(joinedload(Lease.unit).joinedload(Unit.building), joinedload(Lease.tenant))
            .filter(Lease.id == period.lease_id)
            .first()
        )
        if lease is None or lease.status != LeaseStatus.active:
            return False

        self.period_service.refresh_period_status(period, today)
        remaining = period.expected_amount - period.paid_amount

        if remaining <= 0:
            self._resolve_record(period)
            return False

        if today <= period.due_date:
            return False

        period.status = RentPeriodStatus.overdue
        days_overdue = (today - period.due_date).days
        status = (
            OverdueStatus.partially_paid
            if period.paid_amount > 0
            else OverdueStatus.open
        )
        record = (
            self.db.query(OverdueRecord)
            .filter(OverdueRecord.rent_period_id == period.id)
            .first()
        )
        if record is None:
            record = OverdueRecord(
                rent_period_id=period.id,
                lease_id=lease.id,
                tenant_id=lease.tenant_id,
                unit_id=lease.unit_id,
                period_year=period.period_year,
                period_month=period.period_month,
                amount_due=period.expected_amount,
                amount_paid=period.paid_amount,
                amount_remaining=remaining,
                days_overdue=days_overdue,
                status=status,
            )
            self.db.add(record)
            self.db.flush()
            if lease.tenant and lease.unit:
                from app.services.notification_hooks import notify_rent_overdue

                amount = f"{remaining:,.0f}".replace(",", " ")
                notify_rent_overdue(self.db, lease.tenant, lease.unit.code, amount)
        else:
            record.amount_paid = period.paid_amount
            record.amount_remaining = remaining
            record.days_overdue = days_overdue
            record.status = status
            if record.status != OverdueStatus.resolved:
                record.resolved_at = None

        return True

    def _resolve_record(self, period: RentPeriod) -> None:
        record = (
            self.db.query(OverdueRecord)
            .filter(OverdueRecord.rent_period_id == period.id)
            .first()
        )
        if record and record.status != OverdueStatus.resolved:
            record.status = OverdueStatus.resolved
            record.amount_paid = period.paid_amount
            record.amount_remaining = Decimal("0")
            record.resolved_at = datetime.now(UTC)
