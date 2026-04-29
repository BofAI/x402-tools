"""Server command implementation using Python SDK's X402Server."""

import json
import logging
import uuid
from decimal import Decimal
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from bankofai.x402 import TokenRegistry
from bankofai.x402.encoding import decode_payment_payload, encode_payment_payload
from bankofai.x402.facilitator import FacilitatorClient
from bankofai.x402.server import ResourceConfig, X402Server
from bankofai.x402.types import PaymentPayload
import uvicorn

from bankofai.x402_tools.output import OutputMode, emit
from bankofai.x402_tools.schemes import is_known_scheme, pick_scheme

logger = logging.getLogger(__name__)

PAYMENT_SIGNATURE_HEADER = "PAYMENT-SIGNATURE"
PAYMENT_REQUIRED_HEADER = "PAYMENT-REQUIRED"
PAYMENT_RESPONSE_HEADER = "PAYMENT-RESPONSE"


async def _return_payment_required(
    request: Request,
    server: X402Server,
    network: str,
    scheme: str,
    token_symbol: str,
    amount_str: str,
    raw_amount_str: str,
    pay_to: str,
) -> JSONResponse:
    """Return 402 payment required response."""
    try:
        config = ResourceConfig(
            scheme=scheme,
            network=network,
            price=f"{raw_amount_str} {token_symbol}",
            pay_to=pay_to,
            valid_for=3600,
            delivery_mode="PAYMENT_ONLY",
        )
        requirements_list = await server.build_payment_requirements([config])
        if not requirements_list:
            return JSONResponse(
                content={"error": "No supported payment options available"},
                status_code=500,
            )

        payment_required = server.create_payment_required_response(
            requirements=requirements_list,
            resource_info={"url": str(request.url)},
        )

        response_data = payment_required.model_dump(by_alias=True)
        response = JSONResponse(content=response_data, status_code=402)
        response.headers[PAYMENT_REQUIRED_HEADER] = encode_payment_payload(response_data)
        return response
    except Exception as err:
        logger.error(f"Failed to create payment required response: {err}", exc_info=True)
        return JSONResponse(
            content={"error": f"Payment configuration error: {str(err)}"},
            status_code=500,
        )


async def cmd_server(
    pay_to: str,
    raw_amount: str | None,
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
                token_symbol = token_info.symbol
                token_decimals = token_info.decimals
                token_address = token_info.address
            else:
                token_symbol = token or "TOKEN"
                token_decimals = decimals
                token_address = asset
        else:
            token_info = TokenRegistry.get_token(network, token)
            if not token_info:
                raise ValueError(f"Token '{token}' not found in registry for {network}")
            token_symbol = token_info.symbol
            token_decimals = token_info.decimals
            token_address = token_info.address

        # Resolve amount
        if raw_amount and amount:
            raise ValueError("--rawAmount and --amount are mutually exclusive")
        if not raw_amount and not amount:
            raise ValueError("Either --rawAmount or --amount must be provided")

        # Parse amount
        if raw_amount:
            amount_decimal = Decimal(raw_amount)
            amount_smallest = int(amount_decimal * (10 ** token_decimals))
            amount_str = str(amount_smallest)
            raw_amount_str = raw_amount
        else:
            amount_smallest = int(amount or "0")
            amount_str = amount or "0"
            amount_decimal = Decimal(amount_smallest) / (10 ** token_decimals)
            raw_amount_str = str(amount_decimal)

        # Pick scheme
        if not scheme:
            scheme = pick_scheme(network, token_symbol) or "exact_permit"
        if not is_known_scheme(scheme):
            raise ValueError(f"Unknown scheme '{scheme}'")

        resource_url_final = resource_url or f"http://{host}:{port}/pay"
        pay_url = f"http://{host}:{port}/pay"

        # Create X402Server and register mechanisms
        server = X402Server()
        facilitator_url = "https://facilitator.bankofai.io"
        facilitator = FacilitatorClient(base_url=facilitator_url)
        server.set_facilitator(facilitator)

        # Register the appropriate mechanism for this scheme
        if scheme == "exact":
            if network.startswith("eip155:"):
                from bankofai.x402.mechanisms.evm.exact import ExactEvmServerMechanism
                server.register(network, ExactEvmServerMechanism())
            else:
                raise ValueError(f"Scheme 'exact' not supported for network {network}")
        elif scheme == "exact_permit":
            if network.startswith("eip155:"):
                from bankofai.x402.mechanisms.evm.exact_permit import ExactPermitEvmServerMechanism
                server.register(network, ExactPermitEvmServerMechanism())
            elif network.startswith("tron:"):
                from bankofai.x402.mechanisms.tron.exact_permit import ExactPermitTronServerMechanism
                server.register(network, ExactPermitTronServerMechanism())
            else:
                raise ValueError(f"Unknown network prefix: {network}")
        elif scheme == "exact_gasfree":
            if not network.startswith("tron:"):
                raise ValueError(f"Scheme 'exact_gasfree' requires a tron:* network, got {network}")
            from bankofai.x402.mechanisms.tron.exact_gasfree.server import ExactGasFreeServerMechanism
            server.register(network, ExactGasFreeServerMechanism())
        else:
            raise ValueError(f"Unknown scheme: {scheme}")

        # Create FastAPI app
        app = FastAPI()

        @app.get("/health")
        async def health() -> dict:
            return {"ok": True}

        @app.get("/.well-known/x402")
        async def well_known() -> dict:
            return {
                "network": network,
                "scheme": scheme,
                "token": token_symbol,
                "asset": token_address,
                "rawAmount": raw_amount_str,
                "amount": amount_str,
                "pay_to": pay_to.strip(),
                "pay_url": pay_url,
                "resource_url": resource_url_final,
            }

        @app.get("/pay")
        @app.post("/pay")
        async def pay(request: Request) -> Response:
            payment_signature_header = request.headers.get(PAYMENT_SIGNATURE_HEADER)

            if not payment_signature_header:
                return await _return_payment_required(
                    request, server, network, scheme, token_symbol,
                    amount_str, raw_amount_str, pay_to.strip()
                )

            try:
                payload = decode_payment_payload(payment_signature_header, PaymentPayload)
            except Exception as err:
                logger.error(f"Failed to decode payment payload: {err}", exc_info=True)
                return JSONResponse(
                    content={"error": f"Invalid payment payload: {str(err)}"},
                    status_code=400,
                )

            try:
                # Build requirements for verification
                config = ResourceConfig(
                    scheme=scheme,
                    network=network,
                    price=f"{raw_amount_str} {token_symbol}",
                    pay_to=pay_to.strip(),
                    valid_for=3600,
                    delivery_mode="PAYMENT_ONLY",
                )
                requirements = (await server.build_payment_requirements([config]))[0]

                # Verify and settle
                settle_result = await server.settle_payment(payload, requirements)
                if not settle_result.success:
                    logger.error(f"Payment settlement failed: {settle_result.error_reason}")
                    return JSONResponse(
                        content={
                            "error": f"Settlement failed: {settle_result.error_reason}",
                            "txHash": settle_result.transaction,
                        },
                        status_code=500,
                    )

                # Return success response with settlement info
                response_data = settle_result.model_dump(by_alias=True)
                response = JSONResponse(content=response_data, status_code=200)
                response.headers[PAYMENT_RESPONSE_HEADER] = encode_payment_payload(response_data)
                return response

            except Exception as err:
                logger.error(f"Payment settlement error: {err}", exc_info=True)
                return JSONResponse(
                    content={"error": f"Settlement error: {str(err)}"},
                    status_code=500,
                )

        # Print server info
        result = {
            "pid": None,
            "pay_url": pay_url,
            "resource_url": resource_url_final,
            "network": network,
            "scheme": scheme,
            "token": token_symbol,
            "rawAmount": raw_amount_str,
            "amount": amount_str,
            "pay_to": pay_to.strip(),
        }

        emit(
            command="server",
            result=result,
            mode=output_mode,
            network=network,
            scheme=scheme,
        )

        # Start server
        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="info",
        )
        server_instance = uvicorn.Server(config)
        await server_instance.serve()

    except Exception as err:
        import traceback
        traceback.print_exc()
        emit(
            command="server",
            error={"code": "IO_ERROR", "message": str(err)},
            mode=output_mode,
        )
