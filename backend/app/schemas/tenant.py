from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import IdDocumentType, PaymentMethod


class TenantCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone_primary: str = Field(min_length=1, max_length=20)
    phone_secondary: str | None = None
    profession: str | None = None
    previous_address: str | None = None
    id_document_type: IdDocumentType
    id_document_number: str = Field(min_length=1, max_length=50)
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    payment_method: PaymentMethod | None = None
    observations: str | None = None


class TenantUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone_primary: str | None = Field(default=None, min_length=1, max_length=20)
    phone_secondary: str | None = None
    profession: str | None = None
    previous_address: str | None = None
    id_document_type: IdDocumentType | None = None
    id_document_number: str | None = Field(default=None, min_length=1, max_length=50)
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    payment_method: PaymentMethod | None = None
    observations: str | None = None
    is_active: bool | None = None


class CurrentLeaseSummary(BaseModel):
    id: str
    unit_code: str
    building_name: str
    rent_amount: Decimal
    start_date: date
    status: str


class PaymentSummary(BaseModel):
    total_paid: Decimal = Decimal("0")
    total_unpaid: Decimal = Decimal("0")


class TenantSummary(BaseModel):
    id: str
    first_name: str
    last_name: str
    phone_primary: str
    profession: str | None
    is_active: bool
    has_active_lease: bool
    current_unit_code: str | None = None
    created_at: datetime


class TenantDetail(TenantSummary):
    phone_secondary: str | None
    previous_address: str | None
    id_document_type: IdDocumentType
    id_document_number: str
    id_document_url: str | None
    photo_url: str | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    payment_method: PaymentMethod | None
    observations: str | None
    user_id: str | None
    current_lease: CurrentLeaseSummary | None = None
    payment_summary: PaymentSummary
    updated_at: datetime


class TenantListResponse(BaseModel):
    items: list[TenantSummary]
    total: int
    page: int
    page_size: int
    pages: int


class CreateTenantAccountRequest(BaseModel):
    email: str
    password: str | None = None


class CreateTenantAccountResponse(BaseModel):
    user_id: str
    email: str
    temporary_password: str | None = None
