from __future__ import annotations

import difflib
import json
import re
from typing import Any

from mcp.server.fastmcp import FastMCP

from aruba_aos8_mcp.client import AOS8Client, AOS8ClientError
from aruba_aos8_mcp.config import get_settings
from aruba_aos8_mcp.analyzers import analyze_inventory_health, analyze_wlan_security
from aruba_aos8_mcp.models import AccessPoint, ManagedDevice, OperationResult, ToolTarget
from aruba_aos8_mcp.prompts import (
    aos8_ap_group_profile_map,
    aos8_client_connectivity_review,
    aos8_compare_config_paths,
    aos8_config_change_plan,
    aos8_configuration_flow_review,
    aos8_controller_failover_check,
    aos8_hardening_review,
    aos8_health_overview,
    aos8_review_ap_group,
    aos8_safe_show_command,
    aos8_security_review,
    aos8_structured_troubleshooting,
    aos8_troubleshoot_ap,
    aos8_troubleshoot_wlan,
    aos8_wlan_profile_review,
    register_prompts,
)

mcp = FastMCP("aos8-mcp-server")
DiscoveryCacheKey = tuple[str, tuple[tuple[str, str], ...]]
_DISCOVERY_CACHE: dict[DiscoveryCacheKey, dict[str, Any]] = {}
SENSITIVE_FIELD_RE = re.compile(
    r"(passphrase|password|passwd|secret|community|license|private.?key|shared.?key|token|credential)",
    re.IGNORECASE,
)

__all__ = [
    "aos8_ap_group_profile_map",
    "aos8_client_connectivity_review",
    "aos8_compare_config_paths",
    "aos8_config_change_plan",
    "aos8_configuration_flow_review",
    "aos8_controller_failover_check",
    "aos8_hardening_review",
    "aos8_health_overview",
    "aos8_review_ap_group",
    "aos8_safe_show_command",
    "aos8_security_review",
    "aos8_structured_troubleshooting",
    "aos8_troubleshoot_ap",
    "aos8_troubleshoot_wlan",
    "aos8_wlan_profile_review",
]


def _settings_for_target(target_node: str | None = None):
    try:
        return get_settings().for_target(target_node)
    except ValueError as exc:
        raise AOS8ClientError(str(exc)) from exc


def _operation_result(
    data: dict[str, Any],
    *,
    target_node: str | None = None,
    config_path: str | None = None,
    status: str = "ok",
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    settings = _settings_for_target(target_node)
    return OperationResult(
        status=status,  # type: ignore[arg-type]
        target=ToolTarget(
            name=target_node or "default",
            base_url=settings.normalized_base_url,
            config_path=config_path,
        ),
        warnings=warnings or [],
        data=data,
    ).model_dump(mode="json")


async def _run_show(
    command: str,
    config_path: str | None = None,
    target_node: str | None = None,
) -> dict[str, Any]:
    settings = _settings_for_target(target_node)
    async with AOS8Client(settings) as client:
        return await client.show_command(command, config_path=config_path)


async def _get_config_object(
    object_name: str,
    config_path: str = "/md",
    query_params: dict[str, str] | None = None,
    target_node: str | None = None,
) -> dict[str, Any]:
    settings = _settings_for_target(target_node)
    async with AOS8Client(settings) as client:
        return await client.get_config_object(
            object_name,
            config_path=config_path,
            query_params=query_params,
        )


async def _list_config_endpoint(
    endpoint: str,
    query_params: dict[str, str] | None = None,
    *,
    refresh: bool = False,
    target_node: str | None = None,
) -> dict[str, Any]:
    cache_key = (f"{target_node or 'default'}:{endpoint}", tuple(sorted((query_params or {}).items())))
    if not refresh and cache_key in _DISCOVERY_CACHE:
        return {
            **_DISCOVERY_CACHE[cache_key],
            "_mcp_cache": {"hit": True, "endpoint": endpoint},
        }

    settings = _settings_for_target(target_node)
    async with AOS8Client(settings) as client:
        if endpoint == "object":
            result = await client.list_config_objects(query_params=query_params)
        elif endpoint == "container":
            result = await client.list_config_containers(query_params=query_params)
        else:
            raise ValueError(f"Unsupported discovery endpoint: {endpoint}")

    _DISCOVERY_CACHE[cache_key] = result
    return {**result, "_mcp_cache": {"hit": False, "endpoint": endpoint}}


def _redact_license_keys(result: dict[str, Any]) -> dict[str, Any]:
    license_rows = result.get("License Table")
    if not isinstance(license_rows, list):
        return result

    redacted_rows = []
    for row in license_rows:
        if not isinstance(row, dict):
            redacted_rows.append(row)
            continue
        redacted_row = dict(row)
        if redacted_row.get("Key"):
            redacted_row["Key"] = "<redacted>"
        redacted_rows.append(redacted_row)

    return {**result, "License Table": redacted_rows}


def _redact_sensitive_values(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if SENSITIVE_FIELD_RE.search(str(key)):
                redacted[key] = "<redacted>"
            else:
                redacted[key] = _redact_sensitive_values(item)
        return redacted
    if isinstance(value, list):
        return [_redact_sensitive_values(item) for item in value]
    return value


def _json_lines(value: Any) -> list[str]:
    return json.dumps(value, indent=2, sort_keys=True).splitlines()


def _build_json_diff(before: Any, after: Any) -> list[str]:
    return list(
        difflib.unified_diff(
            _json_lines(_redact_sensitive_values(before)),
            _json_lines(_redact_sensitive_values(after)),
            fromfile="current",
            tofile="proposed",
            lineterm="",
        )
    )


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _switch_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in _as_list(result.get("All Switches")) if isinstance(row, dict)]


def _ap_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in _as_list(result.get("AP Database")) if isinstance(row, dict)]


def _normalize_switch(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": row.get("Name"),
        "type": row.get("Type"),
        "ip_address": row.get("IP Address"),
        "ipv6_address": row.get("IPv6 Address"),
        "model": row.get("Model"),
        "version": row.get("Version"),
        "status": row.get("Status"),
        "configuration_state": row.get("Configuration State"),
        "config_sync_time_seconds": row.get("Config Sync Time (sec)"),
        "config_id": row.get("Config ID"),
        "location": row.get("Location"),
        "release_type": row.get("Release Type"),
    }


def _normalize_ap(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": row.get("Name"),
        "group": row.get("Group"),
        "model": f"AP-{row.get('AP Type')}" if row.get("AP Type") else None,
        "ap_type": row.get("AP Type"),
        "ip_address": row.get("IP Address"),
        "status": row.get("Status"),
        "flags": row.get("Flags"),
        "active_controller": row.get("Switch IP"),
        "standby_controller": row.get("Standby IP"),
        "wired_mac_address": row.get("Wired MAC Address"),
        "serial": row.get("Serial #"),
    }


def _count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = row.get(key) or "unknown"
        counts[str(value)] = counts.get(str(value), 0) + 1
    return counts


def _is_up(value: Any) -> bool:
    return str(value or "").lower().startswith("up")


@mcp.tool()
async def aos8_test_connection(target_node: str | None = None) -> dict[str, Any]:
    """Log in to AOS8 and run a safe version check."""
    try:
        result = await _run_show("show version", target_node=target_node)
        return _operation_result(
            {"ok": True, "command": "show version", "result": result}, target_node=target_node
        )
    except AOS8ClientError as exc:
        return _operation_result(
            {"ok": False, "error": str(exc)}, target_node=target_node, status="degraded"
        )


@mcp.tool()
async def aos8_show_command(
    command: str,
    config_path: str | None = None,
    target_node: str | None = None,
) -> dict[str, Any]:
    """Run a read-only Aruba AOS8 show command."""
    return await _run_show(command, config_path=config_path, target_node=target_node)


@mcp.tool()
async def aos8_get_version(target_node: str | None = None) -> dict[str, Any]:
    """Return Aruba AOS8 version information."""
    return await _run_show("show version", target_node=target_node)


@mcp.tool()
async def aos8_get_switches(target_node: str | None = None) -> dict[str, Any]:
    """Return Mobility Conductor and managed-device inventory."""
    return await _run_show("show switches", target_node=target_node)


@mcp.tool()
async def aos8_get_access_points(target_node: str | None = None) -> dict[str, Any]:
    """Return the AOS8 AP database."""
    return await _run_show("show ap database", target_node=target_node)


@mcp.tool()
async def aos8_get_clients(target_node: str | None = None) -> dict[str, Any]:
    """Return connected wireless clients."""
    return await _run_show("show user-table", target_node=target_node)


@mcp.tool()
async def aos8_get_tunnels(target_node: str | None = None) -> dict[str, Any]:
    """Return datapath tunnel information."""
    return await _run_show("show datapath tunnel", target_node=target_node)


@mcp.tool()
async def aos8_get_license_summary(target_node: str | None = None) -> dict[str, Any]:
    """Return AOS8 license information."""
    return _redact_license_keys(await _run_show("show license", target_node=target_node))


@mcp.tool()
async def aos8_get_cluster_status(target_node: str | None = None) -> dict[str, Any]:
    """Return AOS8 cluster membership information."""
    return await _run_show("show lc-cluster group-membership", target_node=target_node)


async def _managed_device_data(target_node: str | None = None) -> dict[str, Any]:
    rows = [
        ManagedDevice.model_validate(_normalize_switch(row)).model_dump(mode="json")
        for row in _switch_rows(await _run_show("show switches", target_node=target_node))
    ]
    return {
        "total": len(rows),
        "up": sum(1 for row in rows if _is_up(row.get("status"))),
        "down": sum(1 for row in rows if not _is_up(row.get("status"))),
        "by_type": _count_by(rows, "type"),
        "devices": rows,
    }


async def _ap_summary_data(target_node: str | None = None) -> dict[str, Any]:
    rows = [
        AccessPoint.model_validate(_normalize_ap(row)).model_dump(mode="json")
        for row in _ap_rows(await _run_show("show ap database long", target_node=target_node))
    ]
    return {
        "total": len(rows),
        "up": sum(1 for row in rows if _is_up(row.get("status"))),
        "down": sum(1 for row in rows if not _is_up(row.get("status"))),
        "by_group": _count_by(rows, "group"),
        "by_model": _count_by(rows, "model"),
        "aps": rows,
    }


@mcp.tool()
async def aos8_get_managed_devices(target_node: str | None = None) -> dict[str, Any]:
    """Return normalized Mobility Conductor and managed-device inventory."""
    return _operation_result(await _managed_device_data(target_node), target_node=target_node)


@mcp.tool()
async def aos8_get_ap_summary(target_node: str | None = None) -> dict[str, Any]:
    """Return normalized AP inventory and AP health summary."""
    return _operation_result(await _ap_summary_data(target_node), target_node=target_node)


@mcp.tool()
async def aos8_get_health_summary(target_node: str | None = None) -> dict[str, Any]:
    """Return a concise AOS8 health summary from safe read-only show commands."""
    switches = await _managed_device_data(target_node)
    aps = await _ap_summary_data(target_node)
    clients = await _run_show("show user-table", target_node=target_node)
    tunnels = await _run_show("show datapath tunnel", target_node=target_node)

    client_rows = _as_list(clients.get("Users")) or _as_list(clients.get("User Table"))
    tunnel_rows = _as_list(tunnels.get("Datapath Tunnel Table"))

    issues: list[str] = []
    if switches["down"]:
        issues.append(f"{switches['down']} switch/controller entries are not up")
    if aps["down"]:
        issues.append(f"{aps['down']} AP entries are not up")
    if clients.get("_meta", {}).get("empty_response"):
        issues.append("Client table returned an empty successful response")

    data = {
        "overall_status": "ok" if not issues else "attention",
        "issues": issues,
        "findings": [
            finding.model_dump(mode="json")
            for finding in analyze_inventory_health(switches["devices"], aps["aps"])
        ],
        "switches": {
            "total": switches["total"],
            "up": switches["up"],
            "down": switches["down"],
            "by_type": switches["by_type"],
        },
        "access_points": {
            "total": aps["total"],
            "up": aps["up"],
            "down": aps["down"],
            "by_group": aps["by_group"],
            "by_model": aps["by_model"],
        },
        "clients": {
            "count": len(client_rows),
            "empty_response": bool(clients.get("_meta", {}).get("empty_response")),
        },
        "tunnels": {
            "count": len(tunnel_rows),
            "empty_response": bool(tunnels.get("_meta", {}).get("empty_response")),
        },
    }
    return _operation_result(
        data,
        target_node=target_node,
        status="attention" if issues else "ok",
    )


@mcp.tool()
async def aos8_list_command_targets() -> dict[str, Any]:
    """List the default AOS8 endpoint and configured direct node targets."""
    settings = get_settings()
    targets = [
        {
            "name": "default",
            "base_url": settings.normalized_base_url,
            "config_path": None,
            "direct_node_api": False,
        }
    ]
    targets.extend(
        {
            "name": name,
            "base_url": target.base_url.unicode_string().rstrip("/"),
            "config_path": target.config_path,
            "direct_node_api": True,
        }
        for name, target in sorted(settings.node_targets.items())
    )
    return _operation_result({"targets": targets}, warnings=[
        "A configured target uses its own API endpoint. Use its name as target_node in operational tools."
    ])


@mcp.tool()
async def aos8_get_node_hierarchy(target_node: str | None = None) -> dict[str, Any]:
    """Return conductor and managed-device nodes, including configured direct targets."""
    inventory = await _managed_device_data(target_node)
    configured = get_settings().node_targets
    nodes = []
    for device in inventory["devices"]:
        name = device.get("name")
        ip_address = device.get("ip_address")
        configured_name = next(
            (key for key in configured if key in {name, ip_address}),
            None,
        )
        nodes.append(
            {
                **device,
                "configured_target": configured_name,
                "direct_node_api_available": configured_name is not None,
            }
        )
    return _operation_result(
        {"root_target": target_node or "default", "nodes": nodes},
        target_node=target_node,
        warnings=[
            "A node is directly queryable only after it is added to AOS8_NODE_TARGETS with its API URL."
        ],
    )


@mcp.tool()
async def aos8_analyze_wlan_security(
    config_path: str = "/md",
    target_node: str | None = None,
) -> dict[str, Any]:
    """Return deterministic WLAN-security findings with raw configuration evidence."""
    config = {
        "virtual_ap": await _get_config_object(
            "virtual_ap", config_path=config_path, target_node=target_node
        ),
        "ssid_prof": await _get_config_object(
            "ssid_prof", config_path=config_path, target_node=target_node
        ),
        "aaa_prof": await _get_config_object(
            "aaa_prof", config_path=config_path, target_node=target_node
        ),
    }
    findings = [finding.model_dump(mode="json") for finding in analyze_wlan_security(config)]
    return _operation_result(
        {"findings": findings, "config_path": config_path},
        target_node=target_node,
        config_path=config_path,
        status="attention" if any(finding["severity"] in {"high", "medium"} for finding in findings) else "ok",
        warnings=["Findings are deterministic checks, not a complete compliance assessment."],
    )


@mcp.tool()
async def aos8_get_config_object(
    object_name: str,
    config_path: str = "/md",
    query_params: dict[str, str] | None = None,
    target_node: str | None = None,
) -> dict[str, Any]:
    """Return a read-only AOS8 configuration object from the hierarchy."""
    return await _get_config_object(
        object_name,
        config_path=config_path,
        query_params=query_params,
        target_node=target_node,
    )


@mcp.tool()
async def aos8_list_config_objects(
    query_params: dict[str, str] | None = None,
    refresh: bool = False,
    target_node: str | None = None,
) -> dict[str, Any]:
    """List native Aruba AOS8 configuration object names exposed by the controller."""
    return await _list_config_endpoint(
        "object", query_params=query_params, refresh=refresh, target_node=target_node
    )


@mcp.tool()
async def aos8_list_config_containers(
    query_params: dict[str, str] | None = None,
    refresh: bool = False,
    target_node: str | None = None,
) -> dict[str, Any]:
    """List native Aruba AOS8 configuration container names exposed by the controller."""
    return await _list_config_endpoint(
        "container", query_params=query_params, refresh=refresh, target_node=target_node
    )


@mcp.tool()
async def aos8_plan_config_object_change(
    object_name: str,
    proposed_payload: dict[str, Any],
    config_path: str = "/md",
    query_params: dict[str, str] | None = None,
    include_current: bool = True,
    target_node: str | None = None,
) -> dict[str, Any]:
    """Plan a native AOS8 config-object change without sending any write request."""
    current = (
        await _get_config_object(
            object_name,
            config_path=config_path,
            query_params=query_params,
            target_node=target_node,
        )
        if include_current
        else None
    )

    params = {"config_path": config_path}
    if query_params:
        params.update(query_params)

    current_object_data = None
    if isinstance(current, dict):
        data = current.get("_data")
        if isinstance(data, dict):
            current_object_data = data.get(object_name)

    before_for_diff = current_object_data if current_object_data is not None else current

    return {
        "mode": "plan_only",
        "writes_executed": False,
        "save_executed": False,
        "message": "No AOS8 configuration write was sent. This is a proposed change plan only.",
        "object_name": object_name,
        "config_path": config_path,
        "proposed_request": {
            "method": "POST",
            "path": f"/v1/configuration/object/{object_name}",
            "params": params,
            "body": _redact_sensitive_values(proposed_payload),
        },
        "current": _redact_sensitive_values(current) if include_current else None,
        "diff": _build_json_diff(before_for_diff, proposed_payload) if include_current else [],
        "warnings": [
            "Plan-only tool: review payload schema against AOS8 object metadata before enabling writes.",
            "No write_memory/save operation is included or executed.",
            "Sensitive-looking fields are redacted in the plan output.",
        ],
    }


@mcp.tool()
async def aos8_get_ap_group_config(
    config_path: str = "/md",
    query_params: dict[str, str] | None = None,
    target_node: str | None = None,
) -> dict[str, Any]:
    """Return AP group configuration from the AOS8 configuration datastore."""
    return await _get_config_object(
        "ap_group", config_path=config_path, query_params=query_params, target_node=target_node
    )


@mcp.tool()
async def aos8_get_virtual_ap_profiles(
    config_path: str = "/md",
    query_params: dict[str, str] | None = None,
    target_node: str | None = None,
) -> dict[str, Any]:
    """Return Virtual AP profile configuration from the AOS8 configuration datastore."""
    return await _get_config_object(
        "virtual_ap", config_path=config_path, query_params=query_params, target_node=target_node
    )


@mcp.tool()
async def aos8_get_ssid_profiles(
    config_path: str = "/md",
    query_params: dict[str, str] | None = None,
    target_node: str | None = None,
) -> dict[str, Any]:
    """Return SSID profile configuration from the AOS8 configuration datastore."""
    return await _get_config_object(
        "ssid_prof", config_path=config_path, query_params=query_params, target_node=target_node
    )


@mcp.tool()
async def aos8_get_aaa_profiles(
    config_path: str = "/md",
    query_params: dict[str, str] | None = None,
    target_node: str | None = None,
) -> dict[str, Any]:
    """Return AAA profile configuration from the AOS8 configuration datastore."""
    return await _get_config_object(
        "aaa_prof", config_path=config_path, query_params=query_params, target_node=target_node
    )


register_prompts(mcp)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
