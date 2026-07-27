from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.audit import ApprovalRequest, AuditLog
from app.models.building import Building, Unit
from app.models.enums import (
    ApprovalRequestStatus,
    ExpenseStatus,
    LeaseStatus,
    OverdueStatus,
    PaymentRecordStatus,
    RepairStatus,
    UnitStatus,
    UnitType,
)
from app.models.expense import Expense, ExpenseCategory
from app.models.overdue import OverdueRecord
from app.models.payment import Payment, RentPeriod
from app.models.repair import Repair
from app.models.tenant import Lease
from app.models.user import User
from app.schemas.dashboard import (
    ActivityItem,
    CategorySlice,
    DashboardAlert,
    DashboardAlerts,
    DashboardKpis,
    ExpenseCategoryChart,
    ExpiringLeaseItem,
    ExpiringLeasesList,
    MonthlySeriesPoint,
    OccupancyChart,
    OccupancyPoint,
    OverdueQuickItem,
    OverdueQuickList,
    PaymentMethodChart,
    PaymentMethodSlice,
    RecentActivity,
    RevenueExpenseChart,
)
from app.services.building_service import BuildingAccessService

PAYMENT_METHOD_LABELS = {
    "cash": "Espèces",
    "orange_money": "Orange Money",
    "wave": "Wave",
    "bank_transfer": "Virement bancaire",
}

ACTIVE_REPAIR_STATUSES = (
    RepairStatus.new,
    RepairStatus.under_review,
    RepairStatus.technician_assigned,
    RepairStatus.in_progress,
)


class DashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _ensure_access(self, actor: User) -> None:
        if actor.role.code not in (
            "super_admin",
            "admin_familial",
            "proprietaire",
            "gestionnaire",
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé")

    def _show_financials(self, actor: User) -> bool:
        return actor.role.code in ("super_admin", "admin_familial", "proprietaire")

    def _building_ids(
        self,
        actor: User,
        building_id: UUID | None = None,
        owner_profile_id: UUID | None = None,
    ) -> list[UUID] | None:
        allowed = BuildingAccessService.accessible_building_ids(self.db, actor)
        query = self.db.query(Building.id).filter(Building.is_active.is_(True))
        if allowed is not None:
            if not allowed:
                return []
            query = query.filter(Building.id.in_(allowed))
        if building_id:
            BuildingAccessService.ensure_building_access(self.db, actor, building_id)
            query = query.filter(Building.id == building_id)
        if owner_profile_id:
            query = query.filter(Building.owner_profile_id == owner_profile_id)
        return [row[0] for row in query.all()]

    def _units_query(
        self,
        actor: User,
        building_id: UUID | None = None,
        owner_profile_id: UUID | None = None,
    ):
        building_ids = self._building_ids(actor, building_id, owner_profile_id)
        query = self.db.query(Unit).join(Building).filter(Building.is_active.is_(True))
        if building_ids is not None:
            if not building_ids:
                return query.filter(Unit.id.is_(None))
            query = query.filter(Unit.building_id.in_(building_ids))
        return query

    def get_kpis(
        self,
        actor: User,
        *,
        year: int | None = None,
        month: int | None = None,
        building_id: UUID | None = None,
        owner_profile_id: UUID | None = None,
    ) -> DashboardKpis:
        self._ensure_access(actor)
        today = date.today()
        year = year or today.year
        month = month or today.month
        show_financials = self._show_financials(actor)

        building_ids = self._building_ids(actor, building_id, owner_profile_id)
        units_q = self._units_query(actor, building_id, owner_profile_id)

        total_buildings = len(building_ids) if building_ids is not None else (
            self.db.query(func.count(Building.id))
            .filter(Building.is_active.is_(True))
            .scalar()
            or 0
        )

        total_apartments = units_q.filter(Unit.type == UnitType.apartment).count()
        total_shops = units_q.filter(Unit.type == UnitType.shop).count()
        occupied_units = units_q.filter(Unit.status == UnitStatus.occupied).count()
        free_units = units_q.filter(Unit.status == UnitStatus.free).count()

        expected_rent = collected_rent = expenses_month = net_profit = None
        if show_financials:
            expected_rent = self._sum_expected_rent(building_ids, year, month)
            collected_rent = self._sum_collected_rent(building_ids, year, month)
            expenses_month = self._sum_expenses(building_ids, year, month)
            net_profit = collected_rent - expenses_month

        overdue_amount = self._sum_overdues(building_ids)
        expiring_leases_count = self._count_expiring_leases(building_ids, today)
        repairs_in_progress = self._count_repairs_in_progress(building_ids)

        return DashboardKpis(
            total_buildings=total_buildings,
            total_apartments=total_apartments,
            total_shops=total_shops,
            occupied_units=occupied_units,
            free_units=free_units,
            expected_rent_month=expected_rent,
            collected_rent_month=collected_rent,
            overdue_amount=overdue_amount,
            expenses_month=expenses_month,
            net_profit_month=net_profit,
            expiring_leases_count=expiring_leases_count,
            repairs_in_progress=repairs_in_progress,
            show_financials=show_financials,
        )

    def get_revenue_expenses_chart(
        self,
        actor: User,
        *,
        year: int | None = None,
        building_id: UUID | None = None,
        owner_profile_id: UUID | None = None,
    ) -> RevenueExpenseChart:
        self._ensure_access(actor)
        if not self._show_financials(actor):
            return RevenueExpenseChart(points=[])
        today = date.today()
        year = year or today.year
        building_ids = self._building_ids(actor, building_id, owner_profile_id)
        points: list[MonthlySeriesPoint] = []
        for month in range(1, 13):
            revenue = self._sum_collected_rent(building_ids, year, month)
            expenses = self._sum_expenses(building_ids, year, month)
            points.append(
                MonthlySeriesPoint(
                    label=f"{month:02d}/{year}",
                    year=year,
                    month=month,
                    revenue=revenue,
                    expenses=expenses,
                    net_profit=revenue - expenses,
                )
            )
        return RevenueExpenseChart(points=points)

    def get_occupancy_chart(
        self,
        actor: User,
        *,
        year: int | None = None,
        building_id: UUID | None = None,
        owner_profile_id: UUID | None = None,
    ) -> OccupancyChart:
        self._ensure_access(actor)
        today = date.today()
        year = year or today.year
        building_ids = self._building_ids(actor, building_id, owner_profile_id)
        points: list[OccupancyPoint] = []
        for month in range(1, 13):
            total = self._count_units_at_month(building_ids, year, month)
            occupied = self._count_occupied_at_month(building_ids, year, month)
            rate = round((occupied / total * 100) if total else 0, 1)
            points.append(
                OccupancyPoint(
                    label=f"{month:02d}/{year}",
                    year=year,
                    month=month,
                    occupancy_rate=rate,
                    occupied=occupied,
                    total=total,
                )
            )
        return OccupancyChart(points=points)

    def get_expenses_by_category(
        self,
        actor: User,
        *,
        year: int | None = None,
        month: int | None = None,
        building_id: UUID | None = None,
        owner_profile_id: UUID | None = None,
    ) -> ExpenseCategoryChart:
        self._ensure_access(actor)
        if not self._show_financials(actor):
            return ExpenseCategoryChart(slices=[], total=Decimal("0"))
        today = date.today()
        year = year or today.year
        month = month or today.month
        building_ids = self._building_ids(actor, building_id, owner_profile_id)

        query = (
            self.db.query(Expense)
            .join(ExpenseCategory, Expense.category_id == ExpenseCategory.id)
            .filter(Expense.status == ExpenseStatus.validated)
            .filter(func.extract("year", Expense.expense_date) == year)
            .filter(func.extract("month", Expense.expense_date) == month)
        )
        if building_ids is not None:
            if not building_ids:
                return ExpenseCategoryChart(slices=[], total=Decimal("0"))
            query = query.filter(Expense.building_id.in_(building_ids))

        records = query.all()
        buckets: dict[str, CategorySlice] = {}
        total = Decimal("0")
        for record in records:
            label = record.category.label
            if label not in buckets:
                buckets[label] = CategorySlice(category=label, amount=Decimal("0"), count=0)
            buckets[label].amount += record.amount
            buckets[label].count += 1
            total += record.amount
        slices = sorted(buckets.values(), key=lambda item: item.amount, reverse=True)
        return ExpenseCategoryChart(slices=slices, total=total)

    def get_payment_methods(
        self,
        actor: User,
        *,
        year: int | None = None,
        month: int | None = None,
        building_id: UUID | None = None,
        owner_profile_id: UUID | None = None,
    ) -> PaymentMethodChart:
        self._ensure_access(actor)
        if actor.role.code not in ("super_admin", "admin_familial", "proprietaire"):
            return PaymentMethodChart(slices=[], total=Decimal("0"))
        today = date.today()
        year = year or today.year
        month = month or today.month
        building_ids = self._building_ids(actor, building_id, owner_profile_id)

        query = (
            self.db.query(Payment)
            .join(Lease)
            .join(Unit)
            .filter(Payment.status != PaymentRecordStatus.cancelled)
            .filter(func.extract("year", Payment.payment_date) == year)
            .filter(func.extract("month", Payment.payment_date) == month)
        )
        if building_ids is not None:
            if not building_ids:
                return PaymentMethodChart(slices=[], total=Decimal("0"))
            query = query.filter(Unit.building_id.in_(building_ids))

        records = query.all()
        buckets: dict[str, PaymentMethodSlice] = {}
        total = Decimal("0")
        for record in records:
            method = record.payment_method.value
            if method not in buckets:
                buckets[method] = PaymentMethodSlice(
                    method=method,
                    label=PAYMENT_METHOD_LABELS.get(method, method),
                    amount=Decimal("0"),
                    count=0,
                )
            buckets[method].amount += record.amount
            buckets[method].count += 1
            total += record.amount
        slices = sorted(buckets.values(), key=lambda item: item.amount, reverse=True)
        return PaymentMethodChart(slices=slices, total=total)

    def get_alerts(
        self,
        actor: User,
        *,
        building_id: UUID | None = None,
        owner_profile_id: UUID | None = None,
    ) -> DashboardAlerts:
        self._ensure_access(actor)
        building_ids = self._building_ids(actor, building_id, owner_profile_id)
        items: list[DashboardAlert] = []

        overdue_q = (
            self.db.query(OverdueRecord)
            .join(Unit)
            .filter(OverdueRecord.status != OverdueStatus.resolved)
            .filter(OverdueRecord.days_overdue >= 30)
        )
        if building_ids is not None:
            overdue_q = overdue_q.filter(
                Unit.building_id.in_(building_ids) if building_ids else Unit.id.is_(None)
            )
        critical_count = overdue_q.count()
        if critical_count:
            items.append(
                DashboardAlert(
                    type="overdue",
                    severity="high",
                    title="Impayés critiques",
                    message=f"{critical_count} échéance(s) avec plus de 30 jours de retard",
                    href="/dashboard/impayes",
                )
            )

        today = date.today()
        expiring = self._count_expiring_leases(building_ids, today)
        if expiring:
            items.append(
                DashboardAlert(
                    type="lease",
                    severity="medium",
                    title="Baux expirants",
                    message=f"{expiring} bail(aux) expire(nt) dans les 30 prochains jours",
                    href="/dashboard/baux",
                )
            )

        if actor.role.code in ("super_admin", "admin_familial"):
            pending_expenses = (
                self.db.query(func.count(Expense.id))
                .filter(Expense.status == ExpenseStatus.pending_validation)
                .scalar()
                or 0
            )
            if pending_expenses:
                items.append(
                    DashboardAlert(
                        type="expense",
                        severity="medium",
                        title="Dépenses à valider",
                        message=f"{pending_expenses} dépense(s) en attente de validation",
                        href="/dashboard/depenses/validation",
                    )
                )
            pending_approvals = (
                self.db.query(func.count(ApprovalRequest.id))
                .filter(ApprovalRequest.status == ApprovalRequestStatus.pending)
                .scalar()
                or 0
            )
            if pending_approvals:
                items.append(
                    DashboardAlert(
                        type="approval",
                        severity="low",
                        title="Validations en attente",
                        message=f"{pending_approvals} demande(s) à traiter",
                        href="/dashboard/validations",
                    )
                )

        return DashboardAlerts(items=items)

    def get_recent_activity(self, actor: User, limit: int = 10) -> RecentActivity:
        self._ensure_access(actor)
        if actor.role.code not in ("super_admin", "admin_familial"):
            return RecentActivity(items=[])
        logs = (
            self.db.query(AuditLog)
            .options(joinedload(AuditLog.user))
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
        return RecentActivity(
            items=[
                ActivityItem(
                    id=str(log.id),
                    user_name=f"{log.user.first_name} {log.user.last_name}",
                    action=log.action,
                    entity_type=log.entity_type,
                    entity_id=str(log.entity_id),
                    created_at=log.created_at.isoformat(),
                )
                for log in logs
            ]
        )

    def get_top_overdues(
        self,
        actor: User,
        *,
        limit: int = 10,
        building_id: UUID | None = None,
        owner_profile_id: UUID | None = None,
    ) -> OverdueQuickList:
        self._ensure_access(actor)
        building_ids = self._building_ids(actor, building_id, owner_profile_id)
        query = (
            self.db.query(OverdueRecord, Unit)
            .join(Unit, OverdueRecord.unit_id == Unit.id)
            .options(joinedload(OverdueRecord.tenant))
            .filter(OverdueRecord.status != OverdueStatus.resolved)
            .order_by(OverdueRecord.amount_remaining.desc())
        )
        if building_ids is not None:
            query = query.filter(
                Unit.building_id.in_(building_ids) if building_ids else Unit.id.is_(None)
            )
        records = query.limit(limit).all()
        return OverdueQuickList(
            items=[
                OverdueQuickItem(
                    tenant_id=str(record.tenant_id),
                    tenant_name=f"{record.tenant.first_name} {record.tenant.last_name}",
                    unit_code=unit.code,
                    amount_remaining=record.amount_remaining,
                    days_overdue=record.days_overdue,
                )
                for record, unit in records
            ]
        )

    def get_expiring_leases(
        self,
        actor: User,
        *,
        days: int = 30,
        building_id: UUID | None = None,
        owner_profile_id: UUID | None = None,
    ) -> ExpiringLeasesList:
        self._ensure_access(actor)
        building_ids = self._building_ids(actor, building_id, owner_profile_id)
        today = date.today()
        deadline = today + timedelta(days=days)
        query = (
            self.db.query(Lease)
            .join(Unit)
            .join(Building)
            .options(
                joinedload(Lease.tenant),
                joinedload(Lease.unit).joinedload(Unit.building),
            )
            .filter(Lease.status == LeaseStatus.active)
            .filter(Lease.end_date.isnot(None))
            .filter(Lease.end_date <= deadline)
            .order_by(Lease.end_date.asc())
        )
        if building_ids is not None:
            query = query.filter(
                Unit.building_id.in_(building_ids) if building_ids else Unit.id.is_(None)
            )
        leases = query.limit(10).all()
        items = []
        for lease in leases:
            end_date = lease.end_date
            assert end_date is not None
            items.append(
                ExpiringLeaseItem(
                    lease_id=str(lease.id),
                    tenant_name=f"{lease.tenant.first_name} {lease.tenant.last_name}",
                    unit_code=lease.unit.code,
                    building_name=lease.unit.building.name,
                    end_date=end_date.isoformat(),
                    days_remaining=max((end_date - today).days, 0),
                )
            )
        return ExpiringLeasesList(items=items)

    def _sum_expected_rent(
        self, building_ids: list[UUID] | None, year: int, month: int
    ) -> Decimal:
        query = self.db.query(func.coalesce(func.sum(RentPeriod.expected_amount), 0)).join(
            Lease
        ).join(Unit)
        query = query.filter(RentPeriod.period_year == year, RentPeriod.period_month == month)
        if building_ids is not None:
            if not building_ids:
                return Decimal("0")
            query = query.filter(Unit.building_id.in_(building_ids))
        return Decimal(str(query.scalar() or 0))

    def _sum_collected_rent(
        self, building_ids: list[UUID] | None, year: int, month: int
    ) -> Decimal:
        query = (
            self.db.query(func.coalesce(func.sum(Payment.amount), 0))
            .join(Lease)
            .join(Unit)
            .filter(Payment.status != PaymentRecordStatus.cancelled)
            .filter(func.extract("year", Payment.payment_date) == year)
            .filter(func.extract("month", Payment.payment_date) == month)
        )
        if building_ids is not None:
            if not building_ids:
                return Decimal("0")
            query = query.filter(Unit.building_id.in_(building_ids))
        return Decimal(str(query.scalar() or 0))

    def _sum_expenses(
        self, building_ids: list[UUID] | None, year: int, month: int
    ) -> Decimal:
        query = (
            self.db.query(func.coalesce(func.sum(Expense.amount), 0))
            .filter(Expense.status == ExpenseStatus.validated)
            .filter(func.extract("year", Expense.expense_date) == year)
            .filter(func.extract("month", Expense.expense_date) == month)
        )
        if building_ids is not None:
            if not building_ids:
                return Decimal("0")
            query = query.filter(Expense.building_id.in_(building_ids))
        return Decimal(str(query.scalar() or 0))

    def _sum_overdues(self, building_ids: list[UUID] | None) -> Decimal:
        query = (
            self.db.query(func.coalesce(func.sum(OverdueRecord.amount_remaining), 0))
            .join(Unit)
            .filter(OverdueRecord.status != OverdueStatus.resolved)
        )
        if building_ids is not None:
            if not building_ids:
                return Decimal("0")
            query = query.filter(Unit.building_id.in_(building_ids))
        return Decimal(str(query.scalar() or 0))

    def _count_expiring_leases(self, building_ids: list[UUID] | None, today: date) -> int:
        deadline = today + timedelta(days=30)
        query = (
            self.db.query(func.count(Lease.id))
            .join(Unit)
            .filter(Lease.status == LeaseStatus.active)
            .filter(Lease.end_date.isnot(None))
            .filter(Lease.end_date <= deadline)
        )
        if building_ids is not None:
            if not building_ids:
                return 0
            query = query.filter(Unit.building_id.in_(building_ids))
        return query.scalar() or 0

    def _count_repairs_in_progress(self, building_ids: list[UUID] | None) -> int:
        query = (
            self.db.query(func.count(Repair.id))
            .join(Unit)
            .filter(Repair.status.in_(ACTIVE_REPAIR_STATUSES))
        )
        if building_ids is not None:
            if not building_ids:
                return 0
            query = query.filter(Unit.building_id.in_(building_ids))
        return query.scalar() or 0

    def _count_units_at_month(
        self, building_ids: list[UUID] | None, year: int, month: int
    ) -> int:
        _ = monthrange(year, month)
        query = self.db.query(func.count(Unit.id)).join(Building).filter(
            Building.is_active.is_(True)
        )
        if building_ids is not None:
            if not building_ids:
                return 0
            query = query.filter(Unit.building_id.in_(building_ids))
        return query.scalar() or 0

    def _count_occupied_at_month(
        self, building_ids: list[UUID] | None, year: int, month: int
    ) -> int:
        _ = (year, month)
        query = self.db.query(func.count(Unit.id)).join(Building).filter(
            Building.is_active.is_(True),
            Unit.status == UnitStatus.occupied,
        )
        if building_ids is not None:
            if not building_ids:
                return 0
            query = query.filter(Unit.building_id.in_(building_ids))
        return query.scalar() or 0

    def collect_report_data(
        self,
        actor: User,
        *,
        period_start: date,
        period_end: date,
        building_id: UUID | None = None,
        owner_profile_id: UUID | None = None,
    ) -> dict:
        year = period_start.year
        month = period_start.month
        kpis = self.get_kpis(
            actor,
            year=year,
            month=month,
            building_id=building_id,
            owner_profile_id=owner_profile_id,
        )
        revenue_chart = self.get_revenue_expenses_chart(
            actor, year=year, building_id=building_id, owner_profile_id=owner_profile_id
        )
        return {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "kpis": kpis.model_dump(mode="json"),
            "revenue_expenses": [p.model_dump(mode="json") for p in revenue_chart.points],
            "top_overdues": self.get_top_overdues(
                actor, building_id=building_id, owner_profile_id=owner_profile_id
            ).model_dump(mode="json"),
            "expiring_leases": self.get_expiring_leases(
                actor, building_id=building_id, owner_profile_id=owner_profile_id
            ).model_dump(mode="json"),
            "expenses_by_category": self.get_expenses_by_category(
                actor,
                year=year,
                month=month,
                building_id=building_id,
                owner_profile_id=owner_profile_id,
            ).model_dump(mode="json"),
        }
