import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.schemas.auth import RoleSummary

EMAIL_PATTERN = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
PASSWORD_PATTERN = re.compile(r"^(?=.*[A-Z])(?=.*\d).{8,}$")


class PermissionItem(BaseModel):
    permission_code: str
    granted: bool = True
    scope_type: str | None = "all"
    scope_id: UUID | None = None


class CreateUserRequest(BaseModel):
    email: str
    password: str | None = None
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = None
    role_code: str
    is_active: bool = True
    permissions: list[PermissionItem] = Field(default_factory=list)
    building_ids: list[UUID] = Field(default_factory=list)
    owner_profile_id: UUID | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        email = value.strip().lower()
        if not EMAIL_PATTERN.match(email):
            raise ValueError("Email invalide")
        return email

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not PASSWORD_PATTERN.match(value):
            raise ValueError(
                "Le mot de passe doit contenir au moins 8 caractères, "
                "une majuscule et un chiffre."
            )
        return value


class UpdateUserRequest(BaseModel):
    email: str | None = None
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = None
    role_code: str | None = None
    is_active: bool | None = None
    permissions: list[PermissionItem] | None = None
    building_ids: list[UUID] | None = None
    owner_profile_id: UUID | None = None

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return value
        email = value.strip().lower()
        if not EMAIL_PATTERN.match(email):
            raise ValueError("Email invalide")
        return email


class UserSummaryResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    phone: str | None
    role: RoleSummary
    is_active: bool
    created_at: datetime


class UserDetailResponse(UserSummaryResponse):
    permissions: list[PermissionItem] = Field(default_factory=list)
    building_ids: list[str] = Field(default_factory=list)
    owner_profile_id: str | None = None
    last_login_at: datetime | None = None


class UserListResponse(BaseModel):
    items: list[UserSummaryResponse]
    total: int
    page: int
    page_size: int
    pages: int


class ResetPasswordResponse(BaseModel):
    temporary_password: str
