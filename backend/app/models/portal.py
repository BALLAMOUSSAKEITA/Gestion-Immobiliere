import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import NoticeType, VisitRequestStatus


class VisitRequest(Base, TimestampMixin):
    __tablename__ = "visit_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("units.id"), nullable=False
    )
    visitor_name: Mapped[str] = mapped_column(String(200), nullable=False)
    visitor_email: Mapped[str] = mapped_column(String(255), nullable=False)
    visitor_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    preferred_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    preferred_time: Mapped[str | None] = mapped_column(String(50), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[VisitRequestStatus] = mapped_column(
        Enum(VisitRequestStatus, native_enum=False, length=20),
        default=VisitRequestStatus.pending,
        nullable=False,
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )

    unit: Mapped["Unit"] = relationship("Unit")
    assignee: Mapped["User | None"] = relationship("User", foreign_keys=[assigned_to])


class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    sender_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    sender_name: Mapped[str] = mapped_column(String(200), nullable=False)
    sender_email: Mapped[str] = mapped_column(String(255), nullable=False)
    sender_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    recipient_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )
    unit_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("units.id"), nullable=True
    )
    subject: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    parent_message_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("contact_messages.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    sender: Mapped["User | None"] = relationship("User", foreign_keys=[sender_user_id])
    recipient: Mapped["User"] = relationship("User", foreign_keys=[recipient_user_id])
    replies: Mapped[list["ContactMessage"]] = relationship(
        "ContactMessage",
        back_populates="parent",
        foreign_keys=[parent_message_id],
    )
    parent: Mapped["ContactMessage | None"] = relationship(
        "ContactMessage",
        back_populates="replies",
        remote_side=[id],
        foreign_keys=[parent_message_id],
    )


class TenantNotice(Base):
    __tablename__ = "tenant_notices"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id"), nullable=False
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("documents.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    notice_type: Mapped[NoticeType] = mapped_column(
        Enum(NoticeType, native_enum=False, length=30),
        default=NoticeType.info,
        nullable=False,
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    published_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    tenant: Mapped["Tenant"] = relationship("Tenant")
    publisher: Mapped["User"] = relationship("User", foreign_keys=[published_by])
