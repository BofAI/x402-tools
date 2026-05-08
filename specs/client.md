# Client Command Design

**Command**: `x402-cli pay <url>`

**Purpose**: Pay an x402-protected URL by probing for 402, parsing requirements, signing, and retrying.

## Architecture

```
User (CLI)
  ↓
Click Entry Point
  ↓
cmd_client()
  ↓
HTTP GET <url>
  ├─ Not 402 → Print summary & exit
  └─ 402 → Continue
      ↓
Parse PAYMENT-REQUIRED Header
  ↓
Extract PaymentRequired
  ↓
Register X402Client Mechanisms
(based on available schemes/networks)
  ↓
Signer Resolution
(agent-wallet or env var)
  ↓
Select Payment Requirements
(apply filters: network, token, scheme)
  ↓
Create Payment Payload
(X402Client.create_payment_payload)
  ↓
Encode PAYMENT-SIGNATURE Header
  ↓
HTTP POST <url> (with signature)
  ↓
Parse Response
  ↓
Output result
```

## Parameters

| Argument | Required | Purpose |
|----------|----------|---------|
| `url` | yes | Target URL |

| Flag | Default | Purpose |
|------|---------|---------|
| `--max-amount` | — | Max human-readable amount allowed (e.g. `1.25`) |
| `--max-rawAmount` | — | Max smallest-unit amount allowed (e.g. `1250000`) |
| `--network` | — | Filter by network (if multiple available) |
| `--token` | — | Filter by token symbol |
| `--scheme` | — | Filter by scheme |
| `--method` | `GET` | HTTP method for request |
| `--header` | — | Custom HTTP headers (repeatable: `Key: Value`) |
| `--body` | — | Request body |
| `--dry-run` | false | Parse requirements but do not sign or pay |
| `--json` | false | JSON output |

## Flow Sequence

### 1. Probe Request

```
GET <url>
  ↓
Response Status?
  ├─ Not 402 → Output result and exit
  └─ 402 → Continue
```

### 2. Parse Challenge

```
HTTP 402 Response
  ↓
Extract PAYMENT-REQUIRED Header
  ↓
Decode Base64
  ↓
Parse PaymentRequired JSON
  ↓
Extract .accepts[] (PaymentRequirements list)
```

### 3. Register Mechanisms

Based on `accepts[]`:

```python
# Pre-build GasFree API clients for each TRON network in accepts[].
# ExactGasFreeClientMechanism requires a `clients={network: GasFreeAPIClient(...)}`
# kwarg, not just the signer.
gasfree_clients = {
    network: GasFreeAPIClient(_get_gasfree_base_url(network))
    for network in tron_networks_with_gasfree
}

for requirement in accepts:
    scheme = requirement.scheme
    network = requirement.network

    if scheme == "exact":
        client.register(network, ExactEvmClientMechanism(signer))
    elif scheme == "exact_permit":
        if network.startswith("eip155:"):
            client.register(network, ExactPermitEvmClientMechanism(signer))
        elif network.startswith("tron:"):
            client.register(network, ExactPermitTronClientMechanism(signer))
    elif scheme == "exact_gasfree":
        # NOTE the `clients=` kwarg — required since SDK 0.5.x.
        client.register(network, ExactGasFreeClientMechanism(signer, clients=gasfree_clients))
```

### 4. Signer Resolution

The cli has no in-tree wallet plumbing. Both `TronClientSigner.create()` and `EvmClientSigner.create()` are called directly; `bankofai-agent-wallet` resolves the actual wallet source internally (encrypted local store at `~/.agent-wallet/`, falling back to env vars `AGENT_WALLET_PRIVATE_KEY` / `TRON_PRIVATE_KEY` / mnemonic forms).

```
Determine network from accepts[]
  ↓
Network prefix?
  ├─ "tron:" → await TronClientSigner.create()    (agent-wallet picks the source)
  └─ "eip155:" → await EvmClientSigner.create()   (agent-wallet picks the source)
```

There is no `--wallet` flag and no in-tree env fallback in the cli itself.

### 5. Select Requirements

```python
selected = await client.select_payment_requirements(
    accepts,
    filters={
        "network": args.network,
        "scheme": args.scheme,
    }
)
```

Filters applied in order:
1. Scheme (if specified)
2. Network (if specified)
3. Mechanism availability
4. Custom policies
5. Token selection strategy (default: lowest cost)

### 6. Create Payload

```python
payload = await client.create_payment_payload(
    selected,
    resource=url,
)
```

Result: PaymentPayload with signed permit/authorization

### 7. Retry Request

```
POST <url>
  PAYMENT-SIGNATURE: [Base64(PaymentPayload)]
  
Response Status?
  ├─ 200 → Success (parse and output)
  └─ Error → Print error and exit
```

## Error Codes

Errors are surfaced through `bankofai.x402_cli.errors.classify()`, which maps the underlying exception to a `(code, message, hint)` triplet. The cli emits the structured form in `--json` mode and prints `code + hint` lines in human mode.

| Code | When you see it | Hint summary |
|---|---|---|
| `WALLET_NOT_CONFIGURED` | agent-wallet has no source (no encrypted store, no env var) | Run `agent-wallet start raw_secret --wallet-id payer --private-key 0x...` once |
| `WALLET_CONFIG_CORRUPT` | `~/.agent-wallet/wallets_config.json` is partial/broken | `agent-wallet reset -y` then re-add |
| `INSUFFICIENT_GASFREE_BALANCE` | gasFreeAddress balance < amount + transferFee + (activateFee if first time) | Top up the gasFreeAddress, not the main wallet |
| `GASFREE_NOT_ACTIVATED` | First-time GasFree settlement | Make sure the GasFree balance covers `activateFee` (~2 USDT); the first settlement auto-activates |
| `TRON_ACCOUNT_NOT_ACTIVATED` | Fresh TRON address as owner of a contract call (TRON node refuses `account [T...] does not exist`) | Send any TRX inflow once to bootstrap the address, or use `--scheme exact_gasfree` |
| `INSUFFICIENT_GAS` | EVM/TRON permit path with no native gas (BNB / TRX) | Fund payer with native token, or switch to `exact_gasfree` on TRON |
| `RATE_LIMITED` | 429 / "too many pending" from facilitator or GasFree relayer | Wait 30–60s and retry |
| `DEADLINE_TOO_SOON` | Clock skew between local machine and chain/facilitator | NTP-sync system clock |
| `PERMIT_REVERTED` | On-chain `permit()` rejected the signature | Use `exact_gasfree` on TRON, or verify token contract supports EIP-2612 |
| `SDK_API_DRIFT` | SDK exposes a different symbol set than cli expects (e.g. TokenRegistry → AssetRegistry rename) | Upgrade cli: `pip install --upgrade bankofai-x402-cli` |
| `IO_ERROR` (fallback) | Anything unmatched | Pointer to `docs/manual-test-guide.md` troubleshooting table |

The classifier rules live in [`src/bankofai/x402_cli/errors.py`](../src/bankofai/x402_cli/errors.py); add a new rule there + a regression test in [`tests/test_errors.py`](../tests/test_errors.py) when a new error pattern emerges from real users.

## Output Examples

### Dry-Run Mode (--dry-run)

```json
{
  "ok": true,
  "command": "client",
  "network": "eip155:97",
  "scheme": "exact_permit",
  "result": {
    "url": "http://...",
    "network": "eip155:97",
    "scheme": "exact_permit",
    "asset": "0x337610d27c682E347C9cD60BD4b3b107C9d34dDd",
    "amount": "100000000000000",
    "message": "Dry run - no payment submitted"
  }
}
```

### Success

```json
{
  "ok": true,
  "command": "client",
  "network": "eip155:97",
  "scheme": "exact_permit",
  "result": {
    "url": "http://...",
    "status": 200,
    "network": "eip155:97",
    "scheme": "exact_permit",
    "asset": "0x337610d27c682E347C9cD60BD4b3b107C9d34dDd",
    "amount": "100000000000000",
    "paid": true,
    "transaction": "0x..."
  }
}
```

### Failure

```json
{
  "ok": false,
  "command": "client",
  "error": {
    "code": "WALLET_NOT_CONFIGURED",
    "message": "resolve_wallet could not find a wallet source in config or env",
    "hint": "Run 'agent-wallet start raw_secret --wallet-id payer --private-key 0x...' once, or set TRON_PRIVATE_KEY / AGENT_WALLET_PRIVATE_KEY in your shell."
  }
}
```

## Constraints

### --max-rawAmount Validation

`--max-rawAmount` is compared directly against `selected.amount` (which the SDK already returns in smallest units):

```python
if args.max_raw_amount:
    if int(selected.amount) > int(args.max_raw_amount):
        raise ValueError(
            f"Payment rawAmount {selected.amount} exceeds "
            f"--max-rawAmount {args.max_raw_amount}"
        )
```

### --max-amount Validation

`--max-amount` is human-readable. The check looks up token decimals from the registry, converts the smallest-unit amount to a Decimal, and compares:

```python
from decimal import Decimal
from bankofai.x402.tokens import TokenRegistry

if args.max_amount:
    token = TokenRegistry.find_by_address(selected.network, selected.asset)
    decimals = token.decimals if token else 6
    actual_human = Decimal(int(selected.amount)) / (10 ** decimals)
    if actual_human > Decimal(args.max_amount):
        raise ValueError(
            f"Payment amount {actual_human} exceeds "
            f"--max-amount {args.max_amount}"
        )
```

## Example Usage

```bash
# Dry-run: probe for 402 and parse requirements
x402-cli pay http://example.com/pay \
  --dry-run \
  --network eip155:97

# Pay with smallest-unit cap (e.g. <= 200000000000000 wei = 0.0002 BSC USDT)
x402-cli pay http://example.com/pay \
  --max-rawAmount 200000000000000 \
  --scheme exact_permit

# Pay with human-readable cap (e.g. <= 0.0002 USDT)
x402-cli pay http://example.com/pay \
  --max-amount 0.0002 \
  --scheme exact_permit
```
