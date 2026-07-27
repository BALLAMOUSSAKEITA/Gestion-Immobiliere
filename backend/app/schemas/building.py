from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import UnitStatus, UnitType


class BuildingCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    address: str = Field(min_length=1)
    commune: str = Field(min_length=1, max_length=100)
    quartier: str | None = Field(default=None, max_length=100)
    floor_count: int = Field(default=0, ge=0)
    owner_profile_id: str | None = None
    manager_user_id: str | None = None
    observations: str | None = None


class BuildingUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    address: str | None = Field(default=None, min_length=1)
    commune: str | None = Field(default=None, min_length=1, max_length=100)
    quartier: str | None = None
    floor_count: int | None = Field(default=None, ge=0)
    owner_profile_id: str | None = None
    manager_user_id: str | None = None
    observations: str | None = None
    is_active: bool | None = None


class BuildingSummary(BaseModel):
    id: str
    code: str
    name: str
    address: str
    commune: str
    quartier: str | None
    photo_url: str | None
    floor_count: int
    apartment_count: int
    shop_count: int
    owner_profile_id: str | None
    manager_user_id: str | None
    is_active: bool
    created_at: datetime


class BuildingDetail(BuildingSummary):
    observations: str | None
    total_units: int
    occupied_units: int
    free_units: int
    under_repair_units: int
    occupancy_rate: float
    monthly_expected_rent: Decimal
    updated_at: datetime


class BuildingListResponse(BaseModel):
    items: list[BuildingSummary]
    total: int
    page: int
    page_size: int
    pages: int
