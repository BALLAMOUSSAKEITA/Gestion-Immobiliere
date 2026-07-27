from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import PaymentMethod, PaymentRecordStatus, RentPeriodStatus


class PeriodAllocationInput(BaseModel):
    period_year: int = Field(ge=2000)
    period_month: int = Field(ge=1, le=12)
    amount: Decimal = Field(gt=0)


class PaymentCreate(BaseModel):
    lease_id: str
    amount: Decimal = Field(gt=0)
    payment_method: PaymentMethod
    payment_date: date
    reference: str | None = None
    notes: str | None = None
    allocations: list[PeriodAllocationInput] = Field(default_factory=list)


class PaymentAllocationResponse(BaseModel):
    period_year: int
    period_month: int
    allocated_amount: Decimal


class PaymentSummary(BaseModel):
    id: str
    lease_id: str
    tenant_id: str
    tenant_name: str
    unit_code: str
    amount: Decimal
    payment_method: PaymentMethod
    payment_date: date
    reference: str | None
    status: PaymentRecordStatus
    recorded_by_name: str
    created_at: datetime
    receipt_id: str | None = None
    receipt_number: str | None = None


class PaymentDetail(PaymentSummary):
    proof_url: str | None
    notes: str | None
    allocations: list[PaymentAllocationResponse]
    validated_by_name: str | None
    validated_at: datetime | None
    updated_at: datetime


class PaymentListResponse(BaseModel):
    items: list[PaymentSummary]
    total: int
    page: int
    page_size: int
    pages: int


class RentPeriodResponse(BaseModel):
    id: str
    period_year: int
    period_month: int
    expected_amount: Decimal
    paid_amount: Decimal
    remaining_amount: Decimal
    status: RentPeriodStatus
    due_date: date
