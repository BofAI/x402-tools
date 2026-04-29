# Changelog

All notable changes to `bankofai-x402-cli` are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this package adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
