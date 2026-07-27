from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.enums import PaymentRecordStatus
from app.models.user import User
from app.schemas.payment import PaymentCreate, PaymentDetail, PaymentListResponse
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("", response_model=PaymentListResponse)
def list_payments(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    tenant_id: UUID | None = None,
    lease_id: UUID | None = None,
    building_id: UUID | None = None,
    payment_method: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    status: PaymentRecordStatus | None = None,
) -> PaymentListResponse:
    from datetime import date as date_type

    return PaymentService(db).list_payments(
        current_user,
        page=page,
        page_size=page_size,
        tenant_id=tenant_id,
        lease_id=lease_id,
        building_id=building_id,
        payment_method=payment_method,
        date_from=date_type.fromisoformat(date_from) if date_from else None,
        date_to=date_type.fromisoformat(date_to) if date_to else None,
        status_filter=status,
    )


@router.post("", response_model=PaymentDetail, status_code=201)
def create_payment(
    payload: PaymentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PaymentDetail:
    return PaymentService(db).record_payment(current_user, payload)


@router.get("/{payment_id}", response_model=PaymentDetail)
def get_payment(
    payment_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PaymentDetail:
    return PaymentService(db).get_payment(current_user, payment_id)


@router.post("/{payment_id}/proof", response_model=PaymentDetail)
def upload_payment_proof(
    payment_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
) -> PaymentDetail:
    return PaymentService(db).upload_proof(current_user, payment_id, file)


@router.post("/{payment_id}/validate", response_model=PaymentDetail)
def validate_payment(
    payment_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PaymentDetail:
    return PaymentService(db).validate_payment(current_user, payment_id)
