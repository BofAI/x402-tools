# `x402-cli` (Python)

One-shot BankofAI x402 CLI built on top of the [`bankofai-x402`](https://pypi.org/project/bankofai-x402/) SDK. Three commands:

- **`serve`** — start a local x402 payment server (advertises payment terms, accepts a signed payload, settles).
- **`pay <url>`** — pay an x402-protected URL when the server returns `402 Payment Required`.
- **`roundtrip`** — one-shot test: spin up `serve` in the background, run `pay` against it, shut down.

Full flag matrix and example output: [`FEATURES.md`](FEATURES.md).

## Install

```bash
pip install bankofai-x402-cli
x402-cli --help
```

Or from source:

```bash
cd x402-cli
pip install -e .
x402-cli --help
```

## Amount conventions

Two mutually exclusive forms are accepted everywhere a price is taken:

```
rawAmount = amount × 10^decimals
```

| Flag | Meaning | Example (USDT, 6 decimals) |
|---|---|---|
| `--amount <decimal>` | Human-readable | `1.25` |
| `--rawAmount <integer>` | Smallest on-chain unit | `1250000` |

Pay-side caps mirror the same split: `--max-amount` (human-readable) / `--max-rawAmount` (smallest unit).

## Quick start

```bash
# Start a server that charges 1.25 USDT on TRON Nile
x402-cli serve --pay-to TJWdoJk8KyrfxZ2iDUqz7fwpXaMkNqPehx \
  --amount 1.25 --network tron:nile

# In another shell — pay it (cap human-readable)
x402-cli pay http://127.0.0.1:4020/pay \
  --max-amount 1.25 --network tron:nile --token USDT

# Or one-shot end-to-end on a single line
x402-cli roundtrip --pay-to TJWdoJk8KyrfxZ2iDUqz7fwpXaMkNqPehx \
  --amount 1.25 --network tron:nile --token USDT
```

## Design

Unlike the TypeScript version which implements its own HTTP server and facilitator client, the Python CLI directly uses the SDK's `X402Server` and `FacilitatorClient` from [`bankofai-x402`](https://pypi.org/project/bankofai-x402/):

```python
from bankofai.x402.server import X402Server
from bankofai.x402.facilitator import FacilitatorClient

server = X402Server()  # No duplication
facilitator = FacilitatorClient(base_url)  # SDK provided
```

This avoids code duplication and keeps the CLI thin (just argument parsing + output formatting).

## Environment variables

| Var | Purpose |
|---|---|
| `TRON_PRIVATE_KEY` | TRON wallet key for `--wallet env` |
| `EVM_PRIVATE_KEY` | EVM wallet key for `--wallet env` |
| `TRON_GRID_API_KEY` | Optional, forwarded to SDK for TronGrid |
| `FACILITATOR_URL` | Override facilitator endpoint (default `https://facilitator.bankofai.io`) |

## Development

```bash
cd x402-cli
pip install -e .[dev]
pytest
x402-cli --help
```
