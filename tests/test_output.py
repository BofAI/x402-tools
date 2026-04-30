"""Tests for output module."""

import json
from io import StringIO
from unittest.mock import patch

from bankofai.x402_cli.output import emit, emit_json, emit_human, OutputMode


def test_emit_json_success() -> None:
    """Test JSON envelope for successful output."""
    with patch("builtins.print") as mock_print:
        emit(
            command="test",
            result={"status": "ok"},
            mode="json",
            network="eip155:97",
            scheme="exact_permit",
        )

        output = mock_print.call_args[0][0]
        parsed = json.loads(output)

        assert parsed["ok"] is True
        assert parsed["command"] == "test"
        assert parsed["network"] == "eip155:97"
        assert parsed["scheme"] == "exact_permit"
        assert parsed["result"]["status"] == "ok"


def test_emit_json_error() -> None:
    """Test JSON envelope for error output."""
    with patch("builtins.print") as mock_print:
        emit(
            command="test",
            error={"code": "TEST_ERROR", "message": "Test failed"},
            mode="json",
        )

        output = mock_print.call_args[0][0]
        parsed = json.loads(output)

        assert parsed["ok"] is False
        assert parsed["command"] == "test"
        assert parsed["error"]["code"] == "TEST_ERROR"
        assert "result" not in parsed


def test_emit_human_success() -> None:
    """Test human-readable output for success."""
    with patch("sys.stdout.write") as mock_write:
        emit_human(
            command="server",
            result={"pay_url": "http://localhost:4020/pay"},
            network="eip155:97",
            scheme="exact_permit",
        )

        # Check that output was written
        assert mock_write.called


def test_emit_human_error() -> None:
    """Test human-readable output for errors."""
    with patch("sys.stderr.write") as mock_write:
        emit_human(
            command="server",
            error={"code": "IO_ERROR", "message": "Server failed to start"},
        )

        # Check that error was written to stderr
        assert mock_write.called
        call_args = [str(call) for call in mock_write.call_args_list]
        output = "".join([c for c in call_args if "call" not in str(c)])
        assert "IO_ERROR" in output or any("IO_ERROR" in str(c) for c in mock_write.call_args_list)
