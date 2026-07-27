from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.portal import (
    MessageSummary,
    PublicContactCreate,
    VisitRequestCreate,
    VisitRequestSummary,
)
from app.schemas.unit import PublicUnitDetail, PublicUnitListResponse
from app.services.message_service import MessageService
from app.services.tenant_portal_service import TenantPortalService
from app.services.unit_service import UnitService
from app.services.visit_request_service import VisitRequestService

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/units", response_model=PublicUnitListResponse)
def list_public_units(
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PublicUnitListResponse:
    return UnitService(db).list_public_units(page=page, page_size=page_size)


@router.get("/units/{unit_id}", response_model=PublicUnitDetail)
def get_public_unit(
    unit_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> PublicUnitDetail:
    return UnitService(db).get_public_unit(unit_id)


@router.post("/visit-requests", response_model=VisitRequestSummary, status_code=201)
def create_visit_request(
    payload: VisitRequestCreate,
    db: Annotated[Session, Depends(get_db)],
) -> VisitRequestSummary:
    return VisitRequestService(db).create_public(payload)


@router.post("/contact", response_model=MessageSummary, status_code=201)
def public_contact(
    payload: PublicContactCreate,
    db: Annotated[Session, Depends(get_db)],
) -> MessageSummary:
    return MessageService(db).create_public_contact(payload)
