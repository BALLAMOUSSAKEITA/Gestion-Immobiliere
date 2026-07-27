from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.tenant import (
    CreateTenantAccountRequest,
    CreateTenantAccountResponse,
    TenantCreate,
    TenantDetail,
    TenantListResponse,
    TenantUpdate,
)
from app.services.tenant_service import TenantService

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("", response_model=TenantListResponse)
def list_tenants(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    building_id: UUID | None = None,
    unit_id: UUID | None = None,
    is_active: bool | None = True,
) -> TenantListResponse:
    return TenantService(db).list_tenants(
        current_user,
        page=page,
        page_size=page_size,
        search=search,
        building_id=building_id,
        unit_id=unit_id,
        is_active=is_active,
    )


@router.post("", response_model=TenantDetail, status_code=201)
def create_tenant(
    payload: TenantCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TenantDetail:
    return TenantService(db).create_tenant(current_user, payload)


@router.get("/{tenant_id}", response_model=TenantDetail)
def get_tenant(
    tenant_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TenantDetail:
    return TenantService(db).get_tenant(current_user, tenant_id)


@router.patch("/{tenant_id}", response_model=TenantDetail)
def update_tenant(
    tenant_id: UUID,
    payload: TenantUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TenantDetail:
    return TenantService(db).update_tenant(current_user, tenant_id, payload)


@router.delete("/{tenant_id}", status_code=204)
def delete_tenant(
    tenant_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    TenantService(db).deactivate_tenant(current_user, tenant_id)


@router.post("/{tenant_id}/photo", response_model=TenantDetail)
def upload_tenant_photo(
    tenant_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
) -> TenantDetail:
    return TenantService(db).upload_photo(current_user, tenant_id, file)


@router.post("/{tenant_id}/id-document", response_model=TenantDetail)
def upload_tenant_id_document(
    tenant_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
) -> TenantDetail:
    return TenantService(db).upload_id_document(current_user, tenant_id, file)


@router.post("/{tenant_id}/create-account", response_model=CreateTenantAccountResponse)
def create_tenant_account(
    tenant_id: UUID,
    payload: CreateTenantAccountRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> CreateTenantAccountResponse:
    return TenantService(db).create_account(current_user, tenant_id, payload)
