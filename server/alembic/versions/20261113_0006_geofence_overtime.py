"""Add geofence evidence and overtime payroll fields.

Revision ID: 20261113_0006
Revises: 20261112_0005
"""

from decimal import Decimal

import sqlalchemy as sa
from alembic import op

revision = "20261113_0006"
down_revision = "20261112_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("employees"):
        existing = {column["name"] for column in inspector.get_columns("employees")}
        if "overtime_multiplier" not in existing:
            with op.batch_alter_table("employees") as batch:
                batch.add_column(
                    sa.Column(
                        "overtime_multiplier",
                        sa.Numeric(4, 2),
                        nullable=False,
                        server_default=str(Decimal("1.50")),
                    )
                )

    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("attendance_records"):
        return
    existing = {column["name"] for column in inspector.get_columns("attendance_records")}
    columns = (
        sa.Column("check_in_geofence_distance_meters", sa.Float(), nullable=True),
        sa.Column("check_out_geofence_distance_meters", sa.Float(), nullable=True),
        sa.Column("overtime_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("approved_overtime_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("overtime_status", sa.String(30), nullable=False, server_default="NONE"),
        sa.Column("overtime_reviewed_by", sa.Integer(), nullable=True),
        sa.Column("overtime_review_note", sa.Text(), nullable=True),
        sa.Column("overtime_reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )
    with op.batch_alter_table("attendance_records") as batch:
        for column in columns:
            if column.name not in existing:
                batch.add_column(column)
        if "overtime_reviewed_by" not in existing:
            batch.create_foreign_key(
                "fk_attendance_overtime_reviewer",
                "users",
                ["overtime_reviewed_by"],
                ["id"],
            )
        if "overtime_status" not in existing:
            batch.create_index("ix_attendance_overtime_status", ["overtime_status"])


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("attendance_records"):
        existing = {column["name"] for column in inspector.get_columns("attendance_records")}
        with op.batch_alter_table("attendance_records") as batch:
            if "overtime_status" in existing:
                batch.drop_index("ix_attendance_overtime_status")
            if "overtime_reviewed_by" in existing:
                batch.drop_constraint("fk_attendance_overtime_reviewer", type_="foreignkey")
            for name in (
                "overtime_reviewed_at",
                "overtime_review_note",
                "overtime_reviewed_by",
                "overtime_status",
                "approved_overtime_minutes",
                "overtime_minutes",
                "check_out_geofence_distance_meters",
                "check_in_geofence_distance_meters",
            ):
                if name in existing:
                    batch.drop_column(name)

    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("employees"):
        existing = {column["name"] for column in inspector.get_columns("employees")}
        if "overtime_multiplier" in existing:
            with op.batch_alter_table("employees") as batch:
                batch.drop_column("overtime_multiplier")
