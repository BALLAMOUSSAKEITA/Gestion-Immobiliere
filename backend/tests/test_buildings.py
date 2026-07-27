import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.models.building import Building, Unit
from app.models.enums import UnitStatus, UnitType
from app.models.owner_profile import OwnerProfile, UserBuildingAssignment
from sqlalchemy.orm import Session


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture()
def super_admin_headers(client: TestClient) -> dict[str, str]:
    token = _login(client, "admin@gestion-immo.local", "Admin123!")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def gestionnaire_headers(client: TestClient) -> dict[str, str]:
    token = _login(client, "gestionnaire@gestion-immo.local", "Agent123!")
    return {"Authorization": f"Bearer {token}"}


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


def test_create_building_generates_code(
    client: TestClient, super_admin_headers: dict[str, str], owner_profile: OwnerProfile
) -> None:
    response = client.post(
        "/api/v1/buildings",
        headers=super_admin_headers,
        json={
            "name": "Tour Horizon",
            "address": "Boulevard Lagunaire",
            "commune": "Abidjan",
            "quartier": "Marcory",
            "owner_profile_id": str(owner_profile.id),
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "KM001"
    assert data["name"] == "Tour Horizon"


def test_gestionnaire_sees_assigned_building_only(
    client: TestClient,
    gestionnaire_headers: dict[str, str],
    sample_building: Building,
) -> None:
    response = client.get("/api/v1/buildings", headers=gestionnaire_headers)
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["code"] == "KM001"


def test_create_unit_generates_code(
    client: TestClient,
    super_admin_headers: dict[str, str],
    sample_building: Building,
) -> None:
    response = client.post(
        f"/api/v1/buildings/{sample_building.id}/units",
        headers=super_admin_headers,
        json={
            "type": "apartment",
            "number": "01",
            "floor": 1,
            "rent_amount": "250000.00",
            "is_public_listing": True,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "KM001-A101"
    assert data["status"] == "free"


def test_public_units_lists_free_listings(
    client: TestClient,
    super_admin_headers: dict[str, str],
    sample_building: Building,
) -> None:
    client.post(
        f"/api/v1/buildings/{sample_building.id}/units",
        headers=super_admin_headers,
        json={
            "type": "shop",
            "number": "01",
            "rent_amount": "150000.00",
            "is_public_listing": True,
        },
    )
    response = client.get("/api/v1/public/units")
    assert response.status_code == 200
    assert response.json()["total"] >= 1


def test_cannot_delete_building_with_occupied_unit(
    client: TestClient,
    super_admin_headers: dict[str, str],
    db_session: Session,
    sample_building: Building,
) -> None:
    unit = Unit(
        id=uuid.UUID("00000000-0000-4000-8000-000000000040"),
        building_id=sample_building.id,
        code="KM001-A102",
        type=UnitType.apartment,
        number="02",
        floor=1,
        rent_amount=Decimal("200000"),
        status=UnitStatus.occupied,
    )
    db_session.add(unit)
    db_session.commit()

    response = client.delete(
        f"/api/v1/buildings/{sample_building.id}",
        headers=super_admin_headers,
    )
    assert response.status_code == 400
