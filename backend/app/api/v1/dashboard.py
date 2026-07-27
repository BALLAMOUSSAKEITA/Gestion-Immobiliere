from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.dashboard import (
    DashboardAlerts,
    DashboardKpis,
    ExpenseCategoryChart,
    ExpiringLeasesList,
    OccupancyChart,
    OverdueQuickList,
    PaymentMethodChart,
    RecentActivity,
    RevenueExpenseChart,
)
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/kpis", response_model=DashboardKpis)
def get_dashboard_kpis(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    year: int | None = None,
    month: int | None = None,
    building_id: UUID | None = None,
    owner_profile_id: UUID | None = None,
) -> DashboardKpis:
    return DashboardService(db).get_kpis(
        current_user,
        year=year,
        month=month,
        building_id=building_id,
        owner_profile_id=owner_profile_id,
    )


@router.get("/charts/revenue-expenses", response_model=RevenueExpenseChart)
def get_revenue_expenses_chart(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    year: int | None = None,
    building_id: UUID | None = None,
    owner_profile_id: UUID | None = None,
) -> RevenueExpenseChart:
    return DashboardService(db).get_revenue_expenses_chart(
        current_user,
        year=year,
        building_id=building_id,
        owner_profile_id=owner_profile_id,
    )


@router.get("/charts/occupancy", response_model=OccupancyChart)
def get_occupancy_chart(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    year: int | None = None,
    building_id: UUID | None = None,
    owner_profile_id: UUID | None = None,
) -> OccupancyChart:
    return DashboardService(db).get_occupancy_chart(
        current_user,
        year=year,
        building_id=building_id,
        owner_profile_id=owner_profile_id,
    )


@router.get("/charts/expenses-by-category", response_model=ExpenseCategoryChart)
def get_expenses_by_category_chart(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    year: int | None = None,
    month: int | None = None,
    building_id: UUID | None = None,
    owner_profile_id: UUID | None = None,
) -> ExpenseCategoryChart:
    return DashboardService(db).get_expenses_by_category(
        current_user,
        year=year,
        month=month,
        building_id=building_id,
        owner_profile_id=owner_profile_id,
    )


@router.get("/charts/payment-methods", response_model=PaymentMethodChart)
def get_payment_methods_chart(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    year: int | None = None,
    month: int | None = None,
    building_id: UUID | None = None,
    owner_profile_id: UUID | None = None,
) -> PaymentMethodChart:
    return DashboardService(db).get_payment_methods(
        current_user,
        year=year,
        month=month,
        building_id=building_id,
        owner_profile_id=owner_profile_id,
    )


@router.get("/alerts", response_model=DashboardAlerts)
def get_dashboard_alerts(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    building_id: UUID | None = None,
    owner_profile_id: UUID | None = None,
) -> DashboardAlerts:
    return DashboardService(db).get_alerts(
        current_user,
        building_id=building_id,
        owner_profile_id=owner_profile_id,
    )


@router.get("/recent-activity", response_model=RecentActivity)
def get_recent_activity(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=10, ge=1, le=50),
) -> RecentActivity:
    return DashboardService(db).get_recent_activity(current_user, limit=limit)


@router.get("/top-overdues", response_model=OverdueQuickList)
def get_top_overdues(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=10, ge=1, le=20),
    building_id: UUID | None = None,
    owner_profile_id: UUID | None = None,
) -> OverdueQuickList:
    return DashboardService(db).get_top_overdues(
        current_user,
        limit=limit,
        building_id=building_id,
        owner_profile_id=owner_profile_id,
    )


@router.get("/expiring-leases", response_model=ExpiringLeasesList)
def get_expiring_leases(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    days: int = Query(default=30, ge=1, le=365),
    building_id: UUID | None = None,
    owner_profile_id: UUID | None = None,
) -> ExpiringLeasesList:
    return DashboardService(db).get_expiring_leases(
        current_user,
        days=days,
        building_id=building_id,
        owner_profile_id=owner_profile_id,
    )
