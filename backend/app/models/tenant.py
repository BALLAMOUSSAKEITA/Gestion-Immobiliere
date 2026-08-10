import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
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
from app.models.enums import IdDocumentType, LeaseStatus, PaymentMethod


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), unique=True, nullable=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone_primary: Mapped[str] = mapped_column(String(20), nullable=False)
    phone_secondary: Mapped[str | None] = mapped_column(String(20), nullable=True)
    profession: Mapped[str | None] = mapped_column(String(200), nullable=True)
    previous_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    id_document_type: Mapped[IdDocumentType] = mapped_column(
        Enum(IdDocumentType, native_enum=False, length=20), nullable=False
    )
    id_document_number: Mapped[str] = mapped_column(String(50), nullable=False)
    id_document_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    payment_method: Mapped[PaymentMethod | None] = mapped_column(
        Enum(PaymentMethod, native_enum=False, length=20), nullable=True
    )
    observations: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )

    user: Mapped["User | None"] = relationship(
        "User", back_populates="tenant_profile", foreign_keys=[user_id]
    )
    leases: Mapped[list["Lease"]] = relationship(
        "Lease", back_populates="tenant", cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="tenant")


class Lease(Base, TimestampMixin):
    __tablename__ = "leases"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("units.id"), nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    rent_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    deposit_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), nullable=False
    )
    deposit_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[LeaseStatus] = mapped_column(
        Enum(LeaseStatus, native_enum=False, length=20),
        default=LeaseStatus.pending,
        nullable=False,
    )
    contract_document_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    termination_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    termination_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )

    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="leases")
    unit: Mapped["Unit"] = relationship("Unit", back_populates="leases")
    rent_history: Mapped[list["LeaseRentHistory"]] = relationship(
        "LeaseRentHistory", back_populates="lease", cascade="all, delete-orphan"
    )
    rent_periods: Mapped[list["RentPeriod"]] = relationship(
        "RentPeriod", back_populates="lease", cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="lease")


class LeaseRentHistory(Base):
    __tablename__ = "lease_rent_history"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    lease_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("leases.id", ondelete="CASCADE"), nullable=False
    )
    old_rent_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    new_rent_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    changed_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    lease: Mapped["Lease"] = relationship("Lease", back_populates="rent_history")
