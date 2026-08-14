"""Capability names used by a runtime mapped to canonical AEP identifiers."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CapabilityMapping:
    external_capability: str
    capability_id: UUID


def build_capability_mapping(
    external_capability: object, capability_id: object
) -> CapabilityMapping:
    if not isinstance(external_capability, str) or not external_capability.strip():
        raise ValueError("external_capability must be a non-empty string")
    try:
        canonical_id = UUID(str(capability_id))
    except (TypeError, ValueError) as error:
        raise ValueError("capability_id must be a UUID") from error
    return CapabilityMapping(external_capability.strip(), canonical_id)
