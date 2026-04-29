# x402-cli

This is a one-shot CLI for the x402 payment protocol, built on the [`bankofai-x402`](https://pypi.org/project/bankofai-x402/) SDK.

## What this is

x402-cli provides three commands:
- **`serve`** — Start a long-running x402 payment server (advertise terms, accept signatures, settle)
- **`pay <url>`** — Pay an x402-protected URL when it returns 402 Payment Required
- **`roundtrip [serve-args]`** — One-shot test: start daemon server, pay it, shut down

The CLI directly uses the SDK's `X402Server` and `FacilitatorClient` — no reimplementation of payment logic.

## Structure

```
.
├── src/bankofai/x402_tools/     # Implementation
│   ├── cli.py                   # Click CLI entry point
│   ├── server_cmd.py            # Server command (402 challenge + settlement)
│   ├── client_cmd.py            # Client command (probe + sign + retry)
│   ├── wallet.py                # Private key resolution
│   ├── schemes.py               # Scheme auto-selection
│   └── output.py                # Output formatting
├── specs/                       # Protocol specifications & design docs
│   ├── server.md                # Server command design
│   ├── client.md                # Client command design
│   └── smoke-tests.md           # Smoke test specification
├── FEATURES.md                  # Feature matrix & examples
├── README.md                    # Getting started
└── CHANGELOG.md                 # Release notes
```

## Key reading order

1. [specs/server.md](specs/server.md) — Payment server design (402 flow, endpoints)
2. [specs/client.md](specs/client.md) — Payment client design (probe → sign → retry)
3. [specs/smoke-tests.md](specs/smoke-tests.md) — Verification & testing approach
4. [rules/python.md](rules/python.md) — Python coding conventions
5. [README.md](README.md) — User-facing documentation

## Conventions

- **CLI design**: Click-based, single binary (`x402-cli`)
- **Commands**: `serve` (foreground/daemon), `pay` (client), `roundtrip` (test utility)
- **Server modes**: Foreground (default, Ctrl+C to stop) or daemon (--daemon flag)
- **Amounts**: `rawAmount = amount × 10^decimals`. Two forms accepted (mutually exclusive): `--amount` human-readable (e.g. `1.25`), `--rawAmount` smallest-unit integer (e.g. `1250000`). Pay-side caps: `--max-amount` / `--max-rawAmount` follow the same split.
- **Wallets**: delegated entirely to `bankofai-agent-wallet` (`TronClientSigner.create()` / `EvmClientSigner.create()`). agent-wallet itself resolves order: encrypted store → env (`AGENT_WALLET_PRIVATE_KEY` / `TRON_PRIVATE_KEY` / mnemonic). No `--wallet` flag and no in-tree env fallback.
- **Output**: JSON envelope by default, human-readable with flag
- **Error codes**: Standardized per command (IO_ERROR, VALIDATION_ERROR, etc.)
- **Async**: Full async/await support via asyncio

## Build & Test

```bash
pip install -e .
x402-cli --help

# Run smoke tests
bash .claude/smoke-test.sh
```

## Safety rules

- **Never** amend commits on `origin/main` — create a branch for fixes
- **Never** commit private keys or wallet seeds — use environment variables
- **Always** test wallet resolution (agent-wallet → env fallback)
- **Always** validate amounts (precision, bounds)
- **Always** test 402 challenge/response flow end-to-end
