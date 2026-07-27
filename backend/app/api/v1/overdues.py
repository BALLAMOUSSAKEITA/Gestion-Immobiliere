from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.overdue import (
    OverdueItem,
    OverdueListResponse,
    OverdueSummary,
    TenantOverdueListResponse,
)
from app.services.overdue_service import OverdueService

router = APIRouter(prefix="/overdues", tags=["overdues"])


@router.get("", response_model=OverdueListResponse)
def list_overdues(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    building_id: UUID | None = None,
    tenant_id: UUID | None = None,
    min_days: int | None = None,
    min_amount: float | None = None,
    sort: str = Query(default="days_overdue"),
) -> OverdueListResponse:
    from decimal import Decimal

    return OverdueService(db).list_overdues(
        current_user,
        page=page,
        page_size=page_size,
        building_id=building_id,
        tenant_id=tenant_id,
        min_days=min_days,
        min_amount=Decimal(str(min_amount)) if min_amount is not None else None,
        sort=sort,
    )


@router.get("/summary", response_model=OverdueSummary)
def get_overdues_summary(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> OverdueSummary:
    return OverdueService(db).get_summary(current_user)


@router.get("/by-tenant", response_model=TenantOverdueListResponse)
def list_overdues_by_tenant(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TenantOverdueListResponse:
    return OverdueService(db).list_by_tenant(current_user)


@router.post("/sync")
def sync_overdues(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, int]:
    if current_user.role.code not in ("super_admin", "admin_familial"):
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Accès non autorisé")
    from app.services.overdue_detection_service import OverdueDetectionService

    count = OverdueDetectionService(db).sync_all()
    return {"synced": count}


@router.get("/{overdue_id}", response_model=OverdueItem)
def get_overdue(
    overdue_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> OverdueItem:
    return OverdueService(db).get_overdue(current_user, overdue_id)


@router.post("/{overdue_id}/resolve", response_model=OverdueItem)
def resolve_overdue(
    overdue_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> OverdueItem:
    return OverdueService(db).resolve_overdue(current_user, overdue_id)
