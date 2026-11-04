"""Allow one workstation to be registered by multiple employees.

Revision ID: 20261104_0003
Revises: 20261030_0002
"""

import sqlalchemy as sa
from alembic import op

revision = "20261104_0003"
down_revision = "20261030_0002"
branch_labels = None
depends_on = None


def _unique_constraints():
    return sa.inspect(op.get_bind()).get_unique_constraints("devices")


def upgrade() -> None:
    constraints = _unique_constraints()
    legacy = next(
        (
            item
            for item in constraints
            if item.get("column_names") == ["fingerprint_hash"]
        ),
        None,
    )
    composite_exists = any(
        set(item.get("column_names") or ()) == {"employee_id", "fingerprint_hash"}
        for item in constraints
    )
    if legacy is None and composite_exists:
        return

    naming_convention = {"uq": "uq_%(table_name)s_%(column_0_name)s"}
    with op.batch_alter_table(
        "devices", naming_convention=naming_convention, recreate="always"
    ) as batch:
        if legacy is not None:
            batch.drop_constraint(
                legacy.get("name") or "uq_devices_fingerprint_hash", type_="unique"
            )
        if not composite_exists:
            batch.create_unique_constraint(
                "uq_device_employee_fingerprint", ["employee_id", "fingerprint_hash"]
            )


def downgrade() -> None:
    # Downgrade is only possible when no fingerprint is shared by multiple employees.
    duplicate = op.get_bind().execute(
        sa.text(
            "SELECT fingerprint_hash FROM devices "
            "GROUP BY fingerprint_hash HAVING COUNT(*) > 1 LIMIT 1"
        )
    ).first()
    if duplicate:
        raise RuntimeError(
            "Không thể downgrade: một thiết bị đang được đăng ký cho nhiều nhân viên"
        )
    with op.batch_alter_table("devices", recreate="always") as batch:
        batch.drop_constraint("uq_device_employee_fingerprint", type_="unique")
        batch.create_unique_constraint("uq_devices_fingerprint_hash", ["fingerprint_hash"])
