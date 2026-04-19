"""add_invitation_role

Revision ID: 0004_add_invitation_role
Revises: 0003_seed_test_users
Create Date: 2026-04-18 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_add_invitation_role"
down_revision: Union[str, None] = "0003_seed_test_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "list_invitations",
        sa.Column("role", sa.String(10), nullable=False, server_default="viewer"),
    )
    op.create_check_constraint(
        "ck_list_invitation_role",
        "list_invitations",
        "role IN ('editor', 'viewer')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_list_invitation_role", "list_invitations", type_="check")
    op.drop_column("list_invitations", "role")
