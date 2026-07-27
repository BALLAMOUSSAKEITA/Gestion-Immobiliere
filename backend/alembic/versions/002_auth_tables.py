"""auth tables and seed data

Revision ID: 002_auth
Revises: 001_initial
Create Date: 2026-07-26

"""

import os
from typing import Sequence, Union

import bcrypt
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_auth"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ROLE_IDS = {
    "super_admin": "00000000-0000-4000-8000-000000000001",
    "admin_familial": "00000000-0000-4000-8000-000000000002",
    "proprietaire": "00000000-0000-4000-8000-000000000003",
    "gestionnaire": "00000000-0000-4000-8000-000000000004",
    "visiteur": "00000000-0000-4000-8000-000000000005",
    "locataire": "00000000-0000-4000-8000-000000000006",
}

SUPER_ADMIN_USER_ID = "00000000-0000-4000-8000-000000000010"


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    roles_table = sa.table(
        "roles",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String()),
        sa.column("label", sa.String()),
        sa.column("description", sa.Text()),
    )

    op.bulk_insert(
        roles_table,
        [
            {"id": ROLE_IDS["super_admin"], "code": "super_admin", "label": "Super Administrateur", "description": None},
            {"id": ROLE_IDS["admin_familial"], "code": "admin_familial", "label": "Administrateur Familial", "description": None},
            {"id": ROLE_IDS["proprietaire"], "code": "proprietaire", "label": "Propriétaire", "description": None},
            {"id": ROLE_IDS["gestionnaire"], "code": "gestionnaire", "label": "Gestionnaire", "description": None},
            {"id": ROLE_IDS["visiteur"], "code": "visiteur", "label": "Visiteur", "description": None},
            {"id": ROLE_IDS["locataire"], "code": "locataire", "label": "Locataire", "description": None},
        ],
    )

    import os

    super_admin_password = os.getenv("SUPER_ADMIN_PASSWORD", "Admin123!")
    super_admin_email = os.getenv("SUPER_ADMIN_EMAIL", "admin@gestion-immo.local")
    password_hash = bcrypt.hashpw(
        super_admin_password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")

    users_table = sa.table(
        "users",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("email", sa.String()),
        sa.column("password_hash", sa.String()),
        sa.column("first_name", sa.String()),
        sa.column("last_name", sa.String()),
        sa.column("phone", sa.String()),
        sa.column("role_id", postgresql.UUID(as_uuid=True)),
        sa.column("is_active", sa.Boolean()),
    )

    op.bulk_insert(
        users_table,
        [
            {
                "id": SUPER_ADMIN_USER_ID,
                "email": super_admin_email,
                "password_hash": password_hash,
                "first_name": "Super",
                "last_name": "Admin",
                "phone": "+2250700000000",
                "role_id": ROLE_IDS["super_admin"],
                "is_active": True,
            }
        ],
    )


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_table("users")
    op.drop_table("roles")
