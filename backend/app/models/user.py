import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("roles.id"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    role: Mapped["Role"] = relationship("Role", back_populates="users")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user"
    )
    permissions: Mapped[list["UserPermission"]] = relationship(
        "UserPermission", back_populates="user", cascade="all, delete-orphan"
    )
    owner_profile: Mapped["OwnerProfile | None"] = relationship(
        "OwnerProfile", back_populates="user", uselist=False
    )
    owner_assignment: Mapped["UserOwnerAssignment | None"] = relationship(
        "UserOwnerAssignment", back_populates="user", uselist=False
    )
    building_assignments: Mapped[list["UserBuildingAssignment"]] = relationship(
        "UserBuildingAssignment",
        back_populates="user",
        foreign_keys="UserBuildingAssignment.user_id",
        cascade="all, delete-orphan",
    )
    tenant_profile: Mapped["Tenant | None"] = relationship(
        "Tenant", back_populates="user", uselist=False, foreign_keys="Tenant.user_id"
    )
    approval_requests: Mapped[list["ApprovalRequest"]] = relationship(
        "ApprovalRequest",
        back_populates="requester",
        foreign_keys="ApprovalRequest.requested_by",
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="user"
    )
