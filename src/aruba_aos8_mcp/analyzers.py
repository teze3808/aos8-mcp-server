"""Deterministic checks used by MCP tools before an AI explains the result."""

from __future__ import annotations

from typing import Any

from aruba_aos8_mcp.models import Finding, WLANProfile


def _is_up(value: Any) -> bool:
    return str(value or "").lower().startswith("up")


def analyze_inventory_health(
    devices: list[dict[str, Any]],
    access_points: list[dict[str, Any]],
) -> list[Finding]:
    """Produce repeatable findings from normalized inventory state."""
    findings: list[Finding] = []
    down_devices = [str(row.get("name") or row.get("ip_address") or "unknown") for row in devices if not _is_up(row.get("status"))]
    down_aps = [str(row.get("name") or row.get("ip_address") or "unknown") for row in access_points if not _is_up(row.get("status"))]

    if down_devices:
        findings.append(
            Finding(
                id="AOS8-INVENTORY-001",
                severity="high",
                title="Controller or managed-device entries are not up",
                evidence=[f"Not up: {', '.join(down_devices)}"],
                recommendation="Verify reachability, configuration synchronization, and redundancy state for the affected nodes.",
                affected_objects=down_devices,
            )
        )
    if down_aps:
        findings.append(
            Finding(
                id="AOS8-INVENTORY-002",
                severity="medium",
                title="Access point entries are not up",
                evidence=[f"Not up: {', '.join(down_aps)}"],
                recommendation="Check AP reachability, discovery, controller assignment, and configuration download state.",
                affected_objects=down_aps,
            )
        )
    if not findings:
        findings.append(
            Finding(
                id="AOS8-INVENTORY-000",
                severity="info",
                title="Inventory entries are up",
                evidence=[f"{len(devices)} controller/managed-device entries and {len(access_points)} AP entries are up."],
                recommendation="Continue monitoring client, tunnel, and WLAN service indicators.",
            )
        )
    return findings


def analyze_wlan_security(config: dict[str, Any]) -> list[Finding]:
    """Find explicit wireless security signals without relying on an LLM judgment."""
    findings: list[Finding] = []
    for wlan in build_wlan_profiles(config):
        value = (wlan.security or "").lower()
        if not value:
            continue
        evidence = [
            f"WLAN {wlan.name}: security={wlan.security or 'unknown'}, "
            f"SSID profile={wlan.ssid_profile or 'unknown'}"
        ]
        if any(term in value for term in ("open", "unencrypted")) and "enhanced-open" not in value:
            findings.append(
                Finding(
                    id="AOS8-WLAN-001",
                    severity="high",
                    title="Open WLAN security mode detected",
                    evidence=evidence,
                    recommendation="Confirm this WLAN is intentionally open and isolate it with an appropriate guest design.",
                    affected_objects=[wlan.name],
                )
            )
        elif "wpa2-psk" in value:
            findings.append(
                Finding(
                    id="AOS8-WLAN-002",
                    severity="medium",
                    title="WPA2-PSK WLAN detected",
                    evidence=evidence,
                    recommendation="Review migration to WPA3-SAE or enterprise authentication where compatible.",
                    affected_objects=[wlan.name],
                )
            )
        elif "wpa3" in value:
            findings.append(
                Finding(
                    id="AOS8-WLAN-000",
                    severity="info",
                    title="WPA3-capable WLAN security detected",
                    evidence=evidence,
                    recommendation="Validate client compatibility and management-frame protection requirements.",
                    affected_objects=[wlan.name],
                )
            )

    return _deduplicate_findings(findings)


def build_wlan_profiles(config: dict[str, Any]) -> list[WLANProfile]:
    """Normalize native VAP, SSID, AAA, and AP-group objects into WLAN relationships."""
    virtual_aps = _profile_records(config.get("virtual_ap"), "virtual_ap")
    ssid_profiles = {
        name: record
        for record in _profile_records(config.get("ssid_prof"), "ssid_prof")
        if (name := _profile_name(record))
    }
    aaa_profiles = {
        name: record
        for record in _profile_records(config.get("aaa_prof"), "aaa_prof")
        if (name := _profile_name(record))
    }
    ap_groups = _profile_records(config.get("ap_group"), "ap_group")

    wlans: list[WLANProfile] = []
    referenced_ssid_profiles: set[str] = set()
    for vap in virtual_aps:
        vap_name = _profile_name(vap)
        if not vap_name:
            continue
        ssid_name = _find_field(vap, "ssid-profile", "ssid_prof", "ssid-profile-name")
        if ssid_name is not None:
            referenced_ssid_profiles.add(str(ssid_name))
        aaa_name = _find_field(vap, "aaa-profile", "aaa_prof", "aaa-profile-name")
        ssid_record = ssid_profiles.get(str(ssid_name), {})
        aaa_record = aaa_profiles.get(str(aaa_name), {})
        essid = _find_field(ssid_record, "essid")
        security = _find_field(ssid_record, "opmode", "security", "encryption")
        matching_groups = [
            name
            for group in ap_groups
            if (name := _profile_name(group)) and _contains_string(group, vap_name)
        ]
        wlans.append(
            WLANProfile(
                name=str(essid or vap_name),
                essid=_as_scalar(essid),
                virtual_ap_profile=vap_name,
                ssid_profile=_as_scalar(ssid_name),
                aaa_profile=_as_scalar(aaa_name),
                security=_as_scalar(security),
                vlan=_find_field(vap, "vlan", "vlan-id", "vlan_id"),
                forward_mode=_as_scalar(
                    _find_field(vap, "forward-mode", "forward_mode", "forwarding-mode")
                ),
                server_group=_as_scalar(
                    _find_field(aaa_record, "server-group", "server_group")
                ),
                default_role=_as_scalar(
                    _find_field(aaa_record, "default-role", "default_role")
                ),
                ap_groups=sorted(set(matching_groups)),
            )
        )
    for ssid_name, ssid_record in ssid_profiles.items():
        if ssid_name in referenced_ssid_profiles:
            continue
        essid = _find_field(ssid_record, "essid")
        wlans.append(
            WLANProfile(
                name=str(essid or ssid_name),
                essid=_as_scalar(essid),
                ssid_profile=str(ssid_name),
                security=_as_scalar(
                    _find_field(ssid_record, "opmode", "security", "encryption")
                ),
            )
        )
    return sorted(wlans, key=lambda wlan: wlan.name.lower())


def _profile_records(value: Any, object_name: str) -> list[dict[str, Any]]:
    if not isinstance(value, dict):
        return [item for item in value or [] if isinstance(item, dict)] if isinstance(value, list) else []
    data = value.get("_data", value)
    if isinstance(data, dict) and object_name in data:
        data = data[object_name]
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        if _profile_name(data):
            return [data]
        return [item for item in data.values() if isinstance(item, dict) and _profile_name(item)]
    return []


def _profile_name(record: dict[str, Any]) -> str | None:
    value = _find_field(record, "profile-name", "profile_name", "name")
    return _as_scalar(value)


def _find_field(value: Any, *wanted_keys: str) -> Any:
    wanted = {key.lower().replace("_", "-") for key in wanted_keys}
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower().replace("_", "-") in wanted:
                scalar = _as_scalar(item)
                if scalar is not None:
                    return scalar
        for item in value.values():
            found = _find_field(item, *wanted_keys)
            if found is not None:
                return found
    elif isinstance(value, list):
        for item in value:
            found = _find_field(item, *wanted_keys)
            if found is not None:
                return found
    return None


def _as_scalar(value: Any) -> str | int | None:
    if isinstance(value, (str, int)) and not isinstance(value, bool):
        return value
    if isinstance(value, dict) and len(value) == 1:
        return _as_scalar(next(iter(value.values())))
    return None


def _contains_string(value: Any, target: str) -> bool:
    if isinstance(value, dict):
        return any(_contains_string(item, target) for item in value.values())
    if isinstance(value, list):
        return any(_contains_string(item, target) for item in value)
    return value == target


def _deduplicate_findings(findings: list[Finding]) -> list[Finding]:
    unique: dict[tuple[str, tuple[str, ...]], Finding] = {}
    for finding in findings:
        key = (finding.id, tuple(finding.evidence))
        unique[key] = finding
    return list(unique.values())
