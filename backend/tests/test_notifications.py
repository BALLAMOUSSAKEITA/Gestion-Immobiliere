import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.enums import EmailQueueStatus
from app.models.notification import EmailQueue, Notification
from app.models.role import Role
from app.models.user import User
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture()
def admin_headers(client: TestClient) -> dict[str, str]:
    return {"Authorization": f"Bearer {_login(client, 'admin@gestion-immo.local', 'Admin123!')}"}


def test_dispatch_and_list_notifications(db_session: Session) -> None:
    admin = db_session.query(User).filter(User.email == "admin@gestion-immo.local").one()
    service = NotificationService(db_session)
    service.dispatch(
        "payment.recorded",
        [admin.id],
        title="Test notification",
        body="Corps de test",
    )
    result = service.list_notifications(admin.id)
    assert result.total >= 1
    assert result.unread_count >= 1
    assert result.items[0].title == "Test notification"


def test_mark_read_and_unread_count(db_session: Session) -> None:
    admin = db_session.query(User).filter(User.email == "admin@gestion-immo.local").one()
    service = NotificationService(db_session)
    service.dispatch("message.received", [admin.id], title="Message", body="Hello")
    notification = (
        db_session.query(Notification)
        .filter(Notification.user_id == admin.id, Notification.is_read.is_(False))
        .first()
    )
    assert notification is not None
    assert service.get_unread_count(admin.id) >= 1
    service.mark_read(admin.id, notification.id)
    assert service.get_unread_count(admin.id) == 0


def test_email_queue_processing(db_session: Session) -> None:
    EmailService(db_session).enqueue("test@example.com", "Sujet test", "<p>Hello</p>")
    db_session.commit()
    processed = EmailService(db_session).process_queue()
    assert processed == 1
    item = db_session.query(EmailQueue).first()
    assert item is not None
    assert item.status == EmailQueueStatus.sent


def test_notification_api(client: TestClient, admin_headers: dict[str, str], db_session: Session) -> None:
    admin = db_session.query(User).filter(User.email == "admin@gestion-immo.local").one()
    NotificationService(db_session).dispatch(
        "repair.new",
        [admin.id],
        title="Réparation",
        body="Fuite signalée",
    )
    response = client.get("/api/v1/notifications/unread-count", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["count"] >= 1

    list_response = client.get("/api/v1/notifications", headers=admin_headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] >= 1


def test_notification_preferences(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = client.get("/api/v1/notification-preferences", headers=admin_headers)
    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1

    update = client.put(
        "/api/v1/notification-preferences",
        headers=admin_headers,
        json={
            "preferences": [
                {"event_code": "payment.recorded", "email_enabled": False},
            ]
        },
    )
    assert update.status_code == 200
    payment_pref = next(
        item for item in update.json()["items"] if item["event_code"] == "payment.recorded"
    )
    assert payment_pref["email_enabled"] is False
