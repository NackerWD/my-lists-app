"""device_tokens unique token + list_items reminded_at

Revision ID: 0005_offline_push_schema
Revises: 0004_add_invitation_role
Create Date: 2026-04-19 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_offline_push_schema"
down_revision: Union[str, None] = "0004_add_invitation_role"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint("uq_device_tokens_token", "device_tokens", ["token"])
    op.add_column(
        "list_items",
        sa.Column("reminded_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("list_items", "reminded_at")
    op.drop_constraint("uq_device_tokens_token", "device_tokens", type_="unique")
