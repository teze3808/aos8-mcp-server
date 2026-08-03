import pytest

from aruba_aos8_mcp.client import AOS8ClientError
from aruba_aos8_mcp.config import Settings
from aruba_aos8_mcp.policy import AOS8Policy


def _policy(**overrides: object) -> AOS8Policy:
    return AOS8Policy(
        Settings(
            base_url="https://aos8.example:4343",
            username="admin",
            password="secret",
            **overrides,
        )
    )


def test_policy_allows_guided_show_commands_and_include_filter() -> None:
    policy = _policy()

    assert policy.validate_show_command("show ap bss-table") == "show ap bss-table"
    assert policy.validate_show_command("show user-table | include aa:bb") == (
        "show user-table | include aa:bb"
    )


def test_policy_rejects_unreviewed_show_command() -> None:
    with pytest.raises(AOS8ClientError, match="policy allowlist"):
        _policy().validate_show_command("show clock")
    with pytest.raises(AOS8ClientError, match="policy allowlist"):
        _policy().validate_show_command("show version extra-argument")


def test_policy_can_add_narrow_show_prefix() -> None:
    policy = _policy(additional_show_command_prefixes=["show clock"])

    assert policy.validate_show_command("show clock") == "show clock"


def test_policy_ignores_blank_show_prefix() -> None:
    with pytest.raises(AOS8ClientError, match="policy allowlist"):
        _policy(additional_show_command_prefixes=[""]).validate_show_command("show clock")


def test_policy_restricts_config_objects_and_paths() -> None:
    policy = _policy()

    assert policy.validate_config_object("ssid_prof") == "ssid_prof"
    assert policy.validate_config_path("/md/Office") == "/md/Office"
    with pytest.raises(AOS8ClientError, match="not allowed by policy"):
        policy.validate_config_object("mgmt_user")
    with pytest.raises(AOS8ClientError, match="outside the allowed roots"):
        policy.validate_config_path("/local/config")


def test_policy_ignores_blank_or_invalid_config_roots() -> None:
    policy = _policy(allowed_config_path_roots=["", "not/absolute"])

    with pytest.raises(AOS8ClientError, match="none configured"):
        policy.validate_config_path("/md/Office")
