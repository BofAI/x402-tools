# x402-tools Specifications

Design documents and protocol specifications for the x402-tools CLI.

## Contents

### Design Documents

- **[server.md](server.md)** — Server command design
  - Architecture and flow
  - All HTTP endpoints (/health, /.well-known/x402, /pay)
  - Parameter reference
  - Error handling
  - Mechanism registration strategy

- **[client.md](client.md)** — Client command design
  - Payment client architecture
  - Complete flow sequence (probe → parse → sign → retry)
  - Signer resolution logic
  - Payment requirement filtering
  - Error handling and examples

- **[smoke-tests.md](smoke-tests.md)** — Smoke test specification
  - Test suite definition
  - Each test's objective and assertions
  - Test execution instructions
  - Coverage analysis
  - Known limitations and future scenarios

## Design Philosophy

### Why These Documents?

The x402-tools CLI has clear, distinct responsibilities:

1. **Server** — Advertise payment terms and verify signatures
2. **Client** — Discover payment requirements and pay them

Each command has a well-defined flow that benefits from upfront specification:
- Helps developers understand the architecture
- Enables early design review (before implementation)
- Documents expected behavior for testing
- Provides a reference for debugging

### What We Document

- **Architecture**: How components fit together (X402Server, X402Client, signers, etc.)
- **Flows**: Step-by-step request/response sequences
- **Parameters**: All CLI flags and their interaction
- **Endpoints**: HTTP request/response formats
- **Errors**: How failures are handled and reported
- **Examples**: Real-world usage patterns

### What We Don't Document

- **Implementation details**: How the code works internally (read the source)
- **SDK internals**: How bankofai-x402 works (refer to SDK docs)
- **User guides**: Getting started and feature matrix (see README.md)

## Reading Order

If you're new to x402-tools, read in this order:

1. **../README.md** — Understand what x402-tools is
2. **server.md** — Learn how the payment server works
3. **client.md** — Learn how the payment client works
4. **smoke-tests.md** — See how we validate the implementation

If you're debugging or adding features:

1. **server.md** or **client.md** — Find the relevant flow
2. **../src/*.py** — Read the implementation
3. **smoke-tests.md** — Check test expectations

## Updating These Specs

When you change behavior:

1. **Update the spec first** (before coding)
2. **Implement the change** (in src/)
3. **Update smoke tests** (if behavior changed)
4. **Verify tests pass** (smoke tests should still pass)

Example:
```
User asks: "Add --max-decimal validation to client"

1. Update specs/client.md → add --max-decimal to parameters
2. Update src/bankofai/x402_tools/client_cmd.py → implement validation
3. Update specs/smoke-tests.md → add test case
4. Run: bash .claude/smoke-test.sh → verify
```

## Protocol Reference

x402-tools implements the **x402 Payment Protocol v2**:

- **Spec**: See the [x402 repository](https://github.com/x402-foundation/x402/blob/main/specs/protocol.md)
- **Our implementation**: Uses `bankofai-x402` SDK directly
- **Key concepts**:
  - **402 Payment Required**: HTTP status code for payment endpoints
  - **PAYMENT-REQUIRED header**: Challenge with payment options
  - **PAYMENT-SIGNATURE header**: Client's signed payment
  - **Three schemes**: exact, exact_permit, exact_gasfree
  - **Two networks**: EVM (CAIP-2) and TRON (tron:name)

## File Structure

```
specs/
├── README.md           ← You are here
├── server.md           ← Server command design
├── client.md           ← Client command design
└── smoke-tests.md      ← Testing specification
```

## Questions?

- **How do I add a new endpoint?** → Update server.md with endpoint docs, then implement
- **How do I support a new scheme?** → Update both server.md and client.md with mechanism info
- **How do I debug a failure?** → Find the relevant flow in the spec, trace the code
- **How do I run tests?** → See smoke-tests.md "Test Execution" section
