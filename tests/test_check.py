from aruba_aos8_mcp.check import _version_line


def test_version_line_extracts_aos_version() -> None:
    result = {
        "_data": [
            "HPE Aruba Networking Wireless Operating System.\n"
            "AOS-8 (MODEL: ArubaMM-VA), Version 8.13.3.0 LSR\n"
            "Switch uptime is 31 days"
        ]
    }

    assert _version_line(result) == "AOS-8 (MODEL: ArubaMM-VA), Version 8.13.3.0 LSR"


def test_version_line_returns_none_for_unexpected_shape() -> None:
    assert _version_line({"_data": []}) is None
    assert _version_line({"result": "unknown"}) is None
