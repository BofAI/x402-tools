# Changelog

All notable changes to `bankofai-x402-cli` are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this package adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0-beta.10] — 2026-04-29

### Fixed

- **`pay --token <symbol>` was a dead flag**. The CLI parsed it and threaded it through to `cmd_client`, but the filter dict passed to `select_payment_requirements` only contained `network` and `scheme`, so `--token foo` was silently ignored. The SDK's selector also doesn't take a `token` filter, so the CLI now filters candidates itself by symbol (case-insensitive) via `TokenRegistry.find_by_address` *before* delegating to the SDK. `--token foo` now errors out with `No payment options match --token foo among N offered`.

### Changed (breaking)

- **Removed `--wallet` flag**. All signing now goes through `bankofai-agent-wallet` unconditionally. agent-wallet itself picks between its encrypted local store (`~/.agent-wallet/`) and env vars (`AGENT_WALLET_PRIVATE_KEY` / `TRON_PRIVATE_KEY` / `AGENT_WALLET_MNEMONIC` / `TRON_MNEMONIC`), so no in-tree fallback is needed.
- Removed `LocalTronWallet` / `LocalEvmWallet` / `read_private_key` from `wallet.py`. The module is now ~10 lines that just call `TronClientSigner.create()` / `EvmClientSigner.create()`.

### Added

- **README "Wallet — agent-wallet" section** explaining the two setup paths (`agent-wallet start` for the encrypted store, or one env var for ad-hoc use).
- `bankofai-agent-wallet>=2.4` declared as a direct dependency (was previously only transitive via `bankofai-x402`).

### Removed

- Direct deps `eth-account` and `eth-keys` (still pulled in transitively by the SDK; the CLI itself no longer imports them).

### Migration

| beta.9 invocation | beta.10 equivalent |
|---|---|
| `x402-cli serve --wallet env ...` | `x402-cli serve ...` (set `TRON_PRIVATE_KEY` first, or run `agent-wallet start`) |
| `x402-cli pay --wallet agent-wallet ...` | `x402-cli pay ...` |

## [0.1.0-beta.9] — 2026-04-29

### Changed (breaking)

- **Swap `--amount` / `--rawAmount` semantics to match the math** `rawAmount = amount × 10^decimals`. Previous betas had this backwards.
  - `--amount` is now the **human-readable** decimal (e.g. `1.25`).
  - `--rawAmount` is now the **smallest-unit integer** (e.g. `1250000` for 1.25 USDT).
  - Same swap for `--max-amount` (human-readable cap) / `--max-rawAmount` (smallest-unit cap).
  - JSON output fields `amount` and `rawAmount` follow the new convention.
- `--max-rawAmount` is now actually wired up (was previously documented but unimplemented).

### Migration from beta.8 and earlier

| Old (wrong) | New (correct) |
|---|---|
| `--rawAmount 1.25` | `--amount 1.25` |
| `--amount 1250000` | `--rawAmount 1250000` |
| `--max-rawAmount 1.25` | `--max-amount 1.25` |
| `--max-amount 1250000` | `--max-rawAmount 1250000` |

## [0.1.0-beta.8] — 2026-04-29

### Fixed

- **Add `web3` and `tronpy` to runtime dependencies**: EVM `exact_permit` allowance checks call `web3` (via the SDK's `EvmClientSigner.ensure_allowance`); TRON balance reads call `tronpy`. Without them, fresh installs fail at first chain access.

## [0.1.0-beta.7] — 2026-04-29

### Fixed

- **Pin httpx < 1.0.0**: PyPI was resolving `httpx 1.0.dev3` (a pre-release with breaking API changes — `httpx.AsyncClient` was removed). Cap to the stable 0.x series.
- **Pin `eth-account` and `eth-keys`** to known-good majors so `eth-account 0.14b1` (currently on PyPI) is not picked up.

## [0.1.0-beta.6] — 2026-04-29

### Fixed

- **Missing runtime dependencies**: add `fastapi`, `uvicorn`, `eth-account`, `eth-keys` to `pyproject.toml`. beta.5 imports these but did not declare them, breaking fresh installs.
- **Documentation**: replace residual `x402-tools` references in `README.md`, `FEATURES.md`, `specs/README.md` with `x402-cli`. Replace deprecated `--max-decimal` with `--max-rawAmount`.

## [0.1.0-beta.5] — 2026-04-29

### Fixed

- **TRON `exact_gasfree`**: properly initialize `ExactGasFreeClientMechanism` with required `clients` argument (`GasFreeAPIClient` instances per network).
- **TRON address format**: convert EVM hex (derived from private key) to TRON Base58 before passing to GasFree API, which rejects 0x-prefixed addresses.
- **EIP-712 / TIP-712 signing**: introduce `LocalTronWallet` and `LocalEvmWallet` classes implementing `sign_typed_data(typed_data)` so that env-based wallets can sign payment permits.
- **`paymentPermitContext`**: forward `extensions` from the 402 response to `create_payment_payload`, fixing `PermitValidationError("missing_context")` for `exact_permit` schemes.
- **HTTP timeout**: bump client timeout from 10s to 60s to accommodate facilitator settlement latency on TRON Nile and BSC.
- **Error logging**: include traceback and `repr(err)` fallback when the exception message is empty.

### Verified on-chain

- **TRON Nile** (`exact_gasfree`): roundtrip + serve/pay both succeed end-to-end via `https://facilitator.bankofai.io/nile`.
- **BSC Testnet** (`exact_permit`): roundtrip succeeds end-to-end via the main facilitator.

## [0.1.0-beta.3] — 2026-04-29

### Added

First public beta of the Python x402-cli CLI.

- **Binary**: `x402-cli`, published as `bankofai-x402-cli`.
- **`x402-cli serve`** — starts a local x402 payment server using the SDK's `X402Server`.
  - Endpoints: `GET /health`, `GET /.well-known/x402`, `GET | POST /pay`.
  - Supports `--rawAmount | --amount`, `--network`, `--token`, `--scheme`, `--host`, `--port`.
  - Human output and `--json` envelope report payment terms.
- **`x402-cli pay <url>`** — pays an x402-protected URL.
  - Probes once; if not 402, prints summary and exits.
  - On 402, parses requirements, filters against `--max-rawAmount | --max-amount | --network | --token | --scheme`.
  - Signs and retries with payment payload.
- **Wallet selector** (D1) — `--wallet agent-wallet` (default) or `--wallet env`.
- **Auto-scheme picker** — maps (network, token) to recommended scheme.
- **Wrapped JSON envelope** (D2) — every command emits `{ ok, command, network?, scheme?, result | error }`.
- **15 standardized error codes**.

### Design note

Unlike the TypeScript CLI which implements its own HTTP server and facilitator client, the Python CLI directly uses:

- `bankofai.x402.server.X402Server` — no duplication of challenge-response logic
- `bankofai.x402.facilitator.FacilitatorClient` — no duplication of `/verify` / `/settle` calls

This keeps the Python tools thin and avoids the code divergence seen in the TS version.
