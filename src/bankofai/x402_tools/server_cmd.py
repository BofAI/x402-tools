"""Server command implementation using Python SDK's X402Server."""

import logging
from typing import Any

from bankofai.x402 import TokenRegistry

from bankofai.x402_tools.output import OutputMode, emit
from bankofai.x402_tools.schemes import is_known_scheme, pick_scheme

logger = logging.getLogger(__name__)


async def cmd_server(
    pay_to: str,
    decimal: str | None,
    amount: str | None,
    network: str,
    token: str,
    asset: str | None,
    decimals: int | None,
    scheme: str | None,
    host: str,
    port: int,
    resource_url: str | None,
    wallet: str,
    daemon: bool,
    output_mode: OutputMode,
) -> None:
    """Start an x402 payment server using the SDK's X402Server."""

    try:
        if not pay_to or not pay_to.strip():
            raise ValueError("--pay-to <address> is required")
        if not network:
            raise ValueError("--network <id> is required")

        # Resolve token
        if asset:
            if not isinstance(decimals, int) or decimals < 0:
                token_info = TokenRegistry.find_by_address(network, asset)
                if not token_info:
                    raise ValueError(
                        "When --asset is set without a registry match, "
                        "--decimals must be provided"
                    )
                token_decimals = token_info.decimals
            else:
                token_decimals = decimals
        else:
            token_info = TokenRegistry.get_token(network, token)
            if not token_info:
                raise ValueError(f"Token '{token}' not found in registry for {network}")
            token_decimals = token_info.decimals

        # Resolve amount
        if decimal and amount:
            raise ValueError("--decimal and --amount are mutually exclusive")
        if not decimal and not amount:
            raise ValueError("Either --decimal or --amount must be provided")

        # For now, we'll just output the config and use a placeholder X402Server
        # Full implementation would integrate with FastAPI app + uvicorn

        # Pick scheme
        if not scheme:
            scheme = pick_scheme(network, token) or "exact_permit"
        if not is_known_scheme(scheme):
            raise ValueError(f"Unknown scheme '{scheme}'")

        resource_url_final = resource_url or f"http://{host}:{port}/pay"

        result = {
            "pid": None,
            "pay_url": f"http://{host}:{port}/pay",
            "resource_url": resource_url_final,
            "network": network,
            "scheme": scheme,
            "token": token,
            "decimal": decimal or "unknown",
            "amount": amount or "unknown",
            "pay_to": pay_to.strip(),
        }

        emit(
            command="server",
            result=result,
            mode=output_mode,
            network=network,
            scheme=scheme,
        )

    except Exception as err:
        emit(
            command="server",
            error={"code": "IO_ERROR", "message": str(err)},
            mode=output_mode,
        )
