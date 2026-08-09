from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.enums import UnitStatus, UnitType
from app.models.user import User
from app.schemas.lease import LeaseDetail
from app.schemas.unit import (
    UnitDetail,
    UnitHistoryItem,
    UnitListResponse,
    UnitPhotoResponse,
    UnitRelease,
    UnitUpdate,
)
from app.services.unit_service import UnitService

router = APIRouter(prefix="/units", tags=["units"])


@router.get("", response_model=UnitListResponse)
def list_units(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    building_id: UUID | None = None,
    type: UnitType | None = None,
    status: UnitStatus | None = None,
    owner_profile_id: UUID | None = None,
    search: str | None = None,
) -> UnitListResponse:
    return UnitService(db).list_units(
        current_user,
        page=page,
        page_size=page_size,
        building_id=building_id,
        unit_type=type,
        status_filter=status,
        owner_profile_id=owner_profile_id,
        search=search,
    )


@router.get("/{unit_id}", response_model=UnitDetail)
def get_unit(
    unit_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UnitDetail:
    return UnitService(db).get_unit(current_user, unit_id)


@router.patch("/{unit_id}", response_model=UnitDetail)
def update_unit(
    unit_id: UUID,
    payload: UnitUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UnitDetail:
    return UnitService(db).update_unit(current_user, unit_id, payload)


@router.delete("/{unit_id}", status_code=204)
def delete_unit(
    unit_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    UnitService(db).deactivate_unit(current_user, unit_id)


@router.post("/{unit_id}/release", response_model=LeaseDetail)
def release_unit(
    unit_id: UUID,
    payload: UnitRelease,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> LeaseDetail:
    return UnitService(db).release_unit(current_user, unit_id, payload)


@router.post("/{unit_id}/photos", response_model=UnitPhotoResponse)
def upload_unit_photo(
    unit_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
) -> UnitPhotoResponse:
    return UnitService(db).upload_photo(current_user, unit_id, file)


@router.delete("/{unit_id}/photos/{photo_id}", status_code=204)
def delete_unit_photo(
    unit_id: UUID,
    photo_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    UnitService(db).delete_photo(current_user, unit_id, photo_id)


@router.get("/{unit_id}/history", response_model=list[UnitHistoryItem])
def get_unit_history(
    unit_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[UnitHistoryItem]:
    return UnitService(db).get_history(current_user, unit_id)


@router.get("/{unit_id}/documents")
def list_unit_documents(
    unit_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    from app.models.enums import EntityType
    from app.services.document_service import DocumentService

    return DocumentService(db).list_documents(
        current_user,
        page=page,
        page_size=page_size,
        entity_type=EntityType.unit,
        entity_id=unit_id,
    )
