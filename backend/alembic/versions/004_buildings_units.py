"""buildings and units tables

Revision ID: 004_buildings
Revises: 003_users
Create Date: 2026-07-28

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_buildings"
down_revision: Union[str, None] = "003_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "buildings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("commune", sa.String(length=100), nullable=False),
        sa.Column("quartier", sa.String(length=100), nullable=True),
        sa.Column("photo_url", sa.String(length=500), nullable=True),
        sa.Column("floor_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("apartment_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("shop_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("owner_profile_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("manager_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("observations", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["manager_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["owner_profile_id"], ["owner_profiles.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "units",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("building_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("number", sa.String(length=20), nullable=False),
        sa.Column("floor", sa.Integer(), nullable=True),
        sa.Column("rent_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("deposit_amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'free'")),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_public_listing", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "unit_photos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "unit_tenant_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("unit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("entry_date", sa.Date(), nullable=False),
        sa.Column("exit_date", sa.Date(), nullable=True),
        sa.Column("rent_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["unit_id"], ["units.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_foreign_key(
        "fk_user_building_assignments_building_id",
        "user_building_assignments",
        "buildings",
        ["building_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_user_building_assignments_building_id",
        "user_building_assignments",
        type_="foreignkey",
    )
    op.drop_table("unit_tenant_history")
    op.drop_table("unit_photos")
    op.drop_table("units")
    op.drop_table("buildings")
