from functools import lru_cache

from pydantic import AnyHttpUrl, BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class NodeTarget(BaseModel):
    """Optional direct API endpoint for a managed device or other AOS8 node."""

    base_url: AnyHttpUrl
    username: str | None = None
    password: str | None = None
    config_path: str | None = None


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables or a local .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="AOS8_", extra="ignore")

    base_url: AnyHttpUrl = Field(description="AOS8 base URL, for example https://mm.example:4343")
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)
    verify_ssl: bool = True
    ca_bundle: str | None = Field(
        default=None,
        description="Path to a PEM CA bundle used to verify the AOS8 HTTPS certificate.",
    )
    request_timeout: float = 30.0
    retry_attempts: int = Field(default=3, ge=1, le=10)
    retry_backoff_seconds: float = Field(default=0.5, ge=0.0, le=30.0)
    max_result_characters: int = Field(default=200_000, ge=1_000, le=5_000_000)
    additional_show_command_prefixes: list[str] = Field(default_factory=list)
    allowed_config_objects: list[str] = Field(
        default_factory=lambda: ["aaa_prof", "ap_group", "ssid_prof", "virtual_ap"]
    )
    allowed_config_path_roots: list[str] = Field(default_factory=lambda: ["/md", "/mm"])
    audit_log_path: str | None = None
    audit_log_max_bytes: int = Field(default=10_000_000, ge=10_000, le=1_000_000_000)
    audit_log_backup_count: int = Field(default=5, ge=1, le=100)
    node_targets: dict[str, NodeTarget] = Field(default_factory=dict)

    @property
    def normalized_base_url(self) -> str:
        return str(self.base_url).rstrip("/")

    @property
    def httpx_verify(self) -> bool | str:
        """Return the verification setting accepted by httpx."""
        return self.ca_bundle or self.verify_ssl

    def for_target(self, target_node: str | None = None) -> "Settings":
        """Return settings for a configured direct node target."""
        if not target_node:
            return self

        target = self.node_targets.get(target_node)
        if target is None:
            known = ", ".join(sorted(self.node_targets)) or "none"
            raise ValueError(f"Unknown AOS8 target '{target_node}'. Configured targets: {known}.")

        updates: dict[str, object] = {"base_url": target.base_url}
        if target.username:
            updates["username"] = target.username
        if target.password:
            updates["password"] = target.password
        return self.model_copy(update=updates)


@lru_cache
def get_settings() -> Settings:
    return Settings()
