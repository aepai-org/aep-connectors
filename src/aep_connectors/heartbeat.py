"""Runtime availability heartbeat mapping."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Heartbeat:
    status: str
    health_status: str
    current_load: int
    max_concurrency: int
    timestamp: datetime


def build_heartbeat(payload: dict[str, object]) -> Heartbeat:
    status = str(payload.get("status", "AVAILABLE")).upper()
    health = str(payload.get("health_status", "HEALTHY")).upper()
    if status not in {"AVAILABLE", "BUSY", "OFFLINE", "DEGRADED", "MAINTENANCE"}:
        raise ValueError("unsupported runtime status")
    if health not in {"HEALTHY", "DEGRADED", "UNHEALTHY", "UNKNOWN"}:
        raise ValueError("unsupported runtime health status")
    current_load = payload.get("current_load", 0)
    max_concurrency = payload.get("max_concurrency", 1)
    if not isinstance(current_load, int) or not isinstance(max_concurrency, int):
        raise ValueError("load values must be integers")
    if current_load < 0 or max_concurrency < 1 or current_load > max_concurrency:
        raise ValueError("runtime load is outside its allowed range")
    timestamp = payload.get("timestamp")
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if not isinstance(timestamp, datetime) or timestamp.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return Heartbeat(status, health, current_load, max_concurrency, timestamp)
