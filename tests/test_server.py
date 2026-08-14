import anyio
import aruba_aos8_mcp.server as server
import pytest

from aruba_aos8_mcp.client import AOS8ClientError
from aruba_aos8_mcp.config import Settings
from aruba_aos8_mcp.server import (
    _build_json_diff,
    _bound_raw_result,
    _normalize_ap,
    _normalize_client,
    _normalize_switch,
    _redact_license_keys,
    _redact_sensitive_values,
)


@pytest.fixture(autouse=True)
def configured_server_settings(monkeypatch) -> None:
    settings = Settings(
        base_url="https://aos8.example:4343",
        username="admin",
        password="test-only-secret",
    )
    monkeypatch.setattr(server, "get_settings", lambda: settings)


def test_redact_license_keys() -> None:
    result = {
        "License Table": [
            {"Key": "secret-license-key", "Service Type": "Access Points: 1000"},
            {"Key": None, "Service Type": "MM-VA: 50"},
        ]
    }

    assert _redact_license_keys(result) == {
        "License Table": [
            {"Key": "<redacted>", "Service Type": "Access Points: 1000"},
            {"Key": None, "Service Type": "MM-VA: 50"},
        ]
    }


def test_redact_sensitive_values_recurses() -> None:
    result = _redact_sensitive_values(
        {
            "profile-name": "SE-MGMT-SSID",
            "wpa_passphrase": {"wpa-passphrase": "do-not-show"},
            "nested": [{"snmp-community": "also-secret"}],
        }
    )

    assert result == {
        "profile-name": "SE-MGMT-SSID",
        "wpa_passphrase": "<redacted>",
        "nested": [{"snmp-community": "<redacted>"}],
    }


def test_redact_sensitive_values_preserves_license_inventory() -> None:
    result = _redact_sensitive_values(
        {"License Table": [{"License Type": "AP", "License Key": "secret"}]}
    )

    assert result == {
        "License Table": [{"License Type": "AP", "License Key": "<redacted>"}]
    }


def test_redact_sensitive_values_redacts_sensitive_text_lines() -> None:
    result = _redact_sensitive_values("username admin\npassword super-secret\nsnmp-community public")

    assert result == "username admin\npassword <redacted>\nsnmp-community <redacted>"


def test_bound_raw_result_truncates_large_output(monkeypatch) -> None:
    from aruba_aos8_mcp.config import Settings

    monkeypatch.setattr(
        server,
        "get_settings",
        lambda: Settings(
            base_url="https://aos8.example:4343",
            username="admin",
            password="secret",
            max_result_characters=1_000,
        ),
    )

    result = _bound_raw_result({"output": "x" * 2_000})

    assert result["_meta"]["truncated"] is True
    assert result["_meta"]["original_characters"] > 1_000


def test_build_json_diff_redacts_sensitive_values() -> None:
    diff = "\n".join(
        _build_json_diff(
            {
                "essid": {"essid": "old-ssid"},
                "profile-name": "SE-MGMT-SSID",
                "wpa_passphrase": {"wpa-passphrase": "old"},
            },
            {
                "essid": {"essid": "new-ssid"},
                "profile-name": "SE-MGMT-SSID",
                "wpa_passphrase": {"wpa-passphrase": "new"},
            },
        )
    )

    assert '"essid": "old-ssid"' in diff
    assert '"essid": "new-ssid"' in diff
    assert '"wpa-passphrase": "old"' not in diff
    assert '"wpa-passphrase": "new"' not in diff
    assert "<redacted>" in diff


def test_plan_config_object_change_returns_plan_only(monkeypatch) -> None:
    async def fake_get_config_object(
        object_name: str,
        config_path: str = "/md",
        query_params: dict[str, str] | None = None,
        target_node: str | None = None,
    ) -> dict:
        assert object_name == "ssid_prof"
        assert config_path == "/md/SE"
        assert query_params is None
        assert target_node is None
        return {"_data": {"ssid_prof": {"profile-name": "SE-MGMT-SSID", "essid": {"essid": "old"}}}}

    monkeypatch.setattr(server, "_get_config_object", fake_get_config_object)

    async def scenario() -> dict:
        return await server.aos8_plan_config_object_change(
            object_name="ssid_prof",
            config_path="/md/SE",
            proposed_payload={
                "profile-name": "SE-MGMT-SSID",
                "essid": {"essid": "new"},
                "wpa_passphrase": {"wpa-passphrase": "secret"},
            },
        )

    result = anyio.run(scenario)

    assert result["mode"] == "plan_only"
    assert result["writes_executed"] is False
    assert result["save_executed"] is False
    assert result["proposed_request"]["method"] == "POST"
    assert result["proposed_request"]["path"] == "/v1/configuration/object/ssid_prof"
    assert result["proposed_request"]["params"] == {"config_path": "/md/SE"}
    assert result["proposed_request"]["body"]["wpa_passphrase"] == "<redacted>"
    assert "secret" not in "\n".join(result["diff"])


def test_plan_config_object_change_validates_query_params_without_current() -> None:
    async def call() -> dict[str, object]:
        return await server.aos8_plan_config_object_change(
            "ssid_prof",
            {"profile-name": "Test"},
            query_params={"bad parameter": "value"},
            include_current=False,
        )

    with pytest.raises(AOS8ClientError, match="Invalid query parameter"):
        anyio.run(call)


def test_normalize_switch() -> None:
    row = {
        "Name": "SE-VMM-1",
        "Type": "conductor",
        "IP Address": "192.168.15.11",
        "IPv6 Address": "None",
        "Model": "ArubaMM-VA",
        "Version": "8.13.3.0-beta_95763",
        "Status": "up",
        "Configuration State": "UPDATE SUCCESSFUL",
        "Config Sync Time (sec)": "0",
        "Config ID": "1026",
        "Location": "Building1.floor1",
        "Release Type": "LSR",
    }

    assert _normalize_switch(row) == {
        "name": "SE-VMM-1",
        "type": "conductor",
        "ip_address": "192.168.15.11",
        "ipv6_address": "None",
        "model": "ArubaMM-VA",
        "version": "8.13.3.0-beta_95763",
        "status": "up",
        "configuration_state": "UPDATE SUCCESSFUL",
        "config_sync_time_seconds": "0",
        "config_id": "1026",
        "location": "Building1.floor1",
        "release_type": "LSR",
    }


def test_normalize_ap() -> None:
    row = {
        "Name": "SE-AP505-AOS8",
        "Group": "SE-AP-ONLY-MGMT",
        "AP Type": "505",
        "IP Address": "192.168.14.17",
        "Status": "Up 11d:1h:0m:34s",
        "Flags": "2",
        "Switch IP": "192.168.15.51",
        "Standby IP": "192.168.15.52",
        "Wired MAC Address": "34:8a:12:ce:01:f6",
        "Serial #": "CNLXKPP13H",
    }

    assert _normalize_ap(row) == {
        "name": "SE-AP505-AOS8",
        "group": "SE-AP-ONLY-MGMT",
        "model": "AP-505",
        "ap_type": "505",
        "ip_address": "192.168.14.17",
        "status": "Up 11d:1h:0m:34s",
        "flags": "2",
        "active_controller": "192.168.15.51",
        "standby_controller": "192.168.15.52",
        "wired_mac_address": "34:8a:12:ce:01:f6",
        "serial": "CNLXKPP13H",
    }


def test_normalize_client_accepts_common_aos8_fields() -> None:
    assert _normalize_client(
        {
            "IP": "192.0.2.100",
            "MAC": "aa:bb:cc:dd:ee:ff",
            "AP name": "AP-01",
            "ESSID": "CORP",
            "VLAN": 100,
            "Role": "employee",
        }
    ) == {
        "ip_address": "192.0.2.100",
        "mac_address": "aa:bb:cc:dd:ee:ff",
        "username": None,
        "device_type": None,
        "ap_name": "AP-01",
        "ssid": "CORP",
        "bssid": None,
        "radio": None,
        "phy": None,
        "vlan": 100,
        "role": "employee",
        "aaa_profile": None,
        "association_state": None,
        "authentication_state": None,
    }


def test_operation_result_has_stable_metadata(monkeypatch) -> None:
    from aruba_aos8_mcp.config import Settings

    monkeypatch.setattr(
        server,
        "get_settings",
        lambda: Settings(
            base_url="https://aos8.example:4343",
            username="admin",
            password="secret",
        ),
    )

    result = server._operation_result({"total": 1}, config_path="/md/SE")

    assert result["source"] == "aos8"
    assert result["target"] == {
        "name": "default",
        "base_url": "https://aos8.example:4343",
        "config_path": "/md/SE",
    }
    assert result["data"] == {"total": 1}


def test_list_command_targets_has_no_warning_for_default_only() -> None:
    result = anyio.run(server.aos8_list_command_targets)

    assert result["warnings"] == []
    assert result["data"]["targets"] == [
        {
            "name": "default",
            "base_url": "https://aos8.example:4343",
            "config_path": None,
            "direct_node_api": False,
        }
    ]


def test_list_command_targets_explains_named_targets(monkeypatch) -> None:
    monkeypatch.setattr(
        server,
        "get_settings",
        lambda: Settings(
            base_url="https://aos8.example:4343",
            username="admin",
            password="secret",
            node_targets={
                "md-1": {
                    "base_url": "https://md-1.example:4343",
                    "config_path": "/md/site-1",
                }
            },
        ),
    )

    result = anyio.run(server.aos8_list_command_targets)

    assert result["warnings"] == [
        "Named direct-node targets use their own API endpoints. Pass a listed name as "
        "target_node; omit target_node to use the default endpoint."
    ]
    assert result["data"]["targets"][1]["name"] == "md-1"
