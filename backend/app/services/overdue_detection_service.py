import logging
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.building import Unit
from app.models.enums import (
    LeaseStatus,
    OverdueStatus,
    ReminderChannel,
    ReminderStatus,
    ReminderType,
    RentPeriodStatus,
)
from app.models.overdue import OverdueRecord, Reminder
from app.models.payment import RentPeriod
from app.models.tenant import Lease, Tenant
from app.services.rent_period_service import RentPeriodService

logger = logging.getLogger(__name__)

REMINDER_TEMPLATES = {
    ReminderType.before_due: (
        "Bonjour {nom}, votre loyer de {mois} d'un montant de {montant} FCFA "
        "est exigible le {date}. Merci de procéder au règlement."
    ),
    ReminderType.after_due: (
        "Bonjour {nom}, sauf erreur, nous n'avons pas reçu votre loyer de {mois} "
        "({montant} FCFA), en retard de {jours} jours."
    ),
    ReminderType.final_notice: (
        "Bonjour {nom}, malgré nos relances, votre loyer de {mois} reste impayé. "
        "Montant total dû : {total} FCFA. Merci de régulariser sous 7 jours."
    ),
}


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

        if today <= period.due_date and period.status == RentPeriodStatus.pending:
            days_until = (period.due_date - today).days
            if days_until == 3:
                self._create_auto_reminder(
                    period, lease, ReminderType.before_due, today, remaining
                )
            return False

        if today > period.due_date:
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

            if days_overdue == 3:
                self._create_auto_reminder(
                    period, lease, ReminderType.after_due, today, remaining, record
                )
            elif days_overdue == 15:
                total = self._tenant_total_overdue(lease.tenant_id)
                self._create_auto_reminder(
                    period, lease, ReminderType.final_notice, today, remaining, record, total
                )
            return True
        return False

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

    def _tenant_total_overdue(self, tenant_id: UUID) -> Decimal:
        records = (
            self.db.query(OverdueRecord)
            .filter(
                OverdueRecord.tenant_id == tenant_id,
                OverdueRecord.status != OverdueStatus.resolved,
            )
            .all()
        )
        return sum((record.amount_remaining for record in records), Decimal("0"))

    def _create_auto_reminder(
        self,
        period: RentPeriod,
        lease: Lease,
        reminder_type: ReminderType,
        today: date,
        remaining: Decimal,
        record: OverdueRecord | None = None,
        tenant_total: Decimal | None = None,
    ) -> None:
        if record:
            existing = (
                self.db.query(Reminder)
                .filter(
                    Reminder.overdue_record_id == record.id,
                    Reminder.reminder_type == reminder_type,
                )
                .first()
            )
            if existing:
                return

        tenant: Tenant = lease.tenant
        mois = f"{period.period_month:02d}/{period.period_year}"
        montant = f"{remaining:,.0f}".replace(",", " ")
        template = REMINDER_TEMPLATES[reminder_type]
        message = template.format(
            nom=f"{tenant.first_name} {tenant.last_name}",
            mois=mois,
            montant=montant,
            date=period.due_date.isoformat(),
            jours=(today - period.due_date).days if today > period.due_date else 0,
            total=f"{(tenant_total or remaining):,.0f}".replace(",", " "),
        )
        reminder = Reminder(
            tenant_id=tenant.id,
            overdue_record_id=record.id if record else None,
            reminder_type=reminder_type,
            channel=ReminderChannel.in_app,
            message=message,
            status=ReminderStatus.sent,
        )
        self.db.add(reminder)
        logger.info("Relance auto %s pour locataire %s", reminder_type.value, tenant.id)
