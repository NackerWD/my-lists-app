"""add list types shopping tasks wishlist (compatibility stub)

Revision ID: 0006_list_types
Revises: 0005_offline_push_schema
Create Date: 2026-05-04

"""

from typing import Sequence, Union

from alembic import op

revision: str = '0006_list_types'
down_revision: Union[str, None] = '0005_offline_push_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(64)")


def downgrade() -> None:
    pass
