"""Round-start "3-2-1-FIGHT" cinematic treatment system.

Mirrors test_camera_paths.py's BSP skip-if-unavailable pattern and
pantheon_ads's assign_set() determinism/repetition-control expectations,
applied to creative_suite.engine.round_intro.
"""
import json
import sys
from pathlib import Path

import pytest
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import camera_paths as cp
from creative_suite.engine import round_intro as ri
from creative_suite.engine import timeline as tl

PK3 = REPO_ROOT / "output" / "demo_v2" / "_wolfcam_staging" / "baseq3" / "pak00.pk3"

SMALL = (320, 180)  # keep rendering fast in tests; production uses 1920x1080


# ── catalog shape ────────────────────────────────────────────────────────────

def test_catalog_has_8_to_10_treatments():
    assert 8 <= len(ri.CATALOG) <= 10


def test_catalog_names_unique():
    names = [t.name for t in ri.CATALOG]
    assert len(names) == len(set(names))


def test_catalog_uses_all_four_camera_functions():
    fns = {t.camera_fn_name for t in ri.CATALOG}
    assert fns == {"orbit", "vertical_orbit", "side_track", "top_down"}


def test_catalog_graphic_styles_distinct():
    styles = {t.graphic_style for t in ri.CATALOG}
    # genuinely distinct styles, not one style reused as a palette swap
    assert len(styles) == len(ri.CATALOG)


def test_by_name_matches_catalog():
    assert set(ri.BY_NAME) == {t.name for t in ri.CATALOG}
    for t in ri.CATALOG:
        assert ri.BY_NAME[t.name] is t


# ── deterministic assignment + repetition control ───────────────────────────

def test_assign_treatment_deterministic():
    a = ri.assign_treatment("asylum", "abc123", 2, [])
    b = ri.assign_treatment("asylum", "abc123", 2, [])
    assert a == b


def test_assign_treatment_varies_with_inputs():
    picks = {ri.assign_treatment("asylum", "abc123", r, []) for r in range(10)}
    assert len(picks) > 1, "assignment should vary across round numbers"


def test_assign_treatment_recency_demotion_avoids_immediate_repeats():
    history: list[dict] = []
    picks = []
    for round_num in range(12):
        name = ri.assign_treatment("campgrounds", "deadbeef", round_num, history)
        history.append({"treatment": name})
        picks.append(name)
    # never repeats the immediately preceding treatment...
    assert all(picks[i] != picks[i + 1] for i in range(len(picks) - 1))
    # ...nor the one before that (matches the "recent 2" demotion window)
    assert all(picks[i] != picks[i + 2] for i in range(len(picks) - 2))


def test_assign_and_log_reproducibility(tmp_path, monkeypatch):
    log_path = tmp_path / "round_intro_assignments.json"
    monkeypatch.setattr(ri, "ASSIGN_LOG", log_path)
    name1 = ri.assign_and_log("asylum", "hash1", 0)
    assert log_path.exists()
    logged = json.loads(log_path.read_text())
    assert logged[-1]["treatment"] == name1
    assert logged[-1]["map"] == "asylum"
    # replaying the same history reproduces the same pick
    name2 = ri.assign_treatment("asylum", "hash1", 0, ri.load_history()[:-1])
    assert name2 == name1


# ── graphic rendering ────────────────────────────────────────────────────────

@pytest.mark.parametrize("treatment", ri.CATALOG, ids=lambda t: t.name)
@pytest.mark.parametrize("word", ri.COUNTDOWN_WORDS)
def test_render_countdown_graphic_all_combinations(treatment, word):
    im = ri.render_countdown_graphic(treatment, word, size=SMALL)
    assert isinstance(im, Image.Image)
    assert im.size == SMALL
    assert im.mode == "RGB"


def test_render_countdown_graphic_deterministic():
    t = ri.CATALOG[0]
    a = ri.render_countdown_graphic(t, "FIGHT", size=SMALL).tobytes()
    b = ri.render_countdown_graphic(t, "FIGHT", size=SMALL).tobytes()
    assert a == b


def test_build_sheet_creates_preview_image(tmp_path, monkeypatch):
    out_dir = tmp_path / "round_intro_assets"
    monkeypatch.setattr(ri, "OUT_DIR", out_dir)
    out = ri.build_sheet()
    assert out.exists()
    im = Image.open(out)
    assert im.width > 0 and im.height > 0


# ── round-start timing approximation ────────────────────────────────────────

def test_default_countdown_window_is_documented_approximation():
    start, end = ri.default_countdown_window(12000.0)
    assert start == 12000.0
    assert end - start == ri.DEFAULT_COUNTDOWN_MS
    assert ri.DEFAULT_COUNTDOWN_MS == len(ri.COUNTDOWN_WORDS) * ri.DEFAULT_BEAT_MS


# ── camera plan ──────────────────────────────────────────────────────────────

SPAWN = (128.0, -64.0, 24.0)


@pytest.mark.parametrize("treatment", ri.CATALOG, ids=lambda t: t.name)
def test_build_camera_plan_produces_valid_keyframes(treatment):
    plan = ri.build_camera_plan(treatment, 10000.0, 14000.0, SPAWN)
    kfs = plan["keyframes"]
    assert kfs, f"{treatment.name} produced no keyframes"
    for kf in kfs:
        assert kf["t_ms"] >= 0
        assert len(kf["pos"]) == 3
        assert len(kf["angles"]) == 3
        assert kf["fov"] > 0
    assert plan["base_servertime"] == 10000
    assert isinstance(plan["timeline"], tl.Timeline)


def test_build_camera_plan_rejects_non_positive_duration():
    t = ri.CATALOG[0]
    with pytest.raises(ValueError):
        ri.build_camera_plan(t, 14000.0, 14000.0, SPAWN)
    with pytest.raises(ValueError):
        ri.build_camera_plan(t, 14000.0, 10000.0, SPAWN)


def test_build_camera_plan_slowmo_treatments_add_timeline_steps():
    slowmo_treatments = [t for t in ri.CATALOG if t.slowmo]
    no_slowmo_treatments = [t for t in ri.CATALOG if not t.slowmo]
    assert slowmo_treatments and no_slowmo_treatments, (
        "catalog should mix slowmo and non-slowmo treatments")
    for t in slowmo_treatments:
        plan = ri.build_camera_plan(t, 10000.0, 14000.0, SPAWN)
        assert len(plan["timeline"].steps) == 2  # slow_to + resume
    for t in no_slowmo_treatments:
        plan = ri.build_camera_plan(t, 10000.0, 14000.0, SPAWN)
        assert len(plan["timeline"].steps) == 0


def test_build_camera_plan_feeds_to_wolfcam_script():
    t = ri.BY_NAME["vertical_arc_dramatic"]
    plan = ri.build_camera_plan(t, 55000.0, 59000.0, SPAWN)
    script = tl.to_wolfcam_script(plan["timeline"], plan["keyframes"],
                                   plan["base_servertime"])
    assert "camera add" in script
    assert "playq3mmecamera" in script
    # camera add lines are anchored at base_servertime + relative t_ms
    first_line = next(l for l in script.splitlines() if l.startswith("camera add"))
    assert first_line.split()[2] == "55000"


def test_build_camera_plan_deterministic():
    t = ri.CATALOG[3]
    p1 = ri.build_camera_plan(t, 20000.0, 24000.0, SPAWN)
    p2 = ri.build_camera_plan(t, 20000.0, 24000.0, SPAWN)
    assert p1["keyframes"] == p2["keyframes"]
    assert p1["timeline"].to_json() == p2["timeline"].to_json()


# ── BSP collision validation on a real map (skip-if-unavailable, mirrors
# test_camera_paths.py's real_tracer fixture) ───────────────────────────────

@pytest.fixture(scope="module")
def real_tracer():
    if not PK3.exists():
        pytest.skip("staging pak00.pk3 not present")
    try:
        tracer = cp.bsp_tracer("aerowalk", str(PK3))
    except Exception as e:
        pytest.skip(f"bsp_geometry unusable: {e}")
    return tracer


@pytest.mark.parametrize("treatment", ri.CATALOG, ids=lambda t: t.name)
def test_camera_plan_bsp_validate_real_map(real_tracer, treatment):
    # Spawn point is arbitrary here (no fixture guarantees an open point on
    # aerowalk at this coordinate) — the assertion is only that validate_path
    # runs cleanly against real geometry, not that every treatment clears it
    # from an unverified spawn (adjust_path is exercised separately in
    # test_camera_paths.py against a known-open point).
    plan = ri.build_camera_plan(treatment, 10000.0, 14000.0, SPAWN)
    ok, report = cp.validate_path(real_tracer, plan["keyframes"])
    assert isinstance(ok, bool)
    assert report["checked"] == len(plan["keyframes"])
