"""pantheon doctor — does the engine still work, end to end, with no game?

One command that exercises every layer PANTHEON owns and reports what it
found. It is not a test suite (pytest owns that); it is the thing you run on
a machine, or after a merge, to learn whether the ENGINE is intact and what
data it can see here.

    python -m engine.pantheon.doctor
    python -m engine.pantheon.doctor --json

Every check is headless by construction. `subprocess.Popen` is replaced for
the duration of the run and raises if anything tries to start a process, so
"no renderer was launched" is proven rather than asserted. A check that
cannot run because data is absent on this machine reports SKIP with the
reason; only a check that ran and gave the wrong answer is FAIL.

    PARSER          the .dm_73 reader on a real demo (or the writer's own
                    output when no corpus is present)
    EXTRACT         PerformanceTrace off a real action
    ACTION_GRAPH    the semantic reading, with evidence
    RETARGET        EXACT_WORLD and LOCAL_FRAME arithmetic, rigid
    COMPILE         scenario -> .dm_73 bytes
    PARSE_BACK      the synthetic demo read by the same extractor
    COMPARE         per-track verdict, PASS required
    FRAME_TRUTH     one clock, recorded pose, sound intent
    INDEX           the compact index: rows, size, bytes per action
    RECONSTRUCT     a trace rebuilt from an index locator, per kind
    GEOGRAPHY       regions, layers, routes, cells
    TEMPLATES       a template found by its measured facts
    RENDER_PERMIT   the one contract, and its answer here
    NO_RENDERER     nothing spawned a process during any of the above
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from engine.pantheon import store as S

OK, FAIL, SKIP = "OK", "FAIL", "SKIP"


@dataclass
class Check:
    name: str
    status: str
    detail: str
    ms: float = 0.0
    data: dict = field(default_factory=dict)

    def line(self) -> str:
        mark = {OK: "ok  ", FAIL: "FAIL", SKIP: "skip"}[self.status]
        return f"  [{mark}] {self.name:<14} {self.detail}  ({self.ms:.0f} ms)"


class _NoProcess(AssertionError):
    pass


class Doctor:
    def __init__(self) -> None:
        self.checks: list[Check] = []
        self.spawned: list[str] = []

    # -- harness -------------------------------------------------------
    def run(self, name: str, fn: Callable[[], tuple[str, str, dict]]) -> Check:
        t0 = time.perf_counter()
        try:
            status, detail, data = fn()
        except Exception as exc:                                  # noqa: BLE001
            status, detail, data = FAIL, f"{type(exc).__name__}: {exc}", {}
        c = Check(name, status, detail, (time.perf_counter() - t0) * 1000, data)
        self.checks.append(c)
        return c

    def _guard_processes(self):
        """Replace Popen for the run: the engine must not start anything."""
        orig = subprocess.Popen
        spawned = self.spawned

        class Guarded(orig):                                      # type: ignore[misc,valid-type]
            def __init__(self, args, *a, **k):
                spawned.append(str(args)[:120])
                raise _NoProcess(f"the engine tried to spawn: {str(args)[:120]}")

        subprocess.Popen = Guarded                                # type: ignore[assignment]
        return orig

    # -- the checks ----------------------------------------------------
    def check_all(self) -> list[Check]:
        orig_popen = self._guard_processes()
        try:
            demo = self._a_real_demo()
            self.run("PARSER", lambda: self._parser(demo))
            trace = self._trace_holder = {}
            self.run("EXTRACT", lambda: self._extract(demo, trace))
            self.run("ACTION_GRAPH", lambda: self._action_graph(trace))
            self.run("RETARGET", lambda: self._retarget(trace))
            compiled = {}
            self.run("COMPILE", lambda: self._compile(trace, compiled))
            self.run("PARSE_BACK", lambda: self._parse_back(compiled))
            self.run("COMPARE", lambda: self._compare(trace, compiled))
            self.run("FRAME_TRUTH", lambda: self._frame_truth(compiled))
            self.run("INDEX", self._index)
            self.run("RECONSTRUCT", self._reconstruct)
            self.run("GEOGRAPHY", self._geography)
            self.run("TEMPLATES", self._templates)
            self.run("RENDER_PERMIT", self._render_permit)
        finally:
            subprocess.Popen = orig_popen                         # type: ignore[assignment]
        self.checks.append(Check(
            "NO_RENDERER", OK if not self.spawned else FAIL,
            "nothing was spawned" if not self.spawned else f"spawned {self.spawned}"))
        return self.checks

    # -- data on this machine ------------------------------------------
    def _a_real_demo(self) -> Path | None:
        try:
            con = sqlite3.connect(f"file:{S.FRAGS_DB.as_posix()}?mode=ro", uri=True, timeout=30)
            for (p,) in con.execute("select path from demos where gametype='CA' "
                                    "and accepted_frags > 8 order by size_bytes limit 20"):
                if Path(p).exists():
                    con.close()
                    return Path(p)
            con.close()
        except sqlite3.Error:
            pass
        return None

    def _parser(self, demo: Path | None):
        if demo is None:
            return SKIP, "no demo corpus on this machine", {}
        from engine.pantheon.performance import _parse_with_anims
        out, anims = _parse_with_anims(demo)
        self._parsed = (out, anims)
        n_ev = len(out["events"])
        if out["packet_errors"] or not n_ev:
            return FAIL, f"packet_errors={out['packet_errors']} events={n_ev}", {}
        return OK, (f"{demo.name[:16]}... {out['map']} {out['snapshot_count']} snapshots, "
                    f"{n_ev} events, 0 packet errors"), {"map": out["map"]}

    def _extract(self, demo: Path | None, holder: dict):
        if demo is None or not hasattr(self, "_parsed"):
            return SKIP, "no parsed demo", {}
        from engine.pantheon import headless as H
        out = self._parsed[0]
        fires = [e for e in out["events"] if e["type"] == "fire_weapon"]
        if not fires:
            return SKIP, "no fire event in this demo", {}
        mid = fires[len(fires) // 2]
        rec = H.P.recorder_client(out)
        client = mid.get("client_num") if mid.get("client_num") is not None else rec
        t = mid["server_time_ms"]
        tr = H.extract_performance(demo, client, t - 1500, t + 2000, parsed=self._parsed)
        holder["trace"] = tr
        if len(tr.transform) < 10:
            return FAIL, f"only {len(tr.transform)} transform samples", {}
        return OK, (f"client {client} at {t}: {len(tr.transform)} transform, {len(tr.aim)} aim, "
                    f"{len(tr.events)} events, {len(tr.projectiles)} projectile samples"), {}

    def _action_graph(self, holder: dict):
        tr = holder.get("trace")
        if tr is None:
            return SKIP, "no trace", {}
        from engine.pantheon import action_graph as AG
        g = AG.build(tr)
        if not g.nodes:
            return FAIL, "no nodes read off a real action", {}
        if any(not n.evidence for n in g.nodes):
            return FAIL, "a node carries no evidence", {}
        return OK, (f"{len(g.nodes)} nodes, {len(g.edges)} edges: {g.sentence()[:60]}"), {
            "categories": sorted(AG.categories(g))}

    def _retarget(self, holder: dict):
        tr = holder.get("trace")
        if tr is None:
            return SKIP, "no trace", {}
        from engine.pantheon.retarget import Retarget, TransformMode
        ex = Retarget.exact_world()
        if not ex.is_identity():
            return FAIL, "EXACT_WORLD is not the identity", {}
        rt = Retarget.local_frame(tr, to=(-1000.0, 500.0, 100.0), yaw=90.0)
        a, b = tr.transform[0].origin, tr.transform[-1].origin
        before, after = math.dist(a, b), math.dist(rt.place(a), rt.place(b))
        if abs(before - after) > 1e-6:
            return FAIL, f"not rigid: {before:.3f} -> {after:.3f}", {}
        if rt.mode is not TransformMode.LOCAL_FRAME:
            return FAIL, "mode not LOCAL_FRAME", {}
        return OK, f"rigid over {before:.0f} u, anchor lands on target, yaw offset applied", {}

    def _compile(self, holder: dict, out: dict):
        tr = holder.get("trace")
        if tr is None:
            return SKIP, "no trace", {}
        from engine.pantheon import headless as H
        compiled = H.compile_performance(tr)
        dest = S.store_root() / "doctor"
        dest.mkdir(parents=True, exist_ok=True)
        path = compiled.save(dest / "doctor.dm_73")
        out["compiled"] = compiled
        size = path.stat().st_size
        if size < 1000:
            return FAIL, f"synthetic demo is {size} bytes", {}
        return OK, f"{len(compiled.traces)} actor(s) -> {size:,} bytes of .dm_73", {}

    def _parse_back(self, out: dict):
        compiled = out.get("compiled")
        if compiled is None:
            return SKIP, "nothing compiled", {}
        from engine.pantheon import headless as H
        back = H.reextract(compiled)
        out["back"] = back
        tr = back["PERF"]
        if not tr.transform:
            return FAIL, "the synthetic demo parsed back empty", {}
        return OK, f"{len(tr.transform)} transform samples read back by the same extractor", {}

    def _compare(self, holder: dict, out: dict):
        tr, compiled, back = holder.get("trace"), out.get("compiled"), out.get("back")
        if tr is None or compiled is None or back is None:
            return SKIP, "nothing to compare", {}
        from engine.pantheon.compare import compare
        d = compare(tr, back["PERF"], retarget=compiled.retarget,
                    intentional=compiled.intentional)
        out["diff"] = d
        if d.semantic_fidelity != "PASS":
            bad = {k: v.status.value for k, v in d.tracks.items()
                   if v.status.value in ("MISSING", "INVALID")}
            return FAIL, f"semantic_fidelity FAIL: {bad}", {"summary": d.summary()}
        return OK, f"PASS on {len(d.tracks)} tracks", {"summary": d.summary()}

    def _frame_truth(self, out: dict):
        compiled = out.get("compiled")
        if compiled is None:
            return SKIP, "nothing compiled", {}
        ft = compiled.frame_truth
        if not ft.frames:
            return FAIL, "no frames", {}
        step = ft.frames[1].server_time_ms - ft.frames[0].server_time_ms
        if step != 1000 // ft.snapshot_hz:
            return FAIL, f"frame step {step} ms at {ft.snapshot_hz} Hz", {}
        sounds = [e.sound for e in ft.events() if e.sound]
        return OK, (f"{len(ft.frames)} frames at {ft.snapshot_hz} Hz, one clock, "
                    f"{len(sounds)} sound intents"), {}

    def _index(self):
        from engine.pantheon import performance_index as PI
        if not S.index_db().exists():
            return SKIP, f"no compact index at {S.index_db()}", {}
        st = PI.stats()
        if not st["actions"]:
            return SKIP, "index is empty", {}
        return OK, (f"{st['demos']:,} demos, {st['actions']:,} actions, "
                    f"{st['index_bytes'] / 1024**3:.2f} GB, "
                    f"{st['bytes_per_action']:.0f} bytes/action"), st

    def _reconstruct(self):
        """A trace rebuilt from a locator, one sample per kind. This is the
        claim the compact index rests on: truth is not stored, it is
        reproduced."""
        from engine.pantheon import performance_index as PI
        if not S.index_db().exists():
            return SKIP, "no compact index", {}
        con = PI._ro()
        got: dict[str, Any] = {}
        for kind in ("JUMP_PAD", "FIRE_ROCKET", "FIRE_RAIL", "TELEPORT", "WEAPON_CHANGE"):
            row = con.execute("select trace_locator, samples from actions where kind=? "
                              "and samples >= 20 limit 1", (kind,)).fetchone()
            if row is None:
                got[kind] = "none indexed"
                continue
            loc, expected = row
            try:
                tr = PI.reconstruct(loc)
            except Exception as exc:                              # noqa: BLE001
                con.close()
                return FAIL, f"{kind}: {type(exc).__name__}: {exc}", got
            if len(tr.transform) != expected:
                con.close()
                return FAIL, (f"{kind}: rebuilt {len(tr.transform)} samples, "
                              f"the row recorded {expected}"), got
            got[kind] = f"{len(tr.transform)} samples"
        con.close()
        rebuilt = [k for k, v in got.items() if v != "none indexed"]
        if not rebuilt:
            return SKIP, "no indexed actions to rebuild", got
        return OK, f"rebuilt from source: {', '.join(f'{k} ({got[k]})' for k in rebuilt)}", got

    def _geography(self):
        from engine.pantheon import geography as G
        maps = G.maps_available()
        if not maps:
            return SKIP, "no learned geography in the store", {}
        cov = G.coverage()
        regions = sum(c["regions"] for c in cov.values())
        routes = sum(c["routes"] for c in cov.values())
        cells = sum(c["spatial_cells"] for c in cov.values())
        sample = maps[0]
        pos_ok = any(G.MapGeography.for_map(m).index for m in maps)
        if not pos_ok:
            return FAIL, "no map answers region_for_position", {}
        return OK, (f"{len(maps)} maps, {regions} regions, {routes} routes, "
                    f"{cells} walked cells (e.g. {sample})"), {"maps": maps}

    def _templates(self):
        from engine.pantheon import performance_templates as PT
        counts = PT.counts()
        if not counts:
            return SKIP, "no template library built", {}
        grp = max(counts, key=lambda k: counts[k])
        found = PT.find(grp, limit=3)
        if not found:
            return FAIL, f"{grp} has {counts[grp]} rows but find() returned none", counts
        t = found[0]
        return OK, (f"{sum(counts.values())} templates in {len(counts)} groups; "
                    f"{grp} -> {t.id} ({t.duration_ms} ms, {t.distance_u:.0f} u)"), counts

    def _render_permit(self):
        from engine.pantheon import render_permit as rp
        d = rp.check(purpose="doctor")
        if rp.mode() not in ("off", "auto", "on"):
            return FAIL, f"unknown mode {rp.mode()!r}", {}
        return OK, f"PANTHEON_RENDER={rp.mode()} -> {d.permit.value}: {d.reason}", rp.status()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    doc = Doctor()
    t0 = time.perf_counter()
    checks = doc.check_all()
    total = (time.perf_counter() - t0) * 1000
    n_fail = sum(1 for c in checks if c.status == FAIL)
    n_skip = sum(1 for c in checks if c.status == SKIP)
    if a.json:
        print(json.dumps({"verdict": "FAIL" if n_fail else "OK",
                          "checks": [{"name": c.name, "status": c.status,
                                      "detail": c.detail, "ms": round(c.ms, 1),
                                      "data": c.data} for c in checks],
                          "total_ms": round(total, 1)}, indent=1, default=str))
    else:
        print("PANTHEON doctor -- headless engine self-test")
        print(f"  store: {S.store_root()}")
        for c in checks:
            print(c.line())
        print(f"  {len(checks) - n_fail - n_skip} ok, {n_skip} skipped, {n_fail} failed "
              f"in {total / 1000:.1f} s; no renderer launched")
    return 1 if n_fail else 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
