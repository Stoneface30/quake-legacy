"""The engine's whole vocabulary, and the rules that keep it honest."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from engine.pantheon import capabilities as CAP
from engine.pantheon import engine_census as EC
from engine.pantheon import engine_inventory as EI

REPO = Path(__file__).resolve().parents[2]
HAVE_CENSUS = EC.load() is not None


pytestmark = pytest.mark.skipif(
    not HAVE_CENSUS, reason="no runtime census on this machine")


# -- nothing is left unsaid --------------------------------------------------

def test_every_engine_item_is_classified():
    """UNKNOWN is a classification; unclassified is not. A new command that
    appears in a future census and matches nothing lands here."""
    items = EI.build()["items"]
    left = EI.unclassified(items)
    assert not left, ("engine items nobody classified: "
                      f"{[i.name for i in left][:8]}")


def test_the_four_inventories_are_kept_apart():
    """They are four different programs. Merging them is how a 12.7 feature
    gets used against an 11.3 binary."""
    src = EI.__file__ and open(EI.__file__, encoding="utf-8").read()
    for origin in ("RUNTIME_11_3", "SOURCE_12_7", "BINARY_11_3", "Q3MME"):
        assert origin in src
    rep = EI.report()
    assert rep["sources"]["runtime_cvars"] > 1000
    assert rep["sources"]["q3mme_commands"] > 0


def test_the_runtime_outranks_the_source():
    """Something the 12.7 tree registers and the 11.3 client does not may not
    be used, however well documented it is."""
    items = {i.name.lower(): i for i in EI.build()["items"]}
    src_only = [i for i in items.values()
                if i.grade is EI.Grade.SOURCE_REGISTERED]
    assert src_only, "the source tree and the runtime cannot be identical"
    for i in src_only[:20]:
        assert not EI.usable(i.name)
        assert "SOURCE_ONLY" in i.note


def test_a_silent_no_op_is_recorded_as_one():
    """A cvar the engine accepted and never registered is the failure mode
    this project keeps hitting; it must be visible, not absent."""
    items = [i for i in EI.build()["items"]
             if i.grade is EI.Grade.RUNTIME_ACCEPTED_UNSET]
    assert items, "the census found no USER_CREATED cvars, which is suspicious"
    for i in items:
        assert "silent no-op" in i.note
        assert not EI.usable(i.name)


# -- the answers this pass was asked for ------------------------------------

def test_cg_force_team_model_is_absent_from_the_target():
    """Asked definitively: it is in no inventory at all."""
    item = EI.find("cg_forceTeamModel")
    assert item is not None
    assert item.grade is EI.Grade.DOCUMENTED_ONLY
    assert item.origins == ()
    cap = CAP.get("FORCE_TEAM_MODEL_SWITCH")
    assert not cap.usable and "ABSENT" in cap.how


def test_the_recorder_cannot_force_their_own_appearance():
    census = EC.load()
    own = [k for k in census["cvars"]
           if k.lower().startswith(("cg_own", "cg_self"))]
    assert own == [], f"the census found self-appearance cvars: {own}"


def test_the_stencil_pass_is_a_silent_no_op_and_the_depth_switch_is_not():
    census = EC.load()
    cv = {k.lower(): v for k, v in census["cvars"].items()}
    assert cv["mme_savestencil"]["registered"] is False
    assert cv["mme_savedepth"]["registered"] is True
    assert not CAP.supports("ACTOR_ID_PASS")
    assert not CAP.supports("DEPTH_CAPTURE"), \
        "a registered switch is not a produced pass"


def test_the_camera_and_seek_commands_are_really_there():
    cmds = set(EC.load()["commands"])
    for name in ("freecam", "follow", "chase", "playcamera", "savecamera",
                 "loadcamera", "seekservertime", "seekclock", "at",
                 "entityfreeze", "remapshader", "runfx", "cvarinterp"):
        assert name in cmds, f"{name} is not in the runtime command list"
    assert CAP.supports("CHASE_ENTITY") and CAP.supports("TIMED_CONSOLE")


def test_commands_the_target_runtime_lacks_are_not_offered():
    """`capture` and `dof` are not in 11.3.

    They are not the same case, and the inventory says so: `capture` is
    q3mme's alone, while `dof` is ALSO in the 12.7 wolfcam source -- the later
    build imported it and the one on disk does not have it. Either way the
    grade keeps it out of production.
    """
    cmds = set(EC.load()["commands"])
    for name in ("capture", "dof"):
        assert name not in cmds
        item = EI.find(name)
        assert item is not None
        assert item.grade in (EI.Grade.UNSUPPORTED_TARGET,
                              EI.Grade.SOURCE_REGISTERED)
        assert not EI.usable(name)
    assert EI.find("capture").origins == ("Q3MME",)
    assert set(EI.find("dof").origins) == {"SOURCE_12_7", "Q3MME"}
    assert not CAP.supports("DEPTH_OF_FIELD")


def test_the_overlay_colour_family_is_a_packed_integer():
    """Corrected from the drawing code: cg_players.c reads the overlay colour
    through cvar->integer, so a decimal triple is read as its first number.
    "60 235 90" became 60, which is 0x00003C, and the silhouettes filmed
    dark blue."""
    from engine.pantheon import color_format as CF
    assert CF.syntax_for("cg_whColor") == CF.ColorSyntax.PACKED_INT
    assert CF.format_for("cg_whColor", (60, 235, 90)) == '"0x3ceb5a"'


# -- no raw engine names above the backend ----------------------------------

ALLOWED_TO_SPELL_COMMANDS = {
    "engine/pantheon/engine_inventory.py",   # its subject is the raw names
    "engine/pantheon/engine_census.py",      # it asks the engine for them
    "engine/pantheon/capabilities.py",       # the registry that maps them
    "engine/pantheon/offscreen.py",          # the backend that issues them
    "engine/pantheon/shot.py",
    "engine/pantheon/cvar_probe.py",
    "engine/pantheon/ab_scene.py",
    "engine/pantheon/color_format.py",
}

RAW_COMMANDS = ("playcamera", "seekservertime", "entityfreeze", "remapshader",
                "runfxat", "cvarinterp", "freecamsetpos", "stopvideo")


def test_no_module_above_the_backend_spells_a_raw_command():
    offenders: list[str] = []
    for path in (REPO / "engine" / "pantheon").rglob("*.py"):
        rel = path.relative_to(REPO).as_posix()
        if rel in ALLOWED_TO_SPELL_COMMANDS or "__pycache__" in rel:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                for cmd in RAW_COMMANDS:
                    if cmd in node.value:
                        offenders.append(f"{rel}:{node.lineno} -> {cmd}")
    assert not offenders, ("raw engine commands outside the backend layer: "
                           f"{offenders[:6]}")
