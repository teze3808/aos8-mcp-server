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
    return await _run_show("show license")


@mcp.tool()
async def aos8_get_cluster_status() -> dict[str, Any]:
    """Return AOS8 cluster membership information."""
    return await _run_show("show lc-cluster group-membership")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
