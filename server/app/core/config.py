import sys
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _environment_file() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().with_name("server.env")
    return Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_environment_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "LAN Attendance Management System"
    environment: str = "development"
    database_url: str = "sqlite:///./data/attendance.db"
    jwt_secret: str = "development-only-change-this-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 480
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    allowed_networks: list[str] = Field(
        default_factory=lambda: [
            "192.168.0.0/16",
            "10.0.0.0/8",
            "172.16.0.0/12",
            "127.0.0.0/8",
        ]
    )
    cors_origins: list[str] = Field(default_factory=list)
    discovery_port: int = 37020
    random_check_interval_minutes: int = 120
    random_check_response_seconds: int = 180
    backup_directory: str = "backups"
    tls_cert_file: str | None = None
    tls_key_file: str | None = None

    @field_validator("database_url")
    @classmethod
    def sqlite_database_only(cls, value: str):
        if not value.startswith("sqlite:///"):
            raise ValueError("DATABASE_URL phải sử dụng SQLite")
        raw_path = value.removeprefix("sqlite:///")
        if raw_path == ":memory:":
            return value
        path = Path(raw_path)
        if not path.is_absolute():
            path = _environment_file().parent / path
        return f"sqlite:///{path.resolve().as_posix()}"

    @field_validator("jwt_secret")
    @classmethod
    def secure_production_secret(cls, value: str, info):
        environment = info.data.get("environment", "development")
        if environment == "production" and (
            len(value) < 32 or value.startswith("development-") or value.startswith("CHANGE_")
        ):
            raise ValueError("JWT_SECRET sản xuất phải là chuỗi ngẫu nhiên tối thiểu 32 ký tự")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
