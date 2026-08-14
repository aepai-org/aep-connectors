"""Hermes runtime mapping without changing or embedding Hermes."""

from typing import Any

from ..capability import CapabilityMapping, build_capability_mapping
from ..core import ConnectorKind
from ..heartbeat import Heartbeat, build_heartbeat
from ..identity import RuntimeIdentity, require_text
from ..result_bridge import AEPResult, RuntimeResult, build_result
from ..task_bridge import AEPTask, RuntimeTask
from ..wallet import PublicWalletReference, build_wallet_reference


class HermesAdapter:
    kind = ConnectorKind.HERMES

    def map_identity(self, payload: dict[str, Any]) -> RuntimeIdentity:
        return RuntimeIdentity(
            require_text(payload, "agent_id"),
            require_text(payload, "display_name"),
            "hermes",
        )

    def map_capability(self, payload: dict[str, Any]) -> CapabilityMapping:
        return build_capability_mapping(
            payload.get("tool_name"), payload.get("aep_capability_id")
        )

    def task_to_runtime(self, task: AEPTask) -> RuntimeTask:
        return RuntimeTask(
            task.session_id,
            {
                "conversation_id": task.session_id,
                "prompt": task.description,
                "context": {
                    "aep_task_id": str(task.id),
                    "title": task.title,
                    **task.input_context,
                },
            },
        )

    def result_to_aep(self, result: RuntimeResult) -> AEPResult:
        return build_result(
            status=result.payload.get("state"),
            artifact_type=result.payload.get("output_type"),
            location=result.payload.get("output_uri"),
            metadata=result.payload.get("output_metadata"),
            checksum=result.payload.get("checksum"),
        )

    def map_heartbeat(self, payload: dict[str, Any]) -> Heartbeat:
        return build_heartbeat(
            {
                "status": payload.get("availability"),
                "health_status": payload.get("health"),
                "current_load": payload.get("current_load"),
                "max_concurrency": payload.get("max_concurrency"),
                "timestamp": payload.get("observed_at"),
            }
        )

    def map_wallet(self, payload: dict[str, Any]) -> PublicWalletReference:
        return build_wallet_reference(
            {"network": payload.get("network"), "address": payload.get("address")}
        )
