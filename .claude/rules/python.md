# Python Conventions (x402-tools)

Target: **Python 3.11+**. Package: `bankofai-x402-tools` (PyPI).

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

Both forms are accepted (never both):

```python
# Human-readable (decimal)
--decimal 1.25

# Smallest-unit integer
--amount 1250000000000000
```

Conversion uses `Decimal` for precision:
```python
from decimal import Decimal
amount_smallest = int(Decimal(decimal) * (10 ** token_decimals))
```

## Wallet Resolution

Priority order:
1. `--wallet agent-wallet` (default) → `EvmClientSigner.create()` / `TronClientSigner.create()`
2. `--wallet env` (fallback) → read `EVM_PRIVATE_KEY` / `TRON_PRIVATE_KEY` from environment

For env fallback:
```python
from eth_account import Account  # EVM
from tronpy.hdwallet import key_to_address  # TRON
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
