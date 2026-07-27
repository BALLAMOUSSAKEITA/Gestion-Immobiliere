def _login(client, email: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_dashboard_kpis_super_admin(client):
    token = _login(client, "admin@gestion-immo.local", "Admin123!")
    response = client.get(
        "/api/v1/dashboard/kpis",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_buildings" in data
    assert "overdue_amount" in data
    assert data["show_financials"] is True


def test_dashboard_kpis_gestionnaire_limited_financials(client):
    token = _login(client, "gestionnaire@gestion-immo.local", "Agent123!")
    response = client.get(
        "/api/v1/dashboard/kpis",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["show_financials"] is False
    assert data["expected_rent_month"] is None
    assert data["net_profit_month"] is None


def test_generate_monthly_report(client):
    token = _login(client, "admin@gestion-immo.local", "Admin123!")
    response = client.post(
        "/api/v1/reports/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "report_type": "monthly",
            "period_start": "2026-07-01",
            "period_end": "2026-07-31",
            "export_formats": ["pdf", "excel"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["pdf_url"] is not None
    assert data["excel_url"] is not None
    assert "kpis" in data["data"]

    list_resp = client.get(
        "/api/v1/reports",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] >= 1
