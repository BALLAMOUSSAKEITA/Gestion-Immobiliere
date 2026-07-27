from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import (
    CreateUserRequest,
    PermissionItem,
    ResetPasswordResponse,
    UpdateUserRequest,
    UserDetailResponse,
    UserListResponse,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UserListResponse)
def list_users(
    _: Annotated[User, Depends(require_roles("super_admin"))],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: str | None = None,
    search: str | None = None,
    is_active: bool | None = None,
) -> UserListResponse:
    return UserService(db).list_users(page, page_size, role, search, is_active)


@router.post("", response_model=UserDetailResponse, status_code=201)
def create_user(
    payload: CreateUserRequest,
    current_user: Annotated[User, Depends(require_roles("super_admin"))],
    db: Annotated[Session, Depends(get_db)],
) -> UserDetailResponse:
    return UserService(db).create_user(payload, current_user)


@router.get("/{user_id}", response_model=UserDetailResponse)
def get_user(
    user_id: UUID,
    _: Annotated[User, Depends(require_roles("super_admin"))],
    db: Annotated[Session, Depends(get_db)],
) -> UserDetailResponse:
    return UserService(db).get_user(user_id)


@router.patch("/{user_id}", response_model=UserDetailResponse)
def update_user(
    user_id: UUID,
    payload: UpdateUserRequest,
    current_user: Annotated[User, Depends(require_roles("super_admin"))],
    db: Annotated[Session, Depends(get_db)],
) -> UserDetailResponse:
    return UserService(db).update_user(user_id, payload, current_user)


@router.delete("/{user_id}", status_code=204)
def deactivate_user(
    user_id: UUID,
    current_user: Annotated[User, Depends(require_roles("super_admin"))],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    UserService(db).deactivate_user(user_id, current_user)


@router.post("/{user_id}/reset-password", response_model=ResetPasswordResponse)
def reset_password(
    user_id: UUID,
    _: Annotated[User, Depends(require_roles("super_admin"))],
    db: Annotated[Session, Depends(get_db)],
) -> ResetPasswordResponse:
    return UserService(db).reset_password(user_id)


@router.get("/{user_id}/permissions", response_model=list[PermissionItem])
def get_permissions(
    user_id: UUID,
    _: Annotated[User, Depends(require_roles("super_admin"))],
    db: Annotated[Session, Depends(get_db)],
) -> list[PermissionItem]:
    return UserService(db).get_permissions(user_id)


@router.put("/{user_id}/permissions", response_model=list[PermissionItem])
def update_permissions(
    user_id: UUID,
    permissions: list[PermissionItem],
    _: Annotated[User, Depends(require_roles("super_admin"))],
    db: Annotated[Session, Depends(get_db)],
) -> list[PermissionItem]:
    return UserService(db).update_permissions(user_id, permissions)
