from pathlib import Path
from uuid import uuid4

import pytest
from app.core.config import Settings
from app.database.session import make_engine
from pydantic import ValidationError
from sqlalchemy import text


def test_non_sqlite_database_is_rejected():
    with pytest.raises(ValidationError):
        Settings(database_url="mysql+pymysql://user:password@localhost/attendance")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("server_port", 0),
        ("discovery_port", 70_000),
        ("random_check_response_seconds", 0),
        ("cleanup_interval_hours", 0),
        ("allowed_networks", ["not-a-network"]),
        ("allowed_networks", []),
    ],
)
def test_invalid_runtime_settings_are_rejected(field, value):
    with pytest.raises(ValidationError):
        Settings(**{field: value})


def test_sqlite_runtime_pragmas_are_enabled():
    runtime = Path(".test-runtime") / str(uuid4()) / "runtime.db"
    runtime.parent.mkdir(parents=True)
    engine = make_engine(f"sqlite:///{runtime.as_posix()}")
    try:
        with engine.connect() as connection:
            assert connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
            assert connection.execute(text("PRAGMA journal_mode")).scalar_one().lower() == "wal"
            assert connection.execute(text("PRAGMA busy_timeout")).scalar_one() == 30000
    finally:
        engine.dispose()


def test_relative_sqlite_path_is_resolved_to_server_directory():
    settings = Settings(database_url="sqlite:///./data/test-location.db")
    assert settings.database_url.startswith("sqlite:///")
    assert Path(settings.database_url.removeprefix("sqlite:///")).is_absolute()


def test_geofencing_requires_company_coordinates():
    with pytest.raises(ValidationError, match="COMPANY_LATITUDE"):
        Settings(geofencing_enabled=True)

    settings = Settings(
        geofencing_enabled=True,
        company_latitude=10.776889,
        company_longitude=106.700806,
        geofence_radius_meters=150,
    )
    assert settings.geofencing_enabled is True
