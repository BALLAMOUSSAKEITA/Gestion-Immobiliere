from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import PaymentMethod, RepairStatus, UrgencyLevel


class RepairCreate(BaseModel):
    unit_id: str | None = None
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    urgency: UrgencyLevel = UrgencyLevel.medium


class RepairUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1)
    urgency: UrgencyLevel | None = None
    estimated_cost: Decimal | None = Field(default=None, ge=0)
    assigned_to: str | None = None
    notes: str | None = None


class RepairStatusUpdate(BaseModel):
    status: RepairStatus
    comment: str | None = None
    assigned_to: str | None = None


class RepairCancel(BaseModel):
    cancellation_reason: str = Field(min_length=1)


class RepairComplete(BaseModel):
    final_cost: Decimal = Field(gt=0)
    create_expense: bool = True
    expense_category_id: str | None = None
    payment_method: PaymentMethod = PaymentMethod.cash
    notes: str | None = None


class RepairAttachmentResponse(BaseModel):
    id: str
    file_url: str
    file_type: str
    uploaded_by_name: str
    uploaded_at: datetime


class RepairHistoryItem(BaseModel):
    id: str
    old_status: str | None
    new_status: str
    changed_by_name: str
    changed_at: datetime
    comment: str | None


class RepairSummaryItem(BaseModel):
    id: str
    title: str
    unit_code: str
    building_name: str
    urgency: UrgencyLevel
    status: RepairStatus
    reported_by_name: str
    assigned_to_name: str | None
    reported_at: datetime
    final_cost: Decimal | None


class RepairDetail(RepairSummaryItem):
    unit_id: str
    building_id: str
    description: str
    estimated_cost: Decimal | None
    expense_id: str | None
    started_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    cancellation_reason: str | None
    notes: str | None
    attachments: list[RepairAttachmentResponse]
    updated_at: datetime


class RepairListResponse(BaseModel):
    items: list[RepairSummaryItem]
    total: int
    page: int
    page_size: int
    pages: int


class RepairSummaryStats(BaseModel):
    in_progress_count: int
    urgent_count: int
    completed_this_month: int
