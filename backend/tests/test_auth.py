def test_login_success(client) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@gestion-immo.local", "password": "Admin123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["user"]["role"] == "super_admin"


def test_login_invalid_password(client) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@gestion-immo.local", "password": "WrongPass1"},
    )
    assert response.status_code == 401


def test_me_without_token_returns_401(client) -> None:
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_with_token(client) -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@gestion-immo.local", "password": "Admin123!"},
    )
    token = login.json()["access_token"]
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@gestion-immo.local"
    assert data["role"]["code"] == "super_admin"


def test_refresh_token(client) -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@gestion-immo.local", "password": "Admin123!"},
    )
    refresh_token = login.json()["refresh_token"]
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_logout_revokes_refresh_token(client) -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@gestion-immo.local", "password": "Admin123!"},
    )
    tokens = login.json()
    logout = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert logout.status_code == 204

    refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh.status_code == 401


def test_admin_ping_forbidden_for_gestionnaire(client) -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "gestionnaire@gestion-immo.local", "password": "Agent123!"},
    )
    token = login.json()["access_token"]
    response = client.get(
        "/api/v1/admin/ping",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_admin_ping_success_for_super_admin(client) -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@gestion-immo.local", "password": "Admin123!"},
    )
    token = login.json()["access_token"]
    response = client.get(
        "/api/v1/admin/ping",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


def test_change_password(client) -> None:
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@gestion-immo.local", "password": "Admin123!"},
    )
    token = login.json()["access_token"]
    response = client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "current_password": "Admin123!",
            "new_password": "NewAdmin123!",
        },
    )
    assert response.status_code == 204

    failed_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@gestion-immo.local", "password": "Admin123!"},
    )
    assert failed_login.status_code == 401

    success_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@gestion-immo.local", "password": "NewAdmin123!"},
    )
    assert success_login.status_code == 200
