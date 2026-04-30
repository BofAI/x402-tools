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

## Wallet

Signing is delegated to [`bankofai-agent-wallet`](https://github.com/BofAI/agent-wallet) (transitive dep). It picks up either an encrypted local wallet (managed by the `agent-wallet` CLI) or a private-key / mnemonic env var. One key derives both EVM and TRON addresses — there is **no `--wallet` flag**, just install once and `x402-cli` picks the wallet up automatically.

Setup steps and full env var list: [agent-wallet — Getting Started](https://github.com/BofAI/agent-wallet/blob/main/doc/getting-started.md).

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

## Schemes

Auto-selected per `(network, token)` from a small registry; override with `--scheme <name>`.

| Network | Token | Default | Why |
|---|---|---|---|
| `eip155:56` / `eip155:97` (BSC) | USDT, USDC | `exact_permit` | EIP-2612 |
| `eip155:97` (BSC Testnet) | DHLU | `exact` | ERC-3009 |
| `tron:mainnet` / `tron:nile` / `tron:shasta` | USDT, USDD | `exact_gasfree` | Hosted `exact_permit` settlement can verify the signature but still revert during on-chain `permitTransferFrom`; GasFree relays through a custodial address. Override with `--scheme exact_permit` if you've hardened the path. |

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
