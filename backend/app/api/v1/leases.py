from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.enums import LeaseStatus
from app.models.user import User
from app.schemas.lease import (
    LeaseCreate,
    LeaseDetail,
    LeaseListResponse,
    LeaseRentUpdate,
    LeaseTerminate,
    LeaseUpdate,
)
from app.services.lease_service import LeaseService

router = APIRouter(prefix="/leases", tags=["leases"])


@router.get("", response_model=LeaseListResponse)
def list_leases(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: LeaseStatus | None = None,
    building_id: UUID | None = None,
    tenant_id: UUID | None = None,
) -> LeaseListResponse:
    return LeaseService(db).list_leases(
        current_user,
        page=page,
        page_size=page_size,
        status_filter=status,
        building_id=building_id,
        tenant_id=tenant_id,
    )


@router.get("/expiring", response_model=LeaseListResponse)
def list_expiring_leases(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    days: int = Query(default=30, ge=1, le=365),
) -> LeaseListResponse:
    return LeaseService(db).list_expiring(current_user, days=days)


@router.post("", response_model=LeaseDetail, status_code=201)
def create_lease(
    payload: LeaseCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> LeaseDetail:
    return LeaseService(db).create_lease(current_user, payload)


@router.get("/{lease_id}", response_model=LeaseDetail)
def get_lease(
    lease_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> LeaseDetail:
    return LeaseService(db).get_lease(current_user, lease_id)


@router.patch("/{lease_id}", response_model=LeaseDetail)
def update_lease(
    lease_id: UUID,
    payload: LeaseUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> LeaseDetail:
    return LeaseService(db).update_lease(current_user, lease_id, payload)


@router.post("/{lease_id}/terminate", response_model=LeaseDetail)
def terminate_lease(
    lease_id: UUID,
    payload: LeaseTerminate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> LeaseDetail:
    return LeaseService(db).terminate_lease(current_user, lease_id, payload)


@router.patch("/{lease_id}/rent", response_model=LeaseDetail)
def update_lease_rent(
    lease_id: UUID,
    payload: LeaseRentUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> LeaseDetail:
    return LeaseService(db).update_rent(current_user, lease_id, payload)


@router.post("/{lease_id}/contract", response_model=LeaseDetail)
def upload_lease_contract(
    lease_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
) -> LeaseDetail:
    return LeaseService(db).upload_contract(current_user, lease_id, file)
