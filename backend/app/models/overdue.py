import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import (
    OverdueStatus,
    ReminderChannel,
    ReminderStatus,
    ReminderType,
)


class OverdueRecord(Base):
    __tablename__ = "overdue_records"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    rent_period_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("rent_periods.id"), unique=True, nullable=False
    )
    lease_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("leases.id"), nullable=False
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id"), nullable=False
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("units.id"), nullable=False
    )
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    period_month: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_due: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    amount_remaining: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    days_overdue: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[OverdueStatus] = mapped_column(
        Enum(OverdueStatus, native_enum=False, length=20),
        default=OverdueStatus.open,
        nullable=False,
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    rent_period: Mapped["RentPeriod"] = relationship("RentPeriod")
    tenant: Mapped["Tenant"] = relationship("Tenant")
    reminders: Mapped[list["Reminder"]] = relationship(
        "Reminder", back_populates="overdue_record"
    )


class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id"), nullable=False
    )
    overdue_record_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("overdue_records.id"), nullable=True
    )
    reminder_type: Mapped[ReminderType] = mapped_column(
        Enum(ReminderType, native_enum=False, length=20), nullable=False
    )
    channel: Mapped[ReminderChannel] = mapped_column(
        Enum(ReminderChannel, native_enum=False, length=20), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    sent_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    status: Mapped[ReminderStatus] = mapped_column(
        Enum(ReminderStatus, native_enum=False, length=20),
        default=ReminderStatus.sent,
        nullable=False,
    )

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="reminders")
    overdue_record: Mapped["OverdueRecord | None"] = relationship(
        "OverdueRecord", back_populates="reminders"
    )
    sender: Mapped["User | None"] = relationship("User", foreign_keys=[sent_by])
