from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.audit import AuditLogDetail, AuditLogListResponse, AuditLogSummary
from app.services.approval_service import AuditLogService

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("", response_model=AuditLogListResponse)
def list_audit_logs(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user_id: UUID | None = None,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    action: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> AuditLogListResponse:
    return AuditLogService(db).list_logs(
        current_user,
        page=page,
        page_size=page_size,
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/entity/{entity_type}/{entity_id}", response_model=list[AuditLogSummary])
def list_entity_audit_logs(
    entity_type: str,
    entity_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[AuditLogSummary]:
    return AuditLogService(db).list_entity_logs(current_user, entity_type, entity_id)


@router.get("/{log_id}", response_model=AuditLogDetail)
def get_audit_log(
    log_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AuditLogDetail:
    return AuditLogService(db).get_log(current_user, log_id)
