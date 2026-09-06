"""Process observation must never send a terminating signal on Windows."""
import os
import subprocess
import sys

from creative_suite.engine.process_liveness import process_alive


def test_current_process_is_alive() -> None:
    assert process_alive(os.getpid())
    assert not process_alive(0)
    assert not process_alive(-1)


def test_observing_child_preserves_it_and_detects_exit() -> None:
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        assert process_alive(child.pid)
        assert child.poll() is None
    finally:
        child.terminate()
        child.wait(timeout=10)
    assert not process_alive(child.pid)
