from aruba_aos8_mcp.analyzers import analyze_inventory_health, analyze_wlan_security


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
