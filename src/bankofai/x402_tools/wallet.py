"""Wallet resolution — delegates to bankofai-agent-wallet.

agent-wallet itself decides the source: the encrypted local store under
`~/.agent-wallet/` first, then env vars (`AGENT_WALLET_PRIVATE_KEY` /
`TRON_PRIVATE_KEY` / `AGENT_WALLET_MNEMONIC` / `TRON_MNEMONIC`). If the
local-store config is missing or broken, we fall back to agent-wallet's
`EnvWalletProvider` directly so a single env var keeps the CLI usable.

There is **no** in-tree env fallback or LocalWallet implementation —
all signing surface stays inside agent-wallet.
"""

from __future__ import annotations

import logging
import sys

from bankofai.x402.signers.client import EvmClientSigner, TronClientSigner

logger = logging.getLogger(__name__)


async def _env_signer_tron() -> TronClientSigner:
    from agent_wallet import EnvWalletProvider

    provider = EnvWalletProvider(network="tron")
    wallet = await provider.get_active_wallet()
    signer = TronClientSigner(wallet)
    signer.set_address(await wallet.get_address())
    return signer


async def _env_signer_evm() -> EvmClientSigner:
    from agent_wallet import EnvWalletProvider

    provider = EnvWalletProvider(network="eip155")
    wallet = await provider.get_active_wallet()
    signer = EvmClientSigner(wallet)
    signer.set_address(await wallet.get_address())
    return signer


async def resolve_tron_signer() -> TronClientSigner:
    """Resolve TRON signer via agent-wallet (encrypted store → env)."""
    try:
        return await TronClientSigner.create()
    except Exception as err:
        sys.stderr.write(
            f"[x402-cli] agent-wallet local store unavailable ({err}); "
            f"falling back to env vars (TRON_PRIVATE_KEY / AGENT_WALLET_PRIVATE_KEY).\n"
        )
        return await _env_signer_tron()


async def resolve_evm_signer() -> EvmClientSigner:
    """Resolve EVM signer via agent-wallet (encrypted store → env)."""
    try:
        return await EvmClientSigner.create()
    except Exception as err:
        sys.stderr.write(
            f"[x402-cli] agent-wallet local store unavailable ({err}); "
            f"falling back to env vars (AGENT_WALLET_PRIVATE_KEY).\n"
        )
        return await _env_signer_evm()
