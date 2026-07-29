"""Stable, vendor-neutral-friendly response models for AOS8 MCP tools."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolTarget(BaseModel):
    name: str = "default"
    base_url: str
    config_path: str | None = None


class OperationResult(BaseModel):
    """Common envelope used by normalized operational tools."""

    source: Literal["aos8"] = "aos8"
    collected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: Literal["ok", "attention", "degraded"] = "ok"
    target: ToolTarget
    warnings: list[str] = Field(default_factory=list)
    data: dict[str, Any]


class ManagedDevice(BaseModel):
    name: str | None = None
    type: str | None = None
    ip_address: str | None = None
    ipv6_address: str | None = None
    model: str | None = None
    version: str | None = None
    status: str | None = None
    configuration_state: str | None = None
    config_sync_time_seconds: str | int | None = None
    config_id: str | int | None = None
    location: str | None = None
    release_type: str | None = None


class AccessPoint(BaseModel):
    name: str | None = None
    group: str | None = None
    model: str | None = None
    ap_type: str | int | None = None
    ip_address: str | None = None
    status: str | None = None
    flags: str | int | None = None
    active_controller: str | None = None
    standby_controller: str | None = None
    wired_mac_address: str | None = None
    serial: str | None = None


class Finding(BaseModel):
    id: str
    severity: Literal["high", "medium", "low", "info"]
    title: str
    evidence: list[str]
    recommendation: str
    affected_objects: list[str] = Field(default_factory=list)
