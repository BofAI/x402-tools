"""Wallet detection and private key handling."""

import json
import os
from typing import Any, Literal

from bankofai.x402.signers.client import EvmClientSigner, TronClientSigner
from bankofai.x402.utils.address import evm_address_to_tron


class LocalTronWallet:
    """Simple TRON wallet implementation for signing via private key."""

    def __init__(self, private_key_hex: str, address: str) -> None:
        self.private_key_hex = private_key_hex.replace("0x", "")
        self.address = address

    async def get_address(self) -> str:
        """Return wallet address."""
        return self.address

    async def sign_message(self, message: bytes) -> str:
        """Sign a raw message using ECDSA."""
        from eth_keys import keys

        priv_key_bytes = bytes.fromhex(self.private_key_hex)
        priv_key = keys.PrivateKey(priv_key_bytes)
        signature = priv_key.sign_msg(message)
        return "0x" + signature.hex()

    async def sign_typed_data(self, typed_data: dict[str, Any]) -> str:
        """Sign EIP-712/TIP-712 typed data."""
        from eth_account.messages import encode_typed_data
        from eth_account import Account

        message = encode_typed_data(
            domain_data=typed_data.get("domain"),
            message_types=typed_data.get("types"),
            message_data=typed_data.get("message"),
        )
        account = Account.from_key("0x" + self.private_key_hex)
        signed = account.sign_message(message)
        return signed.signature.hex()

    async def sign_transaction(self, txn: Any) -> str:
        """Sign a transaction."""
        from eth_keys import keys

        if hasattr(txn, "raw_data_hex"):
            raw_hex = txn.raw_data_hex
        else:
            raw_hex = txn.get("raw_data_hex")

        if not raw_hex:
            raise ValueError("No raw_data_hex in transaction")

        txn_bytes = bytes.fromhex(raw_hex.replace("0x", ""))
        priv_key_bytes = bytes.fromhex(self.private_key_hex)
        priv_key = keys.PrivateKey(priv_key_bytes)
        signature = priv_key.sign_digest(priv_key.msg_hash(txn_bytes))
        sig_json = json.dumps({"signature": ["0x" + signature.hex()]})
        return sig_json


class LocalEvmWallet:
    """Simple EVM wallet implementation for signing via private key."""

    def __init__(self, private_key_hex: str) -> None:
        from eth_account import Account

        self.private_key_hex = private_key_hex.replace("0x", "")
        self._account = Account.from_key("0x" + self.private_key_hex)
        self.address = self._account.address

    async def get_address(self) -> str:
        """Return wallet address."""
        return self.address

    async def sign_message(self, message: bytes) -> str:
        """Sign a raw message using ECDSA (EIP-191)."""
        from eth_account.messages import encode_defunct

        signable = encode_defunct(message)
        signed = self._account.sign_message(signable)
        return signed.signature.hex()

    async def sign_typed_data(self, typed_data: dict[str, Any]) -> str:
        """Sign EIP-712 typed data."""
        from eth_account.messages import encode_typed_data

        message = encode_typed_data(
            domain_data=typed_data.get("domain"),
            message_types=typed_data.get("types"),
            message_data=typed_data.get("message"),
        )
        signed = self._account.sign_message(message)
        return signed.signature.hex()

    async def sign_transaction(self, txn: dict[str, Any]) -> str:
        """Sign an EVM transaction."""
        signed = self._account.sign_transaction(txn)
        return signed.rawTransaction.hex()


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
        import eth_keys
        private_key = read_private_key("tron")
        if private_key.startswith("0x"):
            private_key = private_key[2:]
        priv_key_bytes = bytes.fromhex(private_key)
        eth_priv_key = eth_keys.keys.PrivateKey(priv_key_bytes)
        evm_address = eth_priv_key.public_key.to_checksum_address()
        tron_address = evm_address_to_tron(evm_address)
        wallet = LocalTronWallet(private_key, tron_address)
        signer = TronClientSigner(wallet)
        signer.set_address(tron_address)
        return signer

    try:
        return await TronClientSigner.create()
    except Exception as err:
        import sys

        sys.stderr.write(
            f"[x402-cli] agent-wallet TRON wallet unavailable ({err}); "
            f"falling back to TRON_PRIVATE_KEY.\n"
        )
        import eth_keys
        private_key = read_private_key("tron")
        if private_key.startswith("0x"):
            private_key = private_key[2:]
        priv_key_bytes = bytes.fromhex(private_key)
        eth_priv_key = eth_keys.keys.PrivateKey(priv_key_bytes)
        evm_address = eth_priv_key.public_key.to_checksum_address()
        tron_address = evm_address_to_tron(evm_address)
        wallet = LocalTronWallet(private_key, tron_address)
        signer = TronClientSigner(wallet)
        signer.set_address(tron_address)
        return signer


async def resolve_evm_signer(wallet_source: str = "agent-wallet") -> EvmClientSigner:
    """Resolve EVM signer (agent-wallet or env fallback)."""
    if wallet_source == "env":
        private_key = read_private_key("evm")
        wallet = LocalEvmWallet(private_key)
        signer = EvmClientSigner(wallet)
        signer.set_address(wallet.address)
        return signer

    try:
        return await EvmClientSigner.create()
    except Exception as err:
        import sys

        sys.stderr.write(
            f"[x402-cli] agent-wallet EVM wallet unavailable ({err}); "
            f"falling back to EVM_PRIVATE_KEY.\n"
        )
        private_key = read_private_key("evm")
        wallet = LocalEvmWallet(private_key)
        signer = EvmClientSigner(wallet)
        signer.set_address(wallet.address)
        return signer
