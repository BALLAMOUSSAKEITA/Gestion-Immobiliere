import pytest


def _login(client, email: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture()
def super_admin_headers(client):
    token = _login(client, "admin@gestion-immo.local", "Admin123!")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def gestionnaire_headers(client):
    token = _login(client, "gestionnaire@gestion-immo.local", "Agent123!")
    return {"Authorization": f"Bearer {token}"}


def test_list_users_requires_super_admin(client, gestionnaire_headers) -> None:
    response = client.get("/api/v1/users", headers=gestionnaire_headers)
    assert response.status_code == 403


def test_create_and_list_users(client, super_admin_headers) -> None:
    create = client.post(
        "/api/v1/users",
        headers=super_admin_headers,
        json={
            "email": "admin.familial@gestion-immo.local",
            "password": "FamilyAdmin1!",
            "first_name": "Marie",
            "last_name": "Famille",
            "phone": "+2250700000003",
            "role_code": "admin_familial",
            "permissions": [
                {"permission_code": "buildings.manage", "granted": True},
                {"permission_code": "reports.read", "granted": True},
            ],
        },
    )
    assert create.status_code == 201
    data = create.json()
    assert data["email"] == "admin.familial@gestion-immo.local"
    assert len(data["permissions"]) == 8

    listing = client.get("/api/v1/users", headers=super_admin_headers)
    assert listing.status_code == 200
    assert listing.json()["total"] >= 3


def test_create_proprietaire_requires_profile(client, super_admin_headers) -> None:
    profile = client.post(
        "/api/v1/owner-profiles",
        headers=super_admin_headers,
        json={
            "first_name": "Paul",
            "last_name": "Proprietaire",
            "phone": "+2250700000004",
            "email": "paul@example.com",
        },
    )
    assert profile.status_code == 201
    profile_id = profile.json()["id"]

    create = client.post(
        "/api/v1/users",
        headers=super_admin_headers,
        json={
            "email": "proprietaire@gestion-immo.local",
            "password": "OwnerPass123!",
            "first_name": "Paul",
            "last_name": "Proprietaire",
            "role_code": "proprietaire",
            "owner_profile_id": profile_id,
        },
    )
    assert create.status_code == 201
    assert create.json()["owner_profile_id"] == profile_id


def test_delete_user_removes_account(client, super_admin_headers) -> None:
    create = client.post(
        "/api/v1/users",
        headers=super_admin_headers,
        json={
            "email": "temp.user@gestion-immo.local",
            "password": "TempUser123!",
            "first_name": "Temp",
            "last_name": "User",
            "role_code": "visiteur",
        },
    )
    user_id = create.json()["id"]

    deleted = client.delete(f"/api/v1/users/{user_id}", headers=super_admin_headers)
    assert deleted.status_code == 204

    assert (
        client.get(f"/api/v1/users/{user_id}", headers=super_admin_headers).status_code
        == 404
    )

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "temp.user@gestion-immo.local", "password": "TempUser123!"},
    )
    assert login.status_code == 401


def test_update_permissions(client, super_admin_headers) -> None:
    create = client.post(
        "/api/v1/users",
        headers=super_admin_headers,
        json={
            "email": "permissions@gestion-immo.local",
            "password": "PermUser123!",
            "first_name": "Perm",
            "last_name": "User",
            "role_code": "admin_familial",
            "permissions": [{"permission_code": "reports.read", "granted": True}],
        },
    )
    user_id = create.json()["id"]

    update = client.put(
        f"/api/v1/users/{user_id}/permissions",
        headers=super_admin_headers,
        json=[
            {"permission_code": "reports.read", "granted": True},
            {"permission_code": "payments.manage", "granted": True},
        ],
    )
    assert update.status_code == 200
    granted = [item for item in update.json() if item["granted"]]
    assert len(granted) == 2
