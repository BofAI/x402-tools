# Troubleshooting Guide

Common issues and solutions for x402-cli.

## Server Issues

### Server fails to start

**Error**: `Address already in use`

**Solution**: Change the port with `--port` flag:
```bash
x402-cli serve --pay-to 0x... --amount 1.0 --network eip155:97 --port 4021
```

### Token not found

**Error**: `Token 'USDT' not found in registry for eip155:97`

**Solutions**:
1. Verify the token symbol is correct (case-sensitive)
2. Use an explicit address with `--asset` and `--decimals`:
   ```bash
   x402-cli serve --pay-to 0x... --amount 1.0 --network eip155:97 \
     --asset 0x337610d27c682E347C9cD60BD4b3b107C9d34dDd --decimals 6
   ```
3. Check supported networks in `specs/server.md`

### Invalid network

**Error**: `Unknown network prefix: ethereum`

**Solution**: Use CAIP-2 format for EVM or `tron:name` for TRON:
- EVM: `eip155:1` (mainnet), `eip155:97` (BSC testnet)
- TRON: `tron:mainnet`, `tron:nile`, `tron:shasta`

## Client Issues

### Agent wallet unavailable

**Error**: `agent-wallet ... wallet unavailable`

**Solutions**:
1. Install and configure [agent-wallet](https://github.com/BofAI/agent-wallet)
2. Use environment variables instead:
   ```bash
   export EVM_PRIVATE_KEY=0x...
   x402-cli pay http://... --wallet env
   ```

### Payment required but URL returns 200

**Issue**: URL doesn't require payment

**Solution**: Check that the URL actually requires payment (returns 402):
```bash
curl -i http://your-url/endpoint
```

Should see:
```
HTTP/1.1 402 Payment Required
```

### Invalid signature error

**Error**: `Invalid payment payload: ...`

**Solutions**:
1. Verify the server's `/.well-known/x402` is accessible
2. Check wallet has correct private key
3. Ensure network matches between client and server

### Insufficient balance

**Error**: `Settlement failed: insufficient balance`

**Solutions**:
1. Check wallet has enough token balance:
   ```bash
   # For TRON
   curl https://api.tronstack.io/getBalance/TJWdoJk8...
   
   # For EVM, use a block explorer or web3.py
   ```
2. Verify amount matches what server requires
3. Account for gas/fees

## Wallet Issues

### TRON_PRIVATE_KEY not recognized

**Error**: `TRON_PRIVATE_KEY is not set in the environment`

**Solution**: Set the environment variable with 0x-prefixed hex:
```bash
export TRON_PRIVATE_KEY=0x0123456789abcdef...
```

### EVM_PRIVATE_KEY format invalid

**Error**: `Invalid private key format`

**Solutions**:
1. Use 32-byte hex (64 characters + 0x prefix)
2. Verify no spaces or quotes:
   ```bash
   # Good
   export EVM_PRIVATE_KEY=0xabcd...
   
   # Bad
   export EVM_PRIVATE_KEY="0xabcd..."  # Has quotes
   export EVM_PRIVATE_KEY=0xabcd...ef  # Missing 0x
   ```

## Amount Issues

### Decimal precision errors

**Error**: `ValueError: amount conversion failed`

**Solutions**:
1. Use `--amount` for human-readable amounts (e.g., `1.25`)
2. Or use `--rawAmount` for smallest units (e.g., `1250000`). The relation is `rawAmount = amount × 10^decimals`.
3. Don't use both flags simultaneously

Example:
```bash
# Good (for 1.25 USDT with 6 decimals)
x402-cli serve --amount 1.25
# or
x402-cli serve --rawAmount 1250000

# Bad (both)
x402-cli serve --amount 1.25 --rawAmount 1250000
```

### Incorrect decimals

**Error**: Amount seems wrong after conversion

**Solutions**:
1. Verify token decimals:
   ```bash
   # USDT: 6 decimals (0.000001)
   # USDC: 6 decimals
   # DAI: 18 decimals
   ```
2. When using `--asset`, always specify `--decimals`

## Network Issues

### Cannot reach facilitator

**Error**: `HTTP Request: POST https://facilitator.bankofai.io... failed`

**Solutions**:
1. Check internet connection
2. Check firewall allows outbound HTTPS
3. Try a different network (use testnet)
4. Check facilitator status page

### RPC connection timeout

**Error**: `Connection timeout to RPC`

**Solutions**:
1. Check RPC URL is valid
2. Increase timeout in environment
3. Use a different RPC provider
4. Check network congestion

## Output Issues

### JSON parsing fails

**Error**: `json.JSONDecodeError`

**Solution**: Use proper JSON output flag:
```bash
x402-cli serve ... --json | jq .
```

### Output is empty

**Error**: No output after running command

**Solutions**:
1. Check command completed (wait a few seconds)
2. Check there are no errors (stderr output)
3. Try without `--json` flag to see human-readable output

## Debug Mode

To get detailed logs:

```bash
# With logging (Python environment)
PYTHONVERBOSE=1 x402-cli serve ...

# Or configure logging in code
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
import subprocess
subprocess.run(['x402-cli', 'serve', ...])
"
```

## Still Having Issues?

1. Check [x402-cli README](README.md)
2. Review [specification docs](specs/README.md)
3. Run smoke tests: `bash .claude/smoke-test.sh`
4. Check [FEATURES.md](FEATURES.md) for examples
5. Create an issue with:
   - Full error message/traceback
   - Command you ran
   - Python version (`python --version`)
   - OS and architecture
