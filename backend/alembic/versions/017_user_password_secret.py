"""store recoverable password for super admin view

Revision ID: 017_user_password_secret
Revises: 016_payment_covered_period
Create Date: 2026-10-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "017_user_password_secret"
down_revision: Union[str, None] = "016_payment_covered_period"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_secret", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "password_secret")
