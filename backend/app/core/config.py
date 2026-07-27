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

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
