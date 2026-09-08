"""Non-destructive process observation for capture lock holders."""
from __future__ import annotations

import os


def process_alive(pid: int) -> bool:
    """Treat inaccessible processes as alive, so capture locks fail closed.

    os.kill(pid, 0) is a POSIX probe. On Windows it calls TerminateProcess;
    querying a process handle avoids sending any signal to the owner.
    """
    if pid <= 0:
        return False
    if os.name != "nt":
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True

    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE only
    if not handle:
        # ERROR_INVALID_PARAMETER means the PID does not exist. Access
        # denial or another query failure must not authorize lock takeover.
        return ctypes.get_last_error() != 87
    try:
        return kernel.WaitForSingleObject(handle, 0) != 0  # WAIT_OBJECT_0 = exited
    finally:
        kernel.CloseHandle(handle)
