"""Tests for Rule P1-Z v2 template-matching event recognition."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]  # G:/QUAKE_LEGACY/creative_suite
FFMPEG = ROOT / "tools" / "ffmpeg" / "ffmpeg.exe"
MANIFEST = ROOT / "engine" / "sound_templates" / "manifest.json"
TEMPLATES_RAW = ROOT / "engine" / "sound_templates" / "raw"


def _have_templates() -> bool:
    return MANIFEST.exists() and TEMPLATES_RAW.exists() and FFMPEG.exists()


@pytest.fixture(scope="module")
def tmp_wav_dir(tmp_path_factory) -> Path:
    return tmp_path_factory.mktemp("event_wavs")


def _tpl_wav(rel: str) -> Path:
    return TEMPLATES_RAW / rel


def _pad_wav(src: Path, dst: Path, lead_s: float = 0.3, tail_s: float = 0.3) -> None:
    """Pad a reference template with silence head/tail so we can validate
    that cross-correlation locates the transient at the right offset."""
    subprocess.check_call([
        str(FFMPEG), "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-t", f"{lead_s}", "-i", "anullsrc=r=22050:cl=mono",
        "-i", str(src),
        "-f", "lavfi", "-t", f"{tail_s}", "-i", "anullsrc=r=22050:cl=mono",
        "-filter_complex", "[0][1][2]concat=n=3:v=0:a=1[out]",
        "-map", "[out]", "-ar", "22050", "-ac", "1",
        str(dst),
    ])


@pytest.mark.skipif(not _have_templates(), reason="QL templates not available")
def test_rail_fire_recognized(tmp_wav_dir: Path) -> None:
    from creative_suite.engine import audio_onsets

    src = _tpl_wav("sound/weapons/railgun/railgf1a.wav")
    if not src.exists():
        pytest.skip(f"railgun template missing at {src}")
    dst = tmp_wav_dir / "rail_probe.wav"
    _pad_wav(src, dst, lead_s=0.5, tail_s=0.5)

    events = audio_onsets.recognize_game_events(dst)
    assert events, "expected at least one recognized event"
    types = {e.event_type for e in events}
    assert "rail_fire" in types, f"rail_fire not among recognized types: {types}"
    # Find the rail_fire event and check confidence + approx location.
    rail = next(e for e in events if e.event_type == "rail_fire")
    assert rail.confidence >= 0.7, f"rail conf too low: {rail.confidence}"
    # The transient should sit roughly at 0.5s + mid-template.
    assert 0.4 <= rail.t <= 2.0, f"rail time {rail.t}s out of expected band"


@pytest.mark.skipif(not _have_templates(), reason="QL templates not available")
def test_rocket_impact_recognized(tmp_wav_dir: Path) -> None:
    from creative_suite.engine import audio_onsets

    src = _tpl_wav("sound/weapons/rocket/rocklx1a.wav")
    if not src.exists():
        pytest.skip(f"rocket impact template missing at {src}")
    dst = tmp_wav_dir / "rocket_probe.wav"
    _pad_wav(src, dst, lead_s=0.3, tail_s=0.3)

    events = audio_onsets.recognize_game_events(dst)
    types = {e.event_type for e in events}
    # We accept either rocket_fire or rocket_impact since the envelopes
    # overlap; the key assertion is SOMETHING rocket-ish wins.
    assert "rocket_impact" in types or "rocket_fire" in types, \
        f"no rocket-family event in {types}"


@pytest.mark.skipif(not _have_templates(), reason="QL templates not available")
def test_player_death_recognized(tmp_wav_dir: Path) -> None:
    from creative_suite.engine import audio_onsets

    src = _tpl_wav("sound/player/sarge/death1.wav")
    if not src.exists():
        pytest.skip(f"sarge death template missing at {src}")
    dst = tmp_wav_dir / "death_probe.wav"
    _pad_wav(src, dst, lead_s=0.3, tail_s=0.3)

    events = audio_onsets.recognize_game_events(dst)
    types = {e.event_type for e in events}
    assert "player_death" in types, \
        f"player_death not detected among {types}"
    # player_death weight=1.0 so it should top the ranked list.
    assert events[0].event_type == "player_death"


def test_find_action_peak_v2_returns_tuple():
    """v2 API contract: returns (float|None, tag_str) even with bogus input."""
    from creative_suite.engine import audio_onsets

    # Non-existent file → graceful fallback to (None, 'NONE').
    peak, tag = audio_onsets.find_action_peak_v2("does_not_exist.wav")
    assert peak is None
    assert tag in {"NONE", "RECOGNITION_FAILED"}


def test_v1_api_preserved():
    """Legacy find_action_peak/find_action_peaks_per_clip remain callable."""
    from creative_suite.engine import audio_onsets
    assert callable(audio_onsets.find_action_peak)
    assert callable(audio_onsets.find_action_peaks_per_clip)
