from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.enums import RepairStatus, UrgencyLevel
from app.models.user import User
from app.schemas.repair import (
    RepairCancel,
    RepairComplete,
    RepairCreate,
    RepairDetail,
    RepairHistoryItem,
    RepairListResponse,
    RepairStatusUpdate,
    RepairSummaryStats,
    RepairUpdate,
)
from app.services.repair_service import RepairService

router = APIRouter(prefix="/repairs", tags=["repairs"])


@router.get("", response_model=RepairListResponse)
def list_repairs(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    building_id: UUID | None = None,
    unit_id: UUID | None = None,
    status: RepairStatus | None = None,
    urgency: UrgencyLevel | None = None,
    assigned_to: UUID | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> RepairListResponse:
    from datetime import date as date_type

    return RepairService(db).list_repairs(
        current_user,
        page=page,
        page_size=page_size,
        building_id=building_id,
        unit_id=unit_id,
        status_filter=status,
        urgency=urgency,
        assigned_to=assigned_to,
        date_from=date_type.fromisoformat(date_from) if date_from else None,
        date_to=date_type.fromisoformat(date_to) if date_to else None,
    )


@router.get("/summary", response_model=RepairSummaryStats)
def get_repairs_summary(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RepairSummaryStats:
    return RepairService(db).get_summary(current_user)


@router.post("", response_model=RepairDetail, status_code=201)
def create_repair(
    payload: RepairCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RepairDetail:
    return RepairService(db).create_repair(current_user, payload)


@router.get("/{repair_id}", response_model=RepairDetail)
def get_repair(
    repair_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RepairDetail:
    return RepairService(db).get_repair(current_user, repair_id)


@router.patch("/{repair_id}", response_model=RepairDetail)
def update_repair(
    repair_id: UUID,
    payload: RepairUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RepairDetail:
    return RepairService(db).update_repair(current_user, repair_id, payload)


@router.patch("/{repair_id}/status", response_model=RepairDetail)
def update_repair_status(
    repair_id: UUID,
    payload: RepairStatusUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RepairDetail:
    return RepairService(db).update_status(current_user, repair_id, payload)


@router.post("/{repair_id}/attachments", response_model=RepairDetail)
def upload_repair_attachment(
    repair_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
) -> RepairDetail:
    return RepairService(db).upload_attachment(current_user, repair_id, file)


@router.post("/{repair_id}/complete", response_model=RepairDetail)
def complete_repair(
    repair_id: UUID,
    payload: RepairComplete,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RepairDetail:
    return RepairService(db).complete_repair(current_user, repair_id, payload)


@router.post("/{repair_id}/cancel", response_model=RepairDetail)
def cancel_repair(
    repair_id: UUID,
    payload: RepairCancel,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> RepairDetail:
    return RepairService(db).cancel_repair(current_user, repair_id, payload)


@router.get("/{repair_id}/history", response_model=list[RepairHistoryItem])
def get_repair_history(
    repair_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[RepairHistoryItem]:
    return RepairService(db).get_history(current_user, repair_id)
