from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.enums import ApprovalRequestStatus
from app.models.user import User
from app.schemas.approval import (
    ApprovalRequestCreate,
    ApprovalRequestDetail,
    ApprovalRequestListResponse,
    ApprovalReviewRequest,
)
from app.services.approval_service import ApprovalService, request_meta

router = APIRouter(prefix="/approval-requests", tags=["approval-requests"])


@router.get("", response_model=ApprovalRequestListResponse)
def list_approval_requests(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: ApprovalRequestStatus | None = None,
) -> ApprovalRequestListResponse:
    return ApprovalService(db).list_requests(
        current_user, page=page, page_size=page_size, status_filter=status
    )


@router.get("/mine", response_model=ApprovalRequestListResponse)
def list_my_approval_requests(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: ApprovalRequestStatus | None = None,
) -> ApprovalRequestListResponse:
    return ApprovalService(db).list_requests(
        current_user, page=page, page_size=page_size, status_filter=status, mine=True
    )


@router.post("", response_model=ApprovalRequestDetail, status_code=201)
def create_approval_request(
    payload: ApprovalRequestCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    http_request: Request,
) -> ApprovalRequestDetail:
    ip, ua = request_meta(http_request)
    return ApprovalService(db).create_request(
        current_user, payload, ip_address=ip, user_agent=ua
    )


@router.get("/{request_id}", response_model=ApprovalRequestDetail)
def get_approval_request(
    request_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApprovalRequestDetail:
    return ApprovalService(db).get_request(current_user, request_id)


@router.post("/{request_id}/approve", response_model=ApprovalRequestDetail)
def approve_request(
    request_id: UUID,
    payload: ApprovalReviewRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    http_request: Request,
) -> ApprovalRequestDetail:
    ip, ua = request_meta(http_request)
    return ApprovalService(db).approve(
        current_user,
        request_id,
        review_comment=payload.review_comment,
        ip_address=ip,
        user_agent=ua,
    )


@router.post("/{request_id}/reject", response_model=ApprovalRequestDetail)
def reject_request(
    request_id: UUID,
    payload: ApprovalReviewRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    http_request: Request,
) -> ApprovalRequestDetail:
    ip, ua = request_meta(http_request)
    return ApprovalService(db).reject(
        current_user,
        request_id,
        review_comment=payload.review_comment,
        ip_address=ip,
        user_agent=ua,
    )


@router.post("/{request_id}/cancel", response_model=ApprovalRequestDetail)
def cancel_request(
    request_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApprovalRequestDetail:
    return ApprovalService(db).cancel(current_user, request_id)
