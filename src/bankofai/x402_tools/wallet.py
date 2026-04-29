"""Wallet detection and private key handling."""

import os
from typing import Literal

from bankofai.x402.signers import EvmClientSigner, TronClientSigner


def read_private_key(wallet_network: Literal["tron", "evm"]) -> str:
    """Read private key from environment."""
    env_name = "TRON_PRIVATE_KEY" if wallet_network == "tron" else "EVM_PRIVATE_KEY"
    raw = os.getenv(env_name, "").strip()

    if not raw:
        raise ValueError(
            f"{env_name} is not set in the environment.\n"
            f"Export your {'TRON' if wallet_network == 'tron' else 'EVM'} private key "
            f"(0x-prefixed hex) as {env_name}."
        )

    return raw if raw.startswith("0x") else f"0x{raw}"


async def resolve_tron_signer(wallet_source: str = "agent-wallet") -> TronClientSigner:
    """Resolve TRON signer (agent-wallet or env fallback)."""
    if wallet_source == "env":
        private_key = read_private_key("tron")
        return TronClientSigner.from_private_key(private_key)

    try:
        return await TronClientSigner.create()
    except Exception as err:
        import sys

        sys.stderr.write(
            f"[x402-tools] agent-wallet TRON wallet unavailable ({err}); "
            f"falling back to TRON_PRIVATE_KEY.\n"
        )
        private_key = read_private_key("tron")
        return TronClientSigner.from_private_key(private_key)


async def resolve_evm_signer(wallet_source: str = "agent-wallet") -> EvmClientSigner:
    """Resolve EVM signer (agent-wallet or env fallback)."""
    if wallet_source == "env":
        private_key = read_private_key("evm")
        return EvmClientSigner.from_private_key(private_key)

    try:
        return await EvmClientSigner.create()
    except Exception as err:
        import sys

        sys.stderr.write(
            f"[x402-tools] agent-wallet EVM wallet unavailable ({err}); "
            f"falling back to EVM_PRIVATE_KEY.\n"
        )
        private_key = read_private_key("evm")
        return EvmClientSigner.from_private_key(private_key)
