from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.unit import PublicUnitDetail, PublicUnitListResponse
from app.services.unit_service import UnitService

router = APIRouter(prefix="/public/units", tags=["public"])


@router.get("", response_model=PublicUnitListResponse)
def list_public_units(
    db: Session = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PublicUnitListResponse:
    return UnitService(db).list_public_units(page=page, page_size=page_size)


@router.get("/{unit_id}", response_model=PublicUnitDetail)
def get_public_unit(unit_id: UUID, db: Session = Depends(get_db)) -> PublicUnitDetail:
    return UnitService(db).get_public_unit(unit_id)
