from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import OverdueStatus


class TenantBrief(BaseModel):
    id: str
    full_name: str
    phone: str


class OverdueItem(BaseModel):
    id: str
    tenant: TenantBrief
    unit_code: str
    building_name: str
    period: str
    period_year: int
    period_month: int
    amount_due: Decimal
    amount_paid: Decimal
    amount_remaining: Decimal
    days_overdue: int
    status: OverdueStatus
    tenant_total_overdue: Decimal


class OverdueSummary(BaseModel):
    total_overdue_amount: Decimal
    total_tenants_affected: int
    total_periods_overdue: int


class OverdueListResponse(BaseModel):
    items: list[OverdueItem]
    summary: OverdueSummary
    total: int
    page: int
    page_size: int
    pages: int


class TenantOverdueSummary(BaseModel):
    tenant_id: str
    tenant_name: str
    phone: str
    total_overdue_amount: Decimal
    overdue_months_count: int
    oldest_overdue_days: int


class TenantOverdueListResponse(BaseModel):
    items: list[TenantOverdueSummary]
