import httpx
import pytest

from aruba_aos8_mcp.client import AOS8Client, AOS8ClientError


def test_show_command_rejects_non_show_commands() -> None:
    with pytest.raises(AOS8ClientError):
        AOS8Client.validate_show_command("configure terminal")


def test_show_command_normalizes_whitespace() -> None:
    assert AOS8Client.validate_show_command("  show version  ") == "show version"


def test_config_object_name_validation_accepts_safe_names() -> None:
    assert AOS8Client.validate_config_object_name("ssid_prof") == "ssid_prof"
    assert AOS8Client.validate_config_object_name("int_vlan") == "int_vlan"
    assert AOS8Client.validate_config_object_name("object.name-1") == "object.name-1"


def test_config_object_name_validation_rejects_paths() -> None:
    with pytest.raises(AOS8ClientError):
        AOS8Client.validate_config_object_name("../write_memory")


def test_parse_response_accepts_empty_success_body() -> None:
    response = httpx.Response(200, content=b"")

    assert AOS8Client._parse_response(response) == {
        "_data": [],
        "_meta": {"empty_response": True},
    }
