"""Canonical JSON-over-HTTPS runtime adapter."""

from typing import Any

from ..capability import CapabilityMapping, build_capability_mapping
from ..core import ConnectorKind
from ..heartbeat import Heartbeat, build_heartbeat
from ..identity import RuntimeIdentity, require_text
from ..result_bridge import AEPResult, RuntimeResult, build_result
from ..task_bridge import AEPTask, RuntimeTask
from ..wallet import PublicWalletReference, build_wallet_reference


class HTTPAdapter:
    kind = ConnectorKind.HTTP

    def map_identity(self, payload: dict[str, Any]) -> RuntimeIdentity:
        return RuntimeIdentity(
            require_text(payload, "agent_id"),
            require_text(payload, "name"),
            "http",
        )

    def map_capability(self, payload: dict[str, Any]) -> CapabilityMapping:
        return build_capability_mapping(
            payload.get("external_capability"), payload.get("capability_id")
        )

    def task_to_runtime(self, task: AEPTask) -> RuntimeTask:
        return RuntimeTask(
            task.session_id,
            {
                "task_id": str(task.id),
                "title": task.title,
                "description": task.description,
                "input_context": task.input_context,
            },
        )

    def result_to_aep(self, result: RuntimeResult) -> AEPResult:
        return build_result(**result.payload)

    def map_heartbeat(self, payload: dict[str, Any]) -> Heartbeat:
        return build_heartbeat(payload)

    def map_wallet(self, payload: dict[str, Any]) -> PublicWalletReference:
        return build_wallet_reference(payload)
