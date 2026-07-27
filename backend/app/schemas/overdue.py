from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import OverdueStatus, ReminderChannel, ReminderType


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
    reminders_count: int
    last_reminder_at: datetime | None
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
    last_reminder_at: datetime | None


class TenantOverdueListResponse(BaseModel):
    items: list[TenantOverdueSummary]


class ReminderCreate(BaseModel):
    tenant_id: str
    overdue_record_ids: list[str] = Field(default_factory=list)
    reminder_type: ReminderType = ReminderType.manual
    channel: ReminderChannel = ReminderChannel.email
    message: str = Field(min_length=1)


class ReminderResponse(BaseModel):
    id: str
    tenant_id: str
    tenant_name: str
    overdue_record_id: str | None
    reminder_type: ReminderType
    channel: ReminderChannel
    message: str
    sent_at: datetime
    sent_by_name: str | None
    status: str


class ReminderListResponse(BaseModel):
    items: list[ReminderResponse]
    total: int
    page: int
    page_size: int
    pages: int
