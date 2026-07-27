from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.building import Unit
from app.models.portal import ContactMessage
from app.models.role import Role
from app.models.user import User
from app.schemas.portal import (
    MessageCreate,
    MessageListResponse,
    MessageReplyCreate,
    MessageSummary,
    PublicContactCreate,
)
from app.services.building_service import BuildingAccessService


class MessageService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_public_contact(self, payload: PublicContactCreate) -> MessageSummary:
        recipient_id = self._resolve_recipient(
            UUID(payload.unit_id) if payload.unit_id else None
        )
        message = ContactMessage(
            sender_user_id=None,
            sender_name=payload.sender_name.strip(),
            sender_email=str(payload.sender_email),
            sender_phone=payload.sender_phone,
            recipient_user_id=recipient_id,
            unit_id=UUID(payload.unit_id) if payload.unit_id else None,
            subject=payload.subject.strip(),
            body=payload.body.strip(),
        )
        self.db.add(message)
        self.db.commit()
        from app.services.notification_hooks import notify_message_received

        notify_message_received(self.db, recipient_id, message.subject, message.sender_name)
        return self._to_summary(message)

    def send_as_user(self, actor: User, payload: MessageCreate) -> MessageSummary:
        recipient_id = self._resolve_recipient_for_actor(actor, payload)
        message = ContactMessage(
            sender_user_id=actor.id,
            sender_name=f"{actor.first_name} {actor.last_name}",
            sender_email=actor.email,
            sender_phone=actor.phone,
            recipient_user_id=recipient_id,
            unit_id=UUID(payload.unit_id) if payload.unit_id else None,
            subject=payload.subject.strip(),
            body=payload.body.strip(),
        )
        self.db.add(message)
        self.db.commit()
        from app.services.notification_hooks import notify_message_received

        notify_message_received(self.db, recipient_id, message.subject, message.sender_name)
        return self._to_summary(message)

    def list_messages(self, actor: User) -> MessageListResponse:
        if actor.role.code == "locataire":
            query = self.db.query(ContactMessage).filter(
                (ContactMessage.sender_user_id == actor.id)
                | (ContactMessage.recipient_user_id == actor.id)
            )
        elif actor.role.code in ("super_admin", "admin_familial", "gestionnaire"):
            query = self.db.query(ContactMessage).join(Unit, ContactMessage.unit_id == Unit.id, isouter=True)
            allowed = BuildingAccessService.accessible_building_ids(self.db, actor)
            if allowed is not None:
                query = query.filter(
                    (Unit.building_id.in_(allowed) if allowed else Unit.id.is_(None))
                    | ContactMessage.recipient_user_id == actor.id
                    | ContactMessage.sender_user_id == actor.id
                )
        else:
            raise HTTPException(status_code=403, detail="Accès non autorisé")

        items = query.order_by(ContactMessage.created_at.desc()).limit(100).all()
        return MessageListResponse(
            items=[self._to_summary(item) for item in items],
            total=len(items),
        )

    def reply(self, actor: User, message_id: UUID, payload: MessageReplyCreate) -> MessageSummary:
        if actor.role.code not in ("super_admin", "admin_familial", "gestionnaire"):
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        parent = self._get_or_404(message_id)
        reply = ContactMessage(
            sender_user_id=actor.id,
            sender_name=f"{actor.first_name} {actor.last_name}",
            sender_email=actor.email,
            sender_phone=actor.phone,
            recipient_user_id=parent.sender_user_id or parent.recipient_user_id,
            unit_id=parent.unit_id,
            subject=f"Re: {parent.subject}",
            body=payload.body.strip(),
            parent_message_id=parent.id,
        )
        self.db.add(reply)
        self.db.commit()
        recipient_id = reply.recipient_user_id
        from app.services.notification_hooks import notify_message_received

        notify_message_received(self.db, recipient_id, reply.subject, reply.sender_name)
        return self._to_summary(reply)

    def mark_read(self, actor: User, message_id: UUID) -> MessageSummary:
        message = self._get_or_404(message_id)
        if message.recipient_user_id != actor.id and actor.role.code not in (
            "super_admin",
            "admin_familial",
            "gestionnaire",
        ):
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        message.is_read = True
        message.read_at = datetime.now(UTC)
        self.db.commit()
        return self._to_summary(message)

    def _resolve_recipient_for_actor(self, actor: User, payload: MessageCreate) -> UUID:
        if actor.role.code == "locataire":
            if payload.recipient_user_id:
                return UUID(payload.recipient_user_id)
            return self._resolve_recipient(
                UUID(payload.unit_id) if payload.unit_id else None
            )
        if payload.recipient_user_id:
            return UUID(payload.recipient_user_id)
        raise HTTPException(status_code=400, detail="Destinataire requis")

    def _resolve_recipient(self, unit_id: UUID | None) -> UUID:
        if unit_id:
            unit = (
                self.db.query(Unit)
                .options(joinedload(Unit.building))
                .filter(Unit.id == unit_id)
                .first()
            )
            if unit and unit.building.manager_user_id:
                return unit.building.manager_user_id
        manager = (
            self.db.query(User)
            .join(Role)
            .filter(Role.code.in_(("gestionnaire", "super_admin")), User.is_active.is_(True))
            .first()
        )
        if manager is None:
            raise HTTPException(status_code=400, detail="Aucun gestionnaire disponible")
        return manager.id

    def _get_or_404(self, message_id: UUID) -> ContactMessage:
        message = self.db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
        if message is None:
            raise HTTPException(status_code=404, detail="Message introuvable")
        return message

    def _to_summary(self, message: ContactMessage) -> MessageSummary:
        return MessageSummary(
            id=str(message.id),
            sender_name=message.sender_name,
            sender_email=message.sender_email,
            subject=message.subject,
            body=message.body,
            is_read=message.is_read,
            created_at=message.created_at,
            parent_message_id=str(message.parent_message_id) if message.parent_message_id else None,
        )
