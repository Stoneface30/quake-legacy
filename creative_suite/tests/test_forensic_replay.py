"""Forensic replay: reproducible diagnostic media that consumes nothing."""
from __future__ import annotations

from fractions import Fraction
import json
import sqlite3
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import (demo_truth as dt, forensic_replay as fr,
                                   netcode_anomaly as na, opportunity_graph as og,
                                   projectile_reconstruction as pr, temporal_footprint as tf)


def _case():
    pts = tuple(pr.PathPoint(1_000_000 + t * 25_000, (float(t) * 10, 0.0, 100.0 - t),
                             (400.0, 0.0, -40.0),
                             dt.ENTITY_OBSERVED if t < 2 else dt.PHYSICS_RECONSTRUCTED)
                for t in range(41))
    launch = pr.LaunchState(pr.KIND_GRENADE, pts[0].t_us, pts[0].pos, pts[0].vel, dt.ENTITY_OBSERVED)
    cont = pr.Continuation(pr.KIND_GRENADE, launch, pts, pts[-1].t_us, "FUSE", pts[-1].pos,
                           bounces=(pr.Bounce(1_500_000, (200.0, 0.0, 80.0), (0.0, 0.0, 1.0), 400.0, 260.0),))
    final, res = pr.truncate_at_event(cont, event_kind="missile_miss", event_t_us=cont.end_t_us,
                                      event_pos=(400.0, 5.7, 60.0))
    anomaly = na.from_projectile(final, res, content_hash="h" * 64, subject_client=0,
                                 entity_num=199, weapon_wp=na.WP_GRENADE_LAUNCHER,
                                 event_weapon_wp=na.WP_GRENADE_LAUNCHER)
    return anomaly, final


# ── recipe and time ─────────────────────────────────────────────────────────

def test_recipe_anchors_come_from_the_evidence():
    anomaly, cont = _case()
    r = fr.recipe_for_projectile(anomaly, cont)
    assert r.observation_end_us == 1_025_000            # after the second recorded sample
    assert r.anomaly_end_us == cont.end_t_us == 2_000_000
    assert r.context_before_us == 0 and r.context_after_us == 3_500_000
    assert fr.LAYER_RECONSTRUCTED_PATH in r.layers and fr.LAYER_RECORDED_IMPACT in r.layers
    assert fr.LAYER_BSP_CONTACT in r.layers and fr.LAYER_PROVENANCE_BOUNDARY in r.layers
    assert r.domain == fr.DOMAIN_FORENSIC and r.hud_mode == "CINEMATIC_CLEAN"


def test_time_segments_are_exact_contiguous_and_carry_no_debt():
    anomaly, cont = _case()
    r = fr.recipe_for_projectile(anomaly, cont)
    segs = r.time_segments()
    kinds = [s.kind for s in segs]
    assert kinds == ["normal", "freeze", "slow", "normal"]
    slow = segs[2]
    assert (slow.rate_num, slow.rate_den) == (1, 4)
    assert slow.edit_end_us - slow.edit_start_us == 4 * (slow.demo_end_us - slow.demo_start_us)
    for a, b in zip(segs, segs[1:]):
        assert a.edit_end_us == b.edit_start_us
    tm = r.time_map()                                     # scene_recipe validates the map
    assert tm.edit_to_demo(0) == 0
    rs = [tf.RetimeSegment(s.demo_start_us, s.demo_end_us, Fraction(s.rate_num, s.rate_den), s.kind)
          for s in segs if s.kind != "freeze"]
    assert tf.check_no_temporal_debt(rs) == []


def test_recipe_refuses_the_cinematic_domain_and_a_gameplay_hud():
    anomaly, cont = _case()
    r = fr.recipe_for_projectile(anomaly, cont)
    with pytest.raises(ValueError):
        fr.ForensicReplayRecipe(**{**r.__dict__, "domain": fr.DOMAIN_CINEMATIC})
    with pytest.raises(ValueError):
        fr.ForensicReplayRecipe(**{**r.__dict__, "hud_mode": "GAMEPLAY"})


# ── manifest ────────────────────────────────────────────────────────────────

def test_manifest_is_deterministic_and_reloadable(tmp_path):
    anomaly, cont = _case()
    r = fr.recipe_for_projectile(anomaly, cont)
    m1 = fr.build_manifest(anomaly, r, cont, bsp_hash="b" * 64)
    m2 = fr.build_manifest(anomaly, r, cont, bsp_hash="b" * 64)
    assert m1 == m2 and m1.recipe_hash == r.recipe_hash
    assert m1.anomaly_hash == fr.anomaly_hash(anomaly)
    assert m1.reconstruction_version == pr.RECON_VERSION
    assert m1.physics_constants["GRENADE_FUSE_MS"] == 2500
    assert [s["evidence"] for s in m1.provenance_segments] == [dt.ENTITY_OBSERVED, dt.PHYSICS_RECONSTRUCTED]   # confirmed at the fuse: not cut
    p = m1.write(tmp_path / "m.json")
    assert fr.ForensicManifest.load(p) == m1


def test_overlay_shows_the_numbers_that_explain_the_event():
    anomaly, cont = _case()
    early = fr.overlay_lines(anomaly, cont, 1_000_000)
    late = fr.overlay_lines(anomaly, cont, 2_000_000)
    assert early[0].endswith("RECORDED") and not any("residual" in l for l in early)
    assert any("residual 5.7 u" in l for l in late)
    assert any("FUSE at 1000 ms" in l for l in late)
    assert any(na.CLIENT_OBSERVATION_GAP in l for l in late)
    assert len(late) <= 9          # nine short lines fit the panel (verified on the rendered frame)


# ── rendering consumes nothing ──────────────────────────────────────────────

def test_render_writes_media_and_manifest_only(tmp_path, monkeypatch):
    anomaly, cont = _case()
    r = fr.ForensicReplayRecipe(**{**fr.recipe_for_projectile(anomaly, cont).__dict__,
                                   "fps": 5, "freeze_us": 200_000,
                                   "context_before_us": 900_000, "context_after_us": 2_200_000})
    ffmpeg = REPO_ROOT / "creative_suite" / "tools" / "ffmpeg" / "ffmpeg.exe"
    if not ffmpeg.exists():
        pytest.skip("ffmpeg not on disk")

    def _no_db(*a, **k):
        raise AssertionError("a forensic render must not open the recognition database")
    monkeypatch.setattr(sqlite3, "connect", _no_db)
    cand = og.MomentCandidate(28557, og.KIND_ROCKET_IMPACT, 3_000_000, "MY_FRAG", 1_000_000)
    state_before = cand.moment_state
    out = tmp_path / "forensic.mp4"
    m = fr.render_forensic_replay(anomaly, r, cont, out, ffmpeg=ffmpeg, bsp_hash="b" * 64)
    assert out.exists() and out.stat().st_size > 1000
    side = out.with_suffix(".forensic.json")
    assert side.exists() and json.loads(side.read_text())["output_sha256"] == m.output_sha256
    assert m.output_sha256 and m.domain == fr.DOMAIN_FORENSIC
    assert cand.moment_state == state_before                 # nothing was consumed
    assert sorted(p.name for p in tmp_path.iterdir()) == ["forensic.forensic.json", "forensic.mp4"]


def test_forensic_sheet_has_the_forensic_lanes():
    anomaly, cont = _case()
    sheet = fr.forensic_sheet(anomaly, cont, snapshot_times_us=[1_000_000, 1_025_000])
    names = [l.name for l in sheet.lanes]
    for n in ("SNAPSHOT OBSERVATION", "RECORDED TRAJECTORY", "RECONSTRUCTION",
              "IMPACT/FRAG", "PROVENANCE"):
        assert n in names
    prov = next(l for l in sheet.lanes if l.name == "PROVENANCE")
    assert [iv.state for iv in prov.intervals] == [dt.ENTITY_OBSERVED, dt.PHYSICS_RECONSTRUCTED]   # confirmed at the fuse: not cut
    assert prov.intervals[0].label == ""           # 25 ms segment: colour only, no overlapping text
    assert sheet.hero_us == cont.end_t_us and sheet.hero_label == "FUSE"


# ── creative opportunity graph ──────────────────────────────────────────────

def test_anomaly_metadata_is_searchable_on_the_candidate_but_never_placed():
    anomaly, cont = _case()
    cand = og.MomentCandidate(28557, og.KIND_ROCKET_IMPACT, 3_000_000, "MY_FRAG", 1_000_000,
                              **og.anomaly_fields(anomaly, forensic_replay_available=True))
    assert cand.anomaly_available and cand.forensic_replay_available
    assert cand.anomaly_type == na.CLIENT_OBSERVATION_GAP
    assert cand.anomaly_assessment == na.CLIENT_OBSERVATION_LIMITATION
    assert cand.observation_gap_us == 975_000 and cand.anomaly_residual_u == pytest.approx(5.7)
    assert cand.creative_utility == na.UTILITY_REFERENCE
    assert cand.moment_state == "AVAILABLE"                  # metadata, not a placement
    assert og.MomentCandidate(1, og.KIND_ROCKET_IMPACT, 1, "MY_FRAG", 1,
                              **og.anomaly_fields(None)).anomaly_available is False
