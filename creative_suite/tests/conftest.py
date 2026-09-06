"""Shared pytest fixtures for creative_suite tests."""


# -- HARD GUARANTEE: the test suite never creates a game process -----------
# Every launch site asks render_permit, which denies by default; this is the
# belt to that brace. A Popen / create_subprocess_exec whose argv names a
# game executable fails the test instead of putting a window on the desktop.
import asyncio as _asyncio
import subprocess as _subprocess

import pytest as _pytest

_GAME_EXES = ("wolfcamql", "quakelive", "quake3", "ioquake3")


def _argv_names_a_game(args) -> bool:
    try:
        first = args[0] if isinstance(args, (list, tuple)) else args
        return any(g in str(first).lower() for g in _GAME_EXES)
    except Exception:
        return False


@_pytest.fixture(autouse=True, scope="session")
def _no_game_process_ever():
    orig_popen = _subprocess.Popen
    orig_spawn = _asyncio.create_subprocess_exec

    class GuardedPopen(orig_popen):
        def __init__(self, args, *a, **k):
            if _argv_names_a_game(args):
                raise AssertionError(f"test tried to launch a game process: {args!r}")
            super().__init__(args, *a, **k)

    async def guarded_spawn(program, *args, **kwargs):
        if _argv_names_a_game(program):
            raise AssertionError(f"test tried to launch a game process: {program!r}")
        return await orig_spawn(program, *args, **kwargs)

    _subprocess.Popen = GuardedPopen
    _asyncio.create_subprocess_exec = guarded_spawn
    try:
        yield
    finally:
        _subprocess.Popen = orig_popen
        _asyncio.create_subprocess_exec = orig_spawn
