# x402-cli (Python) — Features & Examples

## Commands

### `x402-cli serve`

Start a local x402 payment server.

```bash
x402-cli serve \
  --pay-to TJWdoJk8KyrfxZ2iDUqz7fwpXaMkNqPehx \
  --amount 1.25 \
  --network tron:nile \
  --token USDT \
  --scheme exact_gasfree \
  --port 4020
```

**Endpoints:**
- `GET /health` → `{ ok: true }`
- `GET /.well-known/x402` → current payment configuration
- `GET/POST /pay` → issue 402, settle on retry

### `x402-cli pay`

Pay an x402-protected URL.

```bash
x402-cli pay http://127.0.0.1:4020/pay \
  --max-amount 1.25 \
  --network tron:nile \
  --token USDT
```

### `x402-cli roundtrip`

Spin up `serve` in the background, run `pay` against it, then shut down. Useful for one-shot validation.

```bash
x402-cli roundtrip \
  --pay-to TJWdoJk8KyrfxZ2iDUqz7fwpXaMkNqPehx \
  --amount 1.25 \
  --network tron:nile \
  --token USDT
```

## Amount conventions

Two mutually exclusive forms. The relationship:

```
rawAmount = amount × 10^decimals
```

| Flag | Meaning | Example (USDT, 6 decimals) |
|---|---|---|
| `--amount <decimal>` | Human-readable | `1.25` |
| `--rawAmount <integer>` | Smallest-unit | `1250000` |

The pay-side caps follow the same convention:

| Flag | Meaning |
|---|---|
| `--max-amount <decimal>` | Human-readable cap, e.g. `1.25` |
| `--max-rawAmount <integer>` | Smallest-unit cap, e.g. `1250000` |

## Output

### Human (default)

```
✓ server (tron:nile) — exact_gasfree
  pay_url: http://127.0.0.1:4020/pay
  token: USDT
  amount: 1.25
  rawAmount: 1250000
```

### JSON (`--json`)

```json
{
  "ok": true,
  "command": "server",
  "network": "tron:nile",
  "scheme": "exact_gasfree",
  "result": {
    "pay_url": "http://127.0.0.1:4020/pay",
    "resource_url": "http://127.0.0.1:4020/pay",
    "token": "USDT",
    "amount": "1.25",
    "rawAmount": "1250000",
    "pay_to": "TJWdoJk8KyrfxZ2iDUqz7fwpXaMkNqPehx"
  }
}
```

## Schemes

Auto-selected per (network, token):

| Network | Token | Default | User fee |
|---|---|---|---|
| `eip155:97` | USDT | `exact_permit` | 0 |
| `tron:nile` | USDT | `exact_gasfree` | ~0.1 USDT |
| `tron:mainnet` | USDT | `exact_gasfree` | ~0.1 USDT |

Override with `--scheme exact_permit`.
