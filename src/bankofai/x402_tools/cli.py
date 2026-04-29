#!/usr/bin/env python3
"""x402-tools CLI — serve or pay x402 endpoints."""

import asyncio
import json
import logging
from typing import Any

import click

from bankofai.x402_tools import __version__
from bankofai.x402_tools.output import OutputMode, emit_json, emit_human
from bankofai.x402_tools.server_cmd import cmd_server
from bankofai.x402_tools.client_cmd import cmd_client


def setup_logging() -> None:
    """Configure logging for CLI."""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(name)s] %(levelname)s: %(message)s",
    )


@click.group()
@click.version_option(__version__, prog_name="x402-tools")
def cli() -> None:
    """One-shot BankofAI x402 tools for serving and paying x402 endpoints."""
    setup_logging()


@cli.command()
@click.option(
    "--pay-to",
    required=True,
    help="Recipient wallet address",
)
@click.option(
    "--decimal",
    type=str,
    help="Human-readable amount, e.g. 1.25",
)
@click.option(
    "--amount",
    type=str,
    help="Smallest-unit amount, e.g. 1250000 for 1.25 USDT",
)
@click.option(
    "--network",
    required=True,
    help="Payment network, e.g. tron:nile, eip155:97",
)
@click.option(
    "--token",
    default="USDT",
    help="Token symbol from the registry (default: USDT)",
)
@click.option(
    "--asset",
    type=str,
    help="Explicit token address (out of registry)",
)
@click.option(
    "--decimals",
    type=int,
    help="Token decimals when --asset is given",
)
@click.option(
    "--scheme",
    type=str,
    help="x402 scheme: exact_permit | exact | exact_gasfree",
)
@click.option(
    "--host",
    default="127.0.0.1",
    help="Bind host (default: 127.0.0.1)",
)
@click.option(
    "--port",
    type=int,
    default=4020,
    help="Bind port (default: 4020)",
)
@click.option(
    "--resource-url",
    type=str,
    help="Resource URL advertised in x402 requirements",
)
@click.option(
    "--wallet",
    type=click.Choice(["agent-wallet", "env"]),
    default="agent-wallet",
    help="Wallet source: agent-wallet | env (default: agent-wallet)",
)
@click.option(
    "--daemon",
    is_flag=True,
    help="Run server in background and print pid",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Print server info as JSON",
)
def server(
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
    output_json: bool,
) -> None:
    """Start a local x402 payment server."""
    output_mode: OutputMode = "json" if output_json else "human"

    async def run() -> None:
        await cmd_server(
            pay_to=pay_to,
            decimal=decimal,
            amount=amount,
            network=network,
            token=token,
            asset=asset,
            decimals=decimals,
            scheme=scheme,
            host=host,
            port=port,
            resource_url=resource_url,
            wallet=wallet,
            daemon=daemon,
            output_mode=output_mode,
        )

    asyncio.run(run())


@cli.command()
@click.argument("url")
@click.option(
    "--max-decimal",
    type=str,
    help="Maximum human-readable amount allowed",
)
@click.option(
    "--max-amount",
    type=str,
    help="Maximum smallest-unit amount allowed",
)
@click.option(
    "--network",
    type=str,
    help="Require a specific network",
)
@click.option(
    "--token",
    type=str,
    help="Require a specific token (default: USDT)",
)
@click.option(
    "--scheme",
    type=str,
    help="Require a specific x402 scheme",
)
@click.option(
    "--method",
    default="GET",
    help="HTTP method (default: GET)",
)
@click.option(
    "--header",
    multiple=True,
    help="HTTP header; can be repeated",
)
@click.option(
    "--body",
    type=str,
    help="Request body string or JSON",
)
@click.option(
    "--wallet",
    type=click.Choice(["agent-wallet", "env"]),
    default="agent-wallet",
    help="Wallet source: agent-wallet | env (default: agent-wallet)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Read payment requirements but do not sign or pay",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Print machine-readable JSON",
)
def client(
    url: str,
    max_decimal: str | None,
    max_amount: str | None,
    network: str | None,
    token: str | None,
    scheme: str | None,
    method: str,
    header: tuple[str, ...],
    body: str | None,
    wallet: str,
    dry_run: bool,
    output_json: bool,
) -> None:
    """Pay an x402-protected URL when the server returns 402 Payment Required."""
    output_mode: OutputMode = "json" if output_json else "human"

    async def run() -> None:
        await cmd_client(
            url=url,
            max_decimal=max_decimal,
            max_amount=max_amount,
            network=network,
            token=token,
            scheme=scheme,
            method=method,
            headers=header,
            body=body,
            wallet=wallet,
            dry_run=dry_run,
            output_mode=output_mode,
        )

    asyncio.run(run())


def main() -> None:
    """CLI entry point."""
    cli()


if __name__ == "__main__":
    main()
