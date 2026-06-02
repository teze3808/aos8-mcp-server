import pytest

from aruba_aos8_mcp.client import AOS8Client, AOS8ClientError


def test_show_command_rejects_non_show_commands() -> None:
    with pytest.raises(AOS8ClientError):
        AOS8Client.validate_show_command("configure terminal")


def test_show_command_normalizes_whitespace() -> None:
    assert AOS8Client.validate_show_command("  show version  ") == "show version"
