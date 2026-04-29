"""Scheme auto-selection for x402-tools."""

from typing import Literal

Scheme = Literal["exact", "exact_permit", "exact_gasfree"]

SCHEME_TABLE: dict[str, dict[str, list[Scheme]]] = {
    # BSC Testnet
    "eip155:97": {
        "DHLU": ["exact"],
        "USDT": ["exact_permit"],
        "USDC": ["exact_permit"],
    },
    # BSC Mainnet
    "eip155:56": {
        "USDT": ["exact_permit"],
        "USDC": ["exact_permit"],
    },
    # TRON: default USDT to GasFree because hosted/self-hosted exact_permit
    # settlement can verify signatures but still fail during permitTransferFrom
    # broadcast.
    "tron:mainnet": {
        "USDT": ["exact_gasfree"],
        "USDD": ["exact_gasfree"],
    },
    "tron:nile": {
        "USDT": ["exact_gasfree"],
        "USDD": ["exact_gasfree"],
    },
    "tron:shasta": {
        "USDT": ["exact_gasfree"],
    },
}


def pick_scheme(network: str, token_symbol: str) -> Scheme | None:
    """Pick recommended scheme for (network, token) pair."""
    network_table = SCHEME_TABLE.get(network)
    if not network_table:
        return None

    schemes = network_table.get(token_symbol.upper())
    return schemes[0] if schemes else None


def is_known_scheme(scheme: str) -> bool:
    """Check if scheme is valid."""
    return scheme in ("exact", "exact_permit", "exact_gasfree")
