from aruba_aos8_mcp.server import _redact_license_keys


def test_redact_license_keys() -> None:
    result = {
        "License Table": [
            {"Key": "secret-license-key", "Service Type": "Access Points: 1000"},
            {"Key": None, "Service Type": "MM-VA: 50"},
        ]
    }

    assert _redact_license_keys(result) == {
        "License Table": [
            {"Key": "<redacted>", "Service Type": "Access Points: 1000"},
            {"Key": None, "Service Type": "MM-VA: 50"},
        ]
    }
