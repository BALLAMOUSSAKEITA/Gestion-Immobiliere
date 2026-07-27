from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.user import User
from app.schemas.portal import (
    MessageListResponse,
    MessageReplyCreate,
    MessageSummary,
    TenantNoticeCreate,
    TenantNoticeSummary,
    VisitRequestListResponse,
    VisitRequestSummary,
    VisitRequestUpdate,
)
from app.services.message_service import MessageService
from app.services.tenant_portal_service import TenantPortalService
from app.services.visit_request_service import VisitRequestService

router = APIRouter(tags=["portal-management"])


@router.get("/visit-requests", response_model=VisitRequestListResponse)
def list_visit_requests(
    current_user: Annotated[
        User, Depends(require_roles("super_admin", "admin_familial", "gestionnaire"))
    ],
    db: Annotated[Session, Depends(get_db)],
) -> VisitRequestListResponse:
    return VisitRequestService(db).list_requests(current_user)


@router.patch("/visit-requests/{request_id}", response_model=VisitRequestSummary)
def update_visit_request(
    request_id: UUID,
    payload: VisitRequestUpdate,
    current_user: Annotated[
        User, Depends(require_roles("super_admin", "admin_familial", "gestionnaire"))
    ],
    db: Annotated[Session, Depends(get_db)],
) -> VisitRequestSummary:
    return VisitRequestService(db).update_request(current_user, request_id, payload)


@router.get("/messages", response_model=MessageListResponse)
def list_messages(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> MessageListResponse:
    return MessageService(db).list_messages(current_user)


@router.post("/messages/{message_id}/reply", response_model=MessageSummary, status_code=201)
def reply_message(
    message_id: UUID,
    payload: MessageReplyCreate,
    current_user: Annotated[
        User, Depends(require_roles("super_admin", "admin_familial", "gestionnaire"))
    ],
    db: Annotated[Session, Depends(get_db)],
) -> MessageSummary:
    return MessageService(db).reply(current_user, message_id, payload)


@router.patch("/messages/{message_id}/read", response_model=MessageSummary)
def mark_message_read(
    message_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> MessageSummary:
    return MessageService(db).mark_read(current_user, message_id)


@router.post("/tenant-notices", response_model=TenantNoticeSummary, status_code=201)
def publish_tenant_notice(
    payload: TenantNoticeCreate,
    current_user: Annotated[
        User, Depends(require_roles("super_admin", "admin_familial", "gestionnaire"))
    ],
    db: Annotated[Session, Depends(get_db)],
) -> TenantNoticeSummary:
    return TenantPortalService(db).publish_notice(current_user, payload)
