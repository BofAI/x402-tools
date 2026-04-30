# `x402-cli` (Python)

One-shot BankofAI x402 CLI built on top of the [`bankofai-x402`](https://pypi.org/project/bankofai-x402/) SDK. Three commands:

- **`serve`** — start a local x402 payment server (advertises payment terms, accepts a signed payload, settles).
- **`pay <url>`** — pay an x402-protected URL when the server returns `402 Payment Required`.
- **`roundtrip`** — one-shot test: spin up `serve` in the background, run `pay` against it, shut down.

Full flag matrix and example output: [`FEATURES.md`](FEATURES.md).
Hands-on walkthrough (TRON GasFree + TRON/BSC permit, copy-paste commands): [`docs/manual-test-guide.md`](docs/manual-test-guide.md).

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

## Wallet — agent-wallet

x402-cli signs every payment through [`bankofai-agent-wallet`](https://pypi.org/project/bankofai-agent-wallet/) (installed as a transitive dependency). agent-wallet provides one signing surface that resolves wallets in this priority order:

1. **Encrypted local store** — wallets you've added via `agent-wallet add`, kept under `~/.agent-wallet/` and unlocked with a master password.
2. **Environment variables** — fallback if no local store is configured. The most common variables (already understood by `agent-wallet`):
   - `AGENT_WALLET_PRIVATE_KEY` or `TRON_PRIVATE_KEY` — 0x-prefixed private key
   - `AGENT_WALLET_MNEMONIC` or `TRON_MNEMONIC` — BIP-39 mnemonic
   - `AGENT_WALLET_MNEMONIC_ACCOUNT_INDEX` (optional, mnemonic only)

A single private key derives both an EVM address and a TRON address — you don't need separate keys per chain.

### One-time setup

Either initialize the encrypted local store:

```bash
agent-wallet start         # creates master password + a default wallet
agent-wallet list          # see configured wallets
agent-wallet use <name>    # set active wallet
```

…or just export an environment variable in the shell where `x402-cli` runs:

```bash
export TRON_PRIVATE_KEY=0x<your-hex-private-key>
```

That's it — `x402-cli serve` and `x402-cli pay` both pick up the wallet automatically. There is no `--wallet` flag.

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

### Default scheme

For TRON USDT the default scheme is `exact_gasfree` rather than `exact_permit`: hosted/self-hosted `exact_permit` settlement can verify the user's signature but still fail during the on-chain `permitTransferFrom` broadcast (TRC-2612 nuances). GasFree side-steps that by relaying through a custodial address. Override with `--scheme exact_permit` if you've hardened your `permit` flow.

## Environment variables

| Var | Purpose |
|---|---|
| `AGENT_WALLET_PRIVATE_KEY` / `TRON_PRIVATE_KEY` | Wallet private key, picked up by agent-wallet's env provider |
| `AGENT_WALLET_MNEMONIC` / `TRON_MNEMONIC` | Alternative: BIP-39 mnemonic (with optional `_ACCOUNT_INDEX`) |
| `TRON_GRID_API_KEY` | Optional, forwarded to SDK for TronGrid |
| `FACILITATOR_URL` | Override facilitator endpoint (default `https://facilitator.bankofai.io`) |

## Development

```bash
cd x402-cli
pip install -e .[dev]
pytest
x402-cli --help
```
