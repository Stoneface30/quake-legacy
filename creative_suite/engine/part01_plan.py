"""Part01 edit-plan engine for the V2 fragmovie (deterministic, reproducible).

Builds an ordered segment list where every frag chain is placed so its PRIMARY
hit lands ON a music beat (HITS ARE BEATS — reuse of hit_to_beat.place_clip;
no audio inference, the ledger's frag_offsets_ms are parser truth).

Era grammar (docs/reference/fragmovie-effect-research.md):
  * default transition is the HARD CUT;
  * at most MAX_NON_HARD_CUTS non-hard transitions per Part;
  * dissolves stay <= 0.4 s (we ship a single 300 ms recipe).

Audio hard rules (CLAUDE.md P1-G): music at ONE fixed level (MUSIC_GAIN), no
sidechain ducking anywhere — sync is achieved by placing ACTION on the music.

Determinism: same inputs -> same plan. edit_plan_id = sha256 of the canonical
plan JSON with volatile keys (created_at) excluded.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from creative_suite.engine import part_rhythm
from creative_suite.engine.hit_to_beat import place_clip

# DATA, not code: under a worktree these differ, and opening a
# database beneath the wrong one silently CREATES an empty file
# rather than failing. See engine.pantheon.store.
from engine.pantheon.store import data_root as _data_root
REPO_ROOT = _data_root()
PART01_DIR = REPO_ROOT / "output" / "demo_v2" / "part01"
DEFAULT_MUSIC_DB = REPO_ROOT / "creative_suite" / "database" / "music_analysis.db"
DEFAULT_CINEMATIC_DB = REPO_ROOT / "creative_suite" / "database" / "cinematic.db"
DEFAULT_SHORTLIST_CSV = REPO_ROOT / "output" / "demo_v2" / "music_shortlist.csv"

PART_NAME = "part01"

# ---- audio contract (P1-G: ONE fixed music level, never ducked) -------------
MUSIC_GAIN = 0.55        # fixed music bed level for the whole body
GAME_AUDIO_GAIN = 0.9    # game foreground level
# NOTE: no sidechain, no compand, no level-following constants exist here on
# purpose. Any "duck" additions violate P1-G and must be rejected in review.

# ---- era grammar ------------------------------------------------------------
ALLOWED_TRANSITIONS = ("hard_cut", "dissolve_300ms", "impact_cut")
DEFAULT_TRANSITION = "hard_cut"
MAX_NON_HARD_CUTS = 4
DISSOLVE_S = 0.300       # <= 0.4 s per research doc / P1-H

# ---- placement --------------------------------------------------------------
MIN_LEAD_S = 1.5         # minimum pre-hit context kept ahead of the primary
MAX_HEAD_TRIM_S = 2.5    # seam trim budget (P1-S spirit): clips play full
                         # length; only a small head trim absorbs beat snap
TARGET_DURATION_S = (270.0, 330.0)

# ---- effect anti-fatigue ----------------------------------------------------
MAX_EFFECT_USES_PER_PART = 3


# =============================================================================
# Music
# =============================================================================

def _extend_grid(points: list[float], duration_s: float,
                 interval_s: float) -> tuple[list[float], bool]:
    """Extend an analysed grid to cover the full track duration.

    music_analysis.db grids come from a fixed-length analysis excerpt, so on
    long tracks they stop well before the end. The tempo is measured and
    stable, so we extrapolate at `interval_s` — deterministic, and flagged so
    downstream consumers know the tail is GRID_EXTRAPOLATED, not measured.
    """
    if not points or interval_s <= 0:
        return points, False
    out = list(points)
    extended = False
    t = out[-1] + interval_s
    while t <= duration_s:
        out.append(round(t, 4))
        extended = True
        t += interval_s
    return out, extended


def load_song(content_id: str, music_db_path: Path | str | None = None) -> dict:
    """Load one analysed song: beats/downbeats/bpm/duration.

    Downbeats are BAR_GRID_ESTIMATE only — consumed as a mild bonus by
    hit_to_beat, never a hard constraint. Grids shorter than the track are
    extrapolated at the measured tempo (see _extend_grid).
    """
    db = Path(music_db_path) if music_db_path else DEFAULT_MUSIC_DB
    conn = sqlite3.connect(db)
    try:
        row = conn.execute(
            "SELECT content_id, name, path, bpm, duration_s, beat_times, "
            "downbeats FROM songs WHERE content_id = ?",
            (content_id,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        raise KeyError(f"song not found in music_analysis.db: {content_id}")
    bpm = float(row[3])
    duration_s = float(row[4])
    beats = json.loads(row[5])
    bar_grid = json.loads(row[6]) if row[6] else []
    beat_interval = 60.0 / bpm if bpm > 0 else 0.0
    beats, ext_b = _extend_grid(beats, duration_s, beat_interval)
    bar_grid, ext_g = _extend_grid(bar_grid, duration_s, beat_interval * 4)
    return {
        "content_id": row[0],
        "name": row[1],
        "path": row[2],
        "bpm": bpm,
        "duration_s": duration_s,
        "beats_s": beats,
        "bar_grid_estimate_s": bar_grid,
        "grid_extrapolated": bool(ext_b or ext_g),
    }


def pick_music_candidates(
    shortlist_csv: Path | str | None = None,
    n: int = 3,
    min_duration_s: float = 300.0,
    bpm_range: tuple[float, float] = (120.0, 150.0),
) -> list[dict]:
    """Top-N Part01 music candidates from the fragmovie shortlist.

    Filter: duration >= min_duration_s (Part01 target is 270-330 s so the
    track must cover the whole body without looping) and BPM inside the
    high-energy fragmovie band. Rank: shortlist frag_score, then onset_rate
    (busier grid = more anchor beats), then name for determinism. Duplicate
    files (same name, different case) are deduped keeping the higher onset.
    """
    path = Path(shortlist_csv) if shortlist_csv else DEFAULT_SHORTLIST_CSV
    rows: dict[str, dict] = {}
    with path.open(newline="", encoding="utf-8-sig") as fh:
        for rec in csv.DictReader(fh):
            try:
                dur = float(rec["duration_s"])
                bpm = float(rec["bpm"])
                score = float(rec["frag_score"])
                onset = float(rec["onset_rate"])
                rms_p90 = float(rec["rms_p90"])
            except (KeyError, ValueError):
                continue
            if dur < min_duration_s:
                continue
            if not (bpm_range[0] <= bpm <= bpm_range[1]):
                continue
            key = rec["name"].strip().lower()
            cand = {
                "content_id": rec["content_id"],
                "name": rec["name"],
                "path": rec["path"],
                "bpm": round(bpm, 2),
                "duration_s": round(dur, 2),
                "frag_score": score,
                "onset_rate": round(onset, 3),
                "rms_p90": round(rms_p90, 3),
            }
            if key not in rows or onset > rows[key]["onset_rate"]:
                rows[key] = cand
    ranked = sorted(
        rows.values(),
        key=lambda c: (-c["frag_score"], -c["onset_rate"], c["name"].lower()),
    )[:n]
    for i, c in enumerate(ranked):
        c["rank"] = i + 1
        c["rationale"] = (
            f"{c['bpm']:.1f} bpm in the {bpm_range[0]:.0f}-{bpm_range[1]:.0f} "
            f"energy band; {c['duration_s']:.0f}s covers the "
            f"{TARGET_DURATION_S[0]:.0f}-{TARGET_DURATION_S[1]:.0f}s Part01 "
            f"body without looping; shortlist frag_score {c['frag_score']}; "
            f"onset_rate {c['onset_rate']:.2f}/s gives a dense anchor grid "
            f"(rms_p90 {c['rms_p90']:.2f} sustains energy)"
        )
    return ranked


def export_music_candidates(
    shortlist_csv: Path | str | None = None,
    out_path: Path | str | None = None,
    n: int = 3,
) -> Path:
    out = Path(out_path) if out_path else PART01_DIR / "music_candidates.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    cands = pick_music_candidates(shortlist_csv, n=n)
    doc = {
        "part": PART_NAME,
        "default_content_id": cands[0]["content_id"] if cands else None,
        "candidates": cands,
    }
    out.write_text(json.dumps(doc, indent=1, sort_keys=True))
    return out


# =============================================================================
# Effects (anti-fatigue)
# =============================================================================

def load_effect_assignments(
    cinematic_db_path: Path | str | None = None,
) -> tuple[dict, dict]:
    """Return ({(demo_name, server_time_ms): [assignment,...]}, prior_usage).

    prior_usage counts effect_usage_registry rows from OTHER parts so a
    Part01 re-plan never double-counts its own previous registrations.
    """
    db = Path(cinematic_db_path) if cinematic_db_path else DEFAULT_CINEMATIC_DB
    assignments: dict = {}
    prior: dict = {}
    if not db.exists():
        return assignments, prior
    conn = sqlite3.connect(db)
    try:
        for demo, st, eid, prio in conn.execute(
            "SELECT demo_name, server_time_ms, effect_id, priority "
            "FROM frag_effect_assignments ORDER BY demo_name, server_time_ms, "
            "priority, effect_id"
        ):
            assignments.setdefault((demo, st), []).append(
                {"effect_id": eid, "priority": prio}
            )
        for eid, cnt in conn.execute(
            "SELECT effect_id, COUNT(*) FROM effect_usage_registry "
            "WHERE part_name != ? GROUP BY effect_id",
            (PART_NAME,),
        ):
            prior[eid] = cnt
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()
    return assignments, prior


def choose_effect(
    candidates: list[dict],
    usage_counts: dict,
    last_effect_id: int | None,
) -> int | None:
    """Pick the highest-priority effect that respects anti-fatigue.

    Rules: never the same effect on two consecutive segments; at most
    MAX_EFFECT_USES_PER_PART uses of any effect_id across the Part.
    """
    for cand in candidates:
        eid = cand["effect_id"]
        if eid == last_effect_id:
            continue
        if usage_counts.get(eid, 0) >= MAX_EFFECT_USES_PER_PART:
            continue
        return eid
    return None


# =============================================================================
# Plan building
# =============================================================================

def _anchor_segment(cursor_s: float, anchors_ms: list[int], primary_ms: int,
                    song: dict) -> dict | None:
    """Place a clip so its primary hit lands ON a beat at/after the cursor.

    Reuses hit_to_beat.place_clip: candidate anchor beats live in
    [cursor + primary_s - MAX_HEAD_TRIM_S, cursor + primary_s] so the segment
    starts exactly at the cursor with a bounded head trim
    (in_ms = (cursor - placement.start) * 1000, 0 <= in_ms <= trim budget).
    Clips otherwise play FULL length — beat snap only ever costs a small
    head trim, never truncates the frag chain (P1-S / P1-P).
    """
    primary_s = primary_ms / 1000.0
    budget = min(MAX_HEAD_TRIM_S, max(0.0, primary_s - MIN_LEAD_S))
    lo = cursor_s + primary_s - budget
    hi = cursor_s + primary_s
    if hi <= lo:
        return None
    placement = place_clip(
        anchors_ms, primary_ms,
        song["beats_s"], song["bar_grid_estimate_s"] or None,
        search_window_s=(lo, hi),
    )
    if placement is None:
        return None
    in_ms = int(round((cursor_s - placement.timeline_start_s) * 1000.0))
    if in_ms < 0:
        return None
    return {
        "anchor_beat_s": round(placement.anchor_beat_s, 4),
        "in_ms": in_ms,
        "alignment_score": round(placement.score, 4),
    }


def build_edit_plan(
    music_content_id: str,
    segments: list[dict],
    music_db_path: Path | str | None = None,
    music_offset_s: float = 0.0,
    part_name: str = PART_NAME,
    song: dict | None = None,
) -> dict:
    """Resolve a segment list into a full deterministic edit plan.

    Each input segment: {clip_id, clip_len_ms, anchors_ms, primary_ms,
    placement: 'beat_anchor'|'sequential', in_ms?, out_ms?, transition?,
    effect_recipe?, reason?, phase?, avi_path?}. Timeline is contiguous —
    every segment starts where the previous one ended (rough-cut concat).
    Beat-anchored segments trim clip head so the primary hit lands ON the
    chosen beat of the music grid (music starts at music_offset_s of the
    timeline; grid times below are timeline times).
    """
    if song is None:
        song = load_song(music_content_id, music_db_path)
    # Beat grid shifted into timeline coordinates.
    grid = {
        "content_id": song["content_id"],
        "name": song["name"],
        "path": song["path"],
        "bpm": song["bpm"],
        "duration_s": song["duration_s"],
        "beats_s": [b + music_offset_s for b in song["beats_s"]],
        "bar_grid_estimate_s": [d + music_offset_s
                                for d in song["bar_grid_estimate_s"]],
    }

    cursor = 0.0
    non_hard = 0
    planned: list[dict] = []
    for seg in segments:
        clip_len_ms = int(seg["clip_len_ms"])
        in_ms = int(seg.get("in_ms", 0))
        out_ms = int(seg.get("out_ms", clip_len_ms))
        out_ms = min(out_ms, clip_len_ms)
        transition = seg.get("transition", DEFAULT_TRANSITION)
        if transition not in ALLOWED_TRANSITIONS:
            raise ValueError(f"transition {transition!r} not in allowed set")
        if transition != "hard_cut":
            non_hard += 1
            if non_hard > MAX_NON_HARD_CUTS:
                transition = DEFAULT_TRANSITION
                non_hard -= 1

        placement = seg.get("placement", "sequential")
        anchor = None
        if placement == "beat_anchor":
            anchor = _anchor_segment(
                cursor, seg["anchors_ms"], seg["primary_ms"], grid,
            )
            if anchor is not None and anchor["in_ms"] < seg["primary_ms"]:
                in_ms = anchor["in_ms"]
            else:
                placement = "sequential"
                anchor = None
        if out_ms <= in_ms:
            raise ValueError(
                f"clip {seg['clip_id']}: empty cut ({in_ms}..{out_ms})"
            )
        est_duration = (out_ms - in_ms) / 1000.0
        planned.append({
            "clip_id": int(seg["clip_id"]),
            "phase": seg.get("phase"),
            "reason": seg.get("reason"),
            "placement": placement,
            "timeline_start_s": round(cursor, 4),
            "anchor_beat_s": anchor["anchor_beat_s"] if anchor else None,
            "alignment_score": anchor["alignment_score"] if anchor else None,
            "in_ms": in_ms,
            "out_ms": out_ms,
            "est_duration": round(est_duration, 4),
            "transition": transition,
            "effect_recipe": seg.get("effect_recipe"),
            "hero_slot": bool(seg.get("hero_slot", False)),
            "avi_path": seg.get("avi_path"),
            "anchors_ms": list(seg.get("anchors_ms", [])),
            "primary_ms": int(seg["primary_ms"]),
        })
        cursor += est_duration

    plan = {
        "version": 1,
        "part": part_name,
        "music": {
            "content_id": grid["content_id"],
            "name": grid["name"],
            "path": grid["path"],
            "bpm": grid["bpm"],
            "duration_s": grid["duration_s"],
            "offset_s": music_offset_s,
            "grid_extrapolated": bool(song.get("grid_extrapolated", False)),
        },
        "audio": {
            "music_gain": MUSIC_GAIN,
            "game_audio_gain": GAME_AUDIO_GAIN,
            "mix": "amix_normalize0_fixed_level",   # P1-G: never ducked
            "true_peak_ceiling_dbtp": -1.0,
        },
        "target_duration_s": list(TARGET_DURATION_S),
        "total_duration_s": round(cursor, 4),
        "segments": planned,
    }
    plan["edit_plan_id"] = compute_edit_plan_id(plan)
    return plan


def compute_edit_plan_id(plan: dict) -> str:
    """sha256 of the canonical plan JSON, volatile keys excluded."""
    scrub = {k: v for k, v in plan.items()
             if k not in ("edit_plan_id", "created_at")}
    blob = json.dumps(scrub, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# =============================================================================
# Auto-plan (ARC ordering)
# =============================================================================

ARC_PHASES = ("OPEN", "BUILD", "ESCALATE", "HERO", "CLIMAX", "OUT")


def _row_meta(row: dict) -> dict:
    """Planner view of one ledger row."""
    anchors = part_rhythm.scene_beat_anchors(row)
    tags = set((row.get("tags") or "").split(","))
    return {
        "clip_id": anchors["clip_id"],
        "anchors_ms": anchors["anchors_ms"],
        "primary_ms": anchors["primary_ms"],
        "clip_len_ms": int(row["capture_end_ms"]) - int(row["capture_start_ms"]),
        "tier": row.get("tier") or "",
        "klass": row.get("class") or "",
        "weapon": row.get("weapon") or "",
        "tags": tags,
        "rank_score": float(row.get("rank_score") or 0.0),
        "captured": bool(row.get("avi_path")),
        "avi_path": row.get("avi_path"),
        "demo_name": row.get("demo_name"),
        "server_time_ms": row.get("server_time_ms"),
        "kills": len(anchors["anchors_ms"]),
    }


def _order(rows: list[dict]) -> list[dict]:
    """Deterministic pick order: captured masters first, then score, then id."""
    return sorted(rows, key=lambda m: (not m["captured"], -m["rank_score"],
                                       m["clip_id"]))


def auto_plan_part01(
    music_content_id: str | None = None,
    ledger_db_path: Path | str | None = None,
    music_db_path: Path | str | None = None,
    cinematic_db_path: Path | str | None = None,
    shortlist_csv: Path | str | None = None,
    target_s: tuple[float, float] = TARGET_DURATION_S,
    song: dict | None = None,
) -> dict:
    """Propose the full Part01 arc from the promoted pool + a beat grid.

    ARC: OPEN strong frag -> BUILD rails/speed -> ESCALATE multikills ->
    HERO S+ cinematic slot placeholder -> CLIMAX best scene -> OUT cooldown.
    Captured rows (avi_path set) are preferred everywhere; hard cuts default;
    effect picks respect the anti-fatigue registry.
    """
    if music_content_id is None:
        cands = pick_music_candidates(shortlist_csv)
        if not cands:
            raise RuntimeError("no music candidates matched the Part01 filter")
        music_content_id = cands[0]["content_id"]

    pool = [_row_meta(r) for r in part_rhythm.load_pool_rows(ledger_db_path)]
    assignments, prior_usage = load_effect_assignments(cinematic_db_path)
    used: set[int] = set()

    def take(pred, count=None, budget_s=None):
        picked = []
        total = 0.0
        for m in _order(pool):
            if m["clip_id"] in used or not pred(m):
                continue
            picked.append(m)
            used.add(m["clip_id"])
            total += m["clip_len_ms"] / 1000.0
            if count is not None and len(picked) >= count:
                break
            if budget_s is not None and total >= budget_s:
                break
        return picked

    lo, hi = target_s
    mid = (lo + hi) / 2.0

    is_frag = lambda m: m["klass"] in ("FRAG_MASTER", "T1_NEW", "CLUTCH_PREMIUM")
    is_scene = lambda m: m["klass"] == "SCENE_MASTER"
    is_multi = lambda m: "multikill" in m["tags"] or m["kills"] >= 3
    is_rail_speed = lambda m: (m["weapon"] == "RAILGUN"
                               or {"airshot", "air_combo", "airborne_kill",
                                   "air_rocket"} & m["tags"])

    arc: list[tuple[str, list[dict], str]] = []
    arc.append(("OPEN", take(is_frag, count=1),
                "strongest available frag opens cold"))
    arc.append(("BUILD", take(lambda m: is_frag(m) and is_rail_speed(m),
                              budget_s=mid * 0.22),
                "rails + aerial speed establish tempo"))
    arc.append(("ESCALATE", take(lambda m: is_frag(m) and is_multi(m),
                                 budget_s=mid * 0.28),
                "multikill chains raise intensity"))
    hero = take(lambda m: m["tier"] == "SP" and is_scene(m), count=1)
    arc.append(("HERO", hero,
                "S+ cinematic slot (placeholder until hero recapture lands)"))
    arc.append(("CLIMAX", take(is_scene, count=2),
                "best remaining scenes peak the part"))
    arc.append(("OUT", take(lambda m: m["tier"] == "A", count=2),
                "A-tier cooldown closes"))

    # Backfill BUILD with any remaining frags until the target floor.
    def planned_total():
        return sum(m["clip_len_ms"] / 1000.0
                   for _, ms, _ in arc for m in ms)

    if planned_total() < lo:
        filler = []
        for m in _order(pool):
            if m["clip_id"] in used or not is_frag(m):
                continue
            filler.append(m)
            used.add(m["clip_id"])
            if planned_total() + sum(
                    f["clip_len_ms"] / 1000.0 for f in filler) >= lo:
                break
        arc.insert(3, ("ESCALATE", filler, "backfill to target floor"))

    # Trim overflow: drop lowest-score non-anchor picks past the ceiling.
    segments: list[dict] = []
    usage_counts = dict(prior_usage)
    last_eid: int | None = None
    non_hard_budget = MAX_NON_HARD_CUTS
    total = 0.0
    prev_phase = None
    for phase, members, why in arc:
        for m in members:
            dur = m["clip_len_ms"] / 1000.0
            if total + dur > hi and phase in ("BUILD", "ESCALATE") \
                    and len(segments) > 3:
                continue
            transition = DEFAULT_TRANSITION
            if phase != prev_phase and non_hard_budget > 0:
                if phase == "HERO":
                    transition, non_hard_budget = "dissolve_300ms", non_hard_budget - 1
                elif phase == "CLIMAX":
                    transition, non_hard_budget = "impact_cut", non_hard_budget - 1
                elif phase == "OUT":
                    transition, non_hard_budget = "dissolve_300ms", non_hard_budget - 1
            eid = choose_effect(
                assignments.get((m["demo_name"], m["server_time_ms"]), []),
                usage_counts, last_eid,
            )
            if eid is not None:
                usage_counts[eid] = usage_counts.get(eid, 0) + 1
                last_eid = eid
            segments.append({
                "clip_id": m["clip_id"],
                "clip_len_ms": m["clip_len_ms"],
                "anchors_ms": m["anchors_ms"],
                "primary_ms": m["primary_ms"],
                "placement": "beat_anchor",
                "transition": transition,
                "effect_recipe": {"effect_id": eid} if eid is not None else None,
                "phase": phase,
                "hero_slot": phase == "HERO",
                "avi_path": m["avi_path"],
                "reason": (
                    f"{phase}: {why} — tier {m['tier']} {m['klass']} "
                    f"score {m['rank_score']:.2f}, {m['kills']} kill(s), "
                    f"{m['weapon'] or 'mixed'}"
                    + (" [CAPTURED]" if m["captured"] else " [pending capture]")
                ),
            })
            total += dur
            prev_phase = phase

    return build_edit_plan(music_content_id, segments,
                           music_db_path=music_db_path, song=song)


# =============================================================================
# Persistence
# =============================================================================

PART_EDIT_PLANS_SCHEMA = """
CREATE TABLE IF NOT EXISTS part_edit_plans (
    edit_plan_id TEXT PRIMARY KEY,
    part_name TEXT NOT NULL,
    music_content_id TEXT,
    total_duration_s REAL,
    segment_count INTEGER,
    plan_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def persist_plan(
    plan: dict,
    cinematic_db_path: Path | str | None = None,
    out_json_path: Path | str | None = None,
) -> Path:
    """Store the plan in cinematic.db part_edit_plans + write the JSON file."""
    db = Path(cinematic_db_path) if cinematic_db_path else DEFAULT_CINEMATIC_DB
    conn = sqlite3.connect(db)
    try:
        conn.executescript(PART_EDIT_PLANS_SCHEMA)
        conn.execute(
            "INSERT OR REPLACE INTO part_edit_plans "
            "(edit_plan_id, part_name, music_content_id, total_duration_s, "
            "segment_count, plan_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                plan["edit_plan_id"], plan["part"],
                plan["music"]["content_id"], plan["total_duration_s"],
                len(plan["segments"]),
                json.dumps(plan, sort_keys=True),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()
    out = Path(out_json_path) if out_json_path \
        else PART01_DIR / "part01_edit_plan.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(plan, indent=1, sort_keys=True))
    return out


__all__ = [
    "MUSIC_GAIN", "GAME_AUDIO_GAIN", "ALLOWED_TRANSITIONS",
    "MAX_NON_HARD_CUTS", "TARGET_DURATION_S",
    "load_song", "pick_music_candidates", "export_music_candidates",
    "load_effect_assignments", "choose_effect",
    "build_edit_plan", "compute_edit_plan_id", "auto_plan_part01",
    "persist_plan",
]


if __name__ == "__main__":  # pragma: no cover
    export_music_candidates()
    plan = auto_plan_part01()
    path = persist_plan(plan)
    print(f"edit_plan_id={plan['edit_plan_id']}")
    print(f"segments={len(plan['segments'])} "
          f"total={plan['total_duration_s']:.1f}s")
    print(f"wrote {path}")
