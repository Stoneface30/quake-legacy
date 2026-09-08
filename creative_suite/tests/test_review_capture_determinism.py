"""A review clip must look the same whoever last used the engine.

WolfcamQL archives every CVAR_ARCHIVE value into its own `q3config.cfg` and
reads that file back at startup. So anything ever set in an interactive
session -- a speedometer switched on to check something, an FPS counter left
running -- survives into the next launch and is burned into the next capture.
That is how a `242ups` readout once appeared in a review clip no review cvar
had asked for.

The fix is not to wipe the user's config. It is for the review profile to
state its own answer for every HUD element it does not want, and for that
statement to be executed AFTER the archived config has been read. These tests
pin both halves; without the second one, the first is decoration.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import master_profile as mp
from creative_suite.engine import wolfcam_capture as wc


# Every route by which the engine can draw something over review footage that
# the reviewer did not ask for. Movement metrics belong in the dossier, where
# they carry their provenance -- not burned into pixels where they cannot be
# questioned.
HUD_LEAK_ROUTES = (
    "cg_drawSpeed",
    "cg_drawSpeedometer",
    "cg_drawFPS",
    "cg_lagometer",
    "cg_drawAttacker",
    "cg_drawRewards",
    "cg_drawKeys",
    "cg_drawPickupItems",
    "cg_drawAmmoWarning",
)


@pytest.fixture()
def staging(tmp_path):
    (tmp_path / "wolfcam-ql").mkdir()
    return tmp_path


def _review_profile() -> dict:
    return mp.PROFILES[mp.profile_for_intent("DIRECTOR_REVIEW")]


def test_the_review_profile_pins_every_hud_leak_route():
    """A missing pin fails here, not in a captured clip.

    `None` is not `0`: deleting one of these lines must break the test rather
    than quietly reopening the route to whatever was archived.
    """
    prof = _review_profile()
    missing = [c for c in HUD_LEAK_ROUTES if c not in prof]
    assert not missing, f"unpinned HUD routes: {missing}"
    wrong = {c: prof[c] for c in HUD_LEAK_ROUTES if prof[c] != 0}
    assert not wrong, f"HUD routes not silenced: {wrong}"


def test_the_pins_reach_the_cfg_the_engine_actually_reads(tmp_path):
    """Pinned in the dict is not pinned on disk.

    `ensure_install()` once returned early when the staging directory already
    existed, so a newly added profile's cfg was never written and the capture
    ran with none of its cvars. A value that never reaches a file is a value
    the engine never sees.
    """
    name = mp.profile_for_intent("DIRECTOR_REVIEW")
    cfg_name = mp._CFG_FILES[name]
    gamedir = tmp_path / "wolfcam-ql"
    gamedir.mkdir()
    mp.write(gamedir)                      # the same call ensure_install makes
    written = gamedir / cfg_name
    assert written.exists(), f"{cfg_name} was never written"
    text = written.read_text(encoding="utf-8", errors="replace")
    for cvar in HUD_LEAK_ROUTES:
        assert f"seta {cvar} 0" in text, f"{cvar} not silenced in {cfg_name}"


def test_the_profile_cfg_runs_after_the_archived_config(staging):
    """Ordering is the whole point.

    `q3config.cfg` is read at engine startup. The profile cfg is exec'd from
    `cgamepostinit.cfg`, which runs after cgame init -- so the profile's
    answer is the last write and wins over whatever was archived. If the
    capture cfg ever stopped exec'ing the profile, every pin above would
    still pass and the footage would still leak.
    """
    name = mp.profile_for_intent("DIRECTOR_REVIEW")
    cfg = wc.write_capture_cfg(
        [{"clip_name": "rp_test", "start_ms": 100_000, "end_ms": 106_000}],
        staging, profile=name)
    assert cfg.splitlines()[0] == f"exec {mp._CFG_FILES[name]}"
    post = (staging / "wolfcam-ql" / "cgamepostinit.cfg").read_text()
    assert "exec capture.cfg" in post


def test_a_review_capture_does_not_use_the_batch_profile(staging):
    """`profile=None` means the BATCH profile, and it once meant that here.

    The same defaulting put opponent handles into six public clips. Review
    has its own profile with its own id, and asking for the wrong one must
    produce a visibly different cfg rather than a silent substitution.
    """
    review = mp.profile_for_intent("DIRECTOR_REVIEW")
    default_cfg = wc.write_capture_cfg(
        [{"clip_name": "a", "start_ms": 1_000, "end_ms": 7_000}], staging)
    review_cfg = wc.write_capture_cfg(
        [{"clip_name": "a", "start_ms": 1_000, "end_ms": 7_000}], staging,
        profile=review)
    assert default_cfg != review_cfg
    assert mp._CFG_FILES[review] in review_cfg


def test_the_review_profile_id_changes_when_its_cvars_change():
    """The proxy cache is keyed by profile id.

    If the id did not move with the cvars, a footage change would be served
    from a cache captured under the old settings and nobody would know.
    """
    name = mp.profile_for_intent("DIRECTOR_REVIEW")
    before = mp.profile_id(name)
    prof = dict(mp.PROFILES[name])
    prof["cg_drawFPS"] = 1
    mp.PROFILES["__determinism_probe__"] = prof
    try:
        assert mp.profile_id("__determinism_probe__") != before
    finally:
        del mp.PROFILES["__determinism_probe__"]
