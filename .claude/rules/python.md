# Python Conventions (x402-cli)

Target: **Python 3.11+**. Package: `bankofai-x402-cli` (PyPI).

## Tooling

- **Package manager**: `pip` + `pyproject.toml` (hatchling build backend)
- **Type checking**: `mypy` (strict mode in `pyproject.toml`)
- **Testing**: `pytest` + `pytest-asyncio`
- **Async**: `asyncio` (no third-party event loops)
- **HTTP**: `httpx.AsyncClient` with explicit timeouts

## Idioms

- **CLI framework**: `click` (command groups, options, decorators)
- **Async/await**: Async-first, entry point uses `asyncio.run()`
- **Pydantic**: v2+ with `model_dump(by_alias=True)` for wire output
- **Signers**: `EvmClientSigner` / `TronClientSigner` from `bankofai.x402.signers.client`
- **Logging**: `logging` stdlib, no `print()` in library code

## Amount Handling

`rawAmount = amount × 10^decimals`. Both forms are accepted (never both):

```python
# Human-readable
--amount 1.25

# Smallest-unit integer (1.25 × 10^6 for USDT)
--rawAmount 1250000
```

Conversion uses `Decimal` for precision:
```python
from decimal import Decimal
# human → raw
raw = int(Decimal(amount) * (10 ** token_decimals))
# raw → human
amount = Decimal(int(raw)) / (10 ** token_decimals)
```

## Wallet Resolution

All signing goes through `bankofai-agent-wallet`. The CLI calls `TronClientSigner.create()` / `EvmClientSigner.create()` and lets agent-wallet pick the source. There is **no** `--wallet` flag and **no** in-tree env-fallback / `LocalTronWallet` / `LocalEvmWallet` — that path was removed in beta.10.

agent-wallet itself resolves in this order:
1. Encrypted local store at `~/.agent-wallet/` (managed by `agent-wallet add` / `agent-wallet use`).
2. Env vars: `AGENT_WALLET_PRIVATE_KEY` or `TRON_PRIVATE_KEY` (private key); `AGENT_WALLET_MNEMONIC` or `TRON_MNEMONIC` (mnemonic).

```python
# In wallet.py — entire surface
from bankofai.x402.signers.client import EvmClientSigner, TronClientSigner

async def resolve_tron_signer() -> TronClientSigner:
    return await TronClientSigner.create()

async def resolve_evm_signer() -> EvmClientSigner:
    return await EvmClientSigner.create()
```

## Output

- **Default**: Human-readable to stdout (line-per-field)
- **`--json`**: Wrapped envelope with ok/command/network/scheme/result|error

Example:
```json
{
  "ok": true,
  "command": "server",
  "network": "eip155:97",
  "scheme": "exact_permit",
  "result": { ... }
}
```

## Don'ts

- **Don't** commit `.env` or private keys
- **Don't** use `from_private_key()` methods (use direct wallet construction)
- **Don't** catch bare `Exception` (be specific in payment path)
- **Don't** use `float` for amounts (use `int` or `Decimal`)
- **Don't** hardcode RPC URLs or facilitator endpoints
