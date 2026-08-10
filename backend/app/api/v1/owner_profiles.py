from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.user import User
from app.schemas.owner_profile import (
    OwnerProfileCreate,
    OwnerProfileListResponse,
    OwnerProfileResponse,
    OwnerProfileUpdate,
)
from app.services.owner_profile_service import OwnerProfileService

router = APIRouter(prefix="/owner-profiles", tags=["owner-profiles"])


@router.get("", response_model=OwnerProfileListResponse)
def list_owner_profiles(
    _: Annotated[User, Depends(require_roles("super_admin", "admin_familial"))],
    db: Annotated[Session, Depends(get_db)],
) -> OwnerProfileListResponse:
    return OwnerProfileService(db).list_profiles()


@router.post("", response_model=OwnerProfileResponse, status_code=201)
def create_owner_profile(
    payload: OwnerProfileCreate,
    _: Annotated[User, Depends(require_roles("super_admin"))],
    db: Annotated[Session, Depends(get_db)],
) -> OwnerProfileResponse:
    return OwnerProfileService(db).create_profile(payload)


@router.patch("/{profile_id}", response_model=OwnerProfileResponse)
def update_owner_profile(
    profile_id: UUID,
    payload: OwnerProfileUpdate,
    _: Annotated[User, Depends(require_roles("super_admin"))],
    db: Annotated[Session, Depends(get_db)],
) -> OwnerProfileResponse:
    return OwnerProfileService(db).update_profile(profile_id, payload)


@router.delete("/{profile_id}", status_code=204)
def delete_owner_profile(
    profile_id: UUID,
    current_user: Annotated[User, Depends(require_roles("super_admin"))],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    OwnerProfileService(db).delete_profile(current_user, profile_id)
    return Response(status_code=204)
