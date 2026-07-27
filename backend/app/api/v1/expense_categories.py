from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.expense import ExpenseCategoryResponse
from app.services.expense_service import ExpenseService

router = APIRouter(prefix="/expense-categories", tags=["expense-categories"])


@router.get("", response_model=list[ExpenseCategoryResponse])
def list_expense_categories(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ExpenseCategoryResponse]:
    return ExpenseService(db).list_categories()
