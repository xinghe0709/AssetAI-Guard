"""GJP PDF schema: locations, load_capacities, assets redesign, evaluation_logs redesign

Revision ID: e1f2a3b4c5d6
Revises: c1d2e3f4a5b6
Create Date: 2026-03-24

"""
import sqlalchemy as sa
from alembic import op

revision = "e1f2a3b4c5d6"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("evaluation_logs")
    op.drop_table("assets")

    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "name", name="uq_location_company_name"),
    )
    op.create_index(op.f("ix_locations_company_id"), "locations", ["company_id"], unique=False)

    op.create_table(
        "assets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_assets_company_id"), "assets", ["company_id"], unique=False)
    op.create_index(op.f("ix_assets_location_id"), "assets", ["location_id"], unique=False)
    op.create_index(op.f("ix_assets_name"), "assets", ["name"], unique=False)

    op.create_table(
        "load_capacities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("metric", sa.String(length=32), nullable=False),
        sa.Column("max_load", sa.Float(), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_load_capacities_asset_id"), "load_capacities", ["asset_id"], unique=False)

    op.create_table(
        "evaluation_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("equipment", sa.String(length=128), nullable=False),
        sa.Column("equipment_model", sa.Text(), nullable=True),
        sa.Column("load_parameter_value", sa.Float(), nullable=False),
        sa.Column("load_parameter_metric", sa.String(length=32), nullable=False),
        sa.Column("matched_capacity_name", sa.String(length=128), nullable=False),
        sa.Column(
            "status",
            sa.Enum("COMPLIANT", "NON_COMPLIANT", name="evaluationstatus"),
            nullable=False,
        ),
        sa.Column("overload_percentage", sa.Float(), nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["assets.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evaluation_logs_asset_id"), "evaluation_logs", ["asset_id"], unique=False)
    op.create_index(op.f("ix_evaluation_logs_user_id"), "evaluation_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_evaluation_logs_evaluated_at"), "evaluation_logs", ["evaluated_at"], unique=False)


def downgrade():
    raise NotImplementedError("Downgrade not supported for this schema pivot")
