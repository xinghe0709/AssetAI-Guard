"""Add unique constraint on load_capacities (asset_id, name, metric)

Revision ID: d3e4f5a6b7c8
Revises: a9b8c7d6e5f4
Create Date: 2026-03-25

"""
from alembic import op


revision = "d3e4f5a6b7c8"
down_revision = "a9b8c7d6e5f4"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("load_capacities", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uq_capacity_asset_name_metric", ["asset_id", "name", "metric"]
        )


def downgrade():
    with op.batch_alter_table("load_capacities", schema=None) as batch_op:
        batch_op.drop_constraint("uq_capacity_asset_name_metric", type_="unique")
