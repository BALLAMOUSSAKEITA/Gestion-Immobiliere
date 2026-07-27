from decimal import Decimal

from pydantic import BaseModel


class KpiTrend(BaseModel):
    value: Decimal | int | float
    previous_value: Decimal | int | float | None = None
    change_percent: float | None = None


class DashboardKpis(BaseModel):
    total_buildings: int
    total_apartments: int
    total_shops: int
    occupied_units: int
    free_units: int
    expected_rent_month: Decimal | None = None
    collected_rent_month: Decimal | None = None
    overdue_amount: Decimal
    expenses_month: Decimal | None = None
    net_profit_month: Decimal | None = None
    expiring_leases_count: int
    repairs_in_progress: int
    show_financials: bool = True


class MonthlySeriesPoint(BaseModel):
    label: str
    year: int
    month: int
    revenue: Decimal
    expenses: Decimal
    net_profit: Decimal


class RevenueExpenseChart(BaseModel):
    points: list[MonthlySeriesPoint]


class OccupancyPoint(BaseModel):
    label: str
    year: int
    month: int
    occupancy_rate: float
    occupied: int
    total: int


class OccupancyChart(BaseModel):
    points: list[OccupancyPoint]


class CategorySlice(BaseModel):
    category: str
    amount: Decimal
    count: int


class ExpenseCategoryChart(BaseModel):
    slices: list[CategorySlice]
    total: Decimal


class PaymentMethodSlice(BaseModel):
    method: str
    label: str
    amount: Decimal
    count: int


class PaymentMethodChart(BaseModel):
    slices: list[PaymentMethodSlice]
    total: Decimal


class DashboardAlert(BaseModel):
    type: str
    severity: str
    title: str
    message: str
    entity_id: str | None = None
    href: str | None = None


class DashboardAlerts(BaseModel):
    items: list[DashboardAlert]


class ActivityItem(BaseModel):
    id: str
    user_name: str
    action: str
    entity_type: str
    entity_id: str
    created_at: str


class RecentActivity(BaseModel):
    items: list[ActivityItem]


class OverdueQuickItem(BaseModel):
    tenant_id: str
    tenant_name: str
    unit_code: str
    amount_remaining: Decimal
    days_overdue: int


class OverdueQuickList(BaseModel):
    items: list[OverdueQuickItem]


class ExpiringLeaseItem(BaseModel):
    lease_id: str
    tenant_name: str
    unit_code: str
    building_name: str
    end_date: str
    days_remaining: int


class ExpiringLeasesList(BaseModel):
    items: list[ExpiringLeaseItem]
