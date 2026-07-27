import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


PASSWORD_PATTERN = re.compile(r"^(?=.*[A-Z])(?=.*\d).{8,}$")
EMAIL_PATTERN = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


class LoginRequest(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=8)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        email = value.strip().lower()
        if not EMAIL_PATTERN.match(email):
            raise ValueError("Email invalide")
        return email


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if not PASSWORD_PATTERN.match(value):
            raise ValueError(
                "Le mot de passe doit contenir au moins 8 caractères, "
                "une majuscule et un chiffre."
            )
        return value


class RoleSummary(BaseModel):
    code: str
    label: str


class AuthUserSummary(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: AuthUserSummary


class UserProfileResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    phone: str | None
    role: RoleSummary
    is_active: bool
    last_login_at: datetime | None
