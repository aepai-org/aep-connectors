"""Dependency-free HTTP client used by installable Runtime connector products."""

import json
from collections.abc import Callable, Mapping
from typing import Any
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .credential import MASKED_CREDENTIAL, SecretValue, redact_value
from .security import validate_credential_transport_url

JsonObject = dict[str, Any]
Transport = Callable[[str, str, Mapping[str, str], bytes | None], tuple[int, object]]


class _RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_NO_REDIRECT_OPENER = build_opener(_RejectRedirects)


def _transport(
    method: str,
    url: str,
    headers: Mapping[str, str],
    body: bytes | None,
) -> tuple[int, object]:
    request = Request(url, data=body, headers=dict(headers), method=method)
    try:
        with _NO_REDIRECT_OPENER.open(request, timeout=15) as response:
            payload = response.read()
            return response.status, json.loads(payload) if payload else {}
    except HTTPError as error:
        payload = error.read()
        try:
            return error.code, json.loads(payload) if payload else {}
        except json.JSONDecodeError:
            return error.code, {"detail": payload.decode(errors="replace")}


class AEPConnectorClient:
    """Call existing AEP onboarding, runtime, execution, and economy APIs."""

    __slots__ = (
        "base_url",
        "__credential",
        "_transport",
        "_allow_insecure_localhost",
    )

    def __init__(
        self,
        base_url: str,
        api_key: str,
        transport: Transport | None = None,
        *,
        allow_insecure_localhost: bool = False,
    ) -> None:
        validate_credential_transport_url(
            base_url,
            allow_insecure_localhost=allow_insecure_localhost,
        )
        self.base_url = base_url.rstrip("/")
        self.__credential = SecretValue(api_key)
        self._transport = transport or _transport
        self._allow_insecure_localhost = allow_insecure_localhost

    def register_agent(self, payload: JsonObject) -> JsonObject:
        return self.request("POST", "/v1/agents/register", payload)

    def publish_capability(self, agent_id: str, capability_id: str) -> JsonObject:
        return self.request(
            "POST",
            f"/v1/developers/agents/{agent_id}/capabilities",
            {"capability_id": capability_id},
        )

    def register_connector(self, payload: JsonObject) -> JsonObject:
        return self.request("POST", "/v1/connectors/register", payload)

    def heartbeat(self, agent_id: str, payload: JsonObject) -> JsonObject:
        return self.request("POST", f"/v1/agents/{agent_id}/heartbeat", payload)

    def get_task(self, task_id: str) -> JsonObject:
        return self.request("GET", f"/v1/tasks/{task_id}")

    def get_execution(self, execution_id: str) -> JsonObject:
        return self.request("GET", f"/v1/executions/{execution_id}")

    def send_collaboration_message(
        self, session_id: str, payload: JsonObject
    ) -> JsonObject:
        return self.request(
            "POST", f"/v1/collaboration-sessions/{session_id}/messages", payload
        )

    def register_artifact(self, subtask_id: str, payload: JsonObject) -> JsonObject:
        return self.request("POST", f"/v1/subtasks/{subtask_id}/artifacts", payload)

    def execution_callback(self, execution_id: str, payload: JsonObject) -> JsonObject:
        return self.request("POST", f"/v1/executions/{execution_id}/callback", payload)

    def get_payment(self, settlement_id: str) -> JsonObject:
        return self.request("GET", f"/v1/settlements/{settlement_id}/payment")

    def get_rewards(self, owner_id: str) -> JsonObject:
        return self.request("GET", f"/v1/economy/rewards/{owner_id}")

    def request(
        self, method: str, path: str, payload: JsonObject | None = None
    ) -> JsonObject:
        validate_credential_transport_url(
            self.base_url,
            allow_insecure_localhost=self._allow_insecure_localhost,
        )
        headers = {
            "Accept": "application/json",
            "X-AEP-API-Key": self.__credential._reveal_for_transport(),
        }
        if payload is not None:
            headers["Content-Type"] = "application/json"
        status, response = self._transport(
            method,
            f"{self.base_url}{path}",
            headers,
            json.dumps(payload).encode() if payload is not None else None,
        )
        if status < 200 or status >= 300:
            detail = response.get("detail") if isinstance(response, dict) else response
            detail = redact_value(
                detail,
                known_secrets=(self.__credential._reveal_for_transport(),),
            )
            raise RuntimeError(f"AEP request failed ({status}): {detail}")
        if not isinstance(response, dict):
            raise RuntimeError("AEP returned an invalid object")
        return response

    def __repr__(self) -> str:
        return (
            f"AEPConnectorClient(base_url={self.base_url!r}, "
            f"credential={MASKED_CREDENTIAL!r})"
        )

    def __getstate__(self) -> dict[str, str]:
        return {"base_url": self.base_url, "credential": MASKED_CREDENTIAL}
