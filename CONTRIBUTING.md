# Contributing to x402-cli

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to x402-cli.

## Code of Conduct

Be respectful, inclusive, and constructive in all interactions.

## Getting Started

### Prerequisites

- Python 3.11+
- pip or uv
- Git

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/BofAI/x402-cli.git
cd x402-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (recommended)
pre-commit install
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/bankofai/x402_cli

# Run type checking
mypy src/bankofai/x402_cli

# Run smoke tests
bash .claude/smoke-test.sh
```

## Development Workflow

### 1. Create a Branch

```bash
# Create a branch from main
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-fix-name
```

**Naming conventions**:
- `feature/` — New features
- `fix/` — Bug fixes
- `docs/` — Documentation only
- `test/` — Tests only
- `refactor/` — Code refactoring

### 2. Make Changes

Follow these principles:

- **Single responsibility**: Each commit should do one thing well
- **Type hints**: Add type annotations to all function parameters and returns
- **Tests**: Write tests for new functionality
- **Documentation**: Update specs and docstrings as needed
- **No print()**: Use logging for library code

### 3. Commit Messages

Follow conventional commits format:

```
<type>(<scope>): <description>

<body (optional)>

<footer (optional)>
```

**Types**: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

**Scopes**: `server`, `client`, `wallet`, `output`, `cli`

**Examples**:
```
feat(server): add request timeout configuration

fix(client): handle 402 responses with missing PAYMENT-REQUIRED header

docs(specs): update server endpoint documentation
```

### 4. Create a Pull Request

```bash
# Push your branch
git push origin feature/your-feature-name

# Create PR via GitHub CLI
gh pr create --title "Your PR Title" \
  --body "PR description with context"
```

**PR requirements**:
- [ ] Tests pass (`pytest`)
- [ ] Type checking passes (`mypy`)
- [ ] Code is formatted consistently
- [ ] Documentation is updated
- [ ] No breaking changes (or justified)

## Code Style

### Python Style Guide

- **PEP 8**: Follow Python Enhancement Proposal 8
- **Line length**: 100 characters maximum
- **Imports**: Alphabetical, group stdlib/third-party/local
- **Docstrings**: One-line for simple functions, multi-line for complex logic

### Type Hints

Always use type hints:

```python
async def resolve_evm_signer(wallet_source: str = "agent-wallet") -> EvmClientSigner:
    """Resolve EVM signer from wallet source.
    
    Args:
        wallet_source: Either "agent-wallet" or "env"
        
    Returns:
        Initialized EvmClientSigner
    """
    ...
```

### Error Handling

Be specific with exceptions:

```python
# Good
if not token_info:
    raise ValueError(f"Token '{token}' not found in registry for {network}")

# Avoid
try:
    ...
except Exception as err:  # Too broad
    pass
```

## Testing Guidelines

### Unit Tests

```python
def test_pick_scheme_bsc_testnet_usdt() -> None:
    """Test scheme picking for BSC testnet USDT."""
    scheme = pick_scheme("eip155:97", "USDT")
    assert scheme == "exact_permit"
```

### Test Organization

- Place tests in `tests/` directory
- Mirror source structure: `tests/test_<module>.py`
- Test function names: `test_<function>_<scenario>`
- Use descriptive docstrings

### Running Tests Locally

```bash
# Run specific test
pytest tests/test_schemes.py::test_pick_scheme_bsc_testnet_usdt

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src/bankofai/x402_cli --cov-report=html
```

## Documentation

### Spec Documents

When adding features, update relevant spec:

- `specs/server.md` — Server endpoint changes
- `specs/client.md` — Client flow changes
- `specs/smoke-tests.md` — Test additions

### README Updates

Update `README.md` for:
- New commands or flags
- Installation changes
- Major feature additions

### Comments in Code

Only add comments for **why**, not **what**:

```python
# Good: explains the non-obvious
# We call build_payment_requirements twice: once for validation,
# once for settlement (requirements may have updated fees)

# Avoid: just restates the code
# Build the payment requirements
requirements = await server.build_payment_requirements([config])
```

## Reporting Issues

### Bug Reports

Include:
- Python version and OS
- `x402-cli --version`
- Minimal reproduction steps
- Expected vs actual behavior
- Full error output/traceback

### Feature Requests

Describe:
- Problem you're solving
- Proposed solution
- Alternative approaches considered
- Example usage

## CI/CD

All PRs are checked:

- **Tests**: `pytest` with coverage
- **Type checking**: `mypy` strict mode
- **Linting**: Checked via GitHub Actions

View checks in the PR or in the Actions tab.

## Release Process

Releases are published by maintainers:

1. Update `pyproject.toml` version
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v0.1.0`
4. Push tag: `git push origin v0.1.0`
5. GitHub Actions publishes to PyPI

## Need Help?

- **Questions about code**: Create a discussion
- **Questions about x402**: See [x402 specs](https://github.com/x402-foundation/x402)
- **SDK issues**: Check [bankofai-x402](https://github.com/BofAI/x402)
- **Local issues**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing! 🙏
