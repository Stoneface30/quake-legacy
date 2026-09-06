"""INTEGRATION: a note written through the storage API reaches production.

WHY THIS FILE EXISTS SEPARATELY FROM `test_production_contract.py`.

That file hands `choreography_input` a Scene it built itself, with the
annotations already attached. It proves the bridge preserves a note it was
handed. It cannot prove the note ever leaves the database -- and in fact it
did not: `scene.build_scene` merged `human_role` and `usage_state` onto its
events and silently dropped the text, while `scene_event_notes` lived in the
HTTP router where the scene builder could not see it. Every unit test passed
the whole time.

So these tests start from a WRITE through the same storage API the reviewer
uses, and end at the production entrypoint, with nothing injected in
between:

    creative_annotation.set_event_annotation()   <- the reviewer's own write
      -> scene.build_scene()                     <- production reads storage
        -> production_contract.scene_ref()
          -> build_choreography_input_for_scene(scene_id)

NOTHING HERE TOUCHES LIVE HUMAN TRUTH. The editorial database is redirected
to a temporary file for every test in this module, so no row the user wrote
is read, modified or counted, and no HUMAN_USER row is ever created.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from creative_suite.engine import creative_annotation as ca
from creative_suite.engine import production_contract as pc
from creative_suite.engine import review_corpus as rc
from creative_suite.engine import scene as sc

RECOGNITION_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"

# A real round in the corpus, used because a scene's SHAPE (which kills, which
# movement runs, in what order) is exactly what a fixture would have to fake.
# Read-only: the recognition cache is never written by these tests.
SCENE_HASH = "022936b4669da860db3d236370b6505b1ec886b8f673eee46aeb8899da1673e1"
SCENE_ROUND = 25
SCENE_ID = "SCENE:022936b4669d:25"
JUMPPAD_EVENT = "MOV:43301"

# Not HUMAN_USER. The user is the only one who writes that, and these tests
# must be incapable of manufacturing the director's voice even by accident.
AS_HUMAN = ca.IMPORTED_LEGACY_HUMAN if hasattr(ca, "IMPORTED_LEGACY_HUMAN") \
    else "IMPORTED_LEGACY_HUMAN"


def _corpus_available() -> bool:
    if not RECOGNITION_DB.exists():
        return False
    try:
        with sqlite3.connect(f"file:{RECOGNITION_DB}?mode=ro", uri=True) as c:
            return bool(c.execute(
                "SELECT 1 FROM kill_occurrences_v1 o JOIN kill_events_v1 k "
                "ON k.kill_event_id = o.best_observation_id "
                "WHERE k.content_hash=? AND o.round=? LIMIT 1",
                (SCENE_HASH, SCENE_ROUND)).fetchone())
    except sqlite3.Error:
        return False


pytestmark = pytest.mark.skipif(
    not _corpus_available(),
    reason="needs the local demo corpus; this is an integration proof")


@pytest.fixture()
def isolated_editorial(tmp_path, monkeypatch):
    """Every annotation read and write goes to a throwaway database.

    The user's three genuine reviews live in the real one. A test that can
    reach them is a test that can destroy them.
    """
    db = tmp_path / "editorial.db"
    monkeypatch.setattr(ca, "EDITORIAL_DB", db)
    monkeypatch.setattr(rc, "EDITORIAL_DB", db, raising=False)
    return db


def test_the_isolation_actually_isolates(isolated_editorial):
    """Guard the guard.

    If this fixture ever stopped redirecting, the tests below would start
    writing into the user's editorial database and would still pass.
    """
    assert ca.EDITORIAL_DB == isolated_editorial
    ca.set_event_annotation("MOV:test-isolation", "scratch", ca.TEST)
    live = REPO_ROOT / "creative_suite" / "database" / "editorial.db"
    if live.exists():
        with sqlite3.connect(f"file:{live}?mode=ro", uri=True) as c:
            rows = c.execute(
                "SELECT COUNT(*) FROM scene_event_notes WHERE event_id=?",
                ("MOV:test-isolation",)).fetchone()[0]
        assert rows == 0, "the test wrote into the live editorial database"


# ── the real path ───────────────────────────────────────────────────────────

def test_a_stored_scene_event_note_is_loaded_by_build_scene(isolated_editorial):
    """The defect, pinned.

    `build_scene` used to return `annotation=""` for every event no matter
    what was in storage. A jump pad is the case that matters: it carries no
    verdict, so its note is the ONLY thing the director can say about it.
    """
    before = sc.build_scene(SCENE_HASH, SCENE_ROUND)
    pad = next(e for e in before.events if e.event_id == JUMPPAD_EVENT)
    assert pad.annotation == ""            # nothing written yet

    ca.set_event_annotation(JUMPPAD_EVENT, "music buildup here", AS_HUMAN)

    after = sc.build_scene(SCENE_HASH, SCENE_ROUND)
    pad = next(e for e in after.events if e.event_id == JUMPPAD_EVENT)
    assert pad.annotation == "music buildup here"
    assert pad.annotation_provenance == AS_HUMAN
    assert pad.takes_verdict is False      # still not a reviewable frag


def test_a_stored_note_reaches_the_production_entrypoint(isolated_editorial):
    """DB -> build_scene -> scene_ref -> ChoreographyInput, from a scene_id.

    The entrypoint is given nothing but a string. If any link in the chain
    drops the text, there is no fixture here to supply it.
    """
    ca.set_event_annotation(JUMPPAD_EVENT, "music buildup here", AS_HUMAN)
    ca.set_round_annotation(SCENE_HASH, SCENE_ROUND, "big finish on F4.",
                            AS_HUMAN)

    ci = pc.build_choreography_input_for_scene(SCENE_ID)

    texts = {(n.scope, n.target): n.text for n in ci.direction}
    assert texts[("EVENT", JUMPPAD_EVENT)] == "music buildup here"
    assert texts[("SCENE", SCENE_ID)] == "big finish on F4."
    assert ci.actions, "the scene resolved no ActionTruth references"
    assert all(a.occurrence_id in ci.scene.occurrence_ids for a in ci.actions)


def test_the_stored_note_is_byte_identical_at_the_boundary(isolated_editorial):
    """Storage must not normalise the director's wording either.

    A round trip through SQLite is one more place the text could be trimmed,
    case-folded or have its newlines rewritten.
    """
    raw = "  XRAY!! on the 2nd one -- slow it WAY down (like 0.25x)\n"
    ca.set_event_annotation(JUMPPAD_EVENT, raw, AS_HUMAN)
    ci = pc.build_choreography_input_for_scene(SCENE_ID)
    assert ci.notes_for(JUMPPAD_EVENT)[0].text == raw


def test_a_test_provenance_note_is_stored_but_never_directs(isolated_editorial):
    """The gate that lets these tests exist safely.

    A TEST note travels as far as the Scene -- the reviewer may want to see
    it -- and stops at the production boundary. Only the director's voice
    plans the film.
    """
    ca.set_event_annotation(JUMPPAD_EVENT, "written by a test", ca.TEST)

    s = sc.build_scene(SCENE_HASH, SCENE_ROUND)
    pad = next(e for e in s.events if e.event_id == JUMPPAD_EVENT)
    assert pad.annotation == "written by a test"      # visible in the scene

    ci = pc.build_choreography_input_for_scene(SCENE_ID)
    assert not ci.notes_for(JUMPPAD_EVENT)            # and not direction

    for prov in ("AI_SUGGESTION", "SYSTEM"):
        ca.set_event_annotation(JUMPPAD_EVENT, "not the director", prov)
        ci = pc.build_choreography_input_for_scene(SCENE_ID)
        assert not ci.notes_for(JUMPPAD_EVENT), f"{prov} became direction"


def test_a_round_note_of_test_provenance_never_directs(isolated_editorial):
    ca.set_round_annotation(SCENE_HASH, SCENE_ROUND, "written by a test",
                            ca.TEST)
    ci = pc.build_choreography_input_for_scene(SCENE_ID)
    assert not ci.scene_notes


def test_an_unknown_scene_id_is_refused_not_guessed():
    for bad in ("SCENE:ffffffffffff:9", "not-a-scene", "SCENE:022936b4669d:x",
                f"SCENE:022936b4669d:{sc.NO_ROUND}"):
        with pytest.raises(pc.SceneNotFound):
            pc.resolve_scene_id(bad)


def test_the_live_note_the_user_actually_wrote_is_reachable():
    """The real row, read through the production entrypoint. Read-only.

    Deliberately NOT isolated: this is the one test that proves the wiring
    against the live database the reviewer writes to. It asserts only that
    the persisted text arrives unchanged, and writes nothing.
    """
    stored = ca.get_event_annotation(JUMPPAD_EVENT)
    if not stored or stored.get("provenance") not in pc.HUMAN_PROVENANCES:
        pytest.skip("no live human note on this event yet")
    ci = pc.build_choreography_input_for_scene(SCENE_ID)
    got = ci.notes_for(JUMPPAD_EVENT)
    assert got and got[0].text == stored["annotation"]


# ── review-time capture reaches production too ──────────────────────────────

def test_tags_and_golden_reach_the_production_entrypoint(isolated_editorial,
                                                          monkeypatch):
    """The same lesson as the notes, one layer up.

    A tag the reviewer's page can see and the planning layer cannot is worth
    exactly as much to the film as a note the scene builder never read. So
    this writes through the real tag API and reads back through the real
    entrypoint, with nothing injected.
    """
    from creative_suite.engine import review_tags as rt
    monkeypatch.setattr(rt, "EDITORIAL_DB", isolated_editorial)

    s = sc.build_scene(SCENE_HASH, SCENE_ROUND)
    frag = next(e for e in s.events if e.occurrence_id is not None)

    rt.set_tag(frag.occurrence_id, "PREDICTION", provenance=AS_HUMAN)
    rt.set_tag(frag.occurrence_id, "ROCKET", provenance=AS_HUMAN)
    rt.set_tag(frag.occurrence_id, rt.GOLDEN, provenance=AS_HUMAN)
    rt.set_tag(frag.occurrence_id, rt.KEEP_CONTEXT, provenance=AS_HUMAN)

    ci = pc.build_choreography_input_for_scene(SCENE_ID)
    got = next(e for e in ci.scene.events
               if e.occurrence_id == frag.occurrence_id)

    assert set(got.human_tags) == {"PREDICTION", "ROCKET", "GOLDEN",
                                   "KEEP_CONTEXT"}
    assert got.golden is True
    assert got.keep_context is True
    assert frag.occurrence_id in ci.scene.golden_ids
    assert frag.occurrence_id in ci.scene.keep_context_ids
    # And the camera count, so a planner can tell a brilliant event from a
    # useless POV apart from an ordinary one filmed perfectly.
    assert got.n_povs >= 1


def test_purpose_never_becomes_quality_at_the_boundary(isolated_editorial,
                                                        monkeypatch):
    """Tags must not be readable as a verdict, or as direction.

    A tag is a machine-legible property the human chose. It is not the
    director's wording, and it must not arrive in `direction` where a
    planner reads instructions.
    """
    from creative_suite.engine import review_tags as rt
    monkeypatch.setattr(rt, "EDITORIAL_DB", isolated_editorial)
    s = sc.build_scene(SCENE_HASH, SCENE_ROUND)
    frag = next(e for e in s.events if e.occurrence_id is not None)
    rt.set_tag(frag.occurrence_id, "FUNNY", provenance=AS_HUMAN)

    ci = pc.build_choreography_input_for_scene(SCENE_ID)
    assert not any("FUNNY" in n.text for n in ci.direction)
    got = next(e for e in ci.scene.events
               if e.occurrence_id == frag.occurrence_id)
    assert got.human_role is None or got.human_role.startswith("T")
