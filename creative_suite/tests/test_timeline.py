"""Timeline steps, easing math, wolfcam script emission, shot plans."""
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import camera_paths as cp
from creative_suite.engine import shot_plan as sp
from creative_suite.engine import timeline as tl
from creative_suite.engine.wolfcam_capture import CfgInjectionError


def sample_keyframes():
    return cp.orbit((0, 0, 0), 300.0, 40.0, 90.0, 1000.0, steps=4)


def sample_timeline():
    return (tl.Timeline()
            .slow_to(200, 0.5, ramp_ms=100, easing="smoothstep")
            .zoom(300, 60.0, ramp_ms=200, easing="ease_out")
            .freeze(500, 250)
            .resume(900, ramp_ms=100)
            .cut_to_camera(950, "q3mme"))


# ── easing math ──────────────────────────────────────────────────────────────

def test_easing_values():
    assert tl.ease("linear", 0.5) == 0.5
    assert tl.ease("ease_in", 0.5) == 0.25
    assert tl.ease("ease_out", 0.5) == 0.75
    assert tl.ease("smoothstep", 0.5) == 0.5
    assert tl.ease("smoothstep", 0.25) == pytest.approx(0.15625)


def test_easing_endpoints_and_monotonic():
    for name in tl.EASINGS:
        assert tl.ease(name, 0.0) == 0.0
        assert tl.ease(name, 1.0) == 1.0
        vals = [tl.ease(name, k / 20) for k in range(21)]
        assert all(b >= a for a, b in zip(vals, vals[1:])), name


def test_easing_clamps_and_rejects_unknown():
    assert tl.ease("linear", -1.0) == 0.0
    assert tl.ease("linear", 2.0) == 1.0
    with pytest.raises(ValueError):
        tl.ease("bounce", 0.5)
    with pytest.raises(ValueError):
        tl.Timeline().slow_to(0, 0.5, easing="bounce")


# ── step validation ──────────────────────────────────────────────────────────

def test_step_validation():
    t = tl.Timeline()
    with pytest.raises(ValueError):
        t.slow_to(0, 0.0)
    with pytest.raises(ValueError):
        t.freeze(0, 0)
    with pytest.raises(ValueError):
        t.zoom(0, 200.0)
    with pytest.raises(ValueError):
        t.slow_to(-5, 0.5)


def test_reverse_is_post_production_only():
    t = tl.Timeline()
    with pytest.raises(ValueError, match="post-production"):
        t.reverse(0, 500, post_production=False)
    t.reverse(0, 500)
    assert t.steps[0]["post_production"] is True


# ── curves ───────────────────────────────────────────────────────────────────

def test_timescale_curve_ramp_and_freeze():
    t = tl.Timeline().slow_to(0, 0.5, ramp_ms=100).freeze(500, 200)
    curve = tl.timescale_curve(t)
    assert curve[0] == (0, 1.0)
    assert (100, 0.5) in curve
    assert (500, 0.0) in curve
    assert (700, 0.5) in curve       # freeze restores the pre-freeze rate


def test_impact_hold_curve():
    t = tl.Timeline().impact_hold(1000, 300, pre_rate=0.3, ramp_ms=200)
    curve = tl.timescale_curve(t)
    assert (1000, 0.0) in curve
    assert (1300, 1.0) in curve
    assert any(t_ == 800 and v == 1.0 for t_, v in curve)   # ramp starts


def test_fov_curve():
    t = tl.Timeline().zoom(100, 60.0, ramp_ms=100, easing="linear")
    curve = tl.fov_curve(t, base_fov=90.0)
    assert curve[0] == (100, 90.0)
    assert curve[-1] == (200, 60.0)
    mid = dict(curve)[150]
    assert mid == pytest.approx(75.0)


# ── script emission ──────────────────────────────────────────────────────────

def test_script_emission_ordering(tmp_path):
    script = tl.to_wolfcam_script(sample_timeline(), sample_keyframes(),
                                  base_servertime=100000, gamedir=tmp_path)
    lines = script.splitlines()
    at_times = [int(ln.split()[1]) for ln in lines if ln.startswith("at ")]
    assert at_times == sorted(at_times)
    # camera path compiles to a real .cam10 file AND executes via the
    # FREECAM_SAMPLED freecamsetpos sequence (the retained fallback
    # backend). Native loadcamera/playcamera works too -- see
    # cam10_runtime_contract.md's CORRECTED section.
    assert any(ln.startswith("seekservertime ") for ln in lines)
    assert "freecam" in lines
    assert any("freecamsetpos" in ln for ln in lines)
    assert not any("loadcamera" in ln or "playcamera" in ln
                  for ln in lines if "cut_to_camera" not in ln)
    cam10_path = tmp_path / "cameras" / "scene.cam10"
    assert cam10_path.exists()
    assert cam10_path.read_text().startswith("WolfcamCamera 10")
    # cut_to_camera is a distinct, still-unverified feature (see module
    # docstring) — it keeps emitting playq3mmecamera <name>.
    assert any("playq3mmecamera q3mme" in ln for ln in lines)
    assert any("cl_freezeDemo 1" in ln for ln in lines)
    assert any("cl_freezeDemo 0" in ln for ln in lines)
    assert any("timescale 0.5000" in ln for ln in lines)
    assert any("cg_fov 60.00" in ln for ln in lines)


def test_script_freeze_before_unfreeze():
    script = tl.to_wolfcam_script(tl.Timeline().freeze(500, 250), [],
                                  base_servertime=0)
    lines = [ln for ln in script.splitlines() if "cl_freezeDemo" in ln]
    assert lines[0].endswith("cl_freezeDemo 1")
    assert lines[1].endswith("cl_freezeDemo 0")
    assert int(lines[0].split()[1]) == 500
    assert int(lines[1].split()[1]) == 750


def test_script_reverse_emits_comment_only():
    t = tl.Timeline().reverse(200, 400)
    script = tl.to_wolfcam_script(t, [], base_servertime=5000)
    assert "// post: reverse" in script
    assert not any(ln.startswith("at ") for ln in script.splitlines())


def test_script_injection_rejected(tmp_path):
    with pytest.raises(CfgInjectionError):
        tl.Timeline().cut_to_camera(100, "evil; quit")
    bad_kf = [{"t_ms": 0, "pos": (0, 0, 0), "angles": (0, 0, 0), "fov": 90.0},
              {"t_ms": 100, "pos": (1, 0, 0), "angles": (0, 0, 0), "fov": 90.0}]
    t = tl.Timeline()
    t.steps.append({"type": "cut_to_camera", "t_ms": 10,
                    "camera": "x\nquit", "seq": 0})
    with pytest.raises(CfgInjectionError):
        tl.to_wolfcam_script(t, bad_kf, 0, gamedir=tmp_path)


def test_script_requires_gamedir_for_camera_path():
    with pytest.raises(ValueError):
        tl.to_wolfcam_script(sample_timeline(), sample_keyframes(), 42000)


def test_script_deterministic(tmp_path):
    a = tl.to_wolfcam_script(sample_timeline(), sample_keyframes(), 42000,
                             gamedir=tmp_path)
    b = tl.to_wolfcam_script(sample_timeline(), sample_keyframes(), 42000,
                             gamedir=tmp_path)
    assert a == b


def test_timeline_json_byte_stable():
    a = sample_timeline().to_json()
    b = sample_timeline().to_json()
    assert a == b
    assert tl.Timeline.from_json(a).to_json() == a


# ── shot plans ───────────────────────────────────────────────────────────────

def _plan():
    return sp.assemble_shot_plan(
        demo_sha256="ab" * 32,
        event={"type": "rail_frag", "t_ms": 61234, "killer": 3, "victim": 7},
        profile_id="taxonomy_v2",
        camera={"name": "target_orbit",
                "params": {"radius": 300.0, "arc_deg": 120.0}},
        keyframes=sample_keyframes(),
        timeline=sample_timeline(),
        effect_ids=["speed_ramp_default", "bass_drop"],
        asset_pack_ids=["zzz_photoreal_d35"])


def test_plan_hash_stable():
    assert _plan()["plan_id"] == _plan()["plan_id"]


def test_plan_hash_sensitive_to_inputs():
    p1 = _plan()
    p2 = _plan()
    p2["camera"]["params"]["radius"] = 301.0
    rehash = sp.canonical_json({k: v for k, v in p2.items() if k != "plan_id"})
    import hashlib
    assert hashlib.sha256(rehash.encode()).hexdigest() != p1["plan_id"]
    p3 = sp.assemble_shot_plan(
        demo_sha256="cd" * 32,
        event={"type": "rail_frag", "t_ms": 61234},
        profile_id="taxonomy_v2",
        camera={"name": "target_orbit", "params": {}},
        keyframes=sample_keyframes(), timeline=sample_timeline())
    assert p3["plan_id"] != p1["plan_id"]


def test_plan_persist_and_load(tmp_path):
    db = tmp_path / "cinematic.db"
    plan = _plan()
    pid = sp.persist_shot_plan(plan, db)
    assert pid == plan["plan_id"]
    loaded = sp.load_shot_plan(pid, db)
    assert loaded == plan
    assert sp.load_shot_plan("0" * 64, db) is None
    rows = sp.list_shot_plans(db)
    assert len(rows) == 1 and rows[0]["camera_name"] == "target_orbit"


def test_plan_db_creates_only_shot_plans_table(tmp_path):
    import sqlite3
    db = tmp_path / "cinematic.db"
    sp.persist_shot_plan(_plan(), db)
    con = sqlite3.connect(db)
    tables = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    con.close()
    assert tables == {"shot_plans"}


def test_plan_id_excludes_created_utc(tmp_path):
    db = tmp_path / "cinematic.db"
    plan = _plan()
    sp.persist_shot_plan(plan, db)
    sp.persist_shot_plan(plan, db)   # upsert, no dup
    assert len(sp.list_shot_plans(db)) == 1
