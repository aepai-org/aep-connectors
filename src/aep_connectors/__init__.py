"""Public AEP Connector Framework exports."""

from .api_client import AEPConnectorClient
from .core import (
    AdapterRegistry,
    ConnectorAdapter,
    ConnectorKind,
    ConnectorStatus,
    RuntimeEnvelope,
)
from .credential import MASKED_CREDENTIAL, redact_text, redact_value
from .security import (
    HTTPS_REQUIRED,
    CredentialTransportError,
    validate_credential_transport_url,
)

__all__ = [
    "AdapterRegistry",
    "ConnectorAdapter",
    "ConnectorKind",
    "ConnectorStatus",
    "CredentialTransportError",
    "HTTPS_REQUIRED",
    "RuntimeEnvelope",
    "AEPConnectorClient",
    "MASKED_CREDENTIAL",
    "redact_text",
    "redact_value",
    "validate_credential_transport_url",
]
