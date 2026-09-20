from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "megabot"
    app_env: Literal["local", "development", "staging", "production"] = "local"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "console"] = "console"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "megabot"
    postgres_password: str = "megabot"
    postgres_db: str = "megabot"

    db_echo: bool = False
    db_pool_size: int = 5
    db_max_overflow: int = 10

    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    @computed_field
    @property
    def database_url(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            path=self.postgres_db,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
