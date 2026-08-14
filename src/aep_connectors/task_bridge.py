"""AEP task to runtime request types."""

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AEPTask:
    id: UUID
    title: str
    description: str
    input_context: dict[str, Any] = field(default_factory=dict)
    session_id: str | None = None


@dataclass(frozen=True, slots=True)
class RuntimeTask:
    external_session_id: str | None
    payload: dict[str, Any]
