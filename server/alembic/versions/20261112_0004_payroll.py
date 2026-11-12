"""Add employee payroll profile fields.

Revision ID: 20261112_0004
Revises: 20261104_0003
"""

import sqlalchemy as sa
from alembic import op

revision = "20261112_0004"
down_revision = "20261104_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("employees")}
    with op.batch_alter_table("employees") as batch:
        if "base_salary" not in columns:
            batch.add_column(
                sa.Column(
                    "base_salary",
                    sa.Numeric(14, 2),
                    nullable=False,
                    server_default="0",
                )
            )
        if "attendance_bonus" not in columns:
            batch.add_column(
                sa.Column(
                    "attendance_bonus",
                    sa.Numeric(14, 2),
                    nullable=False,
                    server_default="0",
                )
            )


def downgrade() -> None:
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("employees")}
    with op.batch_alter_table("employees") as batch:
        if "attendance_bonus" in columns:
            batch.drop_column("attendance_bonus")
        if "base_salary" in columns:
            batch.drop_column("base_salary")
