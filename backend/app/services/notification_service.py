from datetime import UTC, datetime
from urllib.parse import quote
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.notification_events import DEFAULT_EVENT_CODES, EVENT_LABELS
from app.models.enums import NotificationChannel
from app.models.notification import Notification, NotificationPreference
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationPreferenceItem,
    NotificationPreferencesResponse,
    NotificationSummary,
)
from app.services.email_service import EmailService


class NotificationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.email_service = EmailService(db)

    def dispatch(
        self,
        event_code: str,
        user_ids: list[UUID],
        title: str,
        body: str,
        *,
        entity_type: str | None = None,
        entity_id: UUID | None = None,
        email_template: str | None = None,
        email_context: dict | None = None,
        email_subject: str | None = None,
    ) -> None:
        unique_ids = list(dict.fromkeys(user_ids))
        for user_id in unique_ids:
            prefs = self._get_or_create_preference(user_id, event_code)
            user = self.db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
            if user is None:
                continue

            if prefs.in_app_enabled:
                notification = Notification(
                    user_id=user_id,
                    event_code=event_code,
                    title=title,
                    body=body,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    channel=NotificationChannel.in_app,
                    sent_at=datetime.now(UTC),
                )
                self.db.add(notification)

            if prefs.email_enabled and email_template:
                context = email_context or {}
                context.setdefault("title", title)
                context.setdefault("body", body)
                html = self.email_service.render_template(email_template, context)
                self.email_service.enqueue(
                    user.email,
                    email_subject or title,
                    html,
                )
        self.db.commit()

    def list_notifications(
        self, user_id: UUID, *, limit: int = 50, unread_only: bool = False
    ) -> NotificationListResponse:
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read.is_(False))
        total = query.count()
        unread_count = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
            .count()
        )
        items = query.order_by(Notification.created_at.desc()).limit(limit).all()
        return NotificationListResponse(
            items=[self._to_summary(item) for item in items],
            total=total,
            unread_count=unread_count,
        )

    def get_unread_count(self, user_id: UUID) -> int:
        return (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
            .count()
        )

    def mark_read(self, user_id: UUID, notification_id: UUID) -> NotificationSummary:
        notification = self._get_or_404(notification_id)
        if notification.user_id != user_id:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        notification.is_read = True
        notification.read_at = datetime.now(UTC)
        self.db.commit()
        return self._to_summary(notification)

    def mark_all_read(self, user_id: UUID) -> int:
        count = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read.is_(False))
            .update(
                {"is_read": True, "read_at": datetime.now(UTC)},
                synchronize_session=False,
            )
        )
        self.db.commit()
        return count

    def get_preferences(self, user_id: UUID) -> NotificationPreferencesResponse:
        existing = {
            pref.event_code: pref
            for pref in self.db.query(NotificationPreference)
            .filter(NotificationPreference.user_id == user_id)
            .all()
        }
        items = []
        for code in DEFAULT_EVENT_CODES:
            pref = existing.get(code)
            items.append(
                NotificationPreferenceItem(
                    event_code=code,
                    label=EVENT_LABELS.get(code, code),
                    in_app_enabled=pref.in_app_enabled if pref else True,
                    email_enabled=pref.email_enabled if pref else True,
                    whatsapp_enabled=pref.whatsapp_enabled if pref else False,
                )
            )
        return NotificationPreferencesResponse(items=items)

    def update_preferences(
        self, user_id: UUID, updates: list[dict]
    ) -> NotificationPreferencesResponse:
        for item in updates:
            code = item["event_code"]
            pref = self._get_or_create_preference(user_id, code)
            if item.get("in_app_enabled") is not None:
                pref.in_app_enabled = item["in_app_enabled"]
            if item.get("email_enabled") is not None:
                pref.email_enabled = item["email_enabled"]
            if item.get("whatsapp_enabled") is not None:
                pref.whatsapp_enabled = item["whatsapp_enabled"]
        self.db.commit()
        return self.get_preferences(user_id)

    def build_whatsapp_link(self, phone: str, message: str) -> str:
        normalized = "".join(ch for ch in phone if ch.isdigit())
        return f"https://wa.me/{normalized}?text={quote(message)}"

    def _get_or_create_preference(
        self, user_id: UUID, event_code: str
    ) -> NotificationPreference:
        pref = (
            self.db.query(NotificationPreference)
            .filter(
                NotificationPreference.user_id == user_id,
                NotificationPreference.event_code == event_code,
            )
            .first()
        )
        if pref is None:
            pref = NotificationPreference(
                user_id=user_id,
                event_code=event_code,
                in_app_enabled=True,
                email_enabled=True,
                whatsapp_enabled=False,
            )
            self.db.add(pref)
            self.db.flush()
        return pref

    def _get_or_404(self, notification_id: UUID) -> Notification:
        notification = (
            self.db.query(Notification).filter(Notification.id == notification_id).first()
        )
        if notification is None:
            raise HTTPException(status_code=404, detail="Notification introuvable")
        return notification

    def _to_summary(self, notification: Notification) -> NotificationSummary:
        return NotificationSummary(
            id=str(notification.id),
            event_code=notification.event_code,
            title=notification.title,
            body=notification.body,
            entity_type=notification.entity_type,
            entity_id=str(notification.entity_id) if notification.entity_id else None,
            is_read=notification.is_read,
            read_at=notification.read_at,
            created_at=notification.created_at,
        )
