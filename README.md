# `x402-tools` (Python)

One-shot BankofAI x402 CLI built on top of the [`bankofai-x402`](https://pypi.org/project/bankofai-x402/) SDK. Two commands:

- **`server`** — start a local x402 payment server (advertises payment terms, accepts a signed payload, settles).
- **`client <url>`** — pay an x402-protected URL when the server returns `402 Payment Required`.

Full flag matrix and example output: [`FEATURES.md`](FEATURES.md).

## Install

```bash
pip install bankofai-x402-tools
x402-tools --help
```

Or from source:

```bash
cd python/x402-tools
pip install -e .
x402-tools --help
```

## Quick start

```bash
# Start a server that charges 1.25 USDT on TRON Nile
x402-tools server --pay-to TJWdoJk8KyrfxZ2iDUqz7fwpXaMkNqPehx \
  --decimal 1.25 --network tron:nile

# In another shell — pay it
x402-tools client http://127.0.0.1:4020/pay \
  --max-decimal 1.25 --network tron:nile --token USDT
```

## Design

Unlike the TypeScript version which implements its own HTTP server and facilitator client, the Python CLI directly uses the SDK's `X402Server` and `FacilitatorClient` from [`bankofai-x402`](../../python/x402/):

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

## Development

```bash
cd python/x402-tools
pip install -e .[dev]
pytest
python -m bankofai.x402_tools.cli server --help
```
