"""Public wallet reference mapping; custody and transfers are out of scope."""

from dataclasses import dataclass

from .identity import require_text


@dataclass(frozen=True, slots=True)
class PublicWalletReference:
    network: str
    address: str


def build_wallet_reference(payload: dict[str, object]) -> PublicWalletReference:
    return PublicWalletReference(
        network=require_text(payload, "network"),
        address=require_text(payload, "address"),
    )
