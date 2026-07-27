import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.building import Building, Unit
from app.models.enums import IdDocumentType, LeaseStatus, UnitStatus, UnitType
from app.models.owner_profile import OwnerProfile, UserBuildingAssignment
from app.models.role import Role
from app.models.tenant import Lease, Tenant
from app.models.user import User


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
def public_unit(db_session: Session, owner_profile: OwnerProfile) -> Unit:
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
        status=UnitStatus.free,
        is_public_listing=True,
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


@pytest.fixture()
def tenant_user(db_session: Session, owner_profile: OwnerProfile) -> User:
    now = datetime.now(UTC)
    role = db_session.query(Role).filter(Role.code == "locataire").one()
    user = User(
        id=uuid.UUID("00000000-0000-4000-8000-000000000012"),
        email="locataire@gestion-immo.local",
        password_hash=hash_password("Locataire123!"),
        first_name="Aminata",
        last_name="Traoré",
        role_id=role.id,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    tenant = Tenant(
        id=uuid.UUID("00000000-0000-4000-8000-000000000060"),
        user_id=user.id,
        first_name="Aminata",
        last_name="Traoré",
        phone_primary="+2250700000002",
        id_document_type=IdDocumentType.cni,
        id_document_number="CI1234567890",
        created_by=uuid.UUID("00000000-0000-4000-8000-000000000010"),
    )
    building = Building(
        id=uuid.UUID("00000000-0000-4000-8000-000000000031"),
        code="KM002",
        name="Résidence Horizon",
        address="Rue 5, Plateau",
        commune="Abidjan",
        owner_profile_id=owner_profile.id,
        manager_user_id=uuid.UUID("00000000-0000-4000-8000-000000000011"),
        created_by=uuid.UUID("00000000-0000-4000-8000-000000000010"),
    )
    unit = Unit(
        id=uuid.UUID("00000000-0000-4000-8000-000000000051"),
        building_id=building.id,
        code="KM002-B201",
        type=UnitType.apartment,
        number="02",
        floor=2,
        rent_amount=Decimal("300000"),
        status=UnitStatus.occupied,
    )
    lease = Lease(
        id=uuid.UUID("00000000-0000-4000-8000-000000000070"),
        tenant_id=tenant.id,
        unit_id=unit.id,
        start_date=date(2025, 1, 1),
        end_date=date(2026, 12, 31),
        rent_amount=Decimal("300000"),
        deposit_amount=Decimal("600000"),
        status=LeaseStatus.active,
        created_by=uuid.UUID("00000000-0000-4000-8000-000000000010"),
    )
    db_session.add_all([user, tenant, building, unit, lease])
    db_session.commit()
    return user


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture()
def super_admin_headers(client: TestClient) -> dict[str, str]:
    return {"Authorization": f"Bearer {_login(client, 'admin@gestion-immo.local', 'Admin123!')}"}


@pytest.fixture()
def gestionnaire_headers(client: TestClient) -> dict[str, str]:
    return {"Authorization": f"Bearer {_login(client, 'gestionnaire@gestion-immo.local', 'Agent123!')}"}


@pytest.fixture()
def tenant_headers(client: TestClient, tenant_user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {_login(client, 'locataire@gestion-immo.local', 'Locataire123!')}"}


def test_create_public_visit_request(client: TestClient, public_unit: Unit) -> None:
    response = client.post(
        "/api/v1/public/visit-requests",
        json={
            "unit_id": str(public_unit.id),
            "visitor_name": "Jean Dupont",
            "visitor_email": "jean@example.com",
            "visitor_phone": "+22501020304",
            "preferred_date": "2026-08-01",
            "message": "Je souhaite visiter ce logement.",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["visitor_name"] == "Jean Dupont"
    assert data["status"] == "pending"
    assert data["unit_code"] == public_unit.code


def test_public_contact(client: TestClient, public_unit: Unit) -> None:
    response = client.post(
        "/api/v1/public/contact",
        json={
            "sender_name": "Marie Kouassi",
            "sender_email": "marie@example.com",
            "unit_id": str(public_unit.id),
            "subject": "Question sur le loyer",
            "body": "Le loyer inclut-il les charges ?",
        },
    )
    assert response.status_code == 201
    assert response.json()["subject"] == "Question sur le loyer"


def test_list_visit_requests_as_gestionnaire(
    client: TestClient,
    gestionnaire_headers: dict[str, str],
    public_unit: Unit,
) -> None:
    client.post(
        "/api/v1/public/visit-requests",
        json={
            "unit_id": str(public_unit.id),
            "visitor_name": "Paul Visitor",
            "visitor_email": "paul@example.com",
            "visitor_phone": "+22505060708",
        },
    )
    response = client.get("/api/v1/visit-requests", headers=gestionnaire_headers)
    assert response.status_code == 200
    assert response.json()["total"] >= 1


def test_update_visit_request(
    client: TestClient,
    gestionnaire_headers: dict[str, str],
    public_unit: Unit,
) -> None:
    create = client.post(
        "/api/v1/public/visit-requests",
        json={
            "unit_id": str(public_unit.id),
            "visitor_name": "Paul Visitor",
            "visitor_email": "paul@example.com",
            "visitor_phone": "+22505060708",
        },
    )
    request_id = create.json()["id"]
    response = client.patch(
        f"/api/v1/visit-requests/{request_id}",
        headers=gestionnaire_headers,
        json={"status": "confirmed"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"


def test_tenant_dashboard(
    client: TestClient,
    tenant_headers: dict[str, str],
) -> None:
    response = client.get("/api/v1/tenant-portal/dashboard", headers=tenant_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["has_active_lease"] is True
    assert data["tenant"]["full_name"] == "Aminata Traoré"
    assert data["unit"]["code"] == "KM002-B201"


def test_tenant_my_unit_and_lease(
    client: TestClient,
    tenant_headers: dict[str, str],
) -> None:
    unit = client.get("/api/v1/tenant-portal/my-unit", headers=tenant_headers)
    assert unit.status_code == 200
    assert unit.json()["code"] == "KM002-B201"

    lease = client.get("/api/v1/tenant-portal/my-lease", headers=tenant_headers)
    assert lease.status_code == 200
    assert lease.json()["status"] == "active"


def test_publish_tenant_notice(
    client: TestClient,
    super_admin_headers: dict[str, str],
) -> None:
    tenant_id = "00000000-0000-4000-8000-000000000060"
    response = client.post(
        "/api/v1/tenant-notices",
        headers=super_admin_headers,
        json={
            "tenant_id": str(tenant_id),
            "title": "Rappel de paiement",
            "content": "Merci de régulariser votre loyer.",
            "notice_type": "payment_reminder",
        },
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Rappel de paiement"


def test_tenant_notices(
    client: TestClient,
    super_admin_headers: dict[str, str],
    tenant_headers: dict[str, str],
) -> None:
    client.post(
        "/api/v1/tenant-notices",
        headers=super_admin_headers,
        json={
            "tenant_id": "00000000-0000-4000-8000-000000000060",
            "title": "Info maintenance",
            "notice_type": "maintenance",
        },
    )
    response = client.get("/api/v1/tenant-portal/notices", headers=tenant_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_tenant_send_message(
    client: TestClient,
    tenant_headers: dict[str, str],
) -> None:
    response = client.post(
        "/api/v1/tenant-portal/messages",
        headers=tenant_headers,
        json={
            "subject": "Fuite d'eau",
            "body": "Il y a une fuite dans la salle de bain.",
        },
    )
    assert response.status_code == 201
    assert response.json()["subject"] == "Fuite d'eau"
