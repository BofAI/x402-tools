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
    # TRON: default to exact_permit.
    # In the steady state (i.e. from the wallet's second payment onward),
    # per-payment gas is paid by the facilitator — the payer signs an
    # off-chain permit and pays no on-chain TRX. The cli's ensure_allowance
    # step does require the payer to broadcast a one-time `approve` the
    # first time they pay through a given token's PaymentPermit contract
    # (~6 TRX on mainnet); that's a visible one-shot cost from the user's
    # perspective, not a per-payment cost.
    #
    # exact_gasfree remains registered as the opt-in second choice for
    # payers who don't even want to pay that one-time approve. It routes
    # everything through a GasFree relayer that fronts gas in exchange
    # for a per-settlement transferFee plus a one-time activateFee
    # deducted from a derived custodial address. Verified stable but
    # adds per-payment fees — that's why it's no longer the default.
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
