import ipaddress
import sys
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _environment_file() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().with_name("server.env")
    return Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_environment_file(),
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    app_name: str = "LAN Attendance Management System"
    environment: str = "development"
    database_url: str = "sqlite:///./data/attendance.db"
    jwt_secret: str = "development-only-change-this-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = Field(default=480, ge=1, le=43_200)
    server_host: str = "0.0.0.0"
    server_port: int = Field(default=8000, ge=1, le=65_535)
    allowed_networks: list[str] = Field(
        default_factory=lambda: [
            "192.168.0.0/16",
            "10.0.0.0/8",
            "172.16.0.0/12",
            "127.0.0.0/8",
        ]
    )
    allow_lan_ip_location_fallback: bool = True
    geofencing_enabled: bool = False
    company_latitude: float | None = Field(default=None, ge=-90, le=90)
    company_longitude: float | None = Field(default=None, ge=-180, le=180)
    geofence_radius_meters: float = Field(default=200, ge=10, le=50_000)
    geofence_max_accuracy_meters: float = Field(default=250, ge=1, le=10_000)
    cors_origins: list[str] = Field(default_factory=list)
    discovery_port: int = Field(default=37020, ge=1, le=65_535)
    random_check_interval_minutes: int = Field(default=120, ge=1, le=10_080)
    random_check_response_seconds: int = Field(default=180, ge=10, le=86_400)
    work_timezone: str = "Asia/Ho_Chi_Minh"
    cleanup_interval_hours: int = Field(default=6, ge=1, le=168)
    idempotency_retention_hours: int = Field(default=24, ge=1, le=8_760)
    login_session_retention_days: int = Field(default=7, ge=1, le=3_650)
    backup_directory: str = "backups"
    report_pdf_font: str | None = None
    report_pdf_font_bold: str | None = None
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

    @field_validator("work_timezone")
    @classmethod
    def valid_work_timezone(cls, value: str):
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("WORK_TIMEZONE không hợp lệ") from exc
        return value

    @field_validator("allowed_networks")
    @classmethod
    def valid_allowed_networks(cls, value: list[str]):
        if not value:
            raise ValueError("ALLOWED_NETWORKS phải có ít nhất một dải mạng")
        try:
            for network in value:
                ipaddress.ip_network(network)
        except ValueError as exc:
            raise ValueError("ALLOWED_NETWORKS chứa dải mạng không hợp lệ") from exc
        return value

    @model_validator(mode="after")
    def valid_geofencing(self):
        if self.geofencing_enabled and (
            self.company_latitude is None or self.company_longitude is None
        ):
            raise ValueError(
                "COMPANY_LATITUDE và COMPANY_LONGITUDE là bắt buộc khi bật GEOFENCING_ENABLED"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
