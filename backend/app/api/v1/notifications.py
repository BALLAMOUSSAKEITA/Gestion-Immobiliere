from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationPreferencesResponse,
    NotificationPreferencesUpdateRequest,
    NotificationSummary,
    UnreadCountResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])
preferences_router = APIRouter(prefix="/notification-preferences", tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=50, ge=1, le=100),
    unread_only: bool = False,
) -> NotificationListResponse:
    return NotificationService(db).list_notifications(
        current_user.id, limit=limit, unread_only=unread_only
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
def unread_count(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UnreadCountResponse:
    return UnreadCountResponse(count=NotificationService(db).get_unread_count(current_user.id))


@router.patch("/{notification_id}/read", response_model=NotificationSummary)
def mark_notification_read(
    notification_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> NotificationSummary:
    return NotificationService(db).mark_read(current_user.id, notification_id)


@router.post("/read-all")
def mark_all_read(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    count = NotificationService(db).mark_all_read(current_user.id)
    return {"marked": count}


@preferences_router.get("", response_model=NotificationPreferencesResponse)
def get_preferences(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> NotificationPreferencesResponse:
    return NotificationService(db).get_preferences(current_user.id)


@preferences_router.put("", response_model=NotificationPreferencesResponse)
def update_preferences(
    payload: NotificationPreferencesUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> NotificationPreferencesResponse:
    updates = [item.model_dump(exclude_none=True) for item in payload.preferences]
    return NotificationService(db).update_preferences(current_user.id, updates)
