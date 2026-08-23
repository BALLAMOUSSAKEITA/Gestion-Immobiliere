"""store covered rent period on payments

Revision ID: 016_payment_covered_period
Revises: 015_drop_reminders
Create Date: 2026-08-23

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "016_payment_covered_period"
down_revision: Union[str, None] = "015_drop_reminders"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("payments", sa.Column("covered_from", sa.Date(), nullable=True))
    op.add_column("payments", sa.Column("covered_to", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("payments", "covered_to")
    op.drop_column("payments", "covered_from")
