"""Normalize legacy non-English asset units to English canonical values

Revision ID: c1d2e3f4a5b6
Revises: b2c3d4e5f6a7
Create Date: 2026-03-19

"""
from alembic import op


revision = "c1d2e3f4a5b6"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    # Legacy Chinese / mixed labels → English canonical (kg, ton, lb)
    op.execute("UPDATE assets SET unit = 'kg' WHERE unit IN ('千克', 'KG')")
    op.execute("UPDATE assets SET unit = 'ton' WHERE unit IN ('吨', 'T')")
    op.execute("UPDATE assets SET unit = 'lb' WHERE unit IN ('磅')")


def downgrade():
    # Cannot reliably restore previous non-English strings
    pass
