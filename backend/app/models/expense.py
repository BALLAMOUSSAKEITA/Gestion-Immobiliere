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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import ExpenseStatus, PaymentMethod


class ExpenseCategory(Base):
    __tablename__ = "expense_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    expenses: Mapped[list["Expense"]] = relationship("Expense", back_populates="category")


class Expense(Base, TimestampMixin):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("expense_categories.id"), nullable=False
    )
    building_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("buildings.id"), nullable=True
    )
    unit_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("units.id"), nullable=True
    )
    owner_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("owner_profiles.id"), nullable=True
    )
    supplier_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, native_enum=False, length=20), nullable=False
    )
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    receipt_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[ExpenseStatus] = mapped_column(
        Enum(ExpenseStatus, native_enum=False, length=20),
        default=ExpenseStatus.recorded,
        nullable=False,
    )
    requires_validation: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    validated_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=True
    )
    validated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    repair_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("repairs.id"), nullable=True
    )
    recorded_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )

    category: Mapped["ExpenseCategory"] = relationship("ExpenseCategory", back_populates="expenses")
    building: Mapped["Building | None"] = relationship("Building")
    unit: Mapped["Unit | None"] = relationship("Unit")
    owner_profile: Mapped["OwnerProfile | None"] = relationship("OwnerProfile")
    recorder: Mapped["User"] = relationship("User", foreign_keys=[recorded_by])
    validator: Mapped["User | None"] = relationship("User", foreign_keys=[validated_by])
