from aruba_aos8_mcp.server import _normalize_ap, _normalize_switch, _redact_license_keys


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
