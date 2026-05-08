# Server Command Design

**Command**: `x402-cli serve`

**Purpose**: Start a local x402 payment server that advertises payment requirements and settles payments via signature verification.

## Architecture

```
User (CLI)
  ↓
Click Entry Point
  ↓
cmd_server()
  ↓
+-----------+-----------+-----------+
|           |           |           |
Token       Amount      Wallet      Scheme
Resolution  Parsing     Resolution  Selection
|           |           |           |
+-----------+-----------+-----------+
  ↓
X402Server Setup
  ↓
Mechanism Registration
(exact, exact_permit, exact_gasfree)
  ↓
FastAPI App + uvicorn
  ↓
Endpoints:
  GET  /health           → health check
  GET  /.well-known/x402 → config advertisement
  GET  /pay              → issue 402 challenge
  POST /pay              → verify and settle
```

## Parameters

| Flag | Required | Default | Purpose |
|------|----------|---------|---------|
| `--pay-to` | yes | — | Recipient wallet address |
| `--network` | yes | — | Network ID (e.g., `tron:nile`, `eip155:97`) |
| `--token` | no | `USDT` | Token symbol from registry |
| `--amount` \| `--rawAmount` | yes (one) | — | `--amount` = human-readable (e.g. `1.25`); `--rawAmount` = smallest unit (e.g. `1250000`). `rawAmount = amount × 10^decimals`. |
| `--scheme` | no | auto-selected | Payment scheme (exact, exact_permit, exact_gasfree) |
| `--asset` | no | from registry | Explicit token address (out of registry) |
| `--decimals` | no | — | Token decimals (required with `--asset`) |
| `--host` | no | `127.0.0.1` | Bind host |
| `--port` | no | `4020` | Bind port |
| `--resource-url` | no | `/pay` | Resource URL in config |
| `--daemon` | no | false | Reserved flag — currently a no-op (the server still runs in the foreground). Real daemonization is planned for a later release. |
| `--json` | no | false | JSON output |

## Endpoints

### GET /health

**Purpose**: Liveness probe — used by `roundtrip`'s `_wait_for_server_ready` and by external monitoring.

**Response**: HTTP 200

```json
{ "ok": true }
```

That's the entire body. Server configuration (pay_to, amount, asset, etc.) lives at `/.well-known/x402`, not here — `/health` is intentionally tiny so it can return before any chain / facilitator handshakes.

### GET /.well-known/x402

**Purpose**: Advertise payment configuration

**Response**:
```json
{
  "network": "eip155:97",
  "scheme": "exact_permit",
  "token": "USDT",
  "asset": "0x337610d27c682E347C9cD60BD4b3b107C9d34dDd",
  "amount": "0.0001",
  "rawAmount": "100000000000000",
  "pay_to": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
  "pay_url": "http://127.0.0.1:4020/pay",
  "resource_url": "http://127.0.0.1:4020/pay"
}
```

### GET /pay

**Purpose**: Issue 402 challenge (no signature in request)

**Response**: HTTP 402 Payment Required

**Headers**:
```
PAYMENT-REQUIRED: [Base64-encoded PaymentRequired]
```

**Body**:
```json
{
  "x402Version": 2,
  "error": "Payment required",
  "resource": { "url": "http://127.0.0.1:4020/pay" },
  "accepts": [
    {
      "scheme": "exact_permit",
      "network": "eip155:97",
      "amount": "100000000000000",
      "asset": "0x337610d27c682E347C9cD60BD4b3b107C9d34dDd",
      "payTo": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
      "maxTimeoutSeconds": 3600,
      "extra": { ... }
    }
  ],
  "extensions": { "paymentPermitContext": { ... } }
}
```

### POST /pay

**Purpose**: Verify signature and settle payment

**Headers**:
```
PAYMENT-SIGNATURE: [Base64-encoded PaymentPayload]
```

**Response** (success): HTTP 200

**Body**:
```json
{
  "success": true,
  "transaction": "0x...",
  "network": "eip155:97",
  "scheme": "exact_permit"
}
```

**Response** (failure): HTTP 500

**Body**:
```json
{
  "error": "Settlement failed: ...",
  "txHash": "0x..."
}
```

## Flow Sequence

1. **GET /pay** (no PAYMENT-SIGNATURE)
   - Return 402 with challenge (PaymentRequired)

2. **POST /pay** (with PAYMENT-SIGNATURE)
   - Decode signature header → PaymentPayload
   - Build ResourceConfig from CLI args
   - Call `X402Server.build_payment_requirements()`
   - Call `X402Server.settle_payment(payload, requirements)`
   - Return settlement result or error

## Compat shim — `_tron_patch.py`

CLI installs a runtime monkey-patch on `TronClientSigner._build_unsigned_tx_payload` at startup. The SDK ships TRON unsigned-tx payloads with `raw_data_hex=None` because no released `tronpy` (0.4–0.6) exposes that field on the `Transaction` object. The local `raw_secret` / `local_secure` adapters tolerate it (they sign `txID` directly), but the `privy` adapter strictly requires non-empty `raw_data_hex` and refuses the payload.

The patch fills the field by calling tronpy's own protobuf helper (`tronpy.proto._raw_data_to_protobuf` + `tron_pb2.Transaction(raw_data=...).SerializeToString()`) — the same code path tronpy uses for offline txid calculation. SHA-256 of the result equals `txn.txid`, so the bytes are byte-for-byte correct.

The shim is idempotent and forward-compatible: when the SDK starts emitting `raw_data_hex` natively, the patched function short-circuits because `payload.get("raw_data_hex")` is already truthy. At that point the file can be deleted along with the `protobuf` direct dependency.

## Mechanism Registration

Based on scheme + network:

| Scheme | Network | Mechanism | SDK Module |
|--------|---------|-----------|-----------|
| `exact` | `eip155:*` | ExactEvmServerMechanism | `bankofai.x402.mechanisms.evm.exact` |
| `exact_permit` | `eip155:*` | ExactPermitEvmServerMechanism | `bankofai.x402.mechanisms.evm.exact_permit` |
| `exact_permit` | `tron:*` | ExactPermitTronServerMechanism | `bankofai.x402.mechanisms.tron.exact_permit` |
| `exact_gasfree` | `tron:*` | ExactGasFreeServerMechanism | `bankofai.x402.mechanisms.tron.exact_gasfree.server` |

## Error Handling

| Scenario | HTTP Status | Error Code | Message |
|----------|-------------|-----------|---------|
| Invalid pay-to | 400 | VALIDATION_ERROR | "--pay-to is required" |
| Token not found | 400 | VALIDATION_ERROR | "Token '...' not found in registry" |
| Invalid amount | 400 | VALIDATION_ERROR | "--rawAmount and --amount are mutually exclusive" |
| Invalid scheme | 400 | VALIDATION_ERROR | "Unknown scheme '...'" |
| Mechanism registration | 500 | IO_ERROR | "Scheme '...' not supported for network ..." |
| Settlement failure | 500 | SETTLEMENT_ERROR | "Settlement failed: ..." |

## Example Usage

```bash
# Start server on TRON Nile with 1.25 USDT, exact_gasfree
x402-cli serve \
  --pay-to TJWdoJk8KyrfxZ2iDUqz7fwpXaMkNqPehx \
  --amount 1.25 \
  --network tron:nile \
  --token USDT \
  --scheme exact_gasfree \
  --port 4020

# Output (human-readable)
✓ server (tron:nile) — exact_gasfree
  pay_url: http://127.0.0.1:4020/pay
  token: USDT
  amount: 1.25
  rawAmount: 1250000
```
