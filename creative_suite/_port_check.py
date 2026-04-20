"""Atomic port-availability probe with helpful "who is holding it" diagnostics.

Used by `__main__._cmd_serve` to convert the generic `WinError 10048 /
EADDRINUSE` into a message that tells the operator exactly which PID to
kill. This closes the "stale uvicorn from 5 hours ago" footgun that keeps
biting after a bad Ctrl+C.

Public API:
    probe_port(host, port) -> int | None          # returns holding PID or None
    format_port_busy_message(host, port, pid) -> str
    describe_process(pid) -> str                   # "python 24656 (started 21:08)"

Design notes:
    - We bind+close a throwaway socket instead of trusting `psutil.net_connections`
      alone — the bind is the *authoritative* answer to "can uvicorn claim
      this port right now?". psutil is only consulted when the bind fails,
      to attribute the conflict to a PID for the error message.
    - `SO_EXCLUSIVEADDRUSE` on Windows and `SO_REUSEADDR=0` elsewhere mirror
      what uvicorn actually does, so the probe's verdict matches uvicorn's.
    - All psutil calls are wrapped in try/except — a missing process, an
      AccessDenied (common on Windows without elevation), or psutil itself
      being absent must NEVER turn a friendly error into a traceback.
"""
from __future__ import annotations

import platform
import socket
from datetime import datetime


def probe_port(host: str, port: int) -> int | None:
    """Return the PID holding `host:port`, or None if the port is free.

    A `None` return means uvicorn can bind successfully. A positive int
    means something else owns the socket; pass that PID to
    `format_port_busy_message` for a ready-to-print diagnostic.

    If the port is busy but psutil cannot attribute the owner (permission
    denied, process gone, psutil missing), returns -1 — still "busy",
    just "owner unknown". Callers should treat >=0 and -1 the same for
    the purpose of refusing to start.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Match uvicorn: no SO_REUSEADDR, so we fail if anyone else owns it.
        if platform.system() == "Windows":
            # SO_EXCLUSIVEADDRUSE = ~SO_REUSEADDR = -5 on Windows. Refuses
            # to steal the port from another listener even if that listener
            # set SO_REUSEADDR. The 0xFFFFFFFB form overflows Python's C
            # long — use the signed form.
            try:
                s.setsockopt(socket.SOL_SOCKET, ~socket.SO_REUSEADDR, 1)
            except OSError:
                # Older Windows builds don't expose it — no-op is fine.
                pass
        s.bind((host, port))
    except OSError:
        # Port busy. Try to name the owner.
        return _find_pid_listening_on(host, port)
    else:
        return None
    finally:
        s.close()


def _find_pid_listening_on(host: str, port: int) -> int:
    """Return the PID listening on `host:port`, or -1 if unknown."""
    try:
        import psutil  # type: ignore[import-untyped]
    except ImportError:
        return -1

    try:
        for conn in psutil.net_connections(kind="inet"):
            laddr = conn.laddr
            if not laddr:
                continue
            if laddr.port != port:
                continue
            # host='' on wildcard binds; match 127.0.0.1 against both
            # '127.0.0.1' and '0.0.0.0'.
            if host not in (laddr.ip, "0.0.0.0", ""):
                # If caller asked for 127.0.0.1 but this listener is on
                # a different interface, it's not the conflict we care about.
                if host == "127.0.0.1" and laddr.ip not in ("127.0.0.1", "0.0.0.0"):
                    continue
            if conn.status != psutil.CONN_LISTEN:
                continue
            if conn.pid is None:
                continue
            return int(conn.pid)
    except (psutil.AccessDenied, psutil.Error, OSError):
        return -1
    return -1


def describe_process(pid: int) -> str:
    """Human description of a PID — `"python 81816 (started 16:16:39)"`.

    Returns "unknown PID <n>" on any failure. Never raises.
    """
    if pid <= 0:
        return f"unknown (pid={pid})"
    try:
        import psutil  # type: ignore[import-untyped]

        proc = psutil.Process(pid)
        name = proc.name()
        try:
            started = datetime.fromtimestamp(proc.create_time()).strftime("%H:%M:%S")
            return f"{name} pid={pid} (started {started})"
        except (psutil.AccessDenied, OSError):
            return f"{name} pid={pid}"
    except Exception:
        return f"unknown pid={pid}"


def format_port_busy_message(host: str, port: int, pid: int) -> str:
    """Build the "port is busy" error block for operator consumption."""
    owner = describe_process(pid) if pid > 0 else "owner unknown (psutil denied or absent)"
    if platform.system() == "Windows":
        kill_hint = f'  powershell -c "Stop-Process -Id {pid} -Force"' if pid > 0 else \
                    f'  powershell -c "Get-NetTCPConnection -LocalPort {port} | ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force }}"'
    else:
        kill_hint = f"  kill {pid}" if pid > 0 else f"  lsof -ti :{port} | xargs kill"

    lines = [
        "",
        f"ERROR: port {port} on {host} is already in use.",
        f"       held by: {owner}",
        "",
        "To free it:",
        kill_hint,
        "",
        "Then retry `python -m creative_suite`.",
        "",
    ]
    return "\n".join(lines)


__all__ = [
    "probe_port",
    "describe_process",
    "format_port_busy_message",
]
