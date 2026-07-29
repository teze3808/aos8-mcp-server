"""Deterministic checks used by MCP tools before an AI explains the result."""

from __future__ import annotations

from typing import Any

from aruba_aos8_mcp.models import Finding


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
    observations: list[tuple[str, str]] = []

    def walk(value: Any, path: str = "root") -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                walk(item, f"{path}.{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, f"{path}[{index}]")
        elif isinstance(value, str):
            observations.append((path.lower(), value.lower()))

    walk(config)
    for path, value in observations:
        if any(term in value for term in ("open", "unencrypted")) and "enhanced-open" not in value:
            findings.append(
                Finding(
                    id="AOS8-WLAN-001",
                    severity="high",
                    title="Open WLAN security mode detected",
                    evidence=[f"{path} = {value}"],
                    recommendation="Confirm this WLAN is intentionally open and isolate it with an appropriate guest design.",
                )
            )
        elif "wpa2-psk" in value:
            findings.append(
                Finding(
                    id="AOS8-WLAN-002",
                    severity="medium",
                    title="WPA2-PSK WLAN detected",
                    evidence=[f"{path} = {value}"],
                    recommendation="Review migration to WPA3-SAE or enterprise authentication where compatible.",
                )
            )
        elif "wpa3" in value:
            findings.append(
                Finding(
                    id="AOS8-WLAN-000",
                    severity="info",
                    title="WPA3-capable WLAN security detected",
                    evidence=[f"{path} = {value}"],
                    recommendation="Validate client compatibility and management-frame protection requirements.",
                )
            )

    return _deduplicate_findings(findings)


def _deduplicate_findings(findings: list[Finding]) -> list[Finding]:
    unique: dict[tuple[str, tuple[str, ...]], Finding] = {}
    for finding in findings:
        key = (finding.id, tuple(finding.evidence))
        unique[key] = finding
    return list(unique.values())
