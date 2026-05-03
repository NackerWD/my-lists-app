"""add_list_types_shopping_tasks_wishlist

Revision ID: 0006_add_list_types_shopping_tasks_wishlist
Revises: 0005_offline_push_schema
Create Date: 2026-05-03 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "0006_add_list_types_shopping_tasks_wishlist"
down_revision: Union[str, None] = "0005_offline_push_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO list_types (id, slug, label, icon, is_active)
        VALUES
            (gen_random_uuid(), 'shopping', 'Compres', 'shopping-cart', true),
            (gen_random_uuid(), 'tasks', 'Tasques', 'check-square', true),
            (gen_random_uuid(), 'wishlist', 'Wishlist', 'heart', true)
        ON CONFLICT (slug) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM list_types WHERE slug IN ('shopping', 'tasks', 'wishlist')
    """)
