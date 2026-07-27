import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class OwnerProfile(Base, TimestampMixin):
    __tablename__ = "owner_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id"), unique=True, nullable=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User | None"] = relationship("User", back_populates="owner_profile")
    owner_assignments: Mapped[list["UserOwnerAssignment"]] = relationship(
        "UserOwnerAssignment", back_populates="owner_profile"
    )


class UserOwnerAssignment(Base):
    __tablename__ = "user_owner_assignments"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    owner_profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("owner_profiles.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="owner_assignment")
    owner_profile: Mapped["OwnerProfile"] = relationship(
        "OwnerProfile", back_populates="owner_assignments"
    )


class UserBuildingAssignment(Base):
    __tablename__ = "user_building_assignments"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    building_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    assigned_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="building_assignments", foreign_keys=[user_id]
    )
    building: Mapped["Building"] = relationship(
        "Building", back_populates="building_assignments"
    )
