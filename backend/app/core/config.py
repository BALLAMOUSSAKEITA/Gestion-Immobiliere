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
    agency_name: str = "Gestion Immobilière"
    agency_address: str = "Abidjan, Côte d'Ivoire"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
