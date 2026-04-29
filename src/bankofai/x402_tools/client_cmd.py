"""Client command implementation."""

import logging
from decimal import Decimal
from typing import Any

import httpx

from bankofai.x402.clients import X402Client
from bankofai.x402.encoding import decode_payment_payload, encode_payment_payload
from bankofai.x402.types import PaymentRequired
from bankofai.x402_tools.output import OutputMode, emit
from bankofai.x402_tools.wallet import resolve_evm_signer, resolve_tron_signer

logger = logging.getLogger(__name__)

PAYMENT_SIGNATURE_HEADER = "PAYMENT-SIGNATURE"
PAYMENT_REQUIRED_HEADER = "PAYMENT-REQUIRED"
PAYMENT_RESPONSE_HEADER = "PAYMENT-RESPONSE"


async def cmd_client(
    url: str,
    max_decimal: str | None,
    max_amount: str | None,
    network: str | None,
    token: str | None,
    scheme: str | None,
    method: str,
    headers: tuple[str, ...],
    body: str | None,
    wallet: str,
    dry_run: bool,
    output_mode: OutputMode,
) -> None:
    """Pay an x402-protected URL."""

    try:
        if not url:
            raise ValueError("URL is required")

        if max_decimal and max_amount:
            raise ValueError("--max-decimal and --max-amount are mutually exclusive")

        # Parse custom headers into a dict
        custom_headers = {}
        for header in headers:
            if ":" not in header:
                raise ValueError(f"Invalid header format: {header} (expected Key: Value)")
            key, value = header.split(":", 1)
            custom_headers[key.strip()] = value.strip()

        async with httpx.AsyncClient(timeout=10.0) as client:
            # First request: probe for 402
            response = await client.request(
                method=method,
                url=url,
                headers=custom_headers,
                content=body,
            )

            if response.status_code != 402:
                result = {
                    "url": url,
                    "status": response.status_code,
                    "message": "Not a payment-required endpoint",
                }
                emit(
                    command="client",
                    result=result,
                    mode=output_mode,
                )
                return

            # Parse 402 response
            payment_required_header = response.headers.get(PAYMENT_REQUIRED_HEADER)
            if not payment_required_header:
                raise ValueError("402 response missing PAYMENT-REQUIRED header")

            try:
                payment_required = decode_payment_payload(
                    payment_required_header, PaymentRequired
                )
            except Exception as err:
                raise ValueError(f"Failed to parse payment requirements: {err}")

            if not payment_required.accepts:
                raise ValueError("No payment options available")

            # Determine the appropriate signer based on available networks
            # We need to create the right signer type before creating mechanisms
            networks_in_options = set(opt.network for opt in payment_required.accepts)
            primary_network = next(iter(networks_in_options))
            if primary_network.startswith("tron:"):
                signer = await resolve_tron_signer(wallet)
            elif primary_network.startswith("eip155:"):
                signer = await resolve_evm_signer(wallet)
            else:
                raise ValueError(f"Unknown network: {primary_network}")

            # Now create client and register mechanisms with signer
            client_obj = X402Client()
            _register_client_mechanisms(client_obj, payment_required.accepts, signer)

            # Select payment requirements based on filters
            selected = await client_obj.select_payment_requirements(
                payment_required.accepts,
                filters={
                    "network": network,
                    "token": token,
                    "scheme": scheme,
                } if any([network, token, scheme]) else None,
            )

            # Create payment payload
            payload = await client_obj.create_payment_payload(
                selected,
                resource=url,
            )

            if dry_run:
                result = {
                    "url": url,
                    "network": selected.network,
                    "scheme": selected.scheme,
                    "asset": selected.asset,
                    "amount": selected.amount,
                    "pay_to": selected.pay_to,
                    "message": "Dry run - no payment submitted",
                }
                emit(
                    command="client",
                    result=result,
                    mode=output_mode,
                    network=selected.network,
                    scheme=selected.scheme,
                )
                return

            # Second request: submit payment signature
            payment_header = encode_payment_payload(payload.model_dump(by_alias=True))
            retry_headers = custom_headers.copy()
            retry_headers[PAYMENT_SIGNATURE_HEADER] = payment_header

            retry_response = await client.request(
                method=method,
                url=url,
                headers=retry_headers,
                content=body,
            )

            if retry_response.status_code != 200:
                result = {
                    "url": url,
                    "status": retry_response.status_code,
                    "error": retry_response.text[:500],
                }
                emit(
                    command="client",
                    result=result,
                    mode=output_mode,
                )
                return

            # Success
            result = {
                "url": url,
                "status": retry_response.status_code,
                "network": selected.network,
                "scheme": selected.scheme,
                "asset": selected.asset,
                "amount": selected.amount,
                "paid": True,
            }

            # Parse response header if available
            response_header = retry_response.headers.get(PAYMENT_RESPONSE_HEADER)
            if response_header:
                try:
                    import json
                    import base64
                    decoded_bytes = base64.b64decode(response_header)
                    response_data = json.loads(decoded_bytes.decode('utf-8'))
                    if isinstance(response_data, dict):
                        result["transaction"] = response_data.get("transaction")
                except Exception:
                    pass

            emit(
                command="client",
                result=result,
                mode=output_mode,
                network=selected.network,
                scheme=selected.scheme,
            )

    except Exception as err:
        emit(
            command="client",
            error={"code": "IO_ERROR", "message": str(err)},
            mode=output_mode,
        )


def _register_client_mechanisms(
    client: X402Client,
    requires: list[Any],
    signer: Any,
) -> None:
    """Register payment mechanisms based on required payment options."""
    networks_schemes = {}
    for req in requires:
        network = req.network
        scheme = req.scheme
        if network not in networks_schemes:
            networks_schemes[network] = set()
        networks_schemes[network].add(scheme)

    for network, schemes in networks_schemes.items():
        for scheme in schemes:
            try:
                if scheme == "exact":
                    if network.startswith("eip155:"):
                        from bankofai.x402.mechanisms.evm.exact import ExactEvmClientMechanism
                        client.register(network, ExactEvmClientMechanism(signer))
                elif scheme == "exact_permit":
                    if network.startswith("eip155:"):
                        from bankofai.x402.mechanisms.evm.exact_permit import ExactPermitEvmClientMechanism
                        client.register(network, ExactPermitEvmClientMechanism(signer))
                    elif network.startswith("tron:"):
                        from bankofai.x402.mechanisms.tron.exact_permit import ExactPermitTronClientMechanism
                        client.register(network, ExactPermitTronClientMechanism(signer))
                elif scheme == "exact_gasfree":
                    if network.startswith("tron:"):
                        from bankofai.x402.mechanisms.tron.exact_gasfree.client import ExactGasFreeClientMechanism
                        client.register(network, ExactGasFreeClientMechanism(signer))
            except Exception as err:
                logger.warning(f"Failed to register {scheme} mechanism for {network}: {err}")

