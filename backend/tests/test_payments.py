import uuid
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.building import Building, Unit
from app.models.enums import IdDocumentType, LeaseStatus, UnitStatus, UnitType
from app.models.owner_profile import UserBuildingAssignment
from app.models.payment import RentPeriod
from app.models.tenant import Lease, Tenant
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


def test_record_single_month_payment(
    client: TestClient, super_admin_headers: dict[str, str], active_lease: Lease
) -> None:
    response = client.post(
        "/api/v1/payments",
        headers=super_admin_headers,
        json={
            "lease_id": str(active_lease.id),
            "amount": "250000.00",
            "payment_method": "cash",
            "payment_date": "2026-07-26",
            "allocations": [{"period_year": 2026, "period_month": 7, "amount": "250000.00"}],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["amount"] == "250000.00"
    assert data["receipt_number"] is not None


def test_record_multi_month_payment(
    client: TestClient, super_admin_headers: dict[str, str], active_lease: Lease
) -> None:
    response = client.post(
        "/api/v1/payments",
        headers=super_admin_headers,
        json={
            "lease_id": str(active_lease.id),
            "amount": "500000.00",
            "payment_method": "orange_money",
            "payment_date": "2026-07-26",
            "reference": "OM-123456",
            "allocations": [
                {"period_year": 2026, "period_month": 8, "amount": "250000.00"},
                {"period_year": 2026, "period_month": 9, "amount": "250000.00"},
            ],
        },
    )
    assert response.status_code == 201
    assert len(response.json()["allocations"]) == 2


def test_partial_payment_sets_period_partial(
    client: TestClient,
    super_admin_headers: dict[str, str],
    active_lease: Lease,
    db_session: Session,
) -> None:
    response = client.post(
        "/api/v1/payments",
        headers=super_admin_headers,
        json={
            "lease_id": str(active_lease.id),
            "amount": "100000.00",
            "payment_method": "wave",
            "payment_date": "2026-07-26",
            "allocations": [{"period_year": 2026, "period_month": 10, "amount": "100000.00"}],
        },
    )
    assert response.status_code == 201
    period = (
        db_session.query(RentPeriod)
        .filter(
            RentPeriod.lease_id == active_lease.id,
            RentPeriod.period_month == 10,
        )
        .first()
    )
    assert period is not None
    assert period.status.value == "partial"


def test_download_receipt_pdf(
    client: TestClient, super_admin_headers: dict[str, str], active_lease: Lease
) -> None:
    create = client.post(
        "/api/v1/payments",
        headers=super_admin_headers,
        json={
            "lease_id": str(active_lease.id),
            "amount": "250000.00",
            "payment_method": "cash",
            "payment_date": "2026-07-26",
            "allocations": [{"period_year": 2026, "period_month": 11, "amount": "250000.00"}],
        },
    )
    receipt_id = create.json()["receipt_id"]
    pdf_response = client.get(
        f"/api/v1/receipts/{receipt_id}/pdf",
        headers=super_admin_headers,
    )
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
