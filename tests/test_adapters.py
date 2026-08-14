import json
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from aep_connectors import (
    HTTPS_REQUIRED,
    MASKED_CREDENTIAL,
    AEPConnectorClient,
    CredentialTransportError,
    redact_value,
)
from aep_connectors.adapters import HermesAdapter, HTTPAdapter, OpenClawAdapter
from aep_connectors.core import AdapterRegistry, ConnectorKind
from aep_connectors.result_bridge import RuntimeResult
from aep_connectors.security import (
    sanitize_configuration,
    validate_public_https_endpoint,
)
from aep_connectors.task_bridge import AEPTask


@pytest.mark.parametrize(
    ("adapter", "key", "expected"),
    [
        (HTTPAdapter(), "task_id", None),
        (OpenClawAdapter(), "message", "Analyze market"),
        (HermesAdapter(), "prompt", "Analyze market"),
    ],
)
def test_task_adapters(adapter, key, expected) -> None:
    task = AEPTask(uuid4(), "Market", "Analyze market", {"region": "EU"}, "s-1")
    mapped = adapter.task_to_runtime(task)
    assert mapped.external_session_id == "s-1"
    assert key in mapped.payload
    if expected is not None:
        assert mapped.payload[key] == expected


def test_http_result_and_registry() -> None:
    adapter = HTTPAdapter()
    result = adapter.result_to_aep(
        RuntimeResult(
            {
                "status": "COMPLETED",
                "artifact_type": "REPORT",
                "location": "https://artifacts.example/report",
                "metadata": {"pages": 3},
                "checksum": "sha256:abc",
            }
        )
    )
    registry = AdapterRegistry((adapter, OpenClawAdapter(), HermesAdapter()))
    assert result.artifact_type == "REPORT"
    assert registry.get("OPENCLAW").kind is ConnectorKind.OPENCLAW
    assert registry.supported() == (
        ConnectorKind.HERMES,
        ConnectorKind.HTTP,
        ConnectorKind.OPENCLAW,
    )


def test_openclaw_and_hermes_runtime_shapes() -> None:
    openclaw = OpenClawAdapter()
    hermes = HermesAdapter()
    heartbeat = openclaw.map_heartbeat(
        {
            "state": "AVAILABLE",
            "health": "HEALTHY",
            "activeSessions": 1,
            "maxSessions": 4,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )
    hermes_result = hermes.result_to_aep(
        RuntimeResult(
            {
                "state": "COMPLETED",
                "output_type": "DATASET",
                "output_uri": "https://artifacts.example/data",
            }
        )
    )
    assert heartbeat.current_load == 1
    assert hermes_result.location.endswith("/data")


def test_openclaw_and_hermes_identity_and_capability_mapping() -> None:
    capability_id = uuid4()
    openclaw = OpenClawAdapter()
    hermes = HermesAdapter()

    assert (
        openclaw.map_identity(
            {"agentId": "claw-1", "displayName": "Research Claw"}
        ).runtime
        == "openclaw"
    )
    assert (
        openclaw.map_capability(
            {"skill": "web-research", "aepCapabilityId": str(capability_id)}
        ).capability_id
        == capability_id
    )
    assert (
        hermes.map_identity(
            {"agent_id": "hermes-1", "display_name": "Hermes Analyst"}
        ).runtime
        == "hermes"
    )
    assert (
        hermes.map_capability(
            {"tool_name": "analysis", "aep_capability_id": str(capability_id)}
        ).external_capability
        == "analysis"
    )


def test_security_rejects_credentials_and_secret_configuration() -> None:
    assert validate_public_https_endpoint("https://runtime.example/connect")
    assert sanitize_configuration({"timeout_ms": 5000, "features": ["tasks"]})
    with pytest.raises(ValueError, match="HTTPS"):
        validate_public_https_endpoint("http://runtime.example/connect")
    with pytest.raises(ValueError, match="credentials"):
        validate_public_https_endpoint("https://user:pass@runtime.example/connect")
    with pytest.raises(ValueError, match="secret-like"):
        sanitize_configuration({"nested": {"api_token": "never-store"}})
    with pytest.raises(ValueError, match="secret-like"):
        sanitize_configuration({"public_setting": "Bearer never-store"})


def test_connector_credential_transport_policy_blocks_before_transport() -> None:
    calls = []

    def transport(method, url, headers, body):
        calls.append((method, url, headers, body))
        return 200, {"id": "task-1"}

    with pytest.raises(CredentialTransportError) as error:
        AEPConnectorClient(
            "http://connector.example",
            "must-not-leave-process",
            transport,
        )
    assert error.value.code == HTTPS_REQUIRED
    assert calls == []

    with pytest.raises(CredentialTransportError):
        AEPConnectorClient(
            "http://localhost:8000",
            "development-key-without-explicit-flag",
            transport,
        )
    assert calls == []

    local = AEPConnectorClient(
        "http://[::1]:8000",
        "development-only-key",
        transport,
        allow_insecure_localhost=True,
    )
    local.get_task("task-1")
    assert len(calls) == 1

    https = AEPConnectorClient(
        "https://connector.example",
        "production-key",
        transport,
    )
    https.get_task("task-2")
    assert len(calls) == 2

    with pytest.raises(CredentialTransportError):
        AEPConnectorClient(
            "http://connector.example",
            "must-not-leave-process",
            transport,
            allow_insecure_localhost=True,
        )
    assert len(calls) == 2


def test_connector_credential_repr_exception_and_serialization_are_redacted() -> None:
    credential = "aep_dev_connector_super_secret"

    def failing_transport(method, url, headers, body):
        assert headers["X-AEP-API-Key"] == credential
        return 401, {"detail": f"Authorization: Bearer {credential}"}

    client = AEPConnectorClient(
        "https://connector.example", credential, failing_transport
    )
    serialized = json.dumps(client.__getstate__())
    assert credential not in repr(client)
    assert credential not in serialized
    assert MASKED_CREDENTIAL in repr(client)
    assert not hasattr(client, "__dict__")
    with pytest.raises(RuntimeError) as error:
        client.get_task("task-1")
    assert credential not in str(error.value)
    assert MASKED_CREDENTIAL in str(error.value)

    telemetry = redact_value(
        {
            "message": f"AEP_API_KEY={credential}",
            "authorization": f"Bearer {credential}",
            "apiKey": credential,
            "privateKey": (
                "-----BEGIN RSA PRIVATE KEY-----\nsecret\n-----END RSA PRIVATE KEY-----"
            ),
        },
        known_secrets=(credential,),
    )
    rendered = json.dumps(telemetry)
    assert credential not in rendered
    assert "BEGIN RSA PRIVATE KEY" not in rendered
