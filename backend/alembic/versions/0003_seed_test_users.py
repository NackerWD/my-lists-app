"""seed_test_users

Insereix els usuaris de test NOMÉS quan ENVIRONMENT=test.
Permet que els tests d'integració funcionin sense fixtures de BD ad-hoc.

Revision ID: 0003_seed_test_users
Revises: 0002_seed_list_types
Create Date: 2026-04-17 18:00:00.000000

"""

import os
from typing import Sequence, Union

from alembic import op

revision: str = "0003_seed_test_users"
down_revision: Union[str, None] = "0002_seed_list_types"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if os.environ.get("ENVIRONMENT") == "test":
        op.execute("""
            INSERT INTO users (id, email, display_name, created_at)
            VALUES
                (
                    '550e8400-e29b-41d4-a716-446655440000',
                    'test@example.com',
                    'Test User',
                    NOW()
                ),
                (
                    '650e8400-e29b-41d4-a716-446655440001',
                    'other@example.com',
                    'Other User',
                    NOW()
                )
            ON CONFLICT (id) DO NOTHING
        """)


def downgrade() -> None:
    if os.environ.get("ENVIRONMENT") == "test":
        op.execute("""
            DELETE FROM users
            WHERE id IN (
                '550e8400-e29b-41d4-a716-446655440000',
                '650e8400-e29b-41d4-a716-446655440001'
            )
        """)
