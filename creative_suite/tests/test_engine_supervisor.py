# creative_suite/tests/test_engine_supervisor.py
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

from creative_suite.engine.supervisor import EngineSupervisor


@pytest.mark.asyncio
async def test_supervisor_sends_seek_to_stdin(tmp_path: Path) -> None:
    script = tmp_path / "echo.py"
    script.write_text(
        "import sys, pathlib\n"
        "p = pathlib.Path(sys.argv[1])\n"
        "for line in sys.stdin:\n"
        "    with p.open('a') as f: f.write(line)\n",
        encoding="utf-8",
    )
    log = tmp_path / "stdin.log"
    sup = EngineSupervisor(
        engine_cmd=[sys.executable, str(script), str(log)],
        thumb_dir=tmp_path / "thumbs",
        mock_grab=True,
    )
    await sup.start()
    try:
        await sup.seek(ms=343500)
        await asyncio.sleep(0.3)
        assert "seekclock 5:43.5" in log.read_text(encoding="utf-8")
    finally:
        await sup.stop()
