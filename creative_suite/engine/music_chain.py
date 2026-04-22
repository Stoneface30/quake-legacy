"""creative_suite/engine/music_chain.py — Music beatmatch scoring for NLE.

Scores each track in the music library against:
  - Video body BPM (40%)
  - Duration coverage of the part (30%)
  - Chain score vs previous track (30%)

BPM/duration are read from `engine/music/library/metadata.json` sidecar when
present. MusicLibrary.json has no BPM field — detection via librosa is future.
Missing BPM fields default to neutral 0.5 score so the UI still works.

Returns top-N ranked candidates per role slot.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _bpm_match(track_bpm: float | None, video_bpm: float | None) -> float:
    if not track_bpm or not video_bpm or video_bpm == 0:
        return 0.5
    return max(0.0, 1.0 - abs(track_bpm - video_bpm) / video_bpm)


def _duration_score(track_dur: float | None, body_dur: float | None) -> float:
    if not track_dur or not body_dur or body_dur == 0:
        return 0.5
    ratio = track_dur / body_dur
    return 1.0 if ratio >= 1.0 else ratio


def _chain_score(prev_track: dict | None, candidate: dict) -> float:
    """BPM proximity heuristic — score 1.0 within ±5 BPM, linear decay to 0 at ±30."""
    if prev_track is None:
        return 0.5
    prev_bpm = prev_track.get("bpm")
    cand_bpm = candidate.get("bpm")
    if not prev_bpm or not cand_bpm:
        return 0.5
    delta = abs(prev_bpm - cand_bpm)
    return max(0.0, 1.0 - delta / 30.0)


def score_tracks(tracks: list[dict[str, Any]], body_dur: float,
                 video_bpm: float | None,
                 prev_track: dict | None = None,
                 top_n: int = 10) -> list[dict[str, Any]]:
    """Score and rank tracks for a given part + role slot."""
    scored = []
    for t in tracks:
        bpm_s   = _bpm_match(t.get("bpm"), video_bpm)
        dur_s   = _duration_score(t.get("duration_s"), body_dur)
        chain_s = _chain_score(prev_track, t)
        total   = bpm_s * 0.40 + dur_s * 0.30 + chain_s * 0.30
        scored.append({**t, "score": round(total, 3),
                       "score_bpm": round(bpm_s, 3),
                       "score_dur": round(dur_s, 3),
                       "score_chain": round(chain_s, 3)})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_n]


def load_library(library_dir: Path) -> list[dict[str, Any]]:
    """Scan engine/music/library/ and build a track list.

    Reads BPM and duration from `metadata.json` sidecar if present.
    Returns empty list if directory does not exist.
    """
    if not library_dir.exists():
        return []

    meta: dict = {}
    meta_file = library_dir / "metadata.json"
    if meta_file.exists():
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    _AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}
    tracks = []
    for f in sorted(library_dir.iterdir()):
        if f.suffix.lower() not in _AUDIO_EXTS:
            continue
        stem = f.stem
        if "__" in stem:
            parts = stem.split("__", 1)
            artist = parts[0].replace("_", " ").title()
            title  = parts[1].replace("_", " ").title()
        else:
            artist = ""
            title  = stem.replace("_", " ").title()
        m = meta.get(f.name, {})
        tracks.append({
            "filename":   f.name,
            "artist":     artist,
            "title":      title,
            "bpm":        m.get("bpm"),
            "duration_s": m.get("duration_s"),
        })
    return tracks
