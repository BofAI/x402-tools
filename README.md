# `x402-cli`

The BankofAI command-line client for the x402 protocol — pay any x402-protected URL, run your own paywall, or test the full handshake locally. **No code required.**

## 1. Install

```bash
pip install --pre bankofai-x402-cli
x402-cli --version
```

## 2. Set up a wallet (one-time)

`x402-cli` delegates all signing to [`bankofai-agent-wallet`](https://github.com/BofAI/agent-wallet). Fastest path — import a 32-byte hex private key:

```bash
agent-wallet start raw_secret \
  --wallet-id payer \
  --private-key 0x<your-32-byte-hex-private-key>
```

> A single key derives both an EVM address and a TRON address. **You don't need a separate wallet per chain.**
>
> Other setup paths (encrypted local store, mnemonic, Privy-managed): see [agent-wallet — Getting Started](https://github.com/BofAI/agent-wallet/blob/main/doc/getting-started.md).

## 3. What each command does

| Command | Who you are | What it does |
|---|---|---|
| **`x402-cli pay <url>`** | The payer | Hits a URL, and if the server returns `402 Payment Required`, the cli signs + submits the payment + retrieves the response. |
| **`x402-cli serve`** | The recipient | Starts a local `402` paywall endpoint that only returns content after a valid payment is settled. |
| **`x402-cli roundtrip`** | Self-test / one-shot transfer | Spins up a `serve` in the background, runs `pay` against it, and tears it down. **The fastest way to make a payment from the command line** — and the easiest way to verify your install end-to-end. |

## 4. Copy-paste: a GasFree transfer on TRON mainnet

Replace `<recipient-TRON-address>` with a real `T...` address and run:

```bash
x402-cli roundtrip \
  --pay-to <recipient-TRON-address> \
  --amount 1 \
  --token USDT \
  --network tron:mainnet
```

Successful output (excerpt):

```json
{
  "ok": true,
  "result": {
    "scheme": "exact_gasfree",
    "amount": "1000000",
    "paid": true,
    "transaction": "<64-hex-tx-hash>"
  }
}
```

Verify on chain at `https://tronscan.org/#/transaction/<tx-hash>`.

> **Why is this GasFree?** USDT on TRON mainnet defaults to the `exact_gasfree` scheme — a GasFree relayer pays the on-chain TRX gas for you, so **your main wallet does not need any TRX**. The USDT is debited from your derived GasFree custodial address (deterministic from your private key).
>
> **Before the first transfer**, fund that GasFree custodial address with some USDT. Step-by-step instructions: [docs/manual-test-guide.md → Walkthrough A](docs/manual-test-guide.md#4-walkthrough-a--tron-nile--exact_gasfree).

### Templates for other networks

| Network | Replace `--network` with | Notes |
|---|---|---|
| TRON mainnet (default GasFree) | `tron:mainnet` | Main wallet does not need TRX. |
| BSC mainnet (USDT permit) | `eip155:56` | Main wallet **must hold BNB for gas.** |
| TRON Nile (testnet) | `tron:nile` | [Faucet](https://nileex.io/join/getJoinPage) |
| BSC Testnet | `eip155:97` | [Faucet](https://testnet.bnbchain.org/faucet-smart) |

To force a specific settlement scheme (instead of the auto-pick), add `--scheme exact_gasfree | exact_permit | exact`.

## 5. Amount units

```
rawAmount = amount × 10^decimals
```

| What you mean | Flag to use |
|---|---|
| "1.25 USDT" (human-readable decimal) | `--amount 1.25` |
| `1250000` (smallest on-chain unit, USDT has 6 decimals) | `--rawAmount 1250000` |

Spending caps on `pay` follow the same split: `--max-amount` / `--max-rawAmount`.

## 6. Common errors

| Error | Resolution |
|---|---|
| `Insufficient GasFree balance` | The GasFree custodial address is underfunded. See [top-up steps](docs/manual-test-guide.md#42-top-up-gasfreeaddress). |
| `cannot import name 'TokenRegistry' …` | You're on `bankofai-x402-cli ≤ 0.1.0b10`. Upgrade: `pip install --pre --upgrade bankofai-x402-cli`. |
| `resolve_wallet could not find a wallet source` | No wallet configured yet. Go back to step 2. |
| Stuck on `Master Password:` prompt | A `local_secure` wallet without a persisted runtime password. Re-run with `--save-runtime-secrets`. |
| `too many pending transfers` | GasFree relayer rate limit. Wait 30–60s and retry. |

Full troubleshooting matrix: [docs/manual-test-guide.md → Troubleshooting](docs/manual-test-guide.md#7-troubleshooting).

## Learn more

- [docs/manual-test-guide.md](docs/manual-test-guide.md) — full hands-on walkthroughs from install to on-chain tx, covering TRON GasFree, TRON permit, and BSC permit.
- [FEATURES.md](FEATURES.md) — full flag matrix and example output for each command.
- [agent-wallet docs](https://github.com/BofAI/agent-wallet) — wallet setup options (Privy, mnemonic, encrypted local store).
- [bankofai-x402 SDK](https://pypi.org/project/bankofai-x402/) — the underlying protocol and its programmatic API, in case you want to integrate directly instead of through the cli.
