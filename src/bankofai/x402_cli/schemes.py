"""Scheme auto-selection for x402-cli."""

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
    # TRON: default to exact_permit. The exact_permit settlement path is
    # stable on mainnet (verified by multiple QA on-chain receipts) and is
    # cheaper for users than exact_gasfree, which adds a per-settlement
    # transferFee plus a one-time activateFee charged from the payer's
    # GasFree custodial address. exact_gasfree is offered as an explicit
    # opt-in second choice for payers who don't hold any TRX — they can
    # pass `--scheme exact_gasfree` to route through the GasFree relayer.
    "tron:mainnet": {
        "USDT": ["exact_permit", "exact_gasfree"],
        "USDD": ["exact_permit", "exact_gasfree"],
    },
    "tron:nile": {
        "USDT": ["exact_permit", "exact_gasfree"],
        "USDD": ["exact_permit", "exact_gasfree"],
    },
    "tron:shasta": {
        "USDT": ["exact_permit", "exact_gasfree"],
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
