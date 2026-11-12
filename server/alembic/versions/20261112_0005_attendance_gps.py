"""Store GPS coordinates for attendance actions.

Revision ID: 20261112_0005
Revises: 20261112_0004
"""

import sqlalchemy as sa
from alembic import op

revision = "20261112_0005"
down_revision = "20261112_0004"
branch_labels = None
depends_on = None


GPS_COLUMNS = (
    "check_in_latitude",
    "check_in_longitude",
    "check_in_accuracy_meters",
    "check_out_latitude",
    "check_out_longitude",
    "check_out_accuracy_meters",
)


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("attendance_records"):
        return
    existing = {column["name"] for column in inspector.get_columns("attendance_records")}
    with op.batch_alter_table("attendance_records") as batch:
        for name in GPS_COLUMNS:
            if name not in existing:
                batch.add_column(sa.Column(name, sa.Float(), nullable=True))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("attendance_records"):
        return
    existing = {column["name"] for column in inspector.get_columns("attendance_records")}
    with op.batch_alter_table("attendance_records") as batch:
        for name in reversed(GPS_COLUMNS):
            if name in existing:
                batch.drop_column(name)
