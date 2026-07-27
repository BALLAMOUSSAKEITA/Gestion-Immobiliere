import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.building import Building, Unit
from app.models.enums import IdDocumentType, LeaseStatus, UnitStatus, UnitType
from app.models.payment import RentPeriod
from app.models.tenant import Lease, Tenant
from app.services.overdue_detection_service import OverdueDetectionService
from app.services.rent_period_service import RentPeriodService


@pytest.fixture()
def active_lease(db_session: Session) -> Lease:
    building = Building(
        id=uuid.UUID("00000000-0000-4000-8000-000000000030"),
        code="KM001",
        name="Résidence Test",
        address="Rue Test",
        commune="Abidjan",
        created_by=uuid.UUID("00000000-0000-4000-8000-000000000010"),
    )
    unit = Unit(
        id=uuid.UUID("00000000-0000-4000-8000-000000000050"),
        building_id=building.id,
        code="KM001-A101",
        type=UnitType.apartment,
        number="01",
        floor=1,
        rent_amount=Decimal("250000"),
        status=UnitStatus.occupied,
    )
    tenant = Tenant(
        id=uuid.UUID("00000000-0000-4000-8000-000000000060"),
        first_name="Aminata",
        last_name="Traoré",
        phone_primary="+2250700000002",
        id_document_type=IdDocumentType.cni,
        id_document_number="CI1234567890",
        created_by=uuid.UUID("00000000-0000-4000-8000-000000000010"),
    )
    lease = Lease(
        id=uuid.UUID("00000000-0000-4000-8000-000000000070"),
        tenant_id=tenant.id,
        unit_id=unit.id,
        start_date=date(2026, 7, 1),
        end_date=date(2026, 12, 31),
        rent_amount=Decimal("250000"),
        status=LeaseStatus.active,
        created_by=uuid.UUID("00000000-0000-4000-8000-000000000010"),
    )
    db_session.add_all([building, unit, tenant, lease])
    db_session.flush()
    RentPeriodService(db_session).generate_for_lease(lease)
    db_session.commit()
    return lease


def _login(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@gestion-immo.local", "password": "Admin123!"},
    )
    return response.json()["access_token"]


@pytest.fixture()
def super_admin_headers(client: TestClient) -> dict[str, str]:
    return {"Authorization": f"Bearer {_login(client)}"}


def _make_overdue(db_session: Session, lease: Lease, days_overdue: int = 9) -> RentPeriod:
    today = date.today()
    period = (
        db_session.query(RentPeriod)
        .filter(
            RentPeriod.lease_id == lease.id,
            RentPeriod.period_year == 2026,
            RentPeriod.period_month == 7,
        )
        .first()
    )
    assert period is not None
    period.due_date = today - timedelta(days=days_overdue)
    db_session.commit()
    OverdueDetectionService(db_session).sync_all(today=today)
    return period


def test_overdue_detection_and_days(
    client: TestClient,
    super_admin_headers: dict[str, str],
    active_lease: Lease,
    db_session: Session,
) -> None:
    _make_overdue(db_session, active_lease, days_overdue=9)

    response = client.get("/api/v1/overdues", headers=super_admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["days_overdue"] == 9
    assert data["items"][0]["amount_remaining"] == "250000.00"
    assert data["summary"]["total_overdue_amount"] == "250000.00"


def test_overdue_resolved_after_payment(
    client: TestClient,
    super_admin_headers: dict[str, str],
    active_lease: Lease,
    db_session: Session,
) -> None:
    _make_overdue(db_session, active_lease, days_overdue=9)

    payment_response = client.post(
        "/api/v1/payments",
        headers=super_admin_headers,
        json={
            "lease_id": str(active_lease.id),
            "amount": "250000.00",
            "payment_method": "cash",
            "payment_date": date.today().isoformat(),
            "allocations": [{"period_year": 2026, "period_month": 7, "amount": "250000.00"}],
        },
    )
    assert payment_response.status_code == 201

    response = client.get("/api/v1/overdues", headers=super_admin_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_overdues_by_tenant(
    client: TestClient,
    super_admin_headers: dict[str, str],
    active_lease: Lease,
    db_session: Session,
) -> None:
    _make_overdue(db_session, active_lease, days_overdue=14)

    response = client.get("/api/v1/overdues/by-tenant", headers=super_admin_headers)
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["total_overdue_amount"] == "250000.00"
    assert items[0]["overdue_months_count"] == 1


def test_send_manual_reminder(
    client: TestClient,
    super_admin_headers: dict[str, str],
    active_lease: Lease,
    db_session: Session,
) -> None:
    _make_overdue(db_session, active_lease, days_overdue=9)
    overdue_id = client.get("/api/v1/overdues", headers=super_admin_headers).json()["items"][0]["id"]

    response = client.post(
        "/api/v1/reminders",
        headers=super_admin_headers,
        json={
            "tenant_id": str(active_lease.tenant_id),
            "overdue_record_ids": [overdue_id],
            "reminder_type": "manual",
            "channel": "email",
            "message": "Merci de régulariser votre loyer de juillet.",
        },
    )
    assert response.status_code == 201
    assert response.json()["reminder_type"] == "manual"

    list_response = client.get("/api/v1/reminders", headers=super_admin_headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] >= 1
