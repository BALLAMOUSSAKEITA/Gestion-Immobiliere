import shutil
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.building import (
    BuildingCreate,
    BuildingDetail,
    BuildingListResponse,
    BuildingUpdate,
)
from app.schemas.unit import UnitCreate, UnitDetail, UnitListResponse
from app.services.building_service import BuildingService
from app.services.unit_service import UnitService

router = APIRouter(prefix="/buildings", tags=["buildings"])


@router.get("", response_model=BuildingListResponse)
def list_buildings(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    is_active: bool | None = True,
) -> BuildingListResponse:
    return BuildingService(db).list_buildings(
        current_user, page=page, page_size=page_size, search=search, is_active=is_active
    )


@router.post("", response_model=BuildingDetail, status_code=201)
def create_building(
    payload: BuildingCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> BuildingDetail:
    return BuildingService(db).create_building(current_user, payload)


@router.get("/{building_id}", response_model=BuildingDetail)
def get_building(
    building_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> BuildingDetail:
    return BuildingService(db).get_building(current_user, building_id)


@router.patch("/{building_id}", response_model=BuildingDetail)
def update_building(
    building_id: UUID,
    payload: BuildingUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> BuildingDetail:
    return BuildingService(db).update_building(current_user, building_id, payload)


@router.delete("/{building_id}", status_code=204)
def delete_building(
    building_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    BuildingService(db).deactivate_building(current_user, building_id)


@router.get("/{building_id}/units", response_model=UnitListResponse)
def list_building_units(
    building_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
) -> UnitListResponse:
    return UnitService(db).list_units(
        current_user, page=page, page_size=page_size, building_id=building_id
    )


@router.post("/{building_id}/units", response_model=UnitDetail, status_code=201)
def create_building_unit(
    building_id: UUID,
    payload: UnitCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UnitDetail:
    return UnitService(db).create_unit(current_user, building_id, payload)


@router.post("/{building_id}/photo", response_model=BuildingDetail)
def upload_building_photo(
    building_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
) -> BuildingDetail:
    settings = get_settings()
    extension = Path(file.filename or "photo.jpg").suffix.lower() or ".jpg"
    filename = f"{uuid4()}{extension}"
    target_dir = Path(settings.upload_dir) / "buildings"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / filename
    with target_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    photo_url = f"/uploads/buildings/{filename}"
    return BuildingService(db).set_photo_url(current_user, building_id, photo_url)
