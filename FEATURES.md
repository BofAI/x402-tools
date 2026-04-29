# x402-tools (Python) — Features & Examples

## Commands

### `x402-tools server`

Start a local x402 payment server.

```bash
x402-tools server \
  --pay-to TJWdoJk8KyrfxZ2iDUqz7fwpXaMkNqPehx \
  --decimal 1.25 \
  --network tron:nile \
  --token USDT \
  --scheme exact_gasfree \
  --port 4020
```

**Endpoints:**
- `GET /health` → `{ ok: true }`
- `GET /.well-known/x402` → current payment configuration
- `GET/POST /pay` → issue 402, settle on retry

### `x402-tools client`

Pay an x402-protected URL.

```bash
x402-tools client http://127.0.0.1:4020/pay \
  --max-decimal 1.25 \
  --network tron:nile \
  --token USDT
```

## Amount conventions

Both commands accept either form, never both:

| Flag | Meaning | Example |
|---|---|---|
| `--decimal <decimal>` | Human-readable | `1.25` |
| `--amount <integer>` | Smallest-unit | `1250000` for 1.25 USDT |

## Output

### Human (default)

```
✓ server (tron:nile) — exact_gasfree
  pay_url: http://127.0.0.1:4020/pay
  token: USDT
  decimal: 1.25
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
    "token": "USDT",
    "decimal": "1.25",
    "amount": "1250000"
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
