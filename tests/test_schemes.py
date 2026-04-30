"""Tests for schemes module."""

from bankofai.x402_cli.schemes import pick_scheme, is_known_scheme


def test_pick_scheme_tron_nile_usdt() -> None:
    """Test scheme picking for TRON Nile USDT."""
    scheme = pick_scheme("tron:nile", "USDT")
    assert scheme == "exact_gasfree"


def test_pick_scheme_tron_mainnet_usdt() -> None:
    """Test scheme picking for TRON mainnet USDT."""
    scheme = pick_scheme("tron:mainnet", "USDT")
    assert scheme == "exact_gasfree"


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
