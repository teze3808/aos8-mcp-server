import json

from aruba_aos8_mcp.audit import AUDIT_LOG, configure_audit_logging, emit_audit_event
from aruba_aos8_mcp.config import Settings


def test_audit_can_write_sanitized_jsonl(tmp_path) -> None:
    audit_path = tmp_path / "aos8-audit.jsonl"
    settings = Settings(
        base_url="https://aos8.example:4343",
        username="admin",
        password="secret",
        audit_log_path=str(audit_path),
    )
    configure_audit_logging(settings)

    emit_audit_event(
        {
            "event": "aos8_mcp_downstream_call",
            "operation": "show_command",
            "target": "lab",
            "outcome": "ok",
        }
    )
    for handler in AUDIT_LOG.handlers:
        handler.flush()

    event = json.loads(audit_path.read_text().strip())
    assert event["operation"] == "show_command"
    assert "password" not in event
    for handler in AUDIT_LOG.handlers:
        handler.close()
    AUDIT_LOG.handlers.clear()
