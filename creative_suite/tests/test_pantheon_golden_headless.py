"""Golden headless regressions over REAL demos.

Each case is one recorded action from the corpus, chosen through the
performance index, run through extract -> compile -> reextract -> compare
with no game process. The suite skips itself when the index or the demos are
not on this machine; it never launches Wolfcam.

Cases: RUN/STOP, TURN, JUMP, JUMP_PAD, ROCKET, RAIL, TELEPORT, DEATH and an
OBSERVATION GAP (a non-POV client the recorder lost sight of).
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from engine.pantheon import action_graph as AG
from engine.pantheon import headless as H
from engine.pantheon.compare import Status

INDEX_DB = Path("G:/QUAKE_LEGACY/creative_suite/database/performance_index.db")
RECOG_DB = Path("G:/QUAKE_LEGACY/creative_suite/database/frag_recognition.db")
FRAGS_DB = Path("G:/QUAKE_LEGACY/creative_suite/database/frags_rebuilt.db")

pytestmark = pytest.mark.skipif(not INDEX_DB.exists(), reason="performance index not on this machine")

_PARSED: dict[str, tuple] = {}


def _parsed(demo: Path):
    key = str(demo)
    if key not in _PARSED:
        _PARSED.clear()
        _PARSED[key] = H.parse(demo)
    return _PARSED[key]


def _pick(where: str, order: str = "id") -> tuple[Path, int, int, int, int] | None:
    """(demo, client, start, end, t) for the first index row matching."""
    con = sqlite3.connect(f"file:{INDEX_DB.as_posix()}?mode=ro", uri=True, timeout=30)
    row = con.execute(
        f"select d.path, a.client, a.start_ms, a.end_ms, a.t_ms from actions a "
        f"join demos d on d.demo_hash=a.demo_hash where {where} and d.error is null "
        f"order by {order} limit 1").fetchone()
    con.close()
    if row is None or not Path(row[0]).exists():
        return None
    return Path(row[0]), row[1], row[2], row[3], row[4]


def _loop(demo: Path, client: int, lo: int, hi: int, label: str, tmp_path: Path):
    parsed = _parsed(demo)
    tr = H.extract_performance(demo, client, lo, hi, parsed=parsed)
    compiled = H.compile_performance(tr)
    compiled.save(tmp_path / f"{label}.dm_73")
    back = H.reextract(compiled)
    d = H.compare(tr, back["PERF"], retarget=compiled.retarget, intentional=compiled.intentional)
    return tr, d


def _assert_faithful(d, *tracks):
    bad = {k: v.status.value for k, v in d.tracks.items()
           if v.status in (Status.MISSING, Status.INVALID)}
    assert not bad, (bad, d.summary())
    for t in tracks:
        assert d.tracks[t].status in (Status.MATCHED, Status.WITHIN_TOLERANCE), d.tracks[t]


def test_golden_jump_pad(tmp_path):
    pick = _pick("a.kind='JUMP_PAD' and a.is_pov=1 and a.samples>=100 and a.airborne_ms>=800")
    if pick is None:
        pytest.skip("no jump pad in the index")
    demo, client, lo, hi, t = pick
    tr, d = _loop(demo, client, lo, hi, "jump_pad", tmp_path)
    _assert_faithful(d, "position", "velocity", "airborne", "yaw", "animation", "event:jump_pad")
    g = AG.build(tr)
    assert g.of_kind("JUMP_PAD") and g.chain("JUMP_PAD", "AIRBORNE")


def test_golden_rocket_kill(tmp_path):
    pick = _pick("a.kind='FIRE_ROCKET' and a.outcome='KILL' and a.projectile_samples>=8 and a.is_pov=1")
    if pick is None:
        pytest.skip("no rocket kill in the index")
    demo, client, lo, hi, t = pick
    tr, d = _loop(demo, client, lo, hi, "rocket", tmp_path)
    _assert_faithful(d, "position", "projectiles", "event:fire_weapon")
    g = AG.build(tr)
    assert g.chain("FIRE", "PROJECTILE")


def test_golden_rail(tmp_path):
    pick = _pick("a.kind='FIRE_RAIL' and a.is_pov=1 and a.outcome in ('HIT','KILL') and a.max_yaw_rate>=300")
    if pick is None:
        pytest.skip("no rail in the index")
    demo, client, lo, hi, t = pick
    tr, d = _loop(demo, client, lo, hi, "rail", tmp_path)
    _assert_faithful(d, "position", "yaw", "event:fire_weapon")
    g = AG.build(tr)
    assert not g.of_kind("PROJECTILE") or all(n.attrs["weapon"] != "RAIL" for n in g.of_kind("PROJECTILE"))
    assert any(n.attrs.get("weapon") == "RAIL" for n in g.of_kind("FIRE"))


def test_golden_run_stop_and_turn(tmp_path):
    pick = _pick("a.kind='FIRE_ROCKET' and a.is_pov=1 and a.max_speed>=300 and a.max_yaw_rate>=400")
    if pick is None:
        pytest.skip("no fast turning trace in the index")
    demo, client, lo, hi, t = pick
    tr, d = _loop(demo, client, lo, hi, "run_turn", tmp_path)
    _assert_faithful(d, "position", "velocity", "yaw", "pitch")
    g = AG.build(tr)
    assert g.of_kind("RUN")
    assert g.of_kind("TURN") or g.of_kind("FLICK")


def test_golden_jump(tmp_path):
    pick = _pick("a.kind='FIRE_ROCKET' and a.is_pov=1 and a.airborne_ms between 300 and 900 "
                 "and a.max_speed>=250")
    if pick is None:
        pytest.skip("no jump in the index")
    demo, client, lo, hi, t = pick
    tr, d = _loop(demo, client, lo, hi, "jump", tmp_path)
    _assert_faithful(d, "airborne", "animation")
    g = AG.build(tr)
    assert g.of_kind("AIRBORNE") and (g.of_kind("LAND") or g.of_kind("JUMP"))


def test_golden_death(tmp_path):
    pick = _pick("a.kind='KILL' and a.victim is not null and a.is_pov=0 and a.samples>=120")
    if pick is None:
        pytest.skip("no kill in the index")
    demo, killer, lo, hi, t = pick
    parsed = _parsed(demo)
    con = sqlite3.connect(f"file:{INDEX_DB.as_posix()}?mode=ro", uri=True, timeout=30)
    victim = con.execute("select victim from actions where t_ms=? and client=? and kind='KILL' limit 1",
                         (t, killer)).fetchone()[0]
    con.close()
    k = H.extract_performance(demo, killer, lo, hi, parsed=parsed)
    v = H.extract_performance(demo, victim, lo, hi, parsed=parsed)
    if not v.transform:
        pytest.skip("victim never observed in the window")
    compiled = H.compile_performance({"K": k, "V": v})
    compiled.save(tmp_path / "death.dm_73")
    back = H.reextract(compiled)
    dk = H.compare(k, back["K"], intentional=compiled.intentional)
    dv = H.compare(v, back["V"], intentional=compiled.intentional)
    _assert_faithful(dk, "position", "event:obituary")
    _assert_faithful(dv, "position")
    assert AG.build(k).of_kind("KILL")


def test_golden_observation_gap(tmp_path):
    """A non-POV client the recorder lost: the gap survives as UNOBSERVED
    spans and nothing is invented inside it."""
    con = sqlite3.connect(f"file:{INDEX_DB.as_posix()}?mode=ro", uri=True, timeout=30)
    rows = con.execute(
        "select d.path, a.client, a.start_ms, a.end_ms from actions a join demos d "
        "on d.demo_hash=a.demo_hash where a.is_pov=0 and a.samples between 20 and 120 "
        "and d.error is null order by a.id limit 40").fetchall()
    con.close()
    for path, client, lo, hi in rows:
        if not Path(path).exists():
            continue
        tr = H.extract_performance(Path(path), client, lo, hi, parsed=_parsed(Path(path)))
        times = [s.t for s in tr.transform]
        if any(b - a > 50 for a, b in zip(times, times[1:])):
            break
    else:
        pytest.skip("no observation gap among the first candidates")
    compiled = H.compile_performance(tr)
    compiled.save(tmp_path / "gap.dm_73")
    back = H.reextract(compiled)
    d = H.compare(tr, back["PERF"], intentional=compiled.intentional)
    assert d.tracks["position"].unobserved_spans_ms
    assert d.tracks["position"].status in (Status.MATCHED, Status.WITHIN_TOLERANCE)
    # nothing invented: the reproduction carries exactly the observed samples
    assert len(back["PERF"].transform) == len(tr.transform)


def test_golden_teleport(tmp_path):
    if not RECOG_DB.exists():
        pytest.skip("no recognition db")
    con = sqlite3.connect(f"file:{RECOG_DB.as_posix()}?mode=ro", uri=True)
    rows = con.execute(
        "select content_hash, server_time_ms, client from teleport_transits_v1 "
        "where outcome like 'TELEPORT_PLAYER_CONFIRMED%' limit 30").fetchall()
    con.close()
    fr = sqlite3.connect(f"file:{FRAGS_DB.as_posix()}?mode=ro", uri=True)
    case = None
    for h, t, client in rows:
        r = fr.execute("select path from demos where content_hash=?", (h,)).fetchone()
        if r and Path(r[0]).exists():
            case = (Path(r[0]), client, t)
            break
    fr.close()
    if case is None:
        pytest.skip("no teleport demo on disk")
    demo, client, t = case
    tr, d = _loop(demo, client, t - 1500, t + 1500, "teleport", tmp_path)
    _assert_faithful(d, "position")
    g = AG.build(tr)
    assert g.of_kind("TELEPORT"), (g.rejected, [e.kind for e in tr.events])
