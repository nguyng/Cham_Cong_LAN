"""Repair root administrator state for databases that already recorded revision 0007."""

import sqlalchemy as sa
from alembic import op

revision = "20261117_0008"
down_revision = "20261117_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("users"):
        return
    columns = {column["name"] for column in inspector.get_columns("users")}
    if "is_root_admin" not in columns:
        with op.batch_alter_table("users") as batch:
            batch.add_column(
                sa.Column(
                    "is_root_admin",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.false(),
                )
            )
    op.execute(
        "UPDATE users SET is_root_admin = 1 "
        "WHERE id = ("
        "SELECT users.id FROM users "
        "JOIN roles ON roles.id = users.role_id "
        "WHERE roles.name = 'ADMIN' "
        "ORDER BY CASE WHEN users.username = 'admin' THEN 0 ELSE 1 END, users.id "
        "LIMIT 1"
        ") "
        "AND NOT EXISTS (SELECT 1 FROM users WHERE is_root_admin = 1)"
    )
    op.execute("UPDATE users SET active = 1 WHERE is_root_admin = 1")


def downgrade() -> None:
    pass
