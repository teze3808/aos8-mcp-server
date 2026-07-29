import httpx
import anyio
import pytest

from aruba_aos8_mcp.client import AOS8Client, AOS8ClientError
from aruba_aos8_mcp.config import Settings


def _client_with_handler(handler: httpx.MockTransport) -> AOS8Client:
    settings = Settings(
        base_url="https://aos8.example:4343",
        username="admin",
        password="secret",
    )
    client = AOS8Client(settings)
    client._client = httpx.AsyncClient(
        base_url=settings.normalized_base_url,
        transport=handler,
    )
    return client


def test_show_command_rejects_non_show_commands() -> None:
    with pytest.raises(AOS8ClientError):
        AOS8Client.validate_show_command("configure terminal")


def test_show_command_normalizes_whitespace() -> None:
    assert AOS8Client.validate_show_command("  show version  ") == "show version"


def test_config_object_name_validation_accepts_safe_names() -> None:
    assert AOS8Client.validate_config_object_name("ssid_prof") == "ssid_prof"
    assert AOS8Client.validate_config_object_name("int_vlan") == "int_vlan"
    assert AOS8Client.validate_config_object_name("object.name-1") == "object.name-1"


def test_config_object_name_validation_rejects_paths() -> None:
    with pytest.raises(AOS8ClientError):
        AOS8Client.validate_config_object_name("../write_memory")


def test_parse_response_accepts_empty_success_body() -> None:
    response = httpx.Response(200, content=b"")

    assert AOS8Client._parse_response(response) == {
        "_data": [],
        "_meta": {"empty_response": True},
    }


def test_list_config_objects_uses_native_object_endpoint() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"objects": ["ap_group", "ssid_prof"]})

    async def scenario() -> dict:
        client = _client_with_handler(httpx.MockTransport(handler))
        try:
            return await client.list_config_objects({"type": "meta"})
        finally:
            await client.close()

    result = anyio.run(scenario)

    assert result == {"objects": ["ap_group", "ssid_prof"]}
    assert requests[0].url.path == "/v1/configuration/object"
    assert requests[0].url.params["type"] == "meta"


def test_list_config_containers_uses_native_container_endpoint() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"containers": ["configuration", "profile"]})

    async def scenario() -> dict:
        client = _client_with_handler(httpx.MockTransport(handler))
        try:
            return await client.list_config_containers()
        finally:
            await client.close()

    result = anyio.run(scenario)

    assert result == {"containers": ["configuration", "profile"]}
    assert requests[0].url.path == "/v1/configuration/container"


def test_get_retries_temporary_server_error() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) == 1:
            return httpx.Response(503, json={"error": "busy"})
        return httpx.Response(200, json={"result": "ok"})

    async def scenario() -> dict:
        settings = Settings(
            base_url="https://aos8.example:4343",
            username="admin",
            password="secret",
            retry_backoff_seconds=0,
        )
        client = AOS8Client(settings)
        client._client = httpx.AsyncClient(
            base_url=settings.normalized_base_url,
            transport=httpx.MockTransport(handler),
        )
        try:
            return await client.list_config_objects()
        finally:
            await client.close()

    assert anyio.run(scenario) == {"result": "ok"}
    assert len(requests) == 2
