"""OpenClaw runtime mapping without changing or embedding OpenClaw."""

from typing import Any

from ..capability import CapabilityMapping, build_capability_mapping
from ..core import ConnectorKind
from ..heartbeat import Heartbeat, build_heartbeat
from ..identity import RuntimeIdentity, require_text
from ..result_bridge import AEPResult, RuntimeResult, build_result
from ..task_bridge import AEPTask, RuntimeTask
from ..wallet import PublicWalletReference, build_wallet_reference


class OpenClawAdapter:
    kind = ConnectorKind.OPENCLAW

    def map_identity(self, payload: dict[str, Any]) -> RuntimeIdentity:
        return RuntimeIdentity(
            require_text(payload, "agentId"),
            require_text(payload, "displayName"),
            "openclaw",
        )

    def map_capability(self, payload: dict[str, Any]) -> CapabilityMapping:
        return build_capability_mapping(
            payload.get("skill"), payload.get("aepCapabilityId")
        )

    def task_to_runtime(self, task: AEPTask) -> RuntimeTask:
        return RuntimeTask(
            task.session_id,
            {
                "sessionKey": task.session_id,
                "message": task.description,
                "metadata": {
                    "aepTaskId": str(task.id),
                    "title": task.title,
                    "inputContext": task.input_context,
                },
            },
        )

    def result_to_aep(self, result: RuntimeResult) -> AEPResult:
        artifact = result.payload.get("artifact", {})
        if not isinstance(artifact, dict):
            raise ValueError("OpenClaw artifact must be an object")
        return build_result(
            status=result.payload.get("status"),
            artifact_type=artifact.get("type"),
            location=artifact.get("location"),
            metadata=artifact.get("metadata"),
            checksum=artifact.get("checksum"),
        )

    def map_heartbeat(self, payload: dict[str, Any]) -> Heartbeat:
        return build_heartbeat(
            {
                "status": payload.get("state"),
                "health_status": payload.get("health"),
                "current_load": payload.get("activeSessions"),
                "max_concurrency": payload.get("maxSessions"),
                "timestamp": payload.get("timestamp"),
            }
        )

    def map_wallet(self, payload: dict[str, Any]) -> PublicWalletReference:
        return build_wallet_reference(
            {"network": payload.get("network"), "address": payload.get("publicAddress")}
        )
