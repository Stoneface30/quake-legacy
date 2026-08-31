"""Tests for the Part01 planning + assembly engine (demo V2).

Covers: anchor extraction, beat placement math (primary hit ON beat), plan
determinism / hash stability, arc ordering (tiers + effect anti-fatigue),
assembler command generation (no execution), the P1-G fixed-level audio
contract, and edit-plan serialization round-trip.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from creative_suite.database import demo_v2_db
from creative_suite.engine import part01_assemble, part01_plan, part_rhythm


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _song(interval_s: float = 0.5, duration_s: float = 400.0) -> dict:
    n = int(duration_s / interval_s)
    beats = [round(i * interval_s, 4) for i in range(n)]
    return {
        "content_id": "testsong0001",
        "name": "test__song.mp3",
        "path": "X:/nonexistent/test__song.mp3",
        "bpm": 60.0 / interval_s,
        "duration_s": duration_s,
        "beats_s": beats,
        "bar_grid_estimate_s": beats[::4],
    }


def _ledger_row(clip_id: int, **kw) -> dict:
    row = {
        "generated_clip_id": clip_id,
        "demo_name": f"demo{clip_id}.dm_73",
        "server_time_ms": 100000 + clip_id,
        "capture_start_ms": 0,
        "capture_end_ms": 20000,
        "frag_offsets_ms": "[4000, 6000, 9000]",
        "primary_frag_offset_ms": 9000,
        "tier": "S",
        "class": "FRAG_MASTER",
        "weapon": "ROCKET",
        "tags": "multikill",
        "rank_score": 50.0,
        "avi_path": None,
    }
    row.update(kw)
    return row


def _insert(conn, row: dict) -> None:
    r = dict(row)
    r.pop("generated_clip_id", None)
    demo_v2_db.insert_candidate(conn, r)


@pytest.fixture()
def ledger_db(tmp_path: Path) -> Path:
    db = tmp_path / "demo_v2_test.db"
    conn = demo_v2_db.connect(db)
    conn.close()
    return db


@pytest.fixture()
def cinematic_db(tmp_path: Path) -> Path:
    db = tmp_path / "cinematic_test.db"
    conn = sqlite3.connect(db)
    conn.executescript("""
        CREATE TABLE frag_effect_assignments (
            assignment_id INTEGER PRIMARY KEY,
            demo_name TEXT, server_time_ms INTEGER, victim_client INTEGER,
            classification TEXT, effect_id INTEGER, priority INTEGER,
            parameter_overrides TEXT, camera_target TEXT,
            start_offset_ms INTEGER, end_offset_ms INTEGER,
            confidence TEXT, reason TEXT, status TEXT, created_at TEXT
        );
        CREATE TABLE effect_usage_registry (
            usage_id INTEGER PRIMARY KEY, part_name TEXT,
            effect_id INTEGER, frag_ref TEXT, used_at_ms INTEGER
        );
    """)
    conn.commit()
    conn.close()
    return db


# ---------------------------------------------------------------------------
# 1. Anchor extraction
# ---------------------------------------------------------------------------

class TestSceneBeatAnchors:
    def test_extracts_offsets_and_primary(self):
        rec = part_rhythm.scene_beat_anchors(_ledger_row(7))
        assert rec == {"clip_id": 7, "anchors_ms": [4000, 6000, 9000],
                       "primary_ms": 9000}

    def test_primary_fallback_is_last_kill(self):
        row = _ledger_row(8, primary_frag_offset_ms=None)
        assert part_rhythm.scene_beat_anchors(row)["primary_ms"] == 9000

    def test_primary_not_in_offsets_falls_back(self):
        row = _ledger_row(9, primary_frag_offset_ms=12345)
        assert part_rhythm.scene_beat_anchors(row)["primary_ms"] == 9000

    def test_offsets_sorted(self):
        row = _ledger_row(10, frag_offsets_ms="[9000, 4000, 6000]")
        assert part_rhythm.scene_beat_anchors(row)["anchors_ms"] == \
            [4000, 6000, 9000]

    def test_empty_offsets_raise(self):
        with pytest.raises(ValueError):
            part_rhythm.scene_beat_anchors(_ledger_row(11, frag_offsets_ms="[]"))

    def test_export_writes_all_rows(self, ledger_db, tmp_path):
        conn = demo_v2_db.connect(ledger_db)
        _insert(conn, _ledger_row(0))
        _insert(conn, _ledger_row(0, frag_offsets_ms="[2500]",
                                  primary_frag_offset_ms=2500))
        conn.close()
        out = tmp_path / "anchors.json"
        part_rhythm.export_scene_beat_anchors(ledger_db, out)
        doc = json.loads(out.read_text())
        assert doc["count"] == 2
        assert doc["anchors"][0]["anchors_ms"] == [4000, 6000, 9000]
        assert doc["anchors"][1]["primary_ms"] == 2500


# ---------------------------------------------------------------------------
# 2. Beat placement math — primary hit lands ON a beat
# ---------------------------------------------------------------------------

class TestBeatPlacement:
    def test_primary_hit_on_beat(self):
        song = _song()
        segments = [{
            "clip_id": 1, "clip_len_ms": 20000,
            "anchors_ms": [4000, 6000, 9000], "primary_ms": 9000,
            "placement": "beat_anchor",
        }]
        plan = part01_plan.build_edit_plan("x", segments, song=song)
        seg = plan["segments"][0]
        assert seg["placement"] == "beat_anchor"
        primary_t = seg["timeline_start_s"] + \
            (seg["primary_ms"] - seg["in_ms"]) / 1000.0
        assert seg["anchor_beat_s"] == pytest.approx(primary_t, abs=1e-3)
        # ...and the anchor is a real grid beat
        assert min(abs(b - seg["anchor_beat_s"])
                   for b in song["beats_s"]) < 1e-6

    def test_chained_segments_stay_contiguous_and_on_beat(self):
        song = _song()
        segments = [
            {"clip_id": i, "clip_len_ms": 15000,
             "anchors_ms": [3000, 7000], "primary_ms": 7000,
             "placement": "beat_anchor"}
            for i in range(1, 4)
        ]
        plan = part01_plan.build_edit_plan("x", segments, song=song)
        cursor = 0.0
        for seg in plan["segments"]:
            assert seg["timeline_start_s"] == pytest.approx(cursor, abs=1e-3)
            primary_t = seg["timeline_start_s"] + \
                (seg["primary_ms"] - seg["in_ms"]) / 1000.0
            assert min(abs(b - primary_t)
                       for b in song["beats_s"]) < 2e-3
            cursor += seg["est_duration"]

    def test_head_trim_never_negative_and_keeps_lead(self):
        song = _song()
        segments = [{"clip_id": 1, "clip_len_ms": 30000,
                     "anchors_ms": [12000], "primary_ms": 12000,
                     "placement": "beat_anchor"}] * 2
        plan = part01_plan.build_edit_plan("x", segments, song=song)
        for seg in plan["segments"]:
            assert 0 <= seg["in_ms"] < seg["primary_ms"]
            # P1-S/P1-P: beat snap costs at most the seam trim budget
            assert seg["in_ms"] <= part01_plan.MAX_HEAD_TRIM_S * 1000

    def test_extend_grid_covers_full_duration(self):
        pts, ext = part01_plan._extend_grid([0.0, 0.5], 2.2, 0.5)
        assert pts == [0.0, 0.5, 1.0, 1.5, 2.0]
        assert ext is True
        pts, ext = part01_plan._extend_grid([0.0, 0.5], 0.6, 0.5)
        assert ext is False

    def test_sequential_placement_has_no_anchor(self):
        plan = part01_plan.build_edit_plan("x", [
            {"clip_id": 1, "clip_len_ms": 5000, "anchors_ms": [2000],
             "primary_ms": 2000, "placement": "sequential"},
        ], song=_song())
        seg = plan["segments"][0]
        assert seg["anchor_beat_s"] is None
        assert seg["in_ms"] == 0


# ---------------------------------------------------------------------------
# 3. Determinism / hash stability
# ---------------------------------------------------------------------------

class TestDeterminism:
    SEGS = [{"clip_id": 1, "clip_len_ms": 12000,
             "anchors_ms": [3000, 8000], "primary_ms": 8000,
             "placement": "beat_anchor"}]

    def test_same_inputs_same_id(self):
        a = part01_plan.build_edit_plan("x", list(self.SEGS), song=_song())
        b = part01_plan.build_edit_plan("x", list(self.SEGS), song=_song())
        assert a["edit_plan_id"] == b["edit_plan_id"]
        assert len(a["edit_plan_id"]) == 64

    def test_changed_input_changes_id(self):
        a = part01_plan.build_edit_plan("x", list(self.SEGS), song=_song())
        segs2 = [dict(self.SEGS[0], primary_ms=3000)]
        b = part01_plan.build_edit_plan("x", segs2, song=_song())
        assert a["edit_plan_id"] != b["edit_plan_id"]

    def test_created_at_excluded_from_hash(self):
        plan = part01_plan.build_edit_plan("x", list(self.SEGS), song=_song())
        with_ts = dict(plan, created_at="2026-08-31T00:00:00Z")
        assert part01_plan.compute_edit_plan_id(with_ts) == \
            plan["edit_plan_id"]


# ---------------------------------------------------------------------------
# 4. Auto-plan arc ordering + anti-fatigue
# ---------------------------------------------------------------------------

def _populate_pool(db: Path) -> None:
    conn = demo_v2_db.connect(db)
    # captured strong frags (various flavours)
    for i in range(6):
        _insert(conn, _ledger_row(
            0, demo_name=f"fragdemo{i}.dm_73", rank_score=60 - i,
            weapon="RAILGUN" if i % 2 == 0 else "ROCKET",
            tags="airshot,multikill" if i % 2 else "multikill",
            avi_path=__file__,   # any existing file
        ))
    # pending frags
    for i in range(4):
        _insert(conn, _ledger_row(0, demo_name=f"pend{i}.dm_73",
                                  rank_score=40 - i, tags="airshot"))
    # S+ scenes
    for i in range(2):
        _insert(conn, _ledger_row(
            0, demo_name=f"scene_sp{i}.dm_73", tier="SP",
            **{"class": "SCENE_MASTER"}, rank_score=72 - i,
            capture_end_ms=30000))
    # S scene
    _insert(conn, _ledger_row(0, demo_name="scene_s.dm_73", tier="S",
                              **{"class": "SCENE_MASTER"}, rank_score=55))
    # A-tier cooldown clips
    for i in range(3):
        _insert(conn, _ledger_row(0, demo_name=f"cool{i}.dm_73", tier="A",
                                  rank_score=20 - i, tags=""))
    conn.close()


def _populate_effects(db: Path, demos: list[str]) -> None:
    conn = sqlite3.connect(db)
    for d in demos:
        for eid, prio in ((9, 1), (14, 2)):
            conn.execute(
                "INSERT INTO frag_effect_assignments "
                "(demo_name, server_time_ms, effect_id, priority) "
                "VALUES (?, ?, ?, ?)", (d, 100000, eid, prio))
    conn.commit()
    conn.close()


class TestAutoPlanArc:
    def _plan(self, ledger_db, cinematic_db):
        _populate_pool(ledger_db)
        return part01_plan.auto_plan_part01(
            music_content_id="testsong0001",
            ledger_db_path=ledger_db,
            cinematic_db_path=cinematic_db,
            song=_song(),
            target_s=(60.0, 120.0),
        )

    def test_arc_phase_order(self, ledger_db, cinematic_db):
        plan = self._plan(ledger_db, cinematic_db)
        phases = [s["phase"] for s in plan["segments"]]
        order = [part01_plan.ARC_PHASES.index(p) for p in phases]
        assert order == sorted(order)
        assert phases[0] == "OPEN"
        assert "HERO" in phases and "CLIMAX" in phases and "OUT" in phases

    def test_hero_slot_is_sp_scene_placeholder(self, ledger_db, cinematic_db):
        plan = self._plan(ledger_db, cinematic_db)
        hero = [s for s in plan["segments"] if s["phase"] == "HERO"]
        assert len(hero) == 1
        assert hero[0]["hero_slot"] is True
        assert "SP SCENE_MASTER" in hero[0]["reason"]

    def test_climax_prefers_best_scene(self, ledger_db, cinematic_db):
        plan = self._plan(ledger_db, cinematic_db)
        climax = [s for s in plan["segments"] if s["phase"] == "CLIMAX"]
        assert climax, "climax phase missing"
        assert "SCENE_MASTER" in climax[0]["reason"]

    def test_out_phase_is_a_tier(self, ledger_db, cinematic_db):
        plan = self._plan(ledger_db, cinematic_db)
        outs = [s for s in plan["segments"] if s["phase"] == "OUT"]
        assert outs and all("tier A" in s["reason"] for s in outs)

    def test_captured_rows_preferred_in_open(self, ledger_db, cinematic_db):
        plan = self._plan(ledger_db, cinematic_db)
        assert "[CAPTURED]" in plan["segments"][0]["reason"]

    def test_transition_grammar(self, ledger_db, cinematic_db):
        plan = self._plan(ledger_db, cinematic_db)
        trans = [s["transition"] for s in plan["segments"]]
        assert all(t in part01_plan.ALLOWED_TRANSITIONS for t in trans)
        non_hard = [t for t in trans if t != "hard_cut"]
        assert len(non_hard) <= part01_plan.MAX_NON_HARD_CUTS
        # hard cuts are the default (majority)
        assert trans.count("hard_cut") > len(non_hard)

    def test_effect_anti_fatigue(self, ledger_db, cinematic_db):
        _populate_pool(ledger_db)
        conn = demo_v2_db.connect(ledger_db)
        demos = [r[0] for r in conn.execute(
            "SELECT demo_name FROM generated_clips")]
        conn.close()
        _populate_effects(cinematic_db, demos)
        plan = part01_plan.auto_plan_part01(
            music_content_id="testsong0001", ledger_db_path=ledger_db,
            cinematic_db_path=cinematic_db, song=_song(),
            target_s=(60.0, 120.0))
        eids = [s["effect_recipe"]["effect_id"]
                for s in plan["segments"] if s["effect_recipe"]]
        assert eids, "expected some effect assignments"
        for a, b in zip(eids, eids[1:]):
            assert a != b, "same effect on consecutive segments"
        from collections import Counter
        assert max(Counter(eids).values()) <= \
            part01_plan.MAX_EFFECT_USES_PER_PART

    def test_auto_plan_deterministic(self, ledger_db, cinematic_db):
        _populate_pool(ledger_db)
        kw = dict(music_content_id="testsong0001",
                  ledger_db_path=ledger_db, cinematic_db_path=cinematic_db,
                  song=_song(), target_s=(60.0, 120.0))
        a = part01_plan.auto_plan_part01(**kw)
        b = part01_plan.auto_plan_part01(**kw)
        assert a["edit_plan_id"] == b["edit_plan_id"]


# ---------------------------------------------------------------------------
# 5. Assembler command generation (no execution)
# ---------------------------------------------------------------------------

class TestAssemblerCommands:
    def _mini_plan(self, avi: str | None) -> dict:
        return {
            "edit_plan_id": "e" * 64,
            "music": {"content_id": "x", "path": "m.mp3", "offset_s": 0.0},
            "audio": {"music_gain": 0.55, "game_audio_gain": 0.9},
            "segments": [
                {"clip_id": 1, "in_ms": 1500, "out_ms": 9500,
                 "est_duration": 8.0, "avi_path": avi, "phase": "OPEN"},
                {"clip_id": 2, "in_ms": 0, "out_ms": 5000,
                 "est_duration": 5.0, "avi_path": None, "phase": "BUILD"},
            ],
        }

    def test_jobs_and_placeholders(self, tmp_path):
        avi = tmp_path / "c00001.avi"
        avi.write_bytes(b"\x00")
        jobs, ph = part01_assemble.build_segment_jobs(
            self._mini_plan(str(avi)), tmp_path)
        assert len(jobs) == 1 and len(ph) == 1
        assert ph[0]["status"] == "SKIPPED_AVI_MISSING"
        assert ph[0]["clip_id"] == 2

    def test_segment_cmd_shape(self, tmp_path):
        avi = tmp_path / "c00001.avi"
        avi.write_bytes(b"\x00")
        jobs, _ = part01_assemble.build_segment_jobs(
            self._mini_plan(str(avi)), tmp_path)
        cmd = jobs[0]["cmd"]
        assert "-ss" in cmd and cmd[cmd.index("-ss") + 1] == "1.500"
        assert "-t" in cmd and cmd[cmd.index("-t") + 1] == "8.000"
        assert "libx264" in cmd and "20" in cmd and "veryfast" in cmd
        assert "pcm_s16le" in cmd          # P1-BB: no AAC intermediates
        assert cmd[-1].endswith(".mkv")

    def test_missing_avi_only_yields_no_jobs(self, tmp_path):
        jobs, ph = part01_assemble.build_segment_jobs(
            self._mini_plan(None), tmp_path)
        assert jobs == [] and len(ph) == 2

    def test_true_peak_parse(self):
        stderr = ("[Parsed_ebur128_0] Summary:\n"
                  "  True peak:\n    Peak: -3.4 dBFS\n    Peak: -2.1 dBFS\n")
        assert part01_assemble.parse_true_peak_dbfs(stderr) == -2.1
        assert part01_assemble.parse_true_peak_dbfs("nothing") is None

    def test_static_gain_cmd_is_constant_gain(self):
        cmd = part01_assemble.static_gain_cmd("a.mp4", "b.mp4", -1.7)
        af = cmd[cmd.index("-af") + 1]
        assert af == "volume=-1.70dB"


# ---------------------------------------------------------------------------
# 6. P1-G fixed-level audio contract — no sidechain anywhere
# ---------------------------------------------------------------------------

class TestFixedLevelRule:
    def test_gain_constants(self):
        assert part01_plan.MUSIC_GAIN == 0.55
        assert part01_plan.GAME_AUDIO_GAIN == 0.9

    def test_no_sidechain_in_sources(self):
        for mod in (part01_plan, part01_assemble, part_rhythm):
            src = Path(mod.__file__).read_text(encoding="utf-8").lower()
            assert "sidechaincompress" not in src
            assert "acompressor" not in src

    def test_mux_filter_is_fixed_level(self):
        cmd = part01_assemble.music_mux_cmd(
            "body.mkv", "music.mp3", "out.mp4", body_duration_s=300.0,
            music_gain=0.55, game_audio_gain=0.9)
        filt = cmd[cmd.index("-filter_complex") + 1]
        assert "normalize=0" in filt
        assert "sidechain" not in filt
        assert filt.count("volume=0.55") == 1   # ONE fixed music level
        # only permitted level moves: head fade-in + tail fade-out
        assert filt.count("afade") == 2

    def test_plan_audio_block(self):
        plan = part01_plan.build_edit_plan("x", [
            {"clip_id": 1, "clip_len_ms": 5000, "anchors_ms": [2000],
             "primary_ms": 2000, "placement": "sequential"}], song=_song())
        assert plan["audio"]["music_gain"] == 0.55
        assert plan["audio"]["mix"] == "amix_normalize0_fixed_level"
        assert plan["audio"]["true_peak_ceiling_dbtp"] == -1.0


# ---------------------------------------------------------------------------
# 7. Serialization round-trip + persistence
# ---------------------------------------------------------------------------

class TestPersistence:
    def test_round_trip(self, tmp_path, cinematic_db):
        plan = part01_plan.build_edit_plan("x", [
            {"clip_id": 1, "clip_len_ms": 12000, "anchors_ms": [3000, 8000],
             "primary_ms": 8000, "placement": "beat_anchor"}], song=_song())
        out = tmp_path / "plan.json"
        part01_plan.persist_plan(plan, cinematic_db, out)
        loaded = json.loads(out.read_text())
        assert part01_plan.compute_edit_plan_id(loaded) == \
            plan["edit_plan_id"]
        conn = sqlite3.connect(cinematic_db)
        row = conn.execute(
            "SELECT part_name, segment_count, plan_json FROM part_edit_plans "
            "WHERE edit_plan_id = ?", (plan["edit_plan_id"],)).fetchone()
        conn.close()
        assert row[0] == "part01" and row[1] == 1
        assert part01_plan.compute_edit_plan_id(json.loads(row[2])) == \
            plan["edit_plan_id"]

    def test_replan_replaces_row(self, tmp_path, cinematic_db):
        plan = part01_plan.build_edit_plan("x", [
            {"clip_id": 1, "clip_len_ms": 5000, "anchors_ms": [2000],
             "primary_ms": 2000, "placement": "sequential"}], song=_song())
        out = tmp_path / "plan.json"
        part01_plan.persist_plan(plan, cinematic_db, out)
        part01_plan.persist_plan(plan, cinematic_db, out)
        conn = sqlite3.connect(cinematic_db)
        n = conn.execute("SELECT COUNT(*) FROM part_edit_plans").fetchone()[0]
        conn.close()
        assert n == 1
