#!/usr/bin/env python3
"""x402-cli — serve or pay x402 endpoints."""

import asyncio
import json
import logging
import os
import signal
import subprocess
import time
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
@click.version_option(__version__, prog_name="x402-cli")
def cli() -> None:
    """One-shot BankofAI x402 CLI for serving and paying x402 endpoints."""
    setup_logging()


@cli.command()
@click.option(
    "--pay-to",
    required=True,
    help="Recipient wallet address",
)
@click.option(
    "--rawAmount",
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
def serve(
    pay_to: str,
    rawamount: str | None,
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
    """Start a local x402 payment server (foreground or daemon mode)."""
    output_mode: OutputMode = "json" if output_json else "human"

    async def run() -> None:
        await cmd_server(
            pay_to=pay_to,
            raw_amount=rawamount,
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
    "--max-rawAmount",
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
def pay(
    url: str,
    max_rawamount: str | None,
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
            max_raw_amount=max_rawamount,
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


@cli.command()
@click.option(
    "--pay-to",
    required=True,
    help="Recipient wallet address",
)
@click.option(
    "--rawAmount",
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
    "--json",
    "output_json",
    is_flag=True,
    help="Print result as JSON",
)
def roundtrip(
    pay_to: str,
    rawamount: str | None,
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
    output_json: bool,
) -> None:
    """One-shot roundtrip: start server, pay it, shut down (for testing)."""
    output_mode: OutputMode = "json" if output_json else "human"

    async def run() -> None:
        import sys

        # Start daemon server
        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "bankofai.x402_tools.cli",
                "serve",
                "--pay-to", pay_to,
                "--network", network,
                "--token", token,
                "--host", host,
                "--port", str(port),
                "--wallet", wallet,
            ] + (
                ["--rawAmount", rawamount] if rawamount else []
            ) + (
                ["--amount", amount] if amount else []
            ) + (
                ["--asset", asset] if asset else []
            ) + (
                ["--decimals", str(decimals)] if decimals else []
            ) + (
                ["--scheme", scheme] if scheme else []
            ) + (
                ["--resource-url", resource_url] if resource_url else []
            ),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for server to start
        time.sleep(1)

        try:
            # Pay the server
            await cmd_client(
                url=f"http://{host}:{port}/pay",
                max_raw_amount=None,
                max_amount=None,
                network=network,
                token=token,
                scheme=scheme,
                method="GET",
                headers=(),
                body=None,
                wallet=wallet,
                dry_run=False,
                output_mode=output_mode,
            )
        finally:
            # Kill the server
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()

    asyncio.run(run())


def main() -> None:
    """CLI entry point."""
    cli()


if __name__ == "__main__":
    main()
