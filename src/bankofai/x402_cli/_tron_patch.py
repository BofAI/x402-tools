"""Compatibility patch: fill in `raw_data_hex` for TRON unsigned tx payloads.

## Why this exists

`bankofai-x402` ≤ 0.5.9 builds the unsigned-tx dict by trying three sources
in order:

    payload = txn.to_json() if hasattr(txn, "to_json") else {}
    raw_data_hex = payload.get("raw_data_hex")               # not in tronpy 0.4–0.6
    raw_data_hex = raw_data_hex or getattr(txn, "raw_data_hex", None)  # no such attr
    raw_data_hex = raw_data_hex or txn._raw_data_hex()       # legacy method, removed

All three are missing on **every** released `tronpy` (0.4 through 0.6.2 verified),
so the SDK ships `raw_data_hex=None` to the wallet.

* `agent_wallet` raw_secret / local_secure adapters tolerate this — they sign
  `txID` directly when present.
* `agent_wallet` privy adapter does **not** tolerate it — Privy's hosted signer
  requires the full `raw_data_hex` for compliance review and rejects the payload
  with `SigningError("Payload must include raw_data_hex for TRON signing")`.

That's why every internal test passed (we used raw_secret) but QA hit a wall the
moment they ran a fresh `privy` wallet — first-time `exact_permit` triggers
`ensure_allowance` → builds an approval txn → privy refuses the None payload.

## What this patch does

`tronpy` itself can serialize `Transaction.raw_data` via its own protobuf helper
(`tronpy.proto._raw_data_to_protobuf` + `tron_pb2.Transaction(raw_data=...).
SerializeToString()`). It's the same code path tronpy uses to compute `txid`
in offline mode.

We wrap `TronClientSigner._build_unsigned_tx_payload` to call back into the
SDK first, and if `raw_data_hex` is still missing, fill it in by serializing
`txn._raw_data` ourselves. SHA-256 of the result equals tronpy's own `txid`,
so the bytes are byte-for-byte correct.

Idempotent: calling `install()` twice is a no-op.

## Future

When the SDK's own `_build_unsigned_tx_payload` learns to do this, this module
becomes a no-op (the patched function will short-circuit because
`raw_data_hex` is already non-empty), and we can delete the file.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def _serialize_raw_data(raw_data: dict) -> str | None:
    """Serialize a tronpy raw_data dict to hex via tronpy's own protobuf helper.

    Returns None on any failure — the caller falls back to the SDK's payload
    as-is, which still works for raw_secret / local_secure wallets.
    """
    try:
        from tronpy.proto.transaction import _raw_data_to_protobuf
        from tronpy.proto import tron_pb2

        transaction_raw = _raw_data_to_protobuf(raw_data)
        transaction = tron_pb2.Transaction(raw_data=transaction_raw)
        return transaction.raw_data.SerializeToString().hex()
    except Exception as e:  # noqa: BLE001 — best-effort fallback
        logger.debug("Could not serialize raw_data via tronpy.proto: %s", e)
        return None


def install() -> None:
    """Install the patch on `TronClientSigner`. Idempotent and safe to call early."""
    try:
        from bankofai.x402.signers.client.tron_signer import TronClientSigner
    except ImportError:
        # SDK not installed (shouldn't happen — it's a hard dep), nothing to patch.
        return

    if getattr(TronClientSigner, "_x402_cli_raw_data_hex_patched", False):
        return

    original = TronClientSigner._build_unsigned_tx_payload

    @staticmethod  # type: ignore[misc]
    def patched(txn):  # type: ignore[no-untyped-def]
        payload = original(txn)
        if not payload.get("raw_data_hex"):
            raw_data = getattr(txn, "_raw_data", None)
            if isinstance(raw_data, dict):
                rdh = _serialize_raw_data(raw_data)
                if rdh:
                    payload["raw_data_hex"] = rdh
                    logger.debug(
                        "Filled missing raw_data_hex via tronpy.proto serialization"
                    )
                else:
                    logger.debug(
                        "raw_data_hex still missing after serialization attempt; "
                        "downstream wallet may reject (e.g. privy adapter)"
                    )
        return payload

    TronClientSigner._build_unsigned_tx_payload = patched
    TronClientSigner._x402_cli_raw_data_hex_patched = True  # type: ignore[attr-defined]
