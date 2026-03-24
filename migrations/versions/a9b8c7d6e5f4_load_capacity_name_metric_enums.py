"""Restrict load capacity name and metric by enums.

Revision ID: a9b8c7d6e5f4
Revises: f7a8b9c0d1e2
Create Date: 2026-03-24
"""

import sqlalchemy as sa
from alembic import op

revision = "a9b8c7d6e5f4"
down_revision = "f7a8b9c0d1e2"
branch_labels = None
depends_on = None


def upgrade():
    # Normalize existing values before applying enum/check constraints.
    # pylint: disable=no-member
    op.execute("UPDATE load_capacities SET name = lower(trim(name))")
    op.execute(
        """
        UPDATE load_capacities
        SET metric = CASE
            WHEN lower(trim(metric)) = 'kn' THEN 'kN'
            WHEN lower(trim(metric)) = 'kpa' THEN 'kPa'
            WHEN lower(trim(metric)) = 't' THEN 't'
            ELSE metric
        END
        """
    )

    # pylint: disable=no-member
    with op.batch_alter_table("load_capacities", schema=None) as batch_op:
        batch_op.alter_column(
            "name",
            existing_type=sa.String(length=128),
            type_=sa.Enum(
                "max point load",
                "max axle load",
                "max uniform distributor load",
                "max displacement size",
                name="capacityname",
                native_enum=False,
                create_constraint=True,
                validate_strings=True,
            ),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "metric",
            existing_type=sa.String(length=32),
            type_=sa.Enum(
                "kN",
                "t",
                "kPa",
                name="capacitymetric",
                native_enum=False,
                create_constraint=True,
                validate_strings=True,
            ),
            existing_nullable=False,
        )


def downgrade():
    raise NotImplementedError("Downgrade not supported for enum hardening")
