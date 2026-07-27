from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import LeaseStatus


class LeaseCreate(BaseModel):
    tenant_id: str
    unit_id: str
    start_date: date
    end_date: date | None = None
    rent_amount: Decimal = Field(gt=0)
    deposit_amount: Decimal = Field(default=Decimal("0"), ge=0)
    deposit_paid: bool = False


class LeaseUpdate(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    deposit_paid: bool | None = None


class LeaseTerminate(BaseModel):
    termination_date: date
    termination_reason: str = Field(min_length=1)


class LeaseRentUpdate(BaseModel):
    rent_amount: Decimal = Field(gt=0)
    effective_date: date
    reason: str | None = None


class LeaseSummary(BaseModel):
    id: str
    tenant_id: str
    tenant_name: str
    unit_id: str
    unit_code: str
    building_name: str
    start_date: date
    end_date: date | None
    rent_amount: Decimal
    deposit_amount: Decimal
    deposit_paid: bool
    status: LeaseStatus
    created_at: datetime


class LeaseDetail(LeaseSummary):
    contract_document_url: str | None
    termination_date: date | None
    termination_reason: str | None
    updated_at: datetime


class LeaseListResponse(BaseModel):
    items: list[LeaseSummary]
    total: int
    page: int
    page_size: int
    pages: int


class RentHistoryItem(BaseModel):
    id: str
    old_rent_amount: Decimal
    new_rent_amount: Decimal
    effective_date: date
    changed_at: datetime
    reason: str | None
