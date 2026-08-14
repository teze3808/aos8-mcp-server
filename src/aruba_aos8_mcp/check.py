from __future__ import annotations

import asyncio
import json
from typing import Any

from pydantic import ValidationError

from aruba_aos8_mcp.client import AOS8Client, AOS8ClientError
from aruba_aos8_mcp.config import get_settings


def _version_line(result: dict[str, Any]) -> str | None:
    values = result.get("_data")
    if not isinstance(values, list):
        return None
    for value in values:
        if not isinstance(value, str):
            continue
        for line in value.splitlines():
            if "Version " in line:
                return line.strip()
    return None


async def _check() -> dict[str, Any]:
    settings = get_settings()
    client = AOS8Client(settings)
    try:
        await client.login()
        result = await client.show_command("show version")
        return {
            "status": "ok",
            "target": settings.normalized_base_url,
            "command": "show version",
            "version": _version_line(result),
        }
    finally:
        try:
            await client.logout()
        except AOS8ClientError:
            pass
        finally:
            await client.close()


def main() -> None:
    try:
        result = asyncio.run(_check())
    except (AOS8ClientError, ValidationError) as exc:
        result = {"status": "error", "error": str(exc)}
        print(json.dumps(result, indent=2))
        raise SystemExit(1) from None
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
