"""Add indexes used by periodic retention cleanup.

Revision ID: 20261030_0002
Revises: 20261029_0001
"""

import sqlalchemy as sa
from alembic import op

revision = "20261030_0002"
down_revision = "20261029_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    idempotency_indexes = {item["name"] for item in inspector.get_indexes("idempotency_records")}
    session_indexes = {item["name"] for item in inspector.get_indexes("login_sessions")}
    if "ix_idempotency_records_created_at" not in idempotency_indexes:
        with op.batch_alter_table("idempotency_records") as batch:
            batch.create_index("ix_idempotency_records_created_at", ["created_at"], unique=False)
    if "ix_login_sessions_created_at" not in session_indexes:
        with op.batch_alter_table("login_sessions") as batch:
            batch.create_index("ix_login_sessions_created_at", ["created_at"], unique=False)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    idempotency_indexes = {item["name"] for item in inspector.get_indexes("idempotency_records")}
    session_indexes = {item["name"] for item in inspector.get_indexes("login_sessions")}
    if "ix_login_sessions_created_at" in session_indexes:
        with op.batch_alter_table("login_sessions") as batch:
            batch.drop_index("ix_login_sessions_created_at")
    if "ix_idempotency_records_created_at" in idempotency_indexes:
        with op.batch_alter_table("idempotency_records") as batch:
            batch.drop_index("ix_idempotency_records_created_at")
