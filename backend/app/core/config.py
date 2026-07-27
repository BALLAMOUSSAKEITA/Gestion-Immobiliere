from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str = "postgresql://gestion_immo:gestion_immo@localhost:5432/gestion_immo"
    secret_key: str = "dev-secret-key-change-in-production-min-32-chars"
    cors_origins: str = "http://localhost:3000"
    environment: str = "dev"
    app_version: str = "0.1.0"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    super_admin_email: str = "admin@gestion-immo.local"
    super_admin_password: str = "Admin123!"
    jwt_algorithm: str = "HS256"
    upload_dir: str = "uploads"
    building_code_prefix: str = "KM"
    expense_validation_threshold: float = 500_000.0
    repair_set_unit_under_repair: bool = True
    document_max_size_bytes: int = 10 * 1024 * 1024
    document_share_expiry_days: int = 7
    document_share_max_access: int = 10
    agency_name: str = "Gestion Immobilière"
    agency_address: str = "Abidjan, Côte d'Ivoire"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str = "noreply@gestion-immo.local"
    smtp_use_tls: bool = True
    public_api_url: str = "http://localhost:8000"
    enable_scheduler: bool = True

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
