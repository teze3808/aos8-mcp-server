from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or a local .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="AOS8_", extra="ignore")

    base_url: AnyHttpUrl = Field(description="AOS8 base URL, for example https://mm.example:4343")
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    verify_ssl: bool = False
    request_timeout: float = 30.0

    @property
    def normalized_base_url(self) -> str:
        return str(self.base_url).rstrip("/")


@lru_cache
def get_settings() -> Settings:
    return Settings()
