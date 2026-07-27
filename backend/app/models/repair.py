import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import RepairAttachmentType, RepairStatus, UrgencyLevel


class Repair(Base, TimestampMixin):
    __tablename__ = "repairs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("units.id"), nullable=False
    )
    building_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("buildings.id"), nullable=False
    )
    reported_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    urgency: Mapped[UrgencyLevel] = mapped_column(
        Enum(UrgencyLevel, native_enum=False, length=20),
        default=UrgencyLevel.medium,
        nullable=False,
    )
    status: Mapped[RepairStatus] = mapped_column(
        Enum(RepairStatus, native_enum=False, length=30),
        default=RepairStatus.new,
        nullable=False,
    )
    estimated_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    final_cost: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    expense_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("expenses.id"), nullable=True
    )
    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    unit: Mapped["Unit"] = relationship("Unit")
    building: Mapped["Building"] = relationship("Building")
    reporter: Mapped["User"] = relationship("User", foreign_keys=[reported_by])
    assignee: Mapped["User | None"] = relationship("User", foreign_keys=[assigned_to])
    expense: Mapped["Expense | None"] = relationship("Expense", foreign_keys=[expense_id])
    attachments: Mapped[list["RepairAttachment"]] = relationship(
        "RepairAttachment", back_populates="repair", cascade="all, delete-orphan"
    )
    status_history: Mapped[list["RepairStatusHistory"]] = relationship(
        "RepairStatusHistory", back_populates="repair", cascade="all, delete-orphan"
    )


class RepairAttachment(Base):
    __tablename__ = "repair_attachments"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    repair_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("repairs.id", ondelete="CASCADE"), nullable=False
    )
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[RepairAttachmentType] = mapped_column(
        Enum(RepairAttachmentType, native_enum=False, length=20), nullable=False
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    repair: Mapped["Repair"] = relationship("Repair", back_populates="attachments")
    uploader: Mapped["User"] = relationship("User")


class RepairStatusHistory(Base):
    __tablename__ = "repair_status_history"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    repair_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("repairs.id", ondelete="CASCADE"), nullable=False
    )
    old_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    repair: Mapped["Repair"] = relationship("Repair", back_populates="status_history")
    changer: Mapped["User"] = relationship("User")
