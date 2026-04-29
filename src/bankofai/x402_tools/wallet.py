"""Wallet detection and private key handling."""

import os
from typing import Literal

from bankofai.x402.signers.client import EvmClientSigner, TronClientSigner


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
        from tronpy.hdwallet import key_to_address
        private_key = read_private_key("tron")
        if private_key.startswith("0x"):
            private_key = private_key[2:]
        priv_key_bytes = bytes.fromhex(private_key)
        address = key_to_address(priv_key_bytes)
        signer = TronClientSigner({"privateKey": private_key, "address": address})
        signer.set_address(address)
        return signer

    try:
        return await TronClientSigner.create()
    except Exception as err:
        import sys

        sys.stderr.write(
            f"[x402-tools] agent-wallet TRON wallet unavailable ({err}); "
            f"falling back to TRON_PRIVATE_KEY.\n"
        )
        from tronpy.hdwallet import key_to_address
        private_key = read_private_key("tron")
        if private_key.startswith("0x"):
            private_key = private_key[2:]
        priv_key_bytes = bytes.fromhex(private_key)
        address = key_to_address(priv_key_bytes)
        signer = TronClientSigner({"privateKey": private_key, "address": address})
        signer.set_address(address)
        return signer


async def resolve_evm_signer(wallet_source: str = "agent-wallet") -> EvmClientSigner:
    """Resolve EVM signer (agent-wallet or env fallback)."""
    if wallet_source == "env":
        from eth_account import Account
        private_key = read_private_key("evm")
        account = Account.from_key(private_key)
        signer = EvmClientSigner(account)
        signer.set_address(account.address)
        return signer

    try:
        return await EvmClientSigner.create()
    except Exception as err:
        import sys

        sys.stderr.write(
            f"[x402-tools] agent-wallet EVM wallet unavailable ({err}); "
            f"falling back to EVM_PRIVATE_KEY.\n"
        )
        from eth_account import Account
        private_key = read_private_key("evm")
        account = Account.from_key(private_key)
        signer = EvmClientSigner(account)
        signer.set_address(account.address)
        return signer
