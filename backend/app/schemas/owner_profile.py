from datetime import datetime

from pydantic import BaseModel, Field


class OwnerProfileCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = None
    email: str | None = None
    notes: str | None = None


class OwnerProfileUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = None
    email: str | None = None
    notes: str | None = None


class OwnerProfileResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    phone: str | None
    email: str | None
    notes: str | None
    user_id: str | None
    created_at: datetime
    updated_at: datetime


class OwnerProfileListResponse(BaseModel):
    items: list[OwnerProfileResponse]
