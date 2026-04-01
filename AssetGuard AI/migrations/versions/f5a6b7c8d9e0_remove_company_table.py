"""Remove Company table and all company_id foreign keys.

Single-tenant refactor: drop company_id from users and assets,
drop the companies table, add unique constraint (location_id, name)
on assets.

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-03-25

"""
from alembic import op
import sqlalchemy as sa


revision = "f5a6b7c8d9e0"
down_revision = "e4f5a6b7c8d9"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("company_id")

    with op.batch_alter_table("assets", schema=None) as batch_op:
        batch_op.drop_column("company_id")
        batch_op.create_unique_constraint(
            "uq_asset_location_name", ["location_id", "name"]
        )

    op.drop_table("companies")


def downgrade():
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
    )

    with op.batch_alter_table("assets", schema=None) as batch_op:
        batch_op.drop_constraint("uq_asset_location_name", type_="unique")
        batch_op.add_column(
            sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=True)
        )

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=True)
        )
