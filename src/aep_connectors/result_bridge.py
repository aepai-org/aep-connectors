"""External runtime results mapped to AEP artifact references."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class RuntimeResult:
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class AEPResult:
    status: str
    artifact_type: str
    location: str
    metadata: dict[str, Any] = field(default_factory=dict)
    checksum: str | None = None


def build_result(
    *,
    status: object,
    artifact_type: object,
    location: object,
    metadata: object = None,
    checksum: object = None,
) -> AEPResult:
    if status not in {"COMPLETED", "FAILED"}:
        raise ValueError("result status must be COMPLETED or FAILED")
    if not isinstance(artifact_type, str) or not artifact_type.strip():
        raise ValueError("artifact_type must be a non-empty string")
    if not isinstance(location, str) or not location.strip():
        raise ValueError("location must be a non-empty string")
    if metadata is not None and not isinstance(metadata, dict):
        raise ValueError("metadata must be an object")
    if checksum is not None and not isinstance(checksum, str):
        raise ValueError("checksum must be a string")
    return AEPResult(
        status=str(status),
        artifact_type=artifact_type.strip(),
        location=location.strip(),
        metadata=metadata or {},
        checksum=checksum,
    )
