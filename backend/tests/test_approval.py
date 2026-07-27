from app.core import approval_actions


def _login(client, email: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_create_and_approve_tenant_delete_request(client, db_session):
    admin_token = _login(client, "admin@gestion-immo.local", "Admin123!")
    gest_token = _login(client, "gestionnaire@gestion-immo.local", "Agent123!")

    create_resp = client.post(
        "/api/v1/tenants",
        headers={"Authorization": f"Bearer {gest_token}"},
        json={
            "first_name": "Test",
            "last_name": "Approval",
            "phone_primary": "+22370000099",
            "id_document_type": "cni",
            "id_document_number": "APPROVAL-001",
        },
    )
    assert create_resp.status_code == 201
    tenant_id = create_resp.json()["id"]

    delete_resp = client.delete(
        f"/api/v1/tenants/{tenant_id}",
        headers={"Authorization": f"Bearer {gest_token}"},
    )
    assert delete_resp.status_code == 403

    delete_req = client.delete(
        f"/api/v1/tenants/{tenant_id}?reason=Doublon",
        headers={"Authorization": f"Bearer {gest_token}"},
    )
    assert delete_req.status_code == 202
    request_id = delete_req.json()["id"]

    approve_resp = client.post(
        f"/api/v1/approval-requests/{request_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={},
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "approved"

    tenant_resp = client.get(
        f"/api/v1/tenants/{tenant_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert tenant_resp.status_code == 200
    assert tenant_resp.json()["is_active"] is False


def test_reject_approval_requires_comment(client):
    admin_token = _login(client, "admin@gestion-immo.local", "Admin123!")
    gest_token = _login(client, "gestionnaire@gestion-immo.local", "Agent123!")

    create_resp = client.post(
        "/api/v1/approval-requests",
        headers={"Authorization": f"Bearer {gest_token}"},
        json={
            "action_code": approval_actions.TENANT_DELETE,
            "entity_type": "tenant",
            "entity_id": "00000000-0000-0000-0000-000000000099",
            "reason": "Test rejet sans entité réelle",
        },
    )
    assert create_resp.status_code == 201
    request_id = create_resp.json()["id"]

    reject_resp = client.post(
        f"/api/v1/approval-requests/{request_id}/reject",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={},
    )
    assert reject_resp.status_code == 400

    reject_ok = client.post(
        f"/api/v1/approval-requests/{request_id}/reject",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"review_comment": "Demande non justifiée"},
    )
    assert reject_ok.status_code == 200
    assert reject_ok.json()["status"] == "rejected"


def test_audit_logs_list_super_admin_only(client):
    admin_token = _login(client, "admin@gestion-immo.local", "Admin123!")
    gest_token = _login(client, "gestionnaire@gestion-immo.local", "Agent123!")

    client.post(
        "/api/v1/approval-requests",
        headers={"Authorization": f"Bearer {gest_token}"},
        json={
            "action_code": approval_actions.DOCUMENT_DELETE,
            "entity_type": "document",
            "entity_id": "00000000-0000-0000-0000-000000000088",
            "reason": "Document obsolète",
        },
    )

    denied = client.get(
        "/api/v1/audit-logs",
        headers={"Authorization": f"Bearer {gest_token}"},
    )
    assert denied.status_code == 403

    allowed = client.get(
        "/api/v1/audit-logs",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert allowed.status_code == 200
    assert allowed.json()["total"] >= 1
