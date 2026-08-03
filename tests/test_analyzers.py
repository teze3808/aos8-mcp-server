from aruba_aos8_mcp.analyzers import (
    analyze_inventory_health,
    analyze_wlan_security,
    build_wlan_profiles,
)


def test_inventory_health_returns_machine_readable_finding() -> None:
    findings = analyze_inventory_health(
        [{"name": "MD1", "status": "up"}],
        [{"name": "AP-1", "status": "Down"}],
    )

    assert findings[0].id == "AOS8-INVENTORY-002"
    assert findings[0].severity == "medium"
    assert findings[0].affected_objects == ["AP-1"]


def test_wlan_security_detects_open_and_wpa2_psk() -> None:
    findings = analyze_wlan_security(
        {
            "ssid_prof": [
                {"profile-name": "guest", "opmode": "open"},
                {"profile-name": "legacy", "opmode": "wpa2-psk-aes"},
            ]
        }
    )

    assert {(finding.id, finding.severity) for finding in findings} == {
        ("AOS8-WLAN-001", "high"),
        ("AOS8-WLAN-002", "medium"),
    }
    assert {finding.affected_objects[0] for finding in findings} == {"guest", "legacy"}


def test_build_wlan_profiles_maps_vap_ssid_aaa_and_ap_group() -> None:
    config = {
        "virtual_ap": [
            {
                "profile-name": "corp-vap",
                "ssid-profile": "corp-ssid",
                "aaa-profile": "corp-aaa",
                "vlan": 100,
                "forward-mode": "tunnel",
            }
        ],
        "ssid_prof": [
            {"profile-name": "corp-ssid", "essid": "CORP", "opmode": "wpa3-sae-aes"}
        ],
        "aaa_prof": [
            {"profile-name": "corp-aaa", "server-group": "radius", "default-role": "user"}
        ],
        "ap_group": [{"profile-name": "office", "virtual-ap": ["corp-vap"]}],
    }

    wlan = build_wlan_profiles(config)[0]

    assert wlan.name == "CORP"
    assert wlan.ssid_profile == "corp-ssid"
    assert wlan.aaa_profile == "corp-aaa"
    assert wlan.vlan == 100
    assert wlan.ap_groups == ["office"]
