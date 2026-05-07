"""Regression tests for the TRON raw_data_hex compat patch.

Pure offline tests — no network calls, no real tronpy txn build. We construct a
fake `txn` object that mimics the shape of what tronpy 0.4–0.6 hand back from
`build()`: a `_raw_data` dict, no `raw_data_hex` attr, no `_raw_data_hex()`
method, and a `to_json()` that returns dict without `raw_data_hex`.
"""

from __future__ import annotations

import hashlib
from typing import Any

from bankofai.x402_cli import _tron_patch


class _FakeTxn:
    """Mimics tronpy 0.6.x AsyncTransaction for the fields SDK reads."""

    def __init__(self, raw_data: dict[str, Any], txid: str) -> None:
        self._raw_data = raw_data
        self._txid = txid

    def to_json(self) -> dict[str, Any]:
        # tronpy 0.4–0.6 do NOT include raw_data_hex here
        return {
            "txID": self._txid,
            "raw_data": self._raw_data,
            "signature": [],
        }


# A minimal but realistic raw_data dict — 1 TRX TransferContract is the simplest
# Transaction shape tronpy.proto knows how to serialize, so we use that.
_REAL_RAW_DATA = {
    "ref_block_bytes": "1234",
    "ref_block_hash": "5678abcd5678abcd",
    "expiration": 1700000000000,
    "timestamp": 1699999999000,
    "fee_limit": 100_000_000,
    "contract": [
        {
            "type": "TransferContract",
            "parameter": {
                "value": {
                    "owner_address": "TTX1Us19zqsLXhY39PPR7KRUoMa93s3J3i",
                    "to_address": "TJWdoJk8KyrfxZ2iDUqz7fwpXaMkNqPehx",
                    "amount": 1_000_000,
                },
                "type_url": "type.googleapis.com/protocol.TransferContract",
            },
        }
    ],
}


def test_serialize_raw_data_returns_valid_hex() -> None:
    """Serializer should produce hex matching tronpy's own txid calculation."""
    rdh = _tron_patch._serialize_raw_data(_REAL_RAW_DATA)
    assert rdh is not None, "serialization must succeed when protobuf is available"
    assert isinstance(rdh, str) and len(rdh) > 0
    # All hex chars
    int(rdh, 16)


def test_serialize_raw_data_matches_tronpy_txid() -> None:
    """sha256(raw_data_hex) must equal what tronpy itself computes as txid."""
    rdh = _tron_patch._serialize_raw_data(_REAL_RAW_DATA)
    assert rdh is not None
    our_txid = hashlib.sha256(bytes.fromhex(rdh)).hexdigest()

    from tronpy.proto.transaction import calculate_txid_from_raw_data

    tronpy_txid = calculate_txid_from_raw_data(_REAL_RAW_DATA)
    assert our_txid == tronpy_txid, (
        "Our serialization diverged from tronpy's own — "
        "the patch would produce a wrong raw_data_hex"
    )


def test_serialize_raw_data_returns_none_on_garbage() -> None:
    """Missing/malformed dict shouldn't crash — return None and let SDK fall back."""
    assert _tron_patch._serialize_raw_data({}) is None
    assert _tron_patch._serialize_raw_data({"contract": []}) is None
    assert _tron_patch._serialize_raw_data({"not_a_real_field": 42}) is None


def test_install_is_idempotent() -> None:
    """Calling install() twice must not double-patch."""
    from bankofai.x402.signers.client.tron_signer import TronClientSigner

    _tron_patch.install()
    after_first = TronClientSigner._build_unsigned_tx_payload
    _tron_patch.install()
    after_second = TronClientSigner._build_unsigned_tx_payload
    assert after_first is after_second


def test_patched_build_fills_raw_data_hex() -> None:
    """End-to-end: SDK's _build_unsigned_tx_payload, after patch, must populate
    raw_data_hex from a tronpy-shaped txn that has only _raw_data + to_json()."""
    _tron_patch.install()
    from bankofai.x402.signers.client.tron_signer import TronClientSigner

    fake_txid = "01" * 32  # arbitrary
    fake = _FakeTxn(_REAL_RAW_DATA, fake_txid)

    payload = TronClientSigner._build_unsigned_tx_payload(fake)

    # SDK should still set txID
    assert payload.get("txID") == fake_txid
    # And our patch should have filled raw_data_hex
    rdh = payload.get("raw_data_hex")
    assert isinstance(rdh, str) and len(rdh) > 0, (
        f"patched _build_unsigned_tx_payload must produce non-empty raw_data_hex, "
        f"got: {rdh!r}"
    )
    # And it must round-trip to the canonical txid (so wallets get bit-correct bytes)
    from tronpy.proto.transaction import calculate_txid_from_raw_data

    assert hashlib.sha256(bytes.fromhex(rdh)).hexdigest() == calculate_txid_from_raw_data(
        _REAL_RAW_DATA
    )


def test_patched_build_passthrough_when_raw_data_hex_already_present() -> None:
    """If a future SDK version emits raw_data_hex itself, the patch must NOT
    overwrite it — graceful forward compat."""
    _tron_patch.install()
    from bankofai.x402.signers.client.tron_signer import TronClientSigner

    class _FutureTxn:
        # Simulates a future tronpy that exposes raw_data_hex directly
        raw_data_hex = "deadbeef"

        def to_json(self) -> dict[str, Any]:
            return {"txID": "ab" * 32, "raw_data_hex": "deadbeef"}

    payload = TronClientSigner._build_unsigned_tx_payload(_FutureTxn())
    assert payload.get("raw_data_hex") == "deadbeef", (
        "Patch should not overwrite an already-populated raw_data_hex"
    )
