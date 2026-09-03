"""The seam between QUAKE_LEGACY and THE_PANTHEON.

QUAKE_LEGACY knows the game: the demo format, the netcode, the camera, the
whole cinematic vocabulary. THE_PANTHEON needs none of that. It needs a clip
and enough portable metadata to run a blind vote on it. So this module is
deliberately the narrowest thing that could work -- a ten-second MP4 and a
JSON line -- and it is the ONLY thing that crosses.

Nothing about the public platform is built here. No website, no voting, no
community score, no FFmpeg montage grammar. Those belong in the other
project, and keeping them out of this one is the point of having a seam at
all.

TWO WINDOWS, TWO PURPOSES. The internal review clip is +/-3s and stays that
way: the director is judging a moment they already know, and six seconds is
enough to place it. The public clip is +/-5s, because a stranger needs
run-up to understand what they are watching before they score it. These
numbers are not a setting to be unified -- they answer different questions.

WHAT IS NOT BURNED IN. No name, no rank, no score, no director tag, no
PANTHEON overlay of any kind. A voting clip that tells you whose play it is
has already voted for you. The native in-game HUD is whatever the engine
drew at the time and is left alone; that is footage, not editorialising.

IDENTITY TRAVELS AS DATA, NOT AS PIXELS. The manifest carries the actor's
name so THE_PANTHEON can reveal it after a vote. Pixels cannot be un-shown,
a field can be withheld, and that difference is the whole disclosure model.

PUBLICATION IS NOT ASSUMED. Ten years of archive footage was not recorded
with the internet in mind. `public_eligible` defaults to False on every
exported row and only the user can change that.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_DIR = REPO_ROOT / "creative_suite" / "database"
RECOGNITION_DB = DB_DIR / "frag_recognition.db"
FFMPEG = REPO_ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffmpeg.exe"
FFPROBE = REPO_ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffprobe.exe"

# The exchange directory. Not `output/` -- that path carries its own git
# repository for flow-plan history (rule CS-3) and public media has no
# business in it. Gitignored, and the manifest is written beside the clips so
# a copy of this folder is a complete, self-describing handoff.
EXPORT_ROOT = REPO_ROOT / "exchange" / "pantheon"
CLIP_DIR_NAME = "clips"
MANIFEST_NAME = "clips.jsonl"

EXPORT_VERSION = "pantheon-clip-v1"
GAME = "quake_live"

# The public window. Five seconds of run-up so a stranger can read the play,
# five after so they see the consequence.
PUBLIC_PRE_MS = 5000
PUBLIC_POST_MS = 5000
PUBLIC_DURATION_MS = PUBLIC_PRE_MS + PUBLIC_POST_MS

# A batch cannot quietly become the whole corpus. Ask for more than this and
# it is refused, not truncated -- a silent truncation is how you discover
# later that half your export never happened.
MAX_BATCH = 50

# How long a clip waits for the shared capture lock before the export gives
# up on it. Long enough to sit behind one review proxy, short enough that a
# stuck worker does not hold a batch open all afternoon.
LOCK_WAIT_S = 300.0
LOCK_POLL_S = 5.0

# Disclosure defaults. Conservative, and the user moves them, not the code.
ELIGIBLE_DEFAULT = False
VISIBILITY_AFTER_VOTE = "AFTER_VOTE"

_COLOR = re.compile(r"\^[0-9a-zA-Z]")


class ExportRefused(Exception):
    """A batch that would be too large, or a request with no usable source."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def strip_colors(name: str | None) -> str | None:
    if not name:
        return None
    return _COLOR.sub("", name).strip() or None


@dataclass(frozen=True)
class ExportCandidate:
    """One moment worth showing a stranger.

    Sourced from a canonical kill event. `is_actor_pov` is the field that
    stops a clanmate's frag from being sold as their own first-person view:
    when the actor is not the recorder, this footage is somebody else's
    camera pointed at them.
    """
    external_source_id: str          # stable, opaque, safe to publish
    content_hash: str                # private provenance -- never published
    event_time_ms: int
    event_type: str
    mod: int | None
    weapon: str | None
    map_name: str | None
    actor_display_name: str | None
    actor_identity_id: str | None
    recorder_display_name: str | None
    is_actor_pov: bool
    machine_score: float | None
    machine_score_version: str | None
    demo_name: str                   # local only, never enters the manifest
    killer_client: int | None = None
    round_no: int | None = None


def _conn(db: Path = RECOGNITION_DB) -> sqlite3.Connection:
    c = sqlite3.connect(db, timeout=60)
    c.row_factory = sqlite3.Row
    return c


def external_id(content_hash: str, event_time_ms: int, killer: int | None,
                victim: int | None) -> str:
    """A public identifier that leaks nothing.

    The demo's content hash identifies the file, and a file name would
    identify a person -- demo filenames embed aliases. So the public id is a
    digest, and the mapping back to a demo stays in this repository.
    """
    raw = f"{content_hash}|{event_time_ms}|{killer}|{victim}"
    return "ql_" + hashlib.sha256(raw.encode()).hexdigest()[:20]


def candidates_from_kill_events(where: str = "killer_class='PLAYER'",
                                params: Iterable[Any] = (),
                                limit: int = MAX_BATCH,
                                db: Path = RECOGNITION_DB
                                ) -> list[ExportCandidate]:
    """Query the canonical kill events for exportable moments."""
    sql = f"""SELECT k.*, s.demo_name FROM kill_events_v1 k
              JOIN scanned_demos s ON s.content_hash = k.content_hash
              WHERE {where} ORDER BY k.kill_event_id LIMIT ?"""
    out: list[ExportCandidate] = []
    with _conn(db) as c:
        for r in c.execute(sql, (*params, int(limit))):
            out.append(ExportCandidate(
                external_source_id=external_id(
                    r["content_hash"], r["server_time_ms"],
                    r["killer_client"], r["victim_client"]),
                content_hash=r["content_hash"],
                event_time_ms=int(r["server_time_ms"]),
                event_type="FRAG",
                mod=r["mod"],
                weapon=r["mod_name"],
                map_name=r["map"],
                actor_display_name=strip_colors(r["killer_name_raw"]),
                actor_identity_id=r["killer_identity_id"],
                recorder_display_name=None,
                is_actor_pov=bool(r["is_recorder_killer"]),
                machine_score=None,
                machine_score_version=None,
                demo_name=r["demo_name"],
                killer_client=r["killer_client"],
                round_no=r["round"]))
    return out


def attach_machine_scores(cands: list[ExportCandidate],
                          db: Path = RECOGNITION_DB) -> list[ExportCandidate]:
    """Fill in the recogniser's score where one genuinely exists.

    It exists only for the recorder's own frags: every feature behind it was
    computed from the recorder's player state. A clanmate's frag seen from a
    foreign camera has no comparable score, and it is left None rather than
    filled with a number that would not mean the same thing.
    """
    out = []
    with _conn(db) as c:
        for cand in cands:
            score = ver = None
            if cand.is_actor_pov:
                row = c.execute(
                    "SELECT highlight_score, recognition_version FROM recognized_frags"
                    " WHERE content_hash=? AND server_time_ms=? LIMIT 1",
                    (cand.content_hash, cand.event_time_ms)).fetchone()
                if row is not None:
                    score = row["highlight_score"]
                    ver = f"recognition-v{row['recognition_version']}"
            out.append(ExportCandidate(**{**asdict(cand),
                                          "machine_score": score,
                                          "machine_score_version": ver}))
    return out


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def probe_duration_ms(path: Path) -> int | None:
    if not FFPROBE.exists():
        return None
    try:
        r = subprocess.run(
            [str(FFPROBE), "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(path)],
            capture_output=True, text=True, timeout=60)
        return int(float(r.stdout.strip()) * 1000)
    except (ValueError, OSError, subprocess.SubprocessError):
        return None


def _stats_block(cand: ExportCandidate) -> dict[str, Any]:
    """Measurements a voter cannot see in ten seconds of footage.

    A failure here costs the clip its stats, not the export -- an unreadable
    attribute blob is not a reason to lose a captured clip, and the empty
    availability field says the numbers are absent.
    """
    from creative_suite.engine import clip_stats
    try:
        return clip_stats.for_clip(cand.content_hash, cand.event_time_ms,
                                   cand.killer_client, cand.round_no,
                                   cand.is_actor_pov)
    except (sqlite3.Error, ValueError, TypeError, KeyError) as exc:
        return {"stats": {}, "machine_subscores": {},
                "stats_availability": "UNAVAILABLE",
                "stats_note": f"{type(exc).__name__}: {exc}"}


def manifest_row(cand: ExportCandidate, clip_rel: str, clip_hash: str,
                 event_offset_ms: int, duration_ms: int | None,
                 note: str | None = None,
                 public_eligible: bool = ELIGIBLE_DEFAULT) -> dict[str, Any]:
    """The portable record. Everything THE_PANTHEON needs, nothing local.

    `source_demo_ref` is the demo's content hash: enough for this repository
    to find the demo again, and useless to anyone who does not already hold
    the corpus. No filesystem path appears anywhere in this row.
    """
    return {
        "export_version": EXPORT_VERSION,
        "exported_at": _now(),
        "external_source_id": cand.external_source_id,
        "game": GAME,
        "event_type": cand.event_type,
        "event_time_ms": cand.event_time_ms,
        "event_offset_ms": event_offset_ms,
        "duration_ms": duration_ms,
        "clip_path": clip_rel,
        "content_hash": clip_hash,
        "map": cand.map_name,
        "weapon": cand.weapon,
        "mod": cand.mod,
        "actor_display_name": cand.actor_display_name,
        "actor_identity_id": cand.actor_identity_id,
        "recorder_display_name": cand.recorder_display_name,
        "is_actor_pov": cand.is_actor_pov,
        "machine_score": cand.machine_score,
        "machine_score_version": cand.machine_score_version,
        **_stats_block(cand),
        "source_note": note,
        "source_demo_ref": cand.content_hash,
        "source_provenance": "QUAKE_LEGACY/RECORDED_OBSERVED/DEMO_EV_OBITUARY",
        # Disclosure is THE_PANTHEON's to make, but the safe answer travels
        # with the clip so an unconfigured importer cannot publish by default.
        "public_eligible": bool(public_eligible),
        "identity_visibility": VISIBILITY_AFTER_VOTE,
        "overlays_added": [],          # explicitly none; see module docstring
    }


def _capture(cand: ExportCandidate, start_ms: int, end_ms: int,
             dest: Path) -> None:
    """Produce the clip. Same reliable capture route the review proxy uses.

    Deliberately plain: no PANTHEON camera, no world effects, no
    choreography. The viewer is judging the play, and anything this module
    added to the frame would be judged instead.
    """
    if os.getenv("CS_EXPORT_MOCK"):
        dur = max(0.5, (end_ms - start_ms) / 1000.0)
        subprocess.run(
            [str(FFMPEG), "-y", "-f", "lavfi", "-i",
             f"testsrc=size=320x180:rate=30", "-f", "lavfi", "-i",
             "sine=frequency=440", "-t", f"{dur:.3f}", "-c:v", "libx264",
             "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
             "-movflags", "+faststart", "-c:a", "aac", "-b:a", "160k",
             str(dest)], check=True, capture_output=True, timeout=300)
        return

    # WolfcamQL is one-at-a-time, and the review proxy worker drives it too.
    # Without the shared marker the two would launch the engine concurrently
    # and fight over the same staging directory and demo file locks.
    from creative_suite.engine import review_proxy as rp
    waited = 0.0
    while not rp._try_acquire_lock():
        if waited >= LOCK_WAIT_S:
            raise ExportRefused(
                "another capture holds output/demo_v2/_capture.lock; "
                "the review proxy worker is busy -- try again later")
        time.sleep(LOCK_POLL_S)
        waited += LOCK_POLL_S
    try:
        _capture_locked(cand, start_ms, end_ms, dest)
    finally:
        rp._release_lock()


def _capture_locked(cand: ExportCandidate, start_ms: int, end_ms: int,
                    dest: Path) -> None:
    from creative_suite.engine import wolfcam_capture as wc
    wc.ensure_install()
    demo_path = REPO_ROOT / "demos" / cand.demo_name
    if not demo_path.exists():
        demo_path = REPO_ROOT / "demos" / f"{cand.demo_name}.dm_73"
    if not demo_path.exists():
        raise ExportRefused(f"demo file missing for {cand.external_source_id}")
    safe = wc.stage_demo(demo_path)
    clip_name = f"px_{cand.external_source_id[3:19]}"
    res = wc.capture_demo(safe, [{"clip_name": clip_name,
                                  "start_ms": start_ms, "end_ms": end_ms}])
    if not res["ok"]:
        raise ExportRefused(res.get("error") or "wolfcam capture failed")
    avi = Path(res["avis"][clip_name])
    try:
        subprocess.run(
            [str(FFMPEG), "-y", "-i", str(avi), "-c:v", "libx264",
             "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p",
             "-movflags", "+faststart", "-c:a", "aac", "-b:a", "192k",
             str(dest)], check=True, capture_output=True, timeout=1800)
    finally:
        try:
            if avi.exists():
                avi.unlink()          # the AVI is scratch, the MP4 ships
        except OSError:
            pass


def export(cands: list[ExportCandidate], root: Path = EXPORT_ROOT,
           note: str | None = None, public_eligible: bool = ELIGIBLE_DEFAULT,
           overwrite: bool = False) -> dict[str, Any]:
    """Export a batch. Returns a summary; the manifest is on disk.

    Refuses an oversized batch rather than trimming it. Failures are counted
    and named, never swallowed -- a partial export that reports success is
    worse than one that stops.
    """
    if len(cands) > MAX_BATCH:
        raise ExportRefused(
            f"batch of {len(cands)} exceeds MAX_BATCH={MAX_BATCH}; "
            "export is a deliberate act, not a corpus dump")
    if not cands:
        raise ExportRefused("nothing to export")
    clips = root / CLIP_DIR_NAME
    clips.mkdir(parents=True, exist_ok=True)
    manifest = root / MANIFEST_NAME
    existing = set()
    if manifest.exists() and not overwrite:
        for line in manifest.read_text(encoding="utf-8").splitlines():
            if line.strip():
                existing.add(json.loads(line)["external_source_id"])
    elif overwrite and manifest.exists():
        manifest.unlink()

    written, skipped, failures = [], [], []
    t0 = time.monotonic()
    for cand in cands:
        if cand.external_source_id in existing:
            skipped.append(cand.external_source_id)
            continue
        start_ms = max(0, cand.event_time_ms - PUBLIC_PRE_MS)
        end_ms = cand.event_time_ms + PUBLIC_POST_MS
        # If the demo does not reach five seconds before the event, the clip
        # is shorter and the manifest says exactly where the event landed
        # rather than claiming a centred 5000.
        offset = cand.event_time_ms - start_ms
        rel = f"{CLIP_DIR_NAME}/{cand.external_source_id}.mp4"
        dest = clips / f"{cand.external_source_id}.mp4"
        try:
            _capture(cand, start_ms, end_ms, dest)
            row = manifest_row(cand, rel, file_hash(dest), offset,
                               probe_duration_ms(dest), note, public_eligible)
            with manifest.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row) + "\n")
            written.append(row)
        except Exception as exc:                               # noqa: BLE001
            failures.append({"external_source_id": cand.external_source_id,
                             "error": f"{type(exc).__name__}: {exc}"})
            if dest.exists():
                dest.unlink()
    return {"root": str(root), "manifest": str(manifest),
            "written": len(written), "skipped": len(skipped),
            "failed": len(failures), "failures": failures,
            "elapsed_s": round(time.monotonic() - t0, 1),
            "rows": written}


def refresh_manifest(root: Path = EXPORT_ROOT,
                     db: Path = RECOGNITION_DB) -> dict[str, Any]:
    """Rebuild manifest rows for clips already on disk.

    Metadata improves; captured media does not. When a new stat becomes
    available there is no reason to spend forty seconds of wolfcam per clip
    to attach it. Only rows whose media is still present are rebuilt -- a
    manifest entry without its clip is dropped rather than carried.
    """
    manifest = root / MANIFEST_NAME
    if not manifest.exists():
        return {"refreshed": 0, "dropped": 0}
    old = [json.loads(x) for x in
           manifest.read_text(encoding="utf-8").splitlines() if x.strip()]
    by_id = {r["external_source_id"]: r for r in old}
    every = candidates_from_kill_events(limit=1_000_000, db=db)
    cands = {c.external_source_id: c for c in every if c.external_source_id in by_id}
    cands = {c.external_source_id: c
             for c in attach_machine_scores(list(cands.values()), db=db)}
    rows, dropped = [], 0
    for r in old:
        sid = r["external_source_id"]
        clip = root / CLIP_DIR_NAME / f"{sid}.mp4"
        cand = cands.get(sid)
        if not clip.exists() or cand is None:
            dropped += 1
            continue
        rows.append(manifest_row(
            cand, r["clip_path"], r["content_hash"], r["event_offset_ms"],
            r["duration_ms"], r.get("source_note"),
            bool(r.get("public_eligible", ELIGIBLE_DEFAULT))))
    manifest.write_text("".join(json.dumps(x) + chr(10) for x in rows),
                        encoding="utf-8")
    return {"refreshed": len(rows), "dropped": dropped}


def export_summary(root: Path = EXPORT_ROOT) -> dict[str, Any]:
    """What is sitting in the exchange directory right now."""
    manifest = root / MANIFEST_NAME
    if not manifest.exists():
        return {"exists": False, "clips": 0, "public_eligible": 0}
    rows = [json.loads(x) for x in
            manifest.read_text(encoding="utf-8").splitlines() if x.strip()]
    return {
        "exists": True,
        "root": str(root),
        "clips": len(rows),
        "public_eligible": sum(1 for r in rows if r.get("public_eligible")),
        "actor_pov": sum(1 for r in rows if r.get("is_actor_pov")),
        "observed_not_pov": sum(1 for r in rows if not r.get("is_actor_pov")),
        "export_versions": sorted({r.get("export_version") for r in rows}),
        "duration_ms": sorted({r.get("duration_ms") for r in rows}),
    }
