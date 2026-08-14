"""Configuration and endpoint safety checks shared by adapter consumers."""

from collections.abc import Mapping, Sequence
from ipaddress import ip_address
from typing import Any
from urllib.parse import urlsplit

HTTPS_REQUIRED = "HTTPS_REQUIRED"


class CredentialTransportError(ValueError):
    """Raised before an API key can be sent over an unsafe transport."""

    code = HTTPS_REQUIRED

    def __init__(self) -> None:
        super().__init__(
            f"{HTTPS_REQUIRED}: Developer API credentials require HTTPS; "
            "loopback HTTP is allowed only with allow_insecure_localhost=True"
        )


FORBIDDEN_KEY_PARTS = (
    "secret",
    "token",
    "password",
    "private_key",
    "privatekey",
    "signature",
    "credential",
    "api_key",
    "apikey",
    "authorization",
    "cookie",
)


def _is_loopback(hostname: str) -> bool:
    if hostname.lower() == "localhost":
        return True
    try:
        return ip_address(hostname).is_loopback
    except ValueError:
        return False


def validate_credential_transport_url(
    endpoint: str,
    *,
    allow_insecure_localhost: bool = False,
) -> str:
    """Enforce HTTPS, with an explicit loopback-only development exception."""

    parsed = urlsplit(endpoint)
    if not parsed.hostname:
        raise ValueError("AEP base_url must be an absolute HTTP(S) URL")
    if parsed.username or parsed.password:
        raise ValueError("AEP base_url must not contain credentials")
    if parsed.scheme == "https":
        return endpoint
    if (
        parsed.scheme == "http"
        and allow_insecure_localhost
        and _is_loopback(parsed.hostname)
    ):
        return endpoint
    if parsed.scheme == "http":
        raise CredentialTransportError()
    raise ValueError("AEP base_url must use HTTPS")


def validate_public_https_endpoint(endpoint: str) -> str:
    parsed = urlsplit(endpoint)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("connector endpoint must be public HTTPS")
    if parsed.username or parsed.password:
        raise ValueError("connector endpoint must not contain credentials")
    return endpoint


def sanitize_configuration(configuration: Mapping[str, Any]) -> dict[str, Any]:
    """Copy JSON-compatible public settings while rejecting secret-like fields."""

    def visit(value: Any, path: str) -> Any:
        if isinstance(value, Mapping):
            output: dict[str, Any] = {}
            for raw_key, item in value.items():
                if not isinstance(raw_key, str):
                    raise ValueError("connector configuration keys must be strings")
                key = raw_key.strip()
                lowered = key.lower().replace("-", "_")
                if not key or any(part in lowered for part in FORBIDDEN_KEY_PARTS):
                    raise ValueError(
                        f"secret-like connector setting is forbidden: {path}{key}"
                    )
                output[key] = visit(item, f"{path}{key}.")
            return output
        if isinstance(value, Sequence) and not isinstance(
            value, (str, bytes, bytearray)
        ):
            return [visit(item, path) for item in value]
        if isinstance(value, str) and _looks_secret(value):
            raise ValueError(
                f"secret-like connector value is forbidden: {path.rstrip('.')}"
            )
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        raise ValueError("connector configuration must be JSON-compatible")

    return visit(configuration, "")


def _looks_secret(value: str) -> bool:
    normalized = value.strip().lower()
    return (
        normalized.startswith(("bearer ", "basic ", "aep_dev_", "sk-"))
        or "-----begin private key-----" in normalized
        or "-----begin encrypted private key-----" in normalized
    )
