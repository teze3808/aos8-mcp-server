import anyio
import aruba_aos8_mcp.server as server

from aruba_aos8_mcp.server import (
    _build_json_diff,
    _normalize_ap,
    _normalize_switch,
    _redact_license_keys,
    _redact_sensitive_values,
)


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
    ) -> dict:
        assert object_name == "ssid_prof"
        assert config_path == "/md/SE"
        assert query_params is None
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
