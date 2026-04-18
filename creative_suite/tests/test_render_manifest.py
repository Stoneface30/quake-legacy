import json
from pathlib import Path

from creative_suite.clips.parser import write_render_manifest


def test_manifest_written_next_to_mp4(tmp_path: Path) -> None:
    mp4 = tmp_path / "Part4.mp4"
    mp4.write_bytes(b"x")
    cl = tmp_path / "part04.txt"
    cl.write_text("file 'Demo (1) - 42.avi'\n")
    write_render_manifest(mp4, cl, extras={"encoder": "libx264"})
    manifest = tmp_path / "Part4.render_manifest.json"
    assert manifest.exists()
    data = json.loads(manifest.read_text())
    assert data["clip_list"] == str(cl)
    assert data["mp4"] == str(mp4)
    assert data["extras"]["encoder"] == "libx264"
    assert "written_at" in data
