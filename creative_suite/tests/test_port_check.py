"""Unit tests for _port_check — port-availability probe + error messaging."""
from __future__ import annotations

import socket

import pytest

from creative_suite._port_check import (
    describe_process,
    format_port_busy_message,
    probe_port,
)


def _find_free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class TestProbePort:
    def test_free_port_returns_none(self) -> None:
        port = _find_free_port()
        assert probe_port("127.0.0.1", port) is None

    def test_busy_port_returns_owning_pid(self) -> None:
        """When something is listening, probe returns the PID (own PID here)."""
        import os

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        port = s.getsockname()[1]
        try:
            result = probe_port("127.0.0.1", port)
            # psutil may return -1 on AccessDenied, but must not return None
            # since the port IS busy. Either the real PID or -1 is acceptable.
            assert result is not None, "busy port must not report as free"
            if result > 0:
                assert result == os.getpid(), (
                    f"expected own pid {os.getpid()}, got {result}"
                )
        finally:
            s.close()

    def test_probe_does_not_leak_socket(self) -> None:
        """Calling probe 50× on a free port must not exhaust the OS handle table."""
        port = _find_free_port()
        for _ in range(50):
            assert probe_port("127.0.0.1", port) is None


class TestDescribeProcess:
    def test_own_pid_describes_something(self) -> None:
        import os

        s = describe_process(os.getpid())
        # Should at least include our PID. Name varies (python, python.exe, pytest).
        assert str(os.getpid()) in s

    def test_bogus_pid_does_not_raise(self) -> None:
        s = describe_process(-1)
        assert "pid=-1" in s

    def test_unlikely_pid_does_not_raise(self) -> None:
        # PID 9_999_999 almost certainly doesn't exist.
        s = describe_process(9_999_999)
        assert "pid=" in s  # whatever it says, it must not raise


class TestFormatPortBusyMessage:
    def test_message_contains_host_port_and_owner(self) -> None:
        msg = format_port_busy_message("127.0.0.1", 8765, 12345)
        assert "8765" in msg
        assert "127.0.0.1" in msg
        assert "12345" in msg

    def test_message_with_unknown_owner(self) -> None:
        msg = format_port_busy_message("127.0.0.1", 8765, -1)
        assert "8765" in msg
        # When PID is unknown, must still print a usable kill hint.
        assert "Stop-Process" in msg or "kill" in msg

    def test_message_has_retry_instruction(self) -> None:
        msg = format_port_busy_message("127.0.0.1", 8765, 12345)
        assert "creative_suite" in msg

    @pytest.mark.parametrize("pid", [0, -1, 1, 99999])
    def test_message_never_raises_on_odd_pids(self, pid: int) -> None:
        msg = format_port_busy_message("127.0.0.1", 8765, pid)
        assert isinstance(msg, str)
        assert len(msg) > 0
