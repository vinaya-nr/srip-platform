"""enforce case-insensitive unique shop names

Revision ID: 20260220_0003
Revises: 20260218_0002
Create Date: 2026-02-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260220_0003"
down_revision: Union[str, Sequence[str], None] = "20260218_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE shops SET name = btrim(name) WHERE name <> btrim(name)")
    op.create_index("uq_shops_name_ci", "shops", [sa.text("lower(name)")], unique=True)


def downgrade() -> None:
    op.drop_index("uq_shops_name_ci", table_name="shops")
