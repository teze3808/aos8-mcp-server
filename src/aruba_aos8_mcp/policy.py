"""Central deterministic policy for AOS8 MCP targets and read-only capabilities."""

from __future__ import annotations

import re

from aruba_aos8_mcp.client import AOS8Client, AOS8ClientError
from aruba_aos8_mcp.config import Settings


DEFAULT_SHOW_COMMANDS = (
    "show version",
    "show switches",
    "show ap database",
    "show ap database long",
    "show ap active",
    "show ap bss-table",
    "show ap essid",
    "show user-table",
    "show datapath tunnel",
    "show license",
    "show lc-cluster group-membership",
    "show web-server profile",
    "show crypto-local pki trustedcas",
    "show aaa authentication-server all",
    "show log security all",
    "show snmp trap-host",
)
DEFAULT_SHOW_COMMAND_PREFIXES = ("show ap details ap-name ",)
CONFIG_PATH_RE = re.compile(r"^/(?:[A-Za-z0-9_.-]+)(?:/[A-Za-z0-9_.-]+)*$")


class AOS8Policy:
    """Apply one policy consistently across MCP tools and integration helpers."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def validate_show_command(self, command: str) -> str:
        normalized = AOS8Client.validate_show_command(command)
        base_command = re.sub(r"\s+\|\s+include\s+.+$", "", normalized, flags=re.IGNORECASE)
        lowered = base_command.lower()
        additional_prefixes = tuple(
            normalized_prefix
            for prefix in self.settings.additional_show_command_prefixes
            if (normalized_prefix := prefix.strip().lower())
        )
        if lowered not in DEFAULT_SHOW_COMMANDS and not any(
            lowered.startswith(prefix)
            for prefix in DEFAULT_SHOW_COMMAND_PREFIXES + additional_prefixes
        ):
            raise AOS8ClientError(
                "Show command is not in the server policy allowlist. Add a narrowly scoped prefix "
                "to AOS8_ADDITIONAL_SHOW_COMMAND_PREFIXES only after review."
            )
        return normalized

    def validate_config_object(self, object_name: str) -> str:
        normalized = AOS8Client.validate_config_object_name(object_name)
        if normalized not in self.settings.allowed_config_objects:
            allowed = ", ".join(sorted(self.settings.allowed_config_objects))
            raise AOS8ClientError(
                f"Configuration object '{normalized}' is not allowed by policy. Allowed: {allowed}."
            )
        return normalized

    def validate_config_path(self, config_path: str | None) -> str | None:
        if config_path is None:
            return None
        normalized = config_path.strip()
        if not CONFIG_PATH_RE.fullmatch(normalized):
            raise AOS8ClientError("Invalid AOS8 configuration path syntax.")
        allowed_roots = tuple(
            normalized_root
            for root in self.settings.allowed_config_path_roots
            if (normalized_root := root.strip().rstrip("/"))
            and CONFIG_PATH_RE.fullmatch(normalized_root)
        )
        if not any(
            normalized == root or normalized.startswith(f"{root}/")
            for root in allowed_roots
        ):
            roots = ", ".join(allowed_roots) or "none configured"
            raise AOS8ClientError(
                f"Configuration path '{normalized}' is outside the allowed roots: {roots}."
            )
        return normalized


def get_policy(settings: Settings) -> AOS8Policy:
    return AOS8Policy(settings)
