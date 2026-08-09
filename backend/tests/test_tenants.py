import uuid
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.building import Building, Unit
from app.models.enums import IdDocumentType, LeaseStatus, UnitStatus, UnitType
from app.models.owner_profile import OwnerProfile, UserBuildingAssignment
from app.models.tenant import Lease, Tenant


@pytest.fixture()
def owner_profile(db_session: Session) -> OwnerProfile:
    profile = OwnerProfile(
        id=uuid.UUID("00000000-0000-4000-8000-000000000020"),
        first_name="Amadou",
        last_name="Diallo",
    )
    db_session.add(profile)
    db_session.commit()
    return profile


@pytest.fixture()
def sample_building(db_session: Session, owner_profile: OwnerProfile) -> Building:
    building = Building(
        id=uuid.UUID("00000000-0000-4000-8000-000000000030"),
        code="KM001",
        name="Résidence Les Palmiers",
        address="Rue 12, Cocody",
        commune="Abidjan",
        quartier="Cocody",
        floor_count=3,
        owner_profile_id=owner_profile.id,
        manager_user_id=uuid.UUID("00000000-0000-4000-8000-000000000011"),
        created_by=uuid.UUID("00000000-0000-4000-8000-000000000010"),
    )
    db_session.add(building)
    db_session.add(
        UserBuildingAssignment(
            user_id=uuid.UUID("00000000-0000-4000-8000-000000000011"),
            building_id=building.id,
            assigned_by=uuid.UUID("00000000-0000-4000-8000-000000000010"),
        )
    )
    db_session.commit()
    return building


@pytest.fixture()
def free_unit(db_session: Session, sample_building: Building) -> Unit:
    unit = Unit(
        id=uuid.UUID("00000000-0000-4000-8000-000000000050"),
        building_id=sample_building.id,
        code="KM001-A101",
        type=UnitType.apartment,
        number="01",
        floor=1,
        rent_amount=Decimal("250000"),
        status=UnitStatus.free,
    )
    db_session.add(unit)
    db_session.commit()
    return unit


@pytest.fixture()
def sample_tenant(db_session: Session) -> Tenant:
    tenant = Tenant(
        id=uuid.UUID("00000000-0000-4000-8000-000000000060"),
        first_name="Aminata",
        last_name="Traoré",
        phone_primary="+2250700000002",
        id_document_type=IdDocumentType.cni,
        id_document_number="CI1234567890",
        created_by=uuid.UUID("00000000-0000-4000-8000-000000000010"),
    )
    db_session.add(tenant)
    db_session.commit()
    return tenant


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture()
def super_admin_headers(client: TestClient) -> dict[str, str]:
    token = _login(client, "admin@gestion-immo.local", "Admin123!")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_headers(client: TestClient) -> dict[str, str]:
    token = _login(client, "gestionnaire@gestion-immo.local", "Agent123!")
    return {"Authorization": f"Bearer {token}"}


def test_create_tenant(client: TestClient, super_admin_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/tenants",
        headers=super_admin_headers,
        json={
            "first_name": "Kofi",
            "last_name": "Mensah",
            "phone_primary": "+2250700000099",
            "id_document_type": "cni",
            "id_document_number": "CI9988776655",
        },
    )
    assert response.status_code == 201
    assert response.json()["first_name"] == "Kofi"


def test_create_lease_occupies_unit(
    client: TestClient,
    super_admin_headers: dict[str, str],
    sample_tenant: Tenant,
    free_unit: Unit,
) -> None:
    response = client.post(
        "/api/v1/leases",
        headers=super_admin_headers,
        json={
            "tenant_id": str(sample_tenant.id),
            "unit_id": str(free_unit.id),
            "start_date": "2026-08-01",
            "end_date": "2027-07-31",
            "rent_amount": "250000.00",
            "deposit_amount": "500000.00",
            "deposit_paid": True,
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "active"

    unit_response = client.get(
        f"/api/v1/units/{free_unit.id}",
        headers=super_admin_headers,
    )
    assert unit_response.json()["status"] == "occupied"


def test_tenant_can_have_multiple_active_leases(
    client: TestClient,
    super_admin_headers: dict[str, str],
    db_session: Session,
    sample_tenant: Tenant,
    sample_building: Building,
    free_unit: Unit,
) -> None:
    second_unit = Unit(
        id=uuid.UUID("00000000-0000-4000-8000-000000000051"),
        building_id=sample_building.id,
        code="KM001-A102",
        type=UnitType.apartment,
        number="02",
        floor=1,
        rent_amount=Decimal("180000"),
        status=UnitStatus.free,
    )
    db_session.add(second_unit)
    db_session.commit()

    first = client.post(
        "/api/v1/leases",
        headers=super_admin_headers,
        json={
            "tenant_id": str(sample_tenant.id),
            "unit_id": str(free_unit.id),
            "start_date": "2026-08-01",
            "rent_amount": "250000.00",
        },
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/leases",
        headers=super_admin_headers,
        json={
            "tenant_id": str(sample_tenant.id),
            "unit_id": str(second_unit.id),
            "start_date": "2026-08-01",
            "rent_amount": "180000.00",
        },
    )
    assert second.status_code == 201

    detail = client.get(
        f"/api/v1/tenants/{sample_tenant.id}",
        headers=super_admin_headers,
    )
    assert detail.status_code == 200
    assert len(detail.json()["active_leases"]) == 2


def test_terminate_lease_frees_unit(
    client: TestClient,
    super_admin_headers: dict[str, str],
    sample_tenant: Tenant,
    free_unit: Unit,
) -> None:
    create_response = client.post(
        "/api/v1/leases",
        headers=super_admin_headers,
        json={
            "tenant_id": str(sample_tenant.id),
            "unit_id": str(free_unit.id),
            "start_date": "2026-08-01",
            "rent_amount": "250000.00",
        },
    )
    lease_id = create_response.json()["id"]

    terminate_response = client.post(
        f"/api/v1/leases/{lease_id}/terminate",
        headers=super_admin_headers,
        json={
            "termination_date": "2026-12-31",
            "termination_reason": "Fin de bail",
        },
    )
    assert terminate_response.status_code == 200
    assert terminate_response.json()["status"] == "terminated"

    unit_response = client.get(
        f"/api/v1/units/{free_unit.id}",
        headers=super_admin_headers,
    )
    assert unit_response.json()["status"] == "free"


def test_release_unit_terminates_lease_and_frees_unit(
    client: TestClient,
    super_admin_headers: dict[str, str],
    admin_headers: dict[str, str],
    sample_tenant: Tenant,
    free_unit: Unit,
) -> None:
    create_response = client.post(
        "/api/v1/leases",
        headers=super_admin_headers,
        json={
            "tenant_id": str(sample_tenant.id),
            "unit_id": str(free_unit.id),
            "start_date": "2026-08-01",
            "rent_amount": "250000.00",
        },
    )
    assert create_response.status_code == 201

    forbidden = client.post(
        f"/api/v1/units/{free_unit.id}/release",
        headers=admin_headers,
        json={"termination_reason": "Libération"},
    )
    assert forbidden.status_code == 403

    release_response = client.post(
        f"/api/v1/units/{free_unit.id}/release",
        headers=super_admin_headers,
        json={"termination_reason": "Libération du logement"},
    )
    assert release_response.status_code == 200
    assert release_response.json()["status"] == "terminated"

    unit_response = client.get(
        f"/api/v1/units/{free_unit.id}",
        headers=super_admin_headers,
    )
    assert unit_response.json()["status"] == "free"


def test_cannot_create_lease_on_occupied_unit(
    client: TestClient,
    super_admin_headers: dict[str, str],
    db_session: Session,
    sample_tenant: Tenant,
    free_unit: Unit,
) -> None:
    other_tenant = Tenant(
        id=uuid.UUID("00000000-0000-4000-8000-000000000061"),
        first_name="Other",
        last_name="Tenant",
        phone_primary="+2250700000003",
        id_document_type=IdDocumentType.passport,
        id_document_number="P123456",
        created_by=uuid.UUID("00000000-0000-4000-8000-000000000010"),
    )
    db_session.add(other_tenant)
    free_unit.status = UnitStatus.occupied
    db_session.add(
        Lease(
            id=uuid.UUID("00000000-0000-4000-8000-000000000070"),
            tenant_id=sample_tenant.id,
            unit_id=free_unit.id,
            start_date=date(2026, 1, 1),
            rent_amount=Decimal("250000"),
            status=LeaseStatus.active,
            created_by=uuid.UUID("00000000-0000-4000-8000-000000000010"),
        )
    )
    db_session.commit()

    response = client.post(
        "/api/v1/leases",
        headers=super_admin_headers,
        json={
            "tenant_id": str(other_tenant.id),
            "unit_id": str(free_unit.id),
            "start_date": "2026-09-01",
            "rent_amount": "250000.00",
        },
    )
    assert response.status_code == 400


def test_delete_tenant_blocked_when_active_lease(
    client: TestClient,
    super_admin_headers: dict[str, str],
    admin_headers: dict[str, str],
    sample_tenant: Tenant,
    free_unit: Unit,
) -> None:
    create_response = client.post(
        "/api/v1/leases",
        headers=super_admin_headers,
        json={
            "tenant_id": str(sample_tenant.id),
            "unit_id": str(free_unit.id),
            "start_date": "2026-08-01",
            "rent_amount": "250000.00",
        },
    )
    assert create_response.status_code == 201
    lease_id = create_response.json()["id"]

    forbidden = client.delete(
        f"/api/v1/tenants/{sample_tenant.id}",
        headers=admin_headers,
    )
    assert forbidden.status_code in (202, 403)

    blocked = client.delete(
        f"/api/v1/tenants/{sample_tenant.id}",
        headers=super_admin_headers,
    )
    assert blocked.status_code == 400
    assert "bail actif" in blocked.json()["detail"]
    assert "résilier" in blocked.json()["detail"]

    terminate = client.post(
        f"/api/v1/leases/{lease_id}/terminate",
        headers=super_admin_headers,
        json={"termination_date": "2026-08-09", "termination_reason": "Fin de bail"},
    )
    assert terminate.status_code == 200

    deleted = client.delete(
        f"/api/v1/tenants/{sample_tenant.id}",
        headers=super_admin_headers,
    )
    assert deleted.status_code == 204
