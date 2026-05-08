"""Tests for schemes module."""

from bankofai.x402_cli.schemes import SCHEME_TABLE, pick_scheme, is_known_scheme


def test_pick_scheme_tron_nile_usdt() -> None:
    """TRON Nile USDT defaults to exact_permit (exact_gasfree stays opt-in)."""
    scheme = pick_scheme("tron:nile", "USDT")
    assert scheme == "exact_permit"


def test_pick_scheme_tron_mainnet_usdt() -> None:
    """TRON mainnet USDT defaults to exact_permit (exact_gasfree stays opt-in)."""
    scheme = pick_scheme("tron:mainnet", "USDT")
    assert scheme == "exact_permit"


def test_tron_keeps_gasfree_as_second_choice() -> None:
    """exact_gasfree must remain registered on every TRON entry so that
    explicitly passing --scheme exact_gasfree still resolves successfully."""
    for net in ("tron:mainnet", "tron:nile", "tron:shasta"):
        usdt_schemes = SCHEME_TABLE[net]["USDT"]
        assert "exact_gasfree" in usdt_schemes, (
            f"{net} USDT must still list exact_gasfree as an opt-in fallback"
        )
        assert usdt_schemes[0] == "exact_permit", (
            f"{net} USDT first choice must be exact_permit (default)"
        )


def test_pick_scheme_bsc_testnet_usdt() -> None:
    """Test scheme picking for BSC testnet USDT."""
    scheme = pick_scheme("eip155:97", "USDT")
    assert scheme == "exact_permit"


def test_pick_scheme_unknown_network() -> None:
    """Test scheme picking for unknown network."""
    scheme = pick_scheme("unknown:network", "USDT")
    assert scheme is None


def test_pick_scheme_unknown_token() -> None:
    """Test scheme picking for unknown token on known network."""
    scheme = pick_scheme("eip155:97", "UNKNOWN_TOKEN")
    assert scheme is None


def test_is_known_scheme_valid() -> None:
    """Test validation of known schemes."""
    assert is_known_scheme("exact") is True
    assert is_known_scheme("exact_permit") is True
    assert is_known_scheme("exact_gasfree") is True


def test_is_known_scheme_invalid() -> None:
    """Test validation of unknown schemes."""
    assert is_known_scheme("unknown_scheme") is False
    assert is_known_scheme("fake") is False
    assert is_known_scheme("") is False
