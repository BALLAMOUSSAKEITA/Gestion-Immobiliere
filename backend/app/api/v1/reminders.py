from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.overdue import ReminderCreate, ReminderListResponse, ReminderResponse
from app.services.overdue_service import ReminderService

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("", response_model=ReminderListResponse)
def list_reminders(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    tenant_id: UUID | None = None,
) -> ReminderListResponse:
    return ReminderService(db).list_reminders(
        current_user, page=page, page_size=page_size, tenant_id=tenant_id
    )


@router.post("", response_model=ReminderResponse, status_code=201)
def send_reminder(
    payload: ReminderCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ReminderResponse:
    return ReminderService(db).send_reminder(current_user, payload)
