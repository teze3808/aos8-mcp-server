from __future__ import annotations

import logging
import re
from typing import Any

import httpx

from aruba_aos8_mcp.config import Settings

logging.getLogger("httpx").setLevel(logging.WARNING)

CONFIG_OBJECT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


class AOS8ClientError(RuntimeError):
    """Raised when the AOS8 API returns an error or an invalid response."""


class AOS8Client:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._csrf_token: str | None = None
        self._client = httpx.AsyncClient(
            base_url=settings.normalized_base_url,
            verify=settings.verify_ssl,
            timeout=settings.request_timeout,
            follow_redirects=True,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> AOS8Client:
        await self.login()
        return self

    async def __aexit__(self, *_exc: object) -> None:
        try:
            await self.logout()
        finally:
            await self.close()

    async def login(self) -> dict[str, Any]:
        response = await self._client.post(
            "/v1/api/login",
            data={
                "username": self.settings.username,
                "password": self.settings.password,
            },
        )
        data = self._parse_response(response)

        csrf_token = response.headers.get("X-CSRF-Token")
        if not csrf_token and isinstance(data, dict):
            csrf_token = data.get("_global_result", {}).get("X-CSRF-Token") or data.get("csrf_token")
        if csrf_token:
            self._csrf_token = csrf_token
            self._client.headers.update({"X-CSRF-Token": csrf_token})

        return data

    async def logout(self) -> dict[str, Any]:
        response = await self._client.post("/v1/api/logout")
        if response.status_code in {401, 403, 404}:
            return {"status": "logout skipped", "status_code": response.status_code}
        return self._parse_response(response)

    async def show_command(self, command: str, config_path: str | None = None) -> dict[str, Any]:
        normalized = self.validate_show_command(command)

        params: dict[str, str] = {"command": normalized}
        if config_path:
            params["config_path"] = config_path

        response = await self._client.get("/v1/configuration/showcommand", params=params)
        if response.status_code == 401:
            await self.login()
            response = await self._client.get("/v1/configuration/showcommand", params=params)
        return self._parse_response(response)

    async def get_config_object(
        self,
        object_name: str,
        config_path: str = "/md",
        query_params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        normalized_object = self.validate_config_object_name(object_name)
        normalized_config_path = config_path.strip() or "/md"

        params = {"config_path": normalized_config_path}
        if query_params:
            params.update(query_params)

        response = await self._client.get(
            f"/v1/configuration/object/{normalized_object}",
            params=params,
        )
        if response.status_code == 401:
            await self.login()
            response = await self._client.get(
                f"/v1/configuration/object/{normalized_object}",
                params=params,
            )
        return self._parse_response(response)

    @staticmethod
    def validate_show_command(command: str) -> str:
        normalized = command.strip()
        if not normalized.lower().startswith("show "):
            raise AOS8ClientError("Only read-only commands beginning with 'show ' are allowed.")
        return normalized

    @staticmethod
    def validate_config_object_name(object_name: str) -> str:
        normalized = object_name.strip()
        if not CONFIG_OBJECT_RE.fullmatch(normalized):
            raise AOS8ClientError(
                "Configuration object names may only contain letters, numbers, dots, underscores, "
                "and hyphens."
            )
        return normalized

    @staticmethod
    def _parse_response(response: httpx.Response) -> dict[str, Any]:
        if response.status_code == 200 and not response.content.strip():
            return {"_data": [], "_meta": {"empty_response": True}}

        try:
            data = response.json()
        except ValueError as exc:
            snippet = response.text[:300]
            raise AOS8ClientError(
                f"AOS8 returned non-JSON response: HTTP {response.status_code}: {snippet}"
            ) from exc

        if response.is_error:
            raise AOS8ClientError(f"AOS8 API error: HTTP {response.status_code}: {data}")

        if not isinstance(data, dict):
            return {"result": data}
        return data
