#!/bin/bash
# x402-cli smoke test suite
# Validates core server functionality without real blockchain interaction

set -e

echo "=========================================="
echo "x402-cli Smoke Test Suite"
echo "=========================================="
echo ""

# Configuration
TEST_PORT=9999
TEST_NETWORK="eip155:97"
TEST_TOKEN="USDT"
TEST_PAY_TO="0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
TEST_AMOUNT="0.0001"

# Colors (optional)
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Test counter
TESTS_RUN=0
TESTS_PASSED=0

# Helper: Run a test
run_test() {
    local name="$1"
    local command="$2"
    local expected_pattern="$3"

    TESTS_RUN=$((TESTS_RUN + 1))

    echo "[Test $TESTS_RUN] $name"

    output=$(eval "$command" 2>&1 || true)

    if echo "$output" | grep -q "$expected_pattern"; then
        echo -e "${GREEN}✓ PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo "Expected pattern: $expected_pattern"
        echo "Got: $output"
        return 1
    fi
    echo ""
}

# Start server in background
echo "[Setup] Starting server..."
python3 -m bankofai.x402_tools.cli serve \
  --pay-to "$TEST_PAY_TO" \
  --rawAmount "$TEST_AMOUNT" \
  --network "$TEST_NETWORK" \
  --token "$TEST_TOKEN" \
  --scheme exact_permit \
  --port $TEST_PORT > /tmp/x402_server.log 2>&1 &
SERVER_PID=$!

# Wait for server to start
sleep 3
if ! ps -p $SERVER_PID > /dev/null; then
    echo -e "${RED}✗ Server failed to start${NC}"
    cat /tmp/x402_server.log
    exit 1
fi
echo "✓ Server running (PID: $SERVER_PID)"
echo ""

# Test 1: /health endpoint
run_test "/health endpoint" \
    "curl -s http://127.0.0.1:$TEST_PORT/health" \
    '"ok".*true'

# Test 2: /.well-known/x402 endpoint
run_test "/.well-known/x402 configuration" \
    "curl -s http://127.0.0.1:$TEST_PORT/.well-known/x402" \
    '"network".*"eip155:97"'

# Test 3: /pay GET returns 402
run_test "/pay GET returns 402" \
    "curl -s -i http://127.0.0.1:$TEST_PORT/pay 2>&1 | head -1" \
    '402'

# Test 4: /pay response has PAYMENT-REQUIRED header
run_test "/pay has PAYMENT-REQUIRED header" \
    "curl -s -i http://127.0.0.1:$TEST_PORT/pay 2>&1" \
    'payment-required:'

# Test 5: /pay response body is valid JSON
run_test "/pay response is valid JSON" \
    "curl -s http://127.0.0.1:$TEST_PORT/pay 2>&1 | python3 -m json.tool > /dev/null 2>&1 && echo 'valid'" \
    'valid'

# Cleanup
kill $SERVER_PID 2>/dev/null || true
sleep 1

# Results
echo "=========================================="
echo "Test Results"
echo "=========================================="
echo "Passed: $TESTS_PASSED / $TESTS_RUN"
echo ""

if [ $TESTS_PASSED -eq $TESTS_RUN ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
