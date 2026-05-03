"""fix_version

Revision ID: 90844f3ba0d4
Revises: 0006_add_list_types
Create Date: 2026-05-04 00:02:06.601931

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '90844f3ba0d4'
down_revision: Union[str, None] = '0006_add_list_types_shopping_tasks_wishlist'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
