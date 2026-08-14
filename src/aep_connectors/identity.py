"""External runtime identity mapping."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RuntimeIdentity:
    external_agent_id: str
    display_name: str
    runtime: str


def require_text(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()
