import calendar
import re
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.payment import Receipt, RentPeriod
from app.models.tenant import Lease


class ReceiptNumberService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def next_number(self, year: int | None = None) -> str:
        target_year = year or date.today().year
        prefix = f"REC-{target_year}-"
        pattern = re.compile(rf"^{re.escape(prefix)}(\d{{6}})$")

        numbers = []
        for row in self.db.query(Receipt.receipt_number).all():
            match = pattern.match(row[0])
            if match:
                numbers.append(int(match.group(1)))

        next_seq = max(numbers, default=0) + 1
        return f"{prefix}{next_seq:06d}"


class RentPeriodService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def generate_for_lease(self, lease: Lease, months: int = 12) -> list[RentPeriod]:
        existing = {
            (period.period_year, period.period_month)
            for period in self.db.query(RentPeriod)
            .filter(RentPeriod.lease_id == lease.id)
            .all()
        }

        created: list[RentPeriod] = []
        year = lease.start_date.year
        month = lease.start_date.month

        if lease.end_date:
            total_months = (
                (lease.end_date.year - lease.start_date.year) * 12
                + lease.end_date.month
                - lease.start_date.month
                + 1
            )
            months = max(months, total_months)

        for _ in range(months):
            if (year, month) in existing:
                year, month = self._next_month(year, month)
                continue

            due_day = min(lease.start_date.day, calendar.monthrange(year, month)[1])
            period = RentPeriod(
                lease_id=lease.id,
                period_year=year,
                period_month=month,
                expected_amount=lease.rent_amount,
                paid_amount=Decimal("0"),
                due_date=date(year, month, due_day),
            )
            self.db.add(period)
            created.append(period)
            year, month = self._next_month(year, month)

        if created:
            self.db.flush()
        return created

    def refresh_period_status(self, period: RentPeriod, today: date | None = None) -> None:
        from app.models.enums import RentPeriodStatus

        today = today or date.today()
        if period.paid_amount >= period.expected_amount:
            period.status = RentPeriodStatus.paid
        elif period.paid_amount > 0:
            period.status = RentPeriodStatus.partial
        elif period.due_date < today:
            period.status = RentPeriodStatus.overdue
        else:
            period.status = RentPeriodStatus.pending

    def get_period(
        self, lease_id: UUID, year: int, month: int
    ) -> RentPeriod | None:
        return (
            self.db.query(RentPeriod)
            .filter(
                RentPeriod.lease_id == lease_id,
                RentPeriod.period_year == year,
                RentPeriod.period_month == month,
            )
            .first()
        )

    @staticmethod
    def _next_month(year: int, month: int) -> tuple[int, int]:
        if month == 12:
            return year + 1, 1
        return year, month + 1
