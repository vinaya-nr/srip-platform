"""enforce case-insensitive unique category name per shop

Revision ID: 20260220_0004
Revises: 20260220_0003
Create Date: 2026-02-20
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260220_0004"
down_revision: Union[str, Sequence[str], None] = "20260220_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE categories SET name = btrim(name) WHERE name <> btrim(name)")
    op.execute(
        "CREATE UNIQUE INDEX uq_categories_shop_name_ci ON categories (shop_id, lower(name))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX uq_categories_shop_name_ci")
