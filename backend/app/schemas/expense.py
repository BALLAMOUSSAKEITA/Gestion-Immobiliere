from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import ExpenseStatus, PaymentMethod


class ExpenseCategoryResponse(BaseModel):
    id: str
    code: str
    label: str
    is_active: bool


class ExpenseCreate(BaseModel):
    category_id: str
    building_id: str | None = None
    unit_id: str | None = None
    owner_profile_id: str | None = None
    supplier_name: str | None = None
    description: str = Field(min_length=1)
    amount: Decimal = Field(gt=0)
    payment_method: PaymentMethod
    expense_date: date


class ExpenseUpdate(BaseModel):
    category_id: str | None = None
    building_id: str | None = None
    unit_id: str | None = None
    owner_profile_id: str | None = None
    supplier_name: str | None = None
    description: str | None = Field(default=None, min_length=1)
    amount: Decimal | None = Field(default=None, gt=0)
    payment_method: PaymentMethod | None = None
    expense_date: date | None = None


class ExpenseSummaryItem(BaseModel):
    id: str
    category_code: str
    category_label: str
    building_name: str | None
    unit_code: str | None
    supplier_name: str | None
    description: str
    amount: Decimal
    payment_method: PaymentMethod
    expense_date: date
    status: ExpenseStatus
    requires_validation: bool
    recorded_by_name: str
    created_at: datetime


class ExpenseDetail(ExpenseSummaryItem):
    building_id: str | None
    unit_id: str | None
    owner_profile_id: str | None
    receipt_url: str | None
    validated_by_name: str | None
    validated_at: datetime | None
    updated_at: datetime


class ExpenseListResponse(BaseModel):
    items: list[ExpenseSummaryItem]
    total: int
    page: int
    page_size: int
    pages: int


class ExpenseCategoryBreakdown(BaseModel):
    category: str
    amount: Decimal
    count: int


class ExpenseSummaryResponse(BaseModel):
    total_amount: Decimal
    count: int
    by_category: list[ExpenseCategoryBreakdown]
