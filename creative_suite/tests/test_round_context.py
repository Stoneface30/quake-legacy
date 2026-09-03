"""Round/team/1vX truth, victory gates, chat privacy, same-tick collapse."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "engine" / "parser"))

from creative_suite.engine import (chat_index as ci, demo_truth as dt,
                                   opportunity_graph as og, round_context as rc)


# ── 1vX arithmetic ──────────────────────────────────────────────────────────

def test_one_v_x_classes_follow_the_counts():
    assert rc.one_v_x_class(1, 1) == rc.ONE_V_ONE
    assert rc.one_v_x_class(1, 3) == rc.ONE_V_THREE
    assert rc.one_v_x_class(1, 6) == rc.ONE_V_MANY
    assert rc.one_v_x_class(2, 3) == rc.NOT_ONE_V_X
    assert rc.one_v_x_class(1, 0) == rc.NOT_ONE_V_X


def test_a_dead_recorder_is_never_in_a_one_v_x():
    assert rc.AliveState(0, 1, 3, me_alive=False).one_v_x == rc.NOT_ONE_V_X
    assert rc.AliveState(0, 1, 3, me_alive=True).one_v_x == rc.ONE_V_THREE


# ── gates ───────────────────────────────────────────────────────────────────

def _ctx(result=dt.ROUND_WIN, my_alive=1, enemy_alive=3, mates=2, opps=4):
    return rc.RoundContext(1, 0, 10_000_000, "BLUE", "BLUE", result, mates, opps,
                           rc.AliveState(5_000_000, my_alive, enemy_alive, True))


def test_triumph_requires_a_won_round():
    assert rc.gate_triumph(_ctx(dt.ROUND_WIN)).passed
    assert not rc.gate_triumph(_ctx(dt.ROUND_LOSS)).passed
    assert not rc.gate_triumph(_ctx(dt.ROUND_UNKNOWN)).passed
    assert not rc.gate_triumph(None).passed


def test_unknown_never_satisfies_a_required_gate():
    g = rc.gate_triumph(_ctx(dt.ROUND_UNKNOWN))
    assert not g.passed and "UNKNOWN" in g.reason


def test_a_one_v_x_loss_is_usable_but_not_a_triumph():
    lost = _ctx(dt.ROUND_LOSS)
    assert lost.one_v_x_at_hero == rc.ONE_V_THREE
    g = rc.gate_one_v_x_win(lost)
    assert not g.passed and "ONE_V_THREE" in g.reason


def test_a_one_v_x_win_passes():
    g = rc.gate_one_v_x_win(_ctx(dt.ROUND_WIN))
    assert g.passed and "won" in g.reason


def test_team_round_needs_teammates_and_opponents():
    assert rc.gate_team_round(_ctx(mates=2, opps=4)).passed
    assert not rc.gate_team_round(_ctx(mates=0, opps=4)).passed
    assert not rc.gate_team_round(_ctx(mates=2, opps=1)).passed
    assert not rc.gate_team_round(None).passed


def test_projectile_replay_needs_a_presentable_reconstruction():
    good = og.MomentCandidate(1, og.KIND_ROCKET_IMPACT, 3_000_000, "MY_FRAG",
                              1_000_000, reconstruction_available=True,
                              reconstruction_confidence="EXACT_DETERMINISTIC")
    weak = og.MomentCandidate(2, og.KIND_ROCKET_IMPACT, 3_000_000, "MY_FRAG",
                              1_000_000, reconstruction_available=True,
                              reconstruction_confidence="AMBIGUOUS")
    none = og.MomentCandidate(3, og.KIND_ROCKET_IMPACT, 3_000_000, "MY_FRAG",
                              1_000_000)
    assert rc.gate_projectile_replay(good).passed
    assert not rc.gate_projectile_replay(weak).passed
    assert not rc.gate_projectile_replay(none).passed


# ── round context from tables ───────────────────────────────────────────────

def _db(tmp_path):
    p = tmp_path / "r.db"
    db = sqlite3.connect(p)
    db.executescript("""
    CREATE TABLE scanned_demos(content_hash TEXT, demo_name TEXT, recorder_client INTEGER, error TEXT);
    CREATE TABLE recognized_frags(id INTEGER, content_hash TEXT, server_time_ms INTEGER, victim_client INTEGER, weapon_name TEXT);
    CREATE TABLE round_state_v1(content_hash TEXT, server_time_ms INTEGER, round INTEGER, cs INTEGER, value TEXT);
    CREATE TABLE player_teams_v1(content_hash TEXT, client INTEGER, team TEXT);
    CREATE TABLE team_changes_v1(content_hash TEXT, server_time_ms INTEGER, client INTEGER, team TEXT);
    CREATE TABLE semantic_events_v1(content_hash TEXT, server_time_ms INTEGER, round INTEGER, type TEXT,
      entity_num INTEGER, client_num INTEGER, victim INTEGER, weapon INTEGER, x REAL, y REAL, z REAL, parm INTEGER, source TEXT);
    CREATE TABLE server_text_v1(content_hash TEXT, server_time_ms INTEGER, round INTEGER, kind TEXT, text TEXT);
    """)
    h = "h" * 64
    db.execute("INSERT INTO scanned_demos VALUES (?,?,?,NULL)", (h, "x", 4))
    for c, t in ((4, "BLUE"), (5, "BLUE"), (6, "BLUE"), (1, "RED"), (2, "RED"), (3, "RED"), (7, "RED")):
        db.execute("INSERT INTO player_teams_v1 VALUES (?,?,?)", (h, c, t))
    rows = [(1000, 6, "0"), (1000, 7, "0"), (2000, 661, "\\time\\2000\\round\\1"),
            (9000, 662, "-1"), (9000, 7, "1")]
    for t, cs, v in rows:
        db.execute("INSERT INTO round_state_v1 VALUES (?,?,?,?,?)", (h, t, 1, cs, v))
    # my two mates die, then I kill three of four reds before the hero at 8000
    for t, ent, src in ((3000, 5, "entity"), (3500, 6, "entity"), (4000, 1, "entity"),
                        (5000, 2, "entity"), (6000, 3, "entity")):
        db.execute("INSERT INTO semantic_events_v1 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (h, t, 1, "death", ent, None, None, None, None, None, None, None, src))
    db.commit()
    db.close()
    return p, h


def test_round_context_is_derived_from_the_tables(tmp_path):
    p, h = _db(tmp_path)
    ctx = rc.round_context_for(h, 8000, 4, db_path=p)
    assert ctx is not None
    assert ctx.result == dt.ROUND_WIN and ctx.winner_team == "BLUE"
    assert ctx.teammates == 2 and ctx.opponents == 4
    assert ctx.alive_at_hero.my_alive == 1
    assert ctx.alive_at_hero.enemy_alive == 1
    assert ctx.one_v_x_at_hero == rc.ONE_V_ONE
    assert len(ctx.eliminations) == 3 and len(ctx.teammate_deaths) == 2
    assert ctx.is_team_round


def test_a_side_switch_is_honoured_by_the_timeline(tmp_path):
    p, h = _db(tmp_path)
    db = sqlite3.connect(p)
    db.execute("INSERT INTO team_changes_v1 VALUES (?,?,?,?)", (h, 0, 4, "BLUE"))
    db.execute("INSERT INTO team_changes_v1 VALUES (?,?,?,?)", (h, 7000, 4, "RED"))
    db.commit(); db.close()
    ctx = rc.round_context_for(h, 8000, 4, db_path=p)
    assert ctx.recorder_team == "RED"
    assert ctx.result == dt.ROUND_LOSS          # BLUE won; I am RED now


def test_missing_tables_yield_none_not_an_error(tmp_path):
    p = tmp_path / "empty.db"
    sqlite3.connect(p).close()
    assert rc.round_context_for("x" * 64, 1000, 0, db_path=p) is None


# ── chat privacy ────────────────────────────────────────────────────────────

def test_scrub_strips_colour_codes_and_removes_the_sender():
    slot, text = ci.scrub('^1Some^7Name^7: gg wp', {"somename": 3})
    assert slot == 3
    assert text == "gg wp"
    assert "Name" not in text


def test_an_unknown_sender_becomes_none_not_a_name():
    slot, text = ci.scrub("Stranger: lol", {})
    assert slot is None and text == "lol"


def test_search_returns_slots_and_scrubbed_text(tmp_path):
    p, h = _db(tmp_path)
    db = sqlite3.connect(p)
    db.execute("INSERT INTO server_text_v1 VALUES (?,?,?,?,?)", (h, 8500, 1, "chat", '^2Foo^7: GG that was sick'))
    db.execute("INSERT INTO recognized_frags VALUES (?,?,?,?,?)", (77, h, 8000, 1, "ROCKET"))
    db.commit(); db.close()
    hits = ci.search("gg", db_path=p)
    assert len(hits) == 1
    assert hits[0].text == "GG that was sick"
    assert hits[0].sender_client is None
    assert hits[0].nearest_frag_id == 77 and hits[0].ms_to_nearest_frag == 500
    assert not ci.contains_name(hits[0], ["Foo"])


def test_near_frag_windows_chat_around_the_kill(tmp_path):
    p, h = _db(tmp_path)
    db = sqlite3.connect(p)
    db.execute("INSERT INTO recognized_frags VALUES (?,?,?,?,?)", (77, h, 8000, 1, "ROCKET"))
    db.execute("INSERT INTO server_text_v1 VALUES (?,?,?,?,?)", (h, 9000, 1, "chat", 'A: wow'))
    db.execute("INSERT INTO server_text_v1 VALUES (?,?,?,?,?)", (h, 90000, 1, "chat", 'A: later'))
    db.commit(); db.close()
    hits = ci.near_frag(77, db_path=p)
    assert [x.text for x in hits] == ["wow"]


# ── same-tick temp-entity collapse ──────────────────────────────────────────

def test_same_tick_teleports_collapse_to_one():
    from enrich_semantic_events import collapse_same_tick
    ev = [{"type": "teleport_in", "server_time_ms": 100, "pos_x": 0.0, "pos_y": 0.0, "pos_z": 0.0},
          {"type": "teleport_in", "server_time_ms": 100, "pos_x": 5.0, "pos_y": 0.0, "pos_z": 0.0},
          {"type": "teleport_in", "server_time_ms": 100, "pos_x": 900.0, "pos_y": 0.0, "pos_z": 0.0},
          {"type": "jump", "server_time_ms": 100, "pos_x": 0.0, "pos_y": 0.0, "pos_z": 0.0},
          {"type": "jump", "server_time_ms": 100, "pos_x": 0.0, "pos_y": 0.0, "pos_z": 0.0}]
    kept, dropped = collapse_same_tick(ev)
    assert dropped == 1                             # the 5u twin only
    assert sum(1 for e in kept if e["type"] == "teleport_in") == 2   # 900u apart stays
    assert sum(1 for e in kept if e["type"] == "jump") == 2          # jumps never collapsed


def test_playerstate_events_are_never_collapsed():
    from enrich_semantic_events import collapse_same_tick
    ev = [{"type": "teleport_in", "server_time_ms": 1, "pos_x": 0.0, "pos_y": 0.0, "pos_z": 0.0, "source": "playerstate"},
          {"type": "teleport_in", "server_time_ms": 1, "pos_x": 0.0, "pos_y": 0.0, "pos_z": 0.0, "source": "playerstate"}]
    kept, dropped = collapse_same_tick(ev)
    assert dropped == 0 and len(kept) == 2


# ── duplicate identity ──────────────────────────────────────────────────────

def _dup_db(tmp_path):
    p = tmp_path / "d.db"
    db = sqlite3.connect(p)
    db.executescript("""
    CREATE TABLE scanned_demos(content_hash TEXT, demo_name TEXT, recorder_client INTEGER, error TEXT, map TEXT);
    CREATE TABLE recognized_frags(id INTEGER, content_hash TEXT, server_time_ms INTEGER, victim_client INTEGER, weapon_name TEXT);
    CREATE TABLE missile_samples_v1(content_hash TEXT, server_time_ms INTEGER, entity_num INTEGER, x REAL, y REAL, z REAL);
    """)
    full, cut, twin, other = "a" * 64, "b" * 64, "c" * 64, "d" * 64
    # the recorded world: the cut copy shares it tick for tick; the stranger does not
    for t in range(1500, 3500, 100):
        db.execute("INSERT INTO missile_samples_v1 VALUES (?,?,?,?,?,?)", (full, t, 40, float(t), 1.0, 2.0))
        db.execute("INSERT INTO missile_samples_v1 VALUES (?,?,?,?,?,?)", (cut, t, 40, float(t), 1.0, 2.0))
        db.execute("INSERT INTO missile_samples_v1 VALUES (?,?,?,?,?,?)", (other, t, 40, float(-t), 9.0, 9.0))
    for h in (full, cut, twin, other):
        db.execute("INSERT INTO scanned_demos VALUES (?,?,?,NULL,?)", (h, h[:4], 0, "trinity"))
    kills = [(1000, 3, "ROCKET"), (2000, 5, "RAIL"), (3000, 3, "GRENADE")]
    i = 0
    for t, v, w in kills:
        i += 1; db.execute("INSERT INTO recognized_frags VALUES (?,?,?,?,?)", (i, full, t, v, w))
        i += 1; db.execute("INSERT INTO recognized_frags VALUES (?,?,?,?,?)", (i, twin, t, v, w))
    for t, v, w in kills[1:]:
        i += 1; db.execute("INSERT INTO recognized_frags VALUES (?,?,?,?,?)", (i, cut, t, v, w))
    # same map, same times, different victim on one kill: a different match
    for t, v, w in ((1000, 3, "ROCKET"), (2000, 7, "RAIL")):
        i += 1; db.execute("INSERT INTO recognized_frags VALUES (?,?,?,?,?)", (i, other, t, v, w))
    db.commit(); db.close()
    return p, full, cut, twin, other


def test_exact_twins_and_cut_copies_collapse_but_similar_matches_do_not(tmp_path):
    p, full, cut, twin, other = _dup_db(tmp_path)
    reasons = {}
    rep = rc.canonical_demos(p, reasons=reasons)
    assert rep[twin] == full and reasons[twin] == rc.COLLAPSE_EXACT
    assert rep[cut] == full and reasons[cut] == rc.COLLAPSE_CUT
    assert rep[other] == other and other not in reasons     # one kill differs: not the same match
    assert rep[full] == full


def test_kill_containment_without_world_agreement_is_refused(tmp_path):
    """A one-kill stranger whose tuple fits inside a longer demo is NOT a copy."""
    p, full, cut, twin, other = _dup_db(tmp_path)
    db = sqlite3.connect(p)
    stranger = "e" * 64
    db.execute("INSERT INTO scanned_demos VALUES (?,?,?,NULL,?)", (stranger, "e", 0, "trinity"))
    db.execute("INSERT INTO recognized_frags VALUES (?,?,?,?,?)", (99, stranger, 2000, 5, "RAIL"))
    for t in range(1500, 3500, 100):
        db.execute("INSERT INTO missile_samples_v1 VALUES (?,?,?,?,?,?)", (stranger, t, 40, 5.0, 5.0, float(t)))
    db.commit(); db.close()
    reasons = {}
    rep = rc.canonical_demos(p, reasons=reasons)
    assert rep[stranger] == stranger and reasons[stranger] == rc.REFUSED_CUT
    assert rep[cut] == full and reasons[cut] == rc.COLLAPSE_CUT


def test_cut_copy_collapse_can_be_switched_off(tmp_path):
    p, full, cut, twin, other = _dup_db(tmp_path)
    rep = rc.canonical_demos(p, cut_copies=False)
    assert rep[cut] == cut and rep[twin] == full


# ── camera fields come from the reconstruction ──────────────────────────────

def test_candidate_camera_fields_are_derived_from_the_continuation():
    from creative_suite.engine import projectile_reconstruction as pr
    pts = tuple(pr.PathPoint(t * 25_000, (float(t), 0.0, 0.0), (40.0, 0.0, 0.0),
                             dt.ENTITY_OBSERVED if t < 2 else dt.PHYSICS_RECONSTRUCTED)
                for t in range(0, 11))
    launch = pr.LaunchState(pr.KIND_ROCKET, 0, pts[0].pos, pts[0].vel, dt.ENTITY_OBSERVED)
    cont = pr.Continuation(pr.KIND_ROCKET, launch, pts, pts[-1].t_us, "IMPACT", pts[-1].pos)
    cand = og.MomentCandidate(9, og.KIND_ROCKET_IMPACT, 3_000_000, "MY_FRAG", 1_000_000,
                              **og.reconstruction_fields(cont))
    assert cand.reconstruction_available and cand.supports_omniscient_replay
    assert abs(cand.reconstruction_recorded_fraction - 0.1) < 1e-9
    assert cand.reconstruction_class == dt.PHYSICS_RECONSTRUCTED
    assert cand.camera_text == "EXACT_DETERMINISTIC: 10% recorded, 90% PHYSICS_RECONSTRUCTED"
    assert rc.gate_projectile_replay(cand).passed
    none = og.MomentCandidate(1, og.KIND_ROCKET_IMPACT, 1, "MY_FRAG", 1, **og.reconstruction_fields(None))
    assert none.camera_text == "no projectile path" and not rc.gate_projectile_replay(none).passed


# ── similarity is not identity ──────────────────────────────────────────────

def test_same_map_weapon_and_victim_in_another_recording_is_not_a_duplicate(tmp_path):
    """Two matches on the same map where the recorder kills the same slot with
    the same weapon at different server times: not even a candidate."""
    p, full, cut, twin, other = _dup_db(tmp_path)
    db = sqlite3.connect(p)
    replay = "f" * 64
    db.execute("INSERT INTO scanned_demos VALUES (?,?,?,NULL,?)", (replay, "f", 0, "trinity"))
    for t, v, w in ((1500, 3, "ROCKET"), (2500, 5, "RAIL"), (3500, 3, "GRENADE")):
        db.execute("INSERT INTO recognized_frags VALUES (?,?,?,?,?)", (300 + t, replay, t, v, w))
    db.commit(); db.close()
    reasons = {}
    rep = rc.canonical_demos(p, reasons=reasons)
    assert rep[replay] == replay and replay not in reasons


def test_same_server_time_value_in_another_demo_is_not_a_duplicate(tmp_path):
    """server_time recurs across matches. A one-kill demo whose tuple equals
    a kill in a longer demo stays its own occurrence unless the recorded
    world agrees tick for tick."""
    p, full, cut, twin, other = _dup_db(tmp_path)
    db = sqlite3.connect(p)
    coincidence = "9" * 64
    db.execute("INSERT INTO scanned_demos VALUES (?,?,?,NULL,?)", (coincidence, "9", 0, "trinity"))
    db.execute("INSERT INTO recognized_frags VALUES (?,?,?,?,?)", (901, coincidence, 1000, 3, "ROCKET"))
    for t in range(1500, 3500, 100):      # nearly the same coordinates: 1u off, not identical
        db.execute("INSERT INTO missile_samples_v1 VALUES (?,?,?,?,?,?)", (coincidence, t, 40, float(t) + 1.0, 1.0, 2.0))
    db.commit(); db.close()
    reasons = {}
    rep = rc.canonical_demos(p, reasons=reasons)
    assert rep[coincidence] == coincidence
    assert reasons[coincidence] == rc.REFUSED_CUT
    db = sqlite3.connect(p)
    assert rc.world_agreement(db, coincidence, full) == 0.0
    assert rc.world_agreement(db, cut, full) == 1.0
    db.close()


def test_moment_identity_is_content_hash_plus_time_never_map_plus_time():
    a = og.MomentCandidate(1, og.KIND_ROCKET_IMPACT, 1_000_000, "MY_FRAG", 1_000_000, content_hash="a" * 64)
    b = og.MomentCandidate(2, og.KIND_ROCKET_IMPACT, 1_000_000, "MY_FRAG", 1_000_000, content_hash="b" * 64)
    assert (a.content_hash, a.useful_duration_us) != (b.content_hash, b.useful_duration_us)


# ── bounded round recovery ──────────────────────────────────────────────────

def test_a_late_score_is_recovered_when_bounded_by_the_next_round():
    """The fixed window misses a score that lands well after the end mark.
    The next round is a bound that is always true."""
    rows = [(0, 6, "0"), (0, 7, "0"),
            (10_000, 662, "-1"),            # round 1 ends
            (18_000, 7, "1"),               # BLUE scores 8 s later
            (30_000, 662, "-1")]            # round 2 ends
    out = dt.round_outcomes(rows, recorder_team="BLUE")
    assert out[0].winner_team == "BLUE" and out[0].result == dt.ROUND_WIN


def test_recovery_never_forces_an_outcome():
    both = [(0, 6, "0"), (0, 7, "0"), (10_000, 662, "-1"),
            (18_000, 6, "1"), (18_500, 7, "1"), (30_000, 662, "-1")]
    assert dt.round_outcomes(both, recorder_team="BLUE")[0].winner_team == dt.ROUND_UNKNOWN
    neither = [(0, 6, "0"), (0, 7, "0"), (10_000, 662, "-1"), (30_000, 662, "-1")]
    assert dt.round_outcomes(neither, recorder_team="BLUE")[0].winner_team == dt.ROUND_UNKNOWN


def test_a_score_belonging_to_the_next_round_is_not_stolen_by_this_one():
    rows = [(0, 6, "0"), (0, 7, "0"),
            (10_000, 662, "-1"),           # round 1 ends, nothing scores
            (30_000, 662, "-1"),           # round 2 ends
            (31_000, 6, "1")]              # RED's point lands after round 2
    out = dt.round_outcomes(rows, recorder_team="RED")
    assert out[0].winner_team == dt.ROUND_UNKNOWN     # round 1 stays unknown
    assert out[1].winner_team == "RED"


def test_already_attributed_rounds_are_untouched_by_recovery():
    """One side rose in the window, so round 1 is settled. A later rise
    belongs to round 2 and must not disturb it."""
    rows = [(0, 6, "0"), (0, 7, "0"), (9_000, 6, "1"), (10_000, 662, "-1"),
            (25_000, 7, "1"), (30_000, 662, "-1")]
    out = dt.round_outcomes(rows, recorder_team="RED")
    assert out[0].winner_team == "RED"      # the in-window rise still wins
    assert out[1].winner_team == "BLUE"


def test_recovery_fills_a_gap_but_never_breaks_a_tie():
    """Both sides rise inside the window: the demo is ambiguous about this
    round, and a later rise is not allowed to cast the deciding vote."""
    rows = [(0, 6, "0"), (0, 7, "0"), (9_000, 6, "1"), (10_000, 662, "-1"),
            (12_000, 7, "1"), (30_000, 662, "-1")]
    assert dt.round_outcomes(rows, recorder_team="RED")[0].winner_team == dt.ROUND_UNKNOWN


# ── time-aware chat sender resolution ───────────────────────────────────────

def test_a_name_is_resolved_at_the_time_the_line_was_said():
    """Slots get reused. A single static map for the whole demo would credit
    a line to whoever holds the slot last."""
    tl = [(0, 3, "foo"), (5000, 3, "bar"), (6000, 7, "foo")]
    assert ci.slot_at(tl, "foo", 1000) == (3, ci.RESOLVED)
    assert ci.slot_at(tl, "foo", 5500) == (None, ci.UNRESOLVED)   # nobody is foo yet
    assert ci.slot_at(tl, "foo", 7000) == (7, ci.RESOLVED)        # a different player
    assert ci.slot_at(tl, "bar", 7000) == (3, ci.RESOLVED)


def test_two_clients_holding_one_name_is_ambiguous_not_a_coin_toss():
    tl = [(0, 3, "foo"), (100, 9, "foo")]
    assert ci.slot_at(tl, "foo", 1000) == (None, ci.AMBIGUOUS)


def test_colour_codes_and_spacing_do_not_change_identity():
    tl = [(0, 4, ci.normalise("^1Pan^7theon"))]
    assert ci.slot_at(tl, "^3PANTHEON", 10) == (4, ci.RESOLVED)
    assert ci.normalise("^1a^2b   c") == "ab c"


def test_a_resolved_chat_line_reports_its_slot_and_never_the_name(tmp_path):
    p, h = _db(tmp_path)
    db = sqlite3.connect(p)
    db.execute("CREATE TABLE player_names_v1(content_hash TEXT, server_time_ms INTEGER, client INTEGER, name TEXT)")
    db.execute("INSERT INTO player_names_v1 VALUES (?,?,?,?)", (h, 0, 5, "^2Foo"))
    db.execute("INSERT INTO server_text_v1 VALUES (?,?,?,?,?)", (h, 8500, 1, "chat", '^2Foo^7: GG that was sick'))
    db.execute("INSERT INTO recognized_frags VALUES (?,?,?,?,?)", (77, h, 8000, 1, "ROCKET"))
    db.commit(); db.close()
    hit = ci.search("gg", db_path=p)[0]
    assert hit.sender_client == 5 and hit.sender_state == ci.RESOLVED
    assert hit.text == "GG that was sick" and "Foo" not in hit.text
    assert not ci.contains_name(hit, ["Foo"])
    assert hit.nearest_frag_id == 77 and hit.ms_to_nearest_frag == 500


def test_a_line_from_an_unknown_name_stays_unresolved(tmp_path):
    p, h = _db(tmp_path)
    db = sqlite3.connect(p)
    db.execute("CREATE TABLE player_names_v1(content_hash TEXT, server_time_ms INTEGER, client INTEGER, name TEXT)")
    db.execute("INSERT INTO server_text_v1 VALUES (?,?,?,?,?)", (h, 8500, 1, "chat", 'Stranger: lol'))
    db.commit(); db.close()
    hit = ci.search("lol", db_path=p)[0]
    assert hit.sender_client is None and hit.sender_state == ci.UNRESOLVED
    assert hit.text == "lol"


def test_a_missing_names_table_degrades_to_unresolved(tmp_path):
    p, h = _db(tmp_path)
    db = sqlite3.connect(p)
    db.execute("INSERT INTO server_text_v1 VALUES (?,?,?,?,?)", (h, 8500, 1, "chat", '^2Foo^7: gg'))
    db.commit(); db.close()
    hit = ci.search("gg", db_path=p)[0]
    assert hit.sender_state == ci.UNRESOLVED and hit.text == "gg"
