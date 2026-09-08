"""Capabilities carry evidence; profiles speak film, not cvars."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from engine.pantheon import capabilities as CAP
from engine.pantheon import visual_profile as VP

REPO = Path(__file__).resolve().parents[2]


# ── the registry is tied to the runtime capture ────────────────────────────

@pytest.mark.skipif(not CAP.RUNTIME_CVARLIST.exists(), reason="no 11.3 cvarlist capture")
def test_every_execution_proven_cvar_was_listed_by_the_running_client():
    """EXECUTION_PROVEN must mean the RUNNING 11.3 binary listed it. A cvar
    the engine does not register is accepted and silently ignored."""
    registered = CAP.runtime_registered_cvars()
    lower = {c.lower() for c in registered}
    for cap in CAP.WOLFCAM_11_3.values():
        if cap.evidence is not CAP.Evidence.EXECUTION_PROVEN:
            continue
        if cap.measured:
            # Evidence of a different kind: the engine was observed ACTING on
            # the cvar. Stronger than a listing, and the only thing available
            # for a family the probe never asked about.
            assert len(cap.measured) >= 40,                 f"{cap.name} claims a measurement without describing it"
            continue
        for cvar in cap.cvars:
            assert cvar.lower() in lower, (
                f"{cap.name} claims EXECUTION_PROVEN for {cvar}, which the "
                f"11.3 cvarlist capture does not contain")


@pytest.mark.skipif(not CAP.RUNTIME_CVARLIST.exists(), reason="no 11.3 cvarlist capture")
def test_force_team_model_is_settled_as_absent():
    """It WAS unknown because the family probe never asked a wildcard that
    could match it. The 2026-09-06 census asked for everything, and the name
    is in no inventory at all: not the runtime, not the 12.7 source scan, not
    the binary strings. Absent, not merely unproven."""
    cap = CAP.get("FORCE_TEAM_MODEL_SWITCH")
    assert cap.evidence is CAP.Evidence.UNKNOWN and not cap.usable
    assert cap.cvars == ("cg_forceTeamModel",)
    assert "ABSENT" in cap.how and "census" in cap.how
    assert "cg_team*" in cap.note, "it should say what to use instead"
    with pytest.raises(CAP.CapabilityUnavailable):
        CAP.require("FORCE_TEAM_MODEL_SWITCH")
def test_enemy_and_teammate_are_separate_mechanisms():
    """The whole review requirement rests on this: forcing the enemy must not
    touch a teammate. They are different cvar families, and cg_forceModel --
    which cannot tell them apart -- is a different capability again."""
    enemy = CAP.get("FORCE_ENEMY_MODEL")
    team = CAP.get("FORCE_TEAM_MODEL")
    every = CAP.get("FORCE_ALL_MODELS")
    assert not (set(enemy.cvars) & set(team.cvars))
    assert every.cvars == ("cg_forceModel",)
    assert "cannot distinguish" in every.note
    assert enemy.usable and team.usable and every.usable


def test_a_capability_with_no_route_is_unknown_not_false():
    for name in ("ACTOR_ID_PASS", "PLAYER_MASK", "NORMAL_PASS", "MOTION_PASS"):
        cap = CAP.get(name)
        assert cap.evidence is CAP.Evidence.UNKNOWN
        assert cap.probe, f"{name} does not say what would settle it"
    # The depth SWITCHES are registered in 11.3, so this one is no longer
    # unknown -- it is partial, and still below the usable bar, because a
    # registered cvar is not a produced file.
    depth = CAP.get("DEPTH_CAPTURE")
    assert depth.evidence is CAP.Evidence.SOURCE_REGISTERED
    assert not CAP.supports("DEPTH_CAPTURE")
    assert CAP.supports("BEAUTY_PASS")
def test_minimised_is_not_the_offscreen_capability():
    cap = CAP.get("HIDDEN_OFFSCREEN_CONTEXT")
    assert "SW_SHOWMINNOACTIVE" in cap.note and "NOT this capability" in cap.note


# ── profiles ───────────────────────────────────────────────────────────────

def test_the_review_profile_says_what_the_user_asked_for():
    p = VP.profile("REVIEW")
    assert p.enemy is VP.Appearance.READABLE
    assert (p.enemy_model, p.enemy_skin) == (VP.KEEL, VP.BRIGHT)
    assert p.enemy_colour == VP.PANTHEON_GREEN
    assert p.teammate is VP.Appearance.AUTHENTIC
    assert p.self_view is VP.Appearance.AUTHENTIC
    d = p.as_dict()
    assert "cvar" not in repr(d).lower() and "cg_" not in repr(d)


def test_resolving_the_review_profile_forces_only_the_enemy():
    c = VP.profile("REVIEW").resolve()
    assert c["cg_enemyModel"] == '"keel/bright"'
    assert c["cg_enemyHeadModel"] == '"keel/bright"'
    for part in ("Legs", "Torso", "Head"):
        assert c[f"cg_enemy{part}Skin"] == '"bright"'
        assert c[f"cg_enemy{part}Color"], "the enemy colour was not written"
    # teammates and self keep what the demo authored
    for part in ("Model", "HeadModel"):
        assert c[f"cg_team{part}"] == '""'
    for part in ("Legs", "Torso", "Head"):
        assert c[f"cg_team{part}Skin"] == '""'
    # and the switch that would override everyone is off
    assert c["cg_forceModel"] == 0


def test_the_authentic_profile_clears_the_whole_family():
    """A stale q3config once held cg_enemyHeadModel keel/bright and made
    every character the same figure. Clearing is how the demo's own cast
    survives."""
    c = VP.profile("AUTHENTIC").resolve()
    for k, v in c.items():
        if k.startswith(("cg_enemyModel", "cg_enemyHead", "cg_enemyTorso",
                         "cg_enemyLegs", "cg_teamModel", "cg_teamHead",
                         "cg_teamTorso", "cg_teamLegs")):
            assert v == '""', f"{k} = {v!r}, expected cleared"
    assert c["cg_forceModel"] == 0


def test_the_enemy_colour_is_one_integer_not_a_triple():
    """PROOF 0 measured this on pixels: a space-separated triple is read as
    its first number and the body goes nearly black."""
    c = VP.profile("REVIEW").resolve()
    val = str(c["cg_enemyLegsColor"])
    assert " " not in val.strip('"'), f"colour written as a triple: {val!r}"


def test_a_profile_refuses_a_capability_the_backend_has_not_proven(monkeypatch):
    downgraded = dict(CAP.WOLFCAM_11_3)
    downgraded["FORCE_ENEMY_MODEL"] = CAP.Capability(
        "FORCE_ENEMY_MODEL", CAP.Evidence.SOURCE_REGISTERED, "12.7 source only",
        ("cg_enemyModel",), probe="cvarlist on the running client")
    monkeypatch.setitem(CAP.BACKENDS, "TEST_BACKEND", downgraded)
    with pytest.raises(CAP.CapabilityUnavailable) as ei:
        VP.profile("REVIEW").resolve("TEST_BACKEND")
    assert "SOURCE_REGISTERED" in str(ei.value)


def test_xray_is_asked_for_semantically_never_as_cg_wh():
    p = VP.profile("REVIEW_XRAY")
    assert p.xray_enemy and "XRAY_PLAYER" in p.required_capabilities()
    assert "cg_wh" not in repr(p.as_dict())
    assert VP.profile("REVIEW_XRAY").resolve()["cg_wh"] == 1


# ── callers speak film, not engine ─────────────────────────────────────────

def test_only_the_backend_layer_spells_cvars():
    """A cvar name outside these files means a caller learned engine detail."""
    allowed = {
        "engine/pantheon/visual_profile.py",     # the one translator
        "engine/pantheon/capabilities.py",       # names them as backend detail
        "engine/pantheon/engine_inventory.py",   # the raw-to-semantic mapping
        "engine/pantheon/engine_census.py",      # asks the engine for its own
        "engine/pantheon/shot.py",               # the WOLFCAM_REFERENCE backend
        "engine/pantheon/offscreen.py",          # the PANTHEON_QUAKE_OFFSCREEN backend
        "engine/pantheon/cvar_probe.py",         # RUNTIME_CAPABILITY_PROOF
        "engine/pantheon/ab_scene.py",           # the A/B capture harness
        "engine/pantheon/color_format.py",       # the cvar value format itself
        "engine/pantheon/proof0_color.py", "engine/pantheon/proof_b_identity.py",
        "engine/pantheon/proof_c_rails.py", "engine/pantheon/cast_proof.py",
        "engine/pantheon/presenter_proof.py", "engine/pantheon/instruction_proof.py",
        "engine/pantheon/proofs.py", "engine/pantheon/ca_explainer.py",
        "engine/pantheon/presenter_film.py", "engine/pantheon/measure.py",
    }
    offenders: list[str] = []
    for path in (REPO / "engine" / "pantheon").rglob("*.py"):
        rel = path.relative_to(REPO).as_posix()
        if rel in allowed or "__pycache__" in rel:
            continue
        src = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                    and node.value.startswith(("cg_", "r_", "cl_avi")) \
                    and len(node.value) > 4:
                offenders.append(f"{rel}:{node.lineno} -> {node.value}")
    assert not offenders, ("engine code spells cvars outside the backend layer; "
                           f"ask for a capability instead: {offenders[:6]}")
