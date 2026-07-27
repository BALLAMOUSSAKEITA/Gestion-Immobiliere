from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.enums import ExpenseStatus, PaymentMethod
from app.models.user import User
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseDetail,
    ExpenseListResponse,
    ExpenseSummaryResponse,
    ExpenseUpdate,
)
from app.services.expense_service import ExpenseService

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.get("", response_model=ExpenseListResponse)
def list_expenses(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    building_id: UUID | None = None,
    unit_id: UUID | None = None,
    owner_profile_id: UUID | None = None,
    category_id: UUID | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    payment_method: PaymentMethod | None = None,
    supplier: str | None = None,
    status: ExpenseStatus | None = None,
) -> ExpenseListResponse:
    from datetime import date as date_type
    from decimal import Decimal

    return ExpenseService(db).list_expenses(
        current_user,
        page=page,
        page_size=page_size,
        building_id=building_id,
        unit_id=unit_id,
        owner_profile_id=owner_profile_id,
        category_id=category_id,
        date_from=date_type.fromisoformat(date_from) if date_from else None,
        date_to=date_type.fromisoformat(date_to) if date_to else None,
        min_amount=Decimal(str(min_amount)) if min_amount is not None else None,
        max_amount=Decimal(str(max_amount)) if max_amount is not None else None,
        payment_method=payment_method,
        supplier=supplier,
        status_filter=status,
    )


@router.get("/summary", response_model=ExpenseSummaryResponse)
def get_expenses_summary(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    year: int | None = None,
    month: int | None = None,
    building_id: UUID | None = None,
    group_by: str = Query(default="category"),
) -> ExpenseSummaryResponse:
    return ExpenseService(db).get_summary(
        current_user,
        year=year,
        month=month,
        building_id=building_id,
        group_by=group_by,
    )


@router.post("", response_model=ExpenseDetail, status_code=201)
def create_expense(
    payload: ExpenseCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ExpenseDetail:
    return ExpenseService(db).create_expense(current_user, payload)


@router.get("/{expense_id}", response_model=ExpenseDetail)
def get_expense(
    expense_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ExpenseDetail:
    return ExpenseService(db).get_expense(current_user, expense_id)


@router.patch("/{expense_id}", response_model=ExpenseDetail)
def update_expense(
    expense_id: UUID,
    payload: ExpenseUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ExpenseDetail:
    return ExpenseService(db).update_expense(current_user, expense_id, payload)


@router.delete("/{expense_id}", status_code=204)
def delete_expense(
    expense_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    ExpenseService(db).delete_expense(current_user, expense_id)


@router.post("/{expense_id}/receipt", response_model=ExpenseDetail)
def upload_expense_receipt(
    expense_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...),
) -> ExpenseDetail:
    return ExpenseService(db).upload_receipt(current_user, expense_id, file)


@router.post("/{expense_id}/validate", response_model=ExpenseDetail)
def validate_expense(
    expense_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ExpenseDetail:
    return ExpenseService(db).validate_expense(current_user, expense_id)


@router.post("/{expense_id}/reject", response_model=ExpenseDetail)
def reject_expense(
    expense_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ExpenseDetail:
    return ExpenseService(db).reject_expense(current_user, expense_id)
