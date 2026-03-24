"""contractors role, evaluation remark and unit audit fields

Revision ID: b2c3d4e5f6a7
Revises: 9e5aad80191b
Create Date: 2026-03-19

"""
from alembic import op
import sqlalchemy as sa


revision = "b2c3d4e5f6a7"
down_revision = "9e5aad80191b"
branch_labels = None
depends_on = None


def upgrade():
    # Expand user role enum: ENGINEER -> CONTRACTORS (SQLite may recreate the table)
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column(
            "role",
            existing_type=sa.Enum(
                "SYSTEM_ADMIN", "ASSET_MANAGER", "ENGINEER", name="userrole"
            ),
            type_=sa.Enum(
                "SYSTEM_ADMIN", "ASSET_MANAGER", "CONTRACTORS", name="userrole"
            ),
            existing_nullable=False,
        )

    op.execute("UPDATE users SET role = 'CONTRACTORS' WHERE role = 'ENGINEER'")

    with op.batch_alter_table("evaluation_logs", schema=None) as batch_op:
        batch_op.add_column(sa.Column("submitted_planned_load", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("submitted_unit", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("remark", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("evaluation_logs", schema=None) as batch_op:
        batch_op.drop_column("remark")
        batch_op.drop_column("submitted_unit")
        batch_op.drop_column("submitted_planned_load")

    op.execute("UPDATE users SET role = 'ENGINEER' WHERE role = 'CONTRACTORS'")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column(
            "role",
            existing_type=sa.Enum(
                "SYSTEM_ADMIN", "ASSET_MANAGER", "CONTRACTORS", name="userrole"
            ),
            type_=sa.Enum(
                "SYSTEM_ADMIN", "ASSET_MANAGER", "ENGINEER", name="userrole"
            ),
            existing_nullable=False,
        )
