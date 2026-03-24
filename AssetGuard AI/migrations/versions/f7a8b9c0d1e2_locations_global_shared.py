"""Make locations global (not tenant-scoped).

Revision ID: f7a8b9c0d1e2
Revises: e1f2a3b4c5d6
Create Date: 2026-03-24
"""

from alembic import op

revision = "f7a8b9c0d1e2"
down_revision = "e1f2a3b4c5d6"
branch_labels = None
depends_on = None


def upgrade():
    # pylint: disable=no-member
    with op.batch_alter_table("locations", schema=None) as batch_op:
        batch_op.drop_constraint("uq_location_company_name", type_="unique")
        batch_op.drop_index("ix_locations_company_id")
        batch_op.drop_column("company_id")
        batch_op.create_unique_constraint("uq_location_name", ["name"])


def downgrade():
    raise NotImplementedError("Downgrade not supported for this schema pivot")
