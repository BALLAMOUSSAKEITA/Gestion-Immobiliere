import uuid
from datetime import datetime
from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
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

from app.models.base import Base, TimestampMixin
from app.models.enums import UnitStatus, UnitType


class Building(Base, TimestampMixin):
    __tablename__ = "buildings"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    commune: Mapped[str] = mapped_column(String(100), nullable=False)
    quartier: Mapped[str | None] = mapped_column(String(100), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    floor_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    apartment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shop_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    owner_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("owner_profiles.id"), nullable=True
    )
    manager_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    observations: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )

    owner_profile: Mapped["OwnerProfile | None"] = relationship("OwnerProfile")
    manager: Mapped["User | None"] = relationship("User", foreign_keys=[manager_user_id])
    units: Mapped[list["Unit"]] = relationship(
        "Unit", back_populates="building", cascade="all, delete-orphan"
    )
    building_assignments: Mapped[list["UserBuildingAssignment"]] = relationship(
        "UserBuildingAssignment", back_populates="building"
    )


class Unit(Base, TimestampMixin):
    __tablename__ = "units"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    building_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    type: Mapped[UnitType] = mapped_column(
        Enum(UnitType, native_enum=False, length=20), nullable=False
    )
    number: Mapped[str] = mapped_column(String(20), nullable=False)
    floor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rent_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    deposit_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0"), nullable=False
    )
    status: Mapped[UnitStatus] = mapped_column(
        Enum(UnitStatus, native_enum=False, length=20),
        default=UnitStatus.free,
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public_listing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    building: Mapped["Building"] = relationship("Building", back_populates="units")
    photos: Mapped[list["UnitPhoto"]] = relationship(
        "UnitPhoto", back_populates="unit", cascade="all, delete-orphan"
    )
    tenant_history: Mapped[list["UnitTenantHistory"]] = relationship(
        "UnitTenantHistory", back_populates="unit", cascade="all, delete-orphan"
    )
    leases: Mapped[list["Lease"]] = relationship("Lease", back_populates="unit")


class UnitPhoto(Base):
    __tablename__ = "unit_photos"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("units.id", ondelete="CASCADE"), nullable=False
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    unit: Mapped["Unit"] = relationship("Unit", back_populates="photos")


class UnitTenantHistory(Base):
    __tablename__ = "unit_tenant_history"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    unit_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("units.id", ondelete="CASCADE"), nullable=False
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("tenants.id"), nullable=True
    )
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    exit_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    rent_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    unit: Mapped["Unit"] = relationship("Unit", back_populates="tenant_history")
    tenant: Mapped["Tenant | None"] = relationship("Tenant")
