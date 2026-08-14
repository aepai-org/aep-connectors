"""Core adapter contracts and deterministic adapter selection."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol

from .capability import CapabilityMapping
from .credential import MASKED_CREDENTIAL, redact_value
from .heartbeat import Heartbeat
from .identity import RuntimeIdentity
from .result_bridge import AEPResult, RuntimeResult
from .task_bridge import AEPTask, RuntimeTask
from .wallet import PublicWalletReference


class ConnectorKind(StrEnum):
    HTTP = "HTTP"
    OPENCLAW = "OPENCLAW"
    HERMES = "HERMES"


class ConnectorStatus(StrEnum):
    REGISTERED = "REGISTERED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class RuntimeEnvelope:
    operation: str
    payload: dict[str, Any]
    headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if redact_value(self.headers) != self.headers:
            raise ValueError(
                "Credential headers are forbidden in serializable runtime envelopes"
            )

    def __repr__(self) -> str:
        headers = MASKED_CREDENTIAL if self.headers else {}
        return (
            f"RuntimeEnvelope(operation={self.operation!r}, "
            f"payload={redact_value(self.payload)!r}, headers={headers!r})"
        )


class ConnectorAdapter(Protocol):
    kind: ConnectorKind

    def map_identity(self, payload: dict[str, Any]) -> RuntimeIdentity: ...
    def map_capability(self, payload: dict[str, Any]) -> CapabilityMapping: ...
    def task_to_runtime(self, task: AEPTask) -> RuntimeTask: ...
    def result_to_aep(self, result: RuntimeResult) -> AEPResult: ...
    def map_heartbeat(self, payload: dict[str, Any]) -> Heartbeat: ...
    def map_wallet(self, payload: dict[str, Any]) -> PublicWalletReference: ...


class AdapterRegistry:
    """Explicit runtime registry; selection never probes or modifies a runtime."""

    def __init__(self, adapters: tuple[ConnectorAdapter, ...]) -> None:
        self._adapters = {adapter.kind: adapter for adapter in adapters}

    def get(self, kind: ConnectorKind | str) -> ConnectorAdapter:
        normalized = ConnectorKind(kind)
        try:
            return self._adapters[normalized]
        except KeyError as error:
            raise LookupError(
                f"Connector adapter is not installed: {normalized}"
            ) from error

    def supported(self) -> tuple[ConnectorKind, ...]:
        return tuple(sorted(self._adapters, key=str))
