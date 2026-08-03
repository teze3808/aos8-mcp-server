"""Sanitized audit logging for local stdio operation."""

from __future__ import annotations

import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Any

from aruba_aos8_mcp.config import Settings


AUDIT_LOG = logging.getLogger("aruba_aos8_mcp.audit")
AUDIT_LOG.setLevel(logging.INFO)
AUDIT_LOG.propagate = False


def configure_audit_logging(settings: Settings) -> None:
    """Configure stderr plus an optional rotating JSONL audit file."""
    for handler in AUDIT_LOG.handlers:
        handler.close()
    AUDIT_LOG.handlers.clear()
    formatter = logging.Formatter("%(message)s")

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)
    AUDIT_LOG.addHandler(stderr_handler)

    if settings.audit_log_path:
        file_handler = RotatingFileHandler(
            settings.audit_log_path,
            maxBytes=settings.audit_log_max_bytes,
            backupCount=settings.audit_log_backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        AUDIT_LOG.addHandler(file_handler)


def emit_audit_event(event: dict[str, Any]) -> None:
    """Write one compact JSON record without tool payloads or controller output."""
    AUDIT_LOG.info(json.dumps(event, sort_keys=True, separators=(",", ":")))
