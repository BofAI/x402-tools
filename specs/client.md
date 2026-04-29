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
| `--max-rawAmount` | — | Max human-readable amount allowed |
| `--max-amount` | — | Max smallest-unit amount allowed |
| `--network` | — | Filter by network (if multiple available) |
| `--token` | — | Filter by token symbol |
| `--scheme` | — | Filter by scheme |
| `--method` | `GET` | HTTP method for request |
| `--header` | — | Custom HTTP headers (repeatable: `Key: Value`) |
| `--body` | — | Request body |
| `--wallet` | `agent-wallet` | Wallet source (agent-wallet \| env) |
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
for requirement in accepts:
    scheme = requirement.scheme
    network = requirement.network
    
    # Register appropriate mechanism
    if scheme == "exact":
        client.register(network, ExactEvmClientMechanism(signer))
    elif scheme == "exact_permit":
        if network.startswith("eip155:"):
            client.register(network, ExactPermitEvmClientMechanism(signer))
        elif network.startswith("tron:"):
            client.register(network, ExactPermitTronClientMechanism(signer))
    elif scheme == "exact_gasfree":
        client.register(network, ExactGasFreeClientMechanism(signer))
```

### 4. Signer Resolution

```
Determine network from accepts[]
  ↓
Network prefix?
  ├─ "tron:" → TronClientSigner (from agent-wallet or TRON_PRIVATE_KEY)
  └─ "eip155:" → EvmClientSigner (from agent-wallet or EVM_PRIVATE_KEY)
```

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

| Code | Scenario |
|------|----------|
| `IO_ERROR` | Network issues, URL unreachable |
| `VALIDATION_ERROR` | Invalid URL, conflicting flags |
| `PARSE_ERROR` | Invalid 402 response format |
| `WALLET_ERROR` | Signer unavailable or invalid |
| `SIGNATURE_ERROR` | Payment signing failed |
| `SETTLEMENT_ERROR` | Server rejected signature/payment |

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
    "code": "IO_ERROR",
    "message": "EVM_PRIVATE_KEY is not set in the environment..."
  }
}
```

## Constraints

### --max-amount Validation

```python
if args.max_amount:
    if int(selected.amount) > int(args.max_amount):
        raise ValueError(
            f"Payment amount {selected.amount} exceeds "
            f"--max-amount {args.max_amount}"
        )
```

### --max-rawAmount

Currently unimplemented (requires token decimals from external source).

## Example Usage

```bash
# Dry-run: probe for 402 and parse requirements
x402-cli pay http://example.com/pay \
  --dry-run \
  --network eip155:97

# Pay with max-amount constraint
x402-cli pay http://example.com/pay \
  --max-amount 200000000000000 \
  --scheme exact_permit \
  --wallet env
```
