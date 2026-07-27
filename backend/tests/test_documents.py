import io
import uuid
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.document_types_seed import LEASE_CONTRACT_TYPE_ID
from app.models.building import Building, Unit
from app.models.enums import IdDocumentType, LeaseStatus, UnitStatus, UnitType
from app.models.owner_profile import UserBuildingAssignment
from app.models.tenant import Lease, Tenant


@pytest.fixture()
def sample_lease(db_session: Session) -> Lease:
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
    db_session.add(
        UserBuildingAssignment(
            user_id=uuid.UUID("00000000-0000-4000-8000-000000000011"),
            building_id=building.id,
            assigned_by=uuid.UUID("00000000-0000-4000-8000-000000000010"),
        )
    )
    db_session.commit()
    return lease


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


def test_list_document_types(client: TestClient, super_admin_headers: dict[str, str]) -> None:
    response = client.get("/api/v1/document-types", headers=super_admin_headers)
    assert response.status_code == 200
    assert len(response.json()) == 12


def test_upload_and_download_document(
    client: TestClient,
    super_admin_headers: dict[str, str],
    sample_lease: Lease,
) -> None:
    pdf_content = b"%PDF-1.4 test document"
    response = client.post(
        "/api/v1/documents",
        headers=super_admin_headers,
        data={
            "document_type_id": str(LEASE_CONTRACT_TYPE_ID),
            "title": "Contrat bail test",
            "entity_type": "lease",
            "entity_id": str(sample_lease.id),
            "description": "Bail signé",
        },
        files={"file": ("contrat.pdf", io.BytesIO(pdf_content), "application/pdf")},
    )
    assert response.status_code == 201
    document_id = response.json()["id"]
    assert response.json()["document_type_code"] == "lease_contract"

    download = client.get(
        f"/api/v1/documents/{document_id}/download",
        headers=super_admin_headers,
    )
    assert download.status_code == 200
    assert download.content.startswith(b"%PDF")


def test_lease_documents_shortcut(
    client: TestClient,
    super_admin_headers: dict[str, str],
    sample_lease: Lease,
) -> None:
    client.post(
        "/api/v1/documents",
        headers=super_admin_headers,
        data={
            "document_type_id": str(LEASE_CONTRACT_TYPE_ID),
            "title": "Contrat",
            "entity_type": "lease",
            "entity_id": str(sample_lease.id),
        },
        files={"file": ("contrat.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
    )
    response = client.get(
        f"/api/v1/leases/{sample_lease.id}/documents",
        headers=super_admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_document_share_token(
    client: TestClient,
    super_admin_headers: dict[str, str],
    sample_lease: Lease,
) -> None:
    upload = client.post(
        "/api/v1/documents",
        headers=super_admin_headers,
        data={
            "document_type_id": str(LEASE_CONTRACT_TYPE_ID),
            "title": "Contrat partage",
            "entity_type": "lease",
            "entity_id": str(sample_lease.id),
        },
        files={"file": ("contrat.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
    )
    document_id = upload.json()["id"]
    share = client.post(
        f"/api/v1/documents/{document_id}/share",
        headers=super_admin_headers,
        json={"expires_in_days": 7, "max_access": 5},
    )
    assert share.status_code == 200
    token = share.json()["share_token"]

    public = client.get(f"/api/v1/documents/shared/{token}")
    assert public.status_code == 200
    assert public.json()["title"] == "Contrat partage"

    download = client.get(f"/api/v1/documents/shared/{token}/download")
    assert download.status_code == 200
