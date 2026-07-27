from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
    UserProfileResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    return AuthService(db).login(payload.email, payload.password)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    payload: RefreshRequest, db: Annotated[Session, Depends(get_db)]
) -> TokenResponse:
    return AuthService(db).refresh(payload.refresh_token)


@router.post("/logout", status_code=204)
def logout(
    payload: LogoutRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    AuthService(db).logout(current_user, payload.refresh_token)


@router.get("/me", response_model=UserProfileResponse)
def me(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UserProfileResponse:
    return AuthService(db).get_profile(current_user)


@router.post("/change-password", status_code=204)
def change_password(
    payload: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    AuthService(db).change_password(current_user, payload)
