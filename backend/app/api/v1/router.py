from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, require_roles
from app.api.v1 import auth, buildings, document_types, documents, expense_categories, expenses, leases, overdues, owner_profiles, payments, public, receipts, reminders, repairs, tenants, units, users
from app.core.config import get_settings
from app.models.user import User
from app.schemas.common import MessageResponse

router = APIRouter()
settings = get_settings()

router.include_router(auth.router)
router.include_router(users.router)
router.include_router(owner_profiles.router)
router.include_router(buildings.router)
router.include_router(units.router)
router.include_router(tenants.router)
router.include_router(leases.router)
router.include_router(payments.router)
router.include_router(receipts.router)
router.include_router(overdues.router)
router.include_router(reminders.router)
router.include_router(expenses.router)
router.include_router(expense_categories.router)
router.include_router(repairs.router)
router.include_router(documents.router)
router.include_router(document_types.router)
router.include_router(public.router)


@router.get("/", response_model=MessageResponse)
def root() -> MessageResponse:
    return MessageResponse(message="Gestion Immobilière API")


@router.get("/admin/ping", response_model=MessageResponse)
def admin_ping(
    _: Annotated[User, Depends(require_roles("super_admin", "admin_familial"))],
) -> MessageResponse:
    return MessageResponse(message="Accès administrateur autorisé")


@router.get("/profile-check", response_model=MessageResponse)
def profile_check(
    current_user: Annotated[User, Depends(get_current_user)],
) -> MessageResponse:
    return MessageResponse(message=f"Connecté en tant que {current_user.email}")
