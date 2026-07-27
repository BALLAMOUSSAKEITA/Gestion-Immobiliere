from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.database import get_db
from app.models.user import User
from app.schemas.payment import PaymentListResponse
from app.schemas.portal import (
    MessageCreate,
    MessageListResponse,
    MessageSummary,
    TenantLeaseInfo,
    TenantNoticeSummary,
    TenantPortalDashboard,
    TenantUnitInfo,
)
from app.schemas.receipt import ReceiptListResponse
from app.schemas.repair import RepairCreate, RepairDetail, RepairListResponse
from app.services.tenant_portal_service import TenantPortalService

router = APIRouter(prefix="/tenant-portal", tags=["tenant-portal"])


@router.get("/dashboard", response_model=TenantPortalDashboard)
def tenant_dashboard(
    current_user: Annotated[User, Depends(require_roles("locataire"))],
    db: Annotated[Session, Depends(get_db)],
) -> TenantPortalDashboard:
    return TenantPortalService(db).get_dashboard(current_user)


@router.get("/my-unit", response_model=TenantUnitInfo)
def tenant_my_unit(
    current_user: Annotated[User, Depends(require_roles("locataire"))],
    db: Annotated[Session, Depends(get_db)],
) -> TenantUnitInfo:
    return TenantPortalService(db).get_my_unit(current_user)


@router.get("/my-lease", response_model=TenantLeaseInfo)
def tenant_my_lease(
    current_user: Annotated[User, Depends(require_roles("locataire"))],
    db: Annotated[Session, Depends(get_db)],
) -> TenantLeaseInfo:
    return TenantPortalService(db).get_my_lease(current_user)


@router.get("/payments", response_model=PaymentListResponse)
def tenant_payments(
    current_user: Annotated[User, Depends(require_roles("locataire"))],
    db: Annotated[Session, Depends(get_db)],
) -> PaymentListResponse:
    return TenantPortalService(db).list_payments(current_user)


@router.get("/receipts", response_model=ReceiptListResponse)
def tenant_receipts(
    current_user: Annotated[User, Depends(require_roles("locataire"))],
    db: Annotated[Session, Depends(get_db)],
) -> ReceiptListResponse:
    return TenantPortalService(db).list_receipts(current_user)


@router.get("/overdues")
def tenant_overdues(
    current_user: Annotated[User, Depends(require_roles("locataire"))],
    db: Annotated[Session, Depends(get_db)],
):
    return TenantPortalService(db).list_overdues(current_user)


@router.get("/repairs", response_model=RepairListResponse)
def tenant_repairs(
    current_user: Annotated[User, Depends(require_roles("locataire"))],
    db: Annotated[Session, Depends(get_db)],
) -> RepairListResponse:
    return TenantPortalService(db).list_repairs(current_user)


@router.post("/repairs", response_model=RepairDetail, status_code=201)
def tenant_create_repair(
    payload: RepairCreate,
    current_user: Annotated[User, Depends(require_roles("locataire"))],
    db: Annotated[Session, Depends(get_db)],
) -> RepairDetail:
    return TenantPortalService(db).create_repair(current_user, payload)


@router.get("/documents")
def tenant_documents(
    current_user: Annotated[User, Depends(require_roles("locataire"))],
    db: Annotated[Session, Depends(get_db)],
):
    return TenantPortalService(db).list_documents(current_user)


@router.get("/notices", response_model=list[TenantNoticeSummary])
def tenant_notices(
    current_user: Annotated[User, Depends(require_roles("locataire"))],
    db: Annotated[Session, Depends(get_db)],
) -> list[TenantNoticeSummary]:
    return TenantPortalService(db).list_notices(current_user)


@router.patch("/notices/{notice_id}/read", response_model=TenantNoticeSummary)
def tenant_mark_notice_read(
    notice_id: UUID,
    current_user: Annotated[User, Depends(require_roles("locataire"))],
    db: Annotated[Session, Depends(get_db)],
) -> TenantNoticeSummary:
    return TenantPortalService(db).mark_notice_read(current_user, notice_id)


@router.get("/messages", response_model=MessageListResponse)
def tenant_messages(
    current_user: Annotated[User, Depends(require_roles("locataire"))],
    db: Annotated[Session, Depends(get_db)],
) -> MessageListResponse:
    return TenantPortalService(db).list_messages(current_user)


@router.post("/messages", response_model=MessageSummary, status_code=201)
def tenant_send_message(
    payload: MessageCreate,
    current_user: Annotated[User, Depends(require_roles("locataire"))],
    db: Annotated[Session, Depends(get_db)],
) -> MessageSummary:
    return TenantPortalService(db).send_message(current_user, payload)
