"""Replace unique constraint: (asset_id, name, metric) -> (asset_id, name)

Each capacity name is now strictly paired with one metric,
so uniqueness only needs to be enforced on (asset_id, name).

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-03-25

"""
from alembic import op


revision = "e4f5a6b7c8d9"
down_revision = "d3e4f5a6b7c8"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("load_capacities", schema=None) as batch_op:
        batch_op.drop_constraint("uq_capacity_asset_name_metric", type_="unique")
        batch_op.create_unique_constraint(
            "uq_capacity_asset_name", ["asset_id", "name"]
        )


def downgrade():
    with op.batch_alter_table("load_capacities", schema=None) as batch_op:
        batch_op.drop_constraint("uq_capacity_asset_name", type_="unique")
        batch_op.create_unique_constraint(
            "uq_capacity_asset_name_metric", ["asset_id", "name", "metric"]
        )
