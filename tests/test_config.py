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


def test_tls_verification_defaults_to_enabled_and_accepts_ca_bundle() -> None:
    settings = Settings(
        base_url="https://aos8.example:4343",
        username="admin",
        password="secret",
        verify_ssl=True,
        ca_bundle="/etc/ssl/aos8-ca.pem",
    )

    assert settings.verify_ssl is True
    assert settings.httpx_verify == "/etc/ssl/aos8-ca.pem"


def test_settings_can_select_configured_node_target() -> None:
    settings = Settings(
        base_url="https://mm.example:4343",
        username="admin",
        password="secret",
        node_targets={
            "SE-VMC-1": {
                "base_url": "https://md1.example:4343",
                "config_path": "/md/SE/DC1",
            }
        },
    )

    target = settings.for_target("SE-VMC-1")

    assert target.normalized_base_url == "https://md1.example:4343"
    assert target.username == "admin"
    assert target.node_targets["SE-VMC-1"].config_path == "/md/SE/DC1"
