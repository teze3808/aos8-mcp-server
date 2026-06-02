from aruba_aos8_mcp.config import Settings


def test_settings_normalizes_base_url() -> None:
    settings = Settings(
        base_url="https://controller.example.com:4343/",
        username="admin",
        password="secret",
    )

    assert settings.normalized_base_url == "https://controller.example.com:4343"


def test_verify_ssl_accepts_false_string() -> None:
    settings = Settings(
        base_url="https://controller.example.com:4343",
        username="admin",
        password="secret",
        verify_ssl="false",
    )

    assert settings.verify_ssl is False
