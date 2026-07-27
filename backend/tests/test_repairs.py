import uuid
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.building import Building, Unit
from app.models.enums import IdDocumentType, LeaseStatus, UnitStatus, UnitType
from app.models.expense import Expense
from app.models.owner_profile import OwnerProfile, UserBuildingAssignment


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
def sample_unit(db_session: Session, owner_profile: OwnerProfile) -> Unit:
    building = Building(
        id=uuid.UUID("00000000-0000-4000-8000-000000000030"),
        code="KM001",
        name="Résidence Les Palmiers",
        address="Rue 12, Cocody",
        commune="Abidjan",
        owner_profile_id=owner_profile.id,
        manager_user_id=uuid.UUID("00000000-0000-4000-8000-000000000011"),
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
    db_session.add_all([building, unit])
    db_session.add(
        UserBuildingAssignment(
            user_id=uuid.UUID("00000000-0000-4000-8000-000000000011"),
            building_id=building.id,
            assigned_by=uuid.UUID("00000000-0000-4000-8000-000000000010"),
        )
    )
    db_session.commit()
    return unit


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture()
def super_admin_headers(client: TestClient) -> dict[str, str]:
    return {"Authorization": f"Bearer {_login(client, 'admin@gestion-immo.local', 'Admin123!')}"}


@pytest.fixture()
def gestionnaire_headers(client: TestClient) -> dict[str, str]:
    return {"Authorization": f"Bearer {_login(client, 'gestionnaire@gestion-immo.local', 'Agent123!')}"}


def _create_repair(client: TestClient, headers: dict[str, str], unit_id: str) -> dict:
    response = client.post(
        "/api/v1/repairs",
        headers=headers,
        json={
            "unit_id": unit_id,
            "title": "Fuite d'eau",
            "description": "Eau qui coule du plafond",
            "urgency": "high",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_create_repair(
    client: TestClient,
    gestionnaire_headers: dict[str, str],
    sample_unit: Unit,
) -> None:
    data = _create_repair(client, gestionnaire_headers, str(sample_unit.id))
    assert data["status"] == "new"
    assert data["urgency"] == "high"
    assert data["unit_code"] == sample_unit.code


def test_status_transitions_workflow(
    client: TestClient,
    gestionnaire_headers: dict[str, str],
    sample_unit: Unit,
) -> None:
    repair = _create_repair(client, gestionnaire_headers, str(sample_unit.id))
    repair_id = repair["id"]

    for new_status in ("under_review", "technician_assigned", "in_progress"):
        response = client.patch(
            f"/api/v1/repairs/{repair_id}/status",
            headers=gestionnaire_headers,
            json={"status": new_status},
        )
        assert response.status_code == 200
        assert response.json()["status"] == new_status


def test_invalid_status_transition(
    client: TestClient,
    gestionnaire_headers: dict[str, str],
    sample_unit: Unit,
) -> None:
    repair = _create_repair(client, gestionnaire_headers, str(sample_unit.id))
    repair_id = repair["id"]
    response = client.patch(
        f"/api/v1/repairs/{repair_id}/status",
        headers=gestionnaire_headers,
        json={"status": "completed"},
    )
    assert response.status_code == 400


def test_complete_repair_creates_expense(
    client: TestClient,
    gestionnaire_headers: dict[str, str],
    sample_unit: Unit,
    db_session: Session,
) -> None:
    repair = _create_repair(client, gestionnaire_headers, str(sample_unit.id))
    repair_id = repair["id"]
    for status in ("under_review", "technician_assigned", "in_progress"):
        client.patch(
            f"/api/v1/repairs/{repair_id}/status",
            headers=gestionnaire_headers,
            json={"status": status},
        )

    response = client.post(
        f"/api/v1/repairs/{repair_id}/complete",
        headers=gestionnaire_headers,
        json={
            "final_cost": "85000.00",
            "create_expense": True,
            "notes": "Joint remplacé",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["expense_id"] is not None

    expense = db_session.query(Expense).filter(Expense.repair_id == uuid.UUID(repair_id)).first()
    assert expense is not None
    assert expense.amount == Decimal("85000.00")


def test_cancel_requires_reason(
    client: TestClient,
    gestionnaire_headers: dict[str, str],
    sample_unit: Unit,
) -> None:
    repair = _create_repair(client, gestionnaire_headers, str(sample_unit.id))
    response = client.post(
        f"/api/v1/repairs/{repair['id']}/cancel",
        headers=gestionnaire_headers,
        json={"cancellation_reason": "Problème résolu par le locataire"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_repair_history(
    client: TestClient,
    gestionnaire_headers: dict[str, str],
    sample_unit: Unit,
) -> None:
    repair = _create_repair(client, gestionnaire_headers, str(sample_unit.id))
    client.patch(
        f"/api/v1/repairs/{repair['id']}/status",
        headers=gestionnaire_headers,
        json={"status": "under_review"},
    )
    response = client.get(
        f"/api/v1/repairs/{repair['id']}/history",
        headers=gestionnaire_headers,
    )
    assert response.status_code == 200
    assert len(response.json()) >= 2


def test_repairs_summary(
    client: TestClient,
    gestionnaire_headers: dict[str, str],
    sample_unit: Unit,
) -> None:
    _create_repair(client, gestionnaire_headers, str(sample_unit.id))
    response = client.get("/api/v1/repairs/summary", headers=gestionnaire_headers)
    assert response.status_code == 200
    assert response.json()["in_progress_count"] >= 1
