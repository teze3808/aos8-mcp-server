from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from aruba_aos8_mcp.client import AOS8Client, AOS8ClientError
from aruba_aos8_mcp.config import get_settings

mcp = FastMCP("aos8-mcp-server")


async def _run_show(command: str, config_path: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    async with AOS8Client(settings) as client:
        return await client.show_command(command, config_path=config_path)


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
async def aos8_test_connection() -> dict[str, Any]:
    """Log in to AOS8 and run a safe version check."""
    try:
        result = await _run_show("show version")
        return {"ok": True, "command": "show version", "result": result}
    except AOS8ClientError as exc:
        return {"ok": False, "error": str(exc)}


@mcp.tool()
async def aos8_show_command(command: str, config_path: str | None = None) -> dict[str, Any]:
    """Run a read-only Aruba AOS8 show command."""
    return await _run_show(command, config_path=config_path)


@mcp.tool()
async def aos8_get_version() -> dict[str, Any]:
    """Return Aruba AOS8 version information."""
    return await _run_show("show version")


@mcp.tool()
async def aos8_get_switches() -> dict[str, Any]:
    """Return Mobility Conductor and managed-device inventory."""
    return await _run_show("show switches")


@mcp.tool()
async def aos8_get_access_points() -> dict[str, Any]:
    """Return the AOS8 AP database."""
    return await _run_show("show ap database")


@mcp.tool()
async def aos8_get_clients() -> dict[str, Any]:
    """Return connected wireless clients."""
    return await _run_show("show user-table")


@mcp.tool()
async def aos8_get_tunnels() -> dict[str, Any]:
    """Return datapath tunnel information."""
    return await _run_show("show datapath tunnel")


@mcp.tool()
async def aos8_get_license_summary() -> dict[str, Any]:
    """Return AOS8 license information."""
    return _redact_license_keys(await _run_show("show license"))


@mcp.tool()
async def aos8_get_cluster_status() -> dict[str, Any]:
    """Return AOS8 cluster membership information."""
    return await _run_show("show lc-cluster group-membership")


@mcp.tool()
async def aos8_get_managed_devices() -> dict[str, Any]:
    """Return normalized Mobility Conductor and managed-device inventory."""
    rows = [_normalize_switch(row) for row in _switch_rows(await _run_show("show switches"))]
    return {
        "total": len(rows),
        "up": sum(1 for row in rows if _is_up(row.get("status"))),
        "down": sum(1 for row in rows if not _is_up(row.get("status"))),
        "by_type": _count_by(rows, "type"),
        "devices": rows,
    }


@mcp.tool()
async def aos8_get_ap_summary() -> dict[str, Any]:
    """Return normalized AP inventory and AP health summary."""
    rows = [_normalize_ap(row) for row in _ap_rows(await _run_show("show ap database long"))]
    return {
        "total": len(rows),
        "up": sum(1 for row in rows if _is_up(row.get("status"))),
        "down": sum(1 for row in rows if not _is_up(row.get("status"))),
        "by_group": _count_by(rows, "group"),
        "by_model": _count_by(rows, "model"),
        "aps": rows,
    }


@mcp.tool()
async def aos8_get_health_summary() -> dict[str, Any]:
    """Return a concise AOS8 health summary from safe read-only show commands."""
    switches = await aos8_get_managed_devices()
    aps = await aos8_get_ap_summary()
    clients = await _run_show("show user-table")
    tunnels = await _run_show("show datapath tunnel")

    client_rows = _as_list(clients.get("Users")) or _as_list(clients.get("User Table"))
    tunnel_rows = _as_list(tunnels.get("Datapath Tunnel Table"))

    issues: list[str] = []
    if switches["down"]:
        issues.append(f"{switches['down']} switch/controller entries are not up")
    if aps["down"]:
        issues.append(f"{aps['down']} AP entries are not up")
    if clients.get("_meta", {}).get("empty_response"):
        issues.append("Client table returned an empty successful response")

    return {
        "overall_status": "ok" if not issues else "attention",
        "issues": issues,
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


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
