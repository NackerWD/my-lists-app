"""seed_list_types

Revision ID: 0002_seed_list_types
Revises: 0001_initial_schema
Create Date: 2026-04-17 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "0002_seed_list_types"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO list_types (id, slug, label, icon, is_active)
        VALUES (
            gen_random_uuid(),
            'todo',
            'Tasques',
            'check-square',
            true
        )
        ON CONFLICT (slug) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DELETE FROM list_types WHERE slug = 'todo'")
