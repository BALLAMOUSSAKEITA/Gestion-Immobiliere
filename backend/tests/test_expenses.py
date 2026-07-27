import uuid
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.building import Building
from app.models.expense import ExpenseCategory
from app.models.owner_profile import OwnerProfile, UserBuildingAssignment


REPAIR_CATEGORY_ID = "00000000-0000-4000-8000-000000000101"


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


def test_list_expense_categories(
    client: TestClient, super_admin_headers: dict[str, str]
) -> None:
    response = client.get("/api/v1/expense-categories", headers=super_admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10
    assert any(item["code"] == "repair" for item in data)


def test_create_expense_recorded(
    client: TestClient,
    super_admin_headers: dict[str, str],
    sample_building: Building,
) -> None:
    response = client.post(
        "/api/v1/expenses",
        headers=super_admin_headers,
        json={
            "category_id": REPAIR_CATEGORY_ID,
            "building_id": str(sample_building.id),
            "supplier_name": "Plomberie Express",
            "description": "Réparation fuite",
            "amount": "75000.00",
            "payment_method": "cash",
            "expense_date": "2026-07-20",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "recorded"
    assert data["requires_validation"] is False
    assert data["amount"] == "75000.00"


def test_create_expense_requires_validation(
    client: TestClient,
    super_admin_headers: dict[str, str],
    sample_building: Building,
) -> None:
    response = client.post(
        "/api/v1/expenses",
        headers=super_admin_headers,
        json={
            "category_id": REPAIR_CATEGORY_ID,
            "building_id": str(sample_building.id),
            "description": "Gros travaux façade",
            "amount": "600000.00",
            "payment_method": "bank_transfer",
            "expense_date": "2026-07-21",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending_validation"
    assert data["requires_validation"] is True


def test_validate_expense_workflow(
    client: TestClient,
    super_admin_headers: dict[str, str],
    sample_building: Building,
) -> None:
    create = client.post(
        "/api/v1/expenses",
        headers=super_admin_headers,
        json={
            "category_id": REPAIR_CATEGORY_ID,
            "building_id": str(sample_building.id),
            "description": "Réfection toiture",
            "amount": "550000.00",
            "payment_method": "bank_transfer",
            "expense_date": "2026-07-22",
        },
    )
    expense_id = create.json()["id"]

    validate = client.post(
        f"/api/v1/expenses/{expense_id}/validate",
        headers=super_admin_headers,
    )
    assert validate.status_code == 200
    assert validate.json()["status"] == "validated"


def test_summary_excludes_pending_validation(
    client: TestClient,
    super_admin_headers: dict[str, str],
    sample_building: Building,
) -> None:
    client.post(
        "/api/v1/expenses",
        headers=super_admin_headers,
        json={
            "category_id": REPAIR_CATEGORY_ID,
            "building_id": str(sample_building.id),
            "description": "Petite réparation",
            "amount": "50000.00",
            "payment_method": "cash",
            "expense_date": date.today().isoformat(),
        },
    )
    client.post(
        "/api/v1/expenses",
        headers=super_admin_headers,
        json={
            "category_id": REPAIR_CATEGORY_ID,
            "building_id": str(sample_building.id),
            "description": "Gros travaux",
            "amount": "700000.00",
            "payment_method": "bank_transfer",
            "expense_date": date.today().isoformat(),
        },
    )

    summary = client.get("/api/v1/expenses/summary", headers=super_admin_headers)
    assert summary.status_code == 200
    data = summary.json()
    assert data["count"] == 1
    assert data["total_amount"] == "50000.00"


def test_gestionnaire_can_create_on_assigned_building(
    client: TestClient,
    gestionnaire_headers: dict[str, str],
    sample_building: Building,
) -> None:
    response = client.post(
        "/api/v1/expenses",
        headers=gestionnaire_headers,
        json={
            "category_id": REPAIR_CATEGORY_ID,
            "building_id": str(sample_building.id),
            "description": "Nettoyage cage d'escalier",
            "amount": "30000.00",
            "payment_method": "cash",
            "expense_date": "2026-07-18",
        },
    )
    assert response.status_code == 201


def test_create_expense_requires_link(
    client: TestClient,
    super_admin_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/expenses",
        headers=super_admin_headers,
        json={
            "category_id": REPAIR_CATEGORY_ID,
            "description": "Dépense orpheline",
            "amount": "10000.00",
            "payment_method": "cash",
            "expense_date": "2026-07-18",
        },
    )
    assert response.status_code == 400
