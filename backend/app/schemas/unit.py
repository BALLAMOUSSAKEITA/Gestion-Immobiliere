from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import UnitStatus, UnitType


class UnitCreate(BaseModel):
    type: UnitType
    number: str = Field(min_length=1, max_length=20)
    floor: int | None = Field(default=None, ge=0)
    rent_amount: Decimal = Field(gt=0)
    deposit_amount: Decimal = Field(default=Decimal("0"), ge=0)
    status: UnitStatus = UnitStatus.free
    description: str | None = None
    is_public_listing: bool = False


class UnitUpdate(BaseModel):
    rent_amount: Decimal | None = Field(default=None, gt=0)
    deposit_amount: Decimal | None = Field(default=None, ge=0)
    status: UnitStatus | None = None
    description: str | None = None
    is_public_listing: bool | None = None
    is_active: bool | None = None


class UnitPhotoResponse(BaseModel):
    id: str
    url: str
    is_primary: bool
    sort_order: int
    uploaded_at: datetime


class UnitSummary(BaseModel):
    id: str
    building_id: str
    code: str
    type: UnitType
    number: str
    floor: int | None
    rent_amount: Decimal
    deposit_amount: Decimal
    status: UnitStatus
    is_public_listing: bool
    is_active: bool
    building_code: str | None = None
    building_name: str | None = None
    commune: str | None = None
    quartier: str | None = None


class UnitDetail(UnitSummary):
    description: str | None
    photos: list[UnitPhotoResponse]
    created_at: datetime
    updated_at: datetime


class UnitListResponse(BaseModel):
    items: list[UnitSummary]
    total: int
    page: int
    page_size: int
    pages: int


class UnitHistoryItem(BaseModel):
    id: str
    tenant_id: str | None
    tenant_name: str | None = None
    entry_date: date
    exit_date: date | None
    rent_amount: Decimal
    notes: str | None


class PublicUnitSummary(BaseModel):
    id: str
    code: str
    type: UnitType
    rent_amount: Decimal
    deposit_amount: Decimal
    description: str | None
    commune: str
    quartier: str | None
    primary_photo_url: str | None


class PublicUnitDetail(PublicUnitSummary):
    photos: list[UnitPhotoResponse]


class PublicUnitListResponse(BaseModel):
    items: list[PublicUnitSummary]
    total: int
    page: int
    page_size: int
    pages: int
