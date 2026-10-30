"""Create the complete LAN Attendance schema.

Revision ID: 20261029_0001
Revises: None
"""

from alembic import op
from app.database.session import Base
from app.models import entities  # noqa: F401

revision = "20261029_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind(), checkfirst=True)
