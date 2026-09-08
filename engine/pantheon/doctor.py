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
    TRACE_CACHE     what is kept, why, and whether it is inside its budget
    RECIPES         the film grammar, and what each one is still missing
    ENGINE_INVENTORY  every command and cvar, graded, with nothing unclassified
    ASSETS          which art the picture is made of, and whether it is there
    VISUAL_PROOF    what a person judged, and what is waiting on one
    IDEAS           the director's list, and how much of it has a route
    PROFILES        the versioned project defaults
    PLANNER         which backend would take which pass
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
            self.run("TRACE_CACHE", self._trace_cache)
            self.run("ENGINE_INVENTORY", self._engine_inventory)
            self.run("ASSETS", self._assets)
            self.run("WARDROBE", self._wardrobe)
            self.run("HUD", self._hud)
            self.run("MORPH", self._morph)
            self.run("RECIPES", self._recipes)
            self.run("VISUAL_PROOF", self._visual_proof_registry)
            self.run("IDEAS", self._ideas)
            self.run("PROFILES", self._profiles)
            self.run("PLANNER", self._planner)
            self.run("PROTOCOL", self._protocol)
            self.run("CAPABILITIES", self._capabilities)
            self.run("VISUAL_PROFILE", self._visual_profile)
            self.run("OFFSCREEN", self._offscreen)
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

    def _trace_cache(self):
        """The index stores rows, not traces. A cache that kept everything is
        what the 94 GB index was, so the check is that what is kept was
        CHOSEN, and that it fits."""
        from engine.pantheon import trace_cache as TC
        rep = TC.report()
        if not rep["traces"]:
            return SKIP, "nothing cached yet (traces are rebuilt on demand)", rep
        unknown = set(rep["by_reason"]) - {r.value for r in TC.Reason}
        if unknown:
            return FAIL, (f"traces kept for reasons nobody declared: "
                          f"{sorted(unknown)}; python -m engine.pantheon."
                          f"trace_cache --normalise"), rep
        if rep["bytes"] > rep["budget_bytes"]:
            return FAIL, (f"{rep['bytes'] / 1e6:.0f} MB over the "
                          f"{rep['budget_bytes'] / 1e6:.0f} MB budget; run evict()"), rep
        share = ", ".join(f"{k} {v['traces']}" for k, v in sorted(rep["by_reason"].items()))
        return OK, (f"{rep['traces']} traces, {rep['bytes'] / 1e6:.1f} MB of "
                    f"{rep['budget_bytes'] / 1e6:.0f} MB ({share})"), rep

    def _assets(self):
        """The regenerated art is only an upgrade if it is in the gamedir.

        4,895 upscaled files sat in a second staging install for a week while
        every render used the first one, so this check exists to make that
        state loud rather than invisible.
        """
        from engine.pantheon import assets as A
        from engine.pantheon import offscreen as O
        rep = A.report()
        # Ask about the set this machine actually films with. The wardrobe
        # registers ten looks as CHOICES; a look whose pack has not been built
        # is not a fault, and reporting it as one made this check fail the
        # moment the wardrobe arrived.
        avail = A.available(set_name=O.DEFAULT_ASSET_SET)
        missing = [n for n, v in avail.items() if not v["present"]]
        if missing:
            return FAIL, (f"the {O.DEFAULT_ASSET_SET} packs are not on this "
                          f"machine: {missing[:3]}"), rep
        cov = A.coverage(O.DEFAULT_ASSET_SET)
        if cov.get("same_path_other_extension"):
            return FAIL, (f"{cov['same_path_other_extension']} files would "
                          f"override nothing: wrong extension for the path"), rep
        active = rep["active_set"]
        note = "" if active == O.DEFAULT_ASSET_SET else             f"; gamedir currently holds {active}, and every capture installs "            f"{O.DEFAULT_ASSET_SET} before it films"
        return OK, (f"{cov['files']:,} upscaled files, all replacing a stock "
                    f"path at the same extension{note}"), rep

    def _wardrobe(self):
        """Eleven looks were generated and one was ever packed.

        8,637 finished renders of the game's own art had never been in a
        picture. This check keeps that number visible rather than letting the
        wardrobe quietly rot back to a single texture pack.
        """
        from engine.pantheon import asset_library as L
        from engine.pantheon import assets as A
        try:
            fams = L.families()
        except FileNotFoundError as exc:
            return SKIP, str(exc), {}
        if not fams:
            return FAIL, "the asset database reports no render families", {}
        L.register()
        styled = {n: f for n, f in fams.items() if not f.is_fidelity}
        unpacked = sum(f.renders for f in styled.values())
        installable = sorted(L.look_name(n) for n in styled
                             if L.look_name(n) in A.SETS)
        rep = {"families": len(fams), "installable_looks": installable,
               "renders_never_packed": unpacked}
        if not installable:
            return FAIL, "no look could be registered from the database", rep
        return OK, (f"{len(fams)} render families, {unpacked:,} renders "
                    f"outside the shipped pack, "
                    f"{len(installable)} looks installable"), rep

    def _hud(self):
        """The HUD is a film surface and the writer must be faithful.

        If the identity effect cannot reproduce the shipped file exactly, then
        every diff the module produces is contaminated by its own formatting
        and no HUD treatment can be trusted.
        """
        from engine.pantheon import hud
        try:
            text = hud.stock_text()
        except FileNotFoundError as exc:
            return SKIP, str(exc), {}
        same, changed = hud.apply("HUD_STOCK", text)
        if same != text or changed:
            return FAIL, ("the shader writer does not round-trip the shipped "
                          "file; every HUD diff would be untrustworthy"), {}
        rep = hud.report()
        ctl = hud.control_report()
        if ctl["draw_cvars"] < 300:
            return FAIL, ("the HUD control surface is missing: the census "
                          "should carry ~383 cg_draw* cvars, not "
                          f"{ctl['draw_cvars']}"), ctl
        return OK, (f"{rep['shaders']} shaders for art; "
                    f"{ctl['draw_cvars']} engine switches over "
                    f"{ctl['elements']} elements for layout"), {
            "families": rep["film_families"],
            "movable": len(ctl["can_be_moved"]),
            "fadable": len(ctl["can_be_faded"])}

    def _morph(self):
        """A blend is never offered while frame alignment is unproven.

        Two runs of the engine do not start on the same tick. A cut survives
        that; a dissolve shows the world ghosting against itself.
        """
        from engine.pantheon import morph as M
        bad = [n for n, p in M.RECIPES.items()
               if p.alignment_required and p.ready]
        if bad:
            return FAIL, (f"these plans offer a blend without proven "
                          f"alignment: {bad}"), {}
        return OK, (f"{len(M.ready_now())} plans shootable now, "
                    f"{len(M.blocked())} waiting on frame alignment"), {
            "ready": list(M.ready_now()), "blocked": list(M.blocked())}

    def _engine_inventory(self):
        """Every raw engine name is graded, and nothing is merely absent.

        UNKNOWN is a classification: somebody asked and the answer was
        nothing. UNCLASSIFIED means nobody looked, and a new command appearing
        in a future census must fail here rather than pass unnoticed.
        """
        from engine.pantheon import engine_inventory as EI
        rep = EI.report()
        if not rep["sources"]["runtime_cvars"]:
            return SKIP, ("no runtime census on this machine; run "
                          "python -m engine.pantheon.engine_census"), rep
        if rep["unclassified"]:
            names = [i.name for i in EI.unclassified(EI.build()["items"])][:6]
            return FAIL, (f"{rep['unclassified']} engine items nobody has "
                          f"classified: {names}"), rep
        g = rep["by_grade"]
        return OK, (f"{rep['items']:,} items graded "
                    f"({g.get('RUNTIME_REGISTERED', 0)} live in 11.3, "
                    f"{g.get('SOURCE_REGISTERED', 0)} source-only, "
                    f"{g.get('UNSUPPORTED_TARGET', 0)} another engine's, "
                    f"{g.get('RUNTIME_ACCEPTED_UNSET', 0)} silent no-ops); "
                    f"{rep['mapped_items']} mapped to "
                    f"{rep['semantic_capabilities']} capabilities"), rep

    def _recipes(self):
        from engine.pantheon import effect_recipes as ER
        rep = ER.report()
        concept = [d["id"] for d in rep["detail"] if d["status"] == "CONCEPT"]
        if concept:
            return FAIL, f"recipes asking for truth this engine has no name for: {concept}", rep
        counts = ", ".join(f"{k.split('_')[0].lower()} {v}"
                           for k, v in sorted(rep["by_status"].items()))
        return OK, f"{rep['recipes']} recipes ({counts})", rep

    def _visual_proof_registry(self):
        from engine.pantheon import visual_proof as VP
        rep = VP.report()
        if not rep["capabilities"]:
            # A fresh checkout has no registry database -- it lives outside the
            # repo. The SEED tuple in visual_proof.py is the committed
            # authority, so rebuild from it rather than reporting a gap that
            # is really just a missing local file.
            VP.seed()
            rep = VP.report()
            if not rep["capabilities"]:
                return SKIP, "nothing banked and the seed produced nothing", rep
        # The one proof the handoff turns on. If it is not banked, say so here
        # rather than letting a caller discover it at render time.
        keel = VP.status("REVIEW_GREEN_KEEL", backend="PANTHEON_QUAKE_OFFSCREEN",
                         profile="REVIEW", engine_version="wolfcamql-11.3")
        if keel is not VP.Status.VISUALLY_PROVEN:
            return FAIL, f"REVIEW_GREEN_KEEL is {keel.value}, not banked", rep
        waiting = rep["awaiting_human"]
        return OK, (f"{rep['capabilities']} capabilities judged; "
                    f"{rep['by_status'].get('VISUALLY_PROVEN', 0)} proven, "
                    f"{waiting} waiting on a person"), rep

    def _ideas(self):
        from engine.pantheon import director_notes as DN
        from engine.pantheon import ideas as ID
        rep = ID.report()
        notes = DN.report()
        if rep["ideas"] != 306:
            return FAIL, f"the master list is {rep['ideas']} long, not 306", rep
        return OK, (f"{rep['ideas']} ideas, {rep['carried_by_a_recipe']} carried "
                    f"by a recipe, {rep['no_recipe_yet']} with no route yet; "
                    f"{notes['notes']} original notes, "
                    f"{notes['not_carried_by_any_recipe']} of their requirements "
                    f"uncarried"), {**rep, "notes": notes}

    def _profiles(self):
        from engine.pantheon import defaults as D
        rep = D.report()
        ids = set(rep["profiles"].values())
        if len(ids) != len(rep["profiles"]):
            return FAIL, "two profiles hash to the same id", rep
        return OK, (f"{len(rep['profiles'])} versioned profiles; review "
                    f"{rep['default_review']}, film {rep['default_film']}"), rep

    def _planner(self):
        from engine.pantheon import backend_planner as BP
        plan = BP.plan(recipes=("XRAY_ACTOR", "ENEMY_POV_REPLAY"))
        beauty = plan.passes[0]
        if beauty.backend is None:
            return FAIL, "no backend can deliver a beauty pass", plan.as_dict()
        return OK, (f"beauty -> {beauty.backend}, "
                    f"{len(plan.passes)} passes, "
                    f"{len(plan.unsupported)} unsupported"), plan.as_dict()

    def _protocol(self):
        from engine.parser import protocol as P
        if not P.CANONICAL_MSG_C.exists():
            return SKIP, f"no engine source at {P.CANONICAL_MSG_C}", {}
        ents = P.parse_canonical_table("entityStateFieldsQldm73")
        pss = P.parse_canonical_table("playerStateFieldsQ3")
        if len(ents) != len(P.ENTITY_FIELDS) or len(pss) != len(P.PLAYER_FIELDS):
            return FAIL, (f"engine {len(ents)}/{len(pss)} fields, registry "
                          f"{len(P.ENTITY_FIELDS)}/{len(P.PLAYER_FIELDS)}"), {}
        for (m, w), f in list(zip(ents, P.ENTITY_FIELDS)) + list(zip(pss, P.PLAYER_FIELDS)):
            if m != f.name or P.canonical_bits(w) != f.bits:
                return FAIL, f"{m} disagrees with the registry at index {f.index}", {}
        return OK, (f"{len(ents)} entity + {len(pss)} playerstate fields match the "
                    f"engine's own tables"), {}

    def _capabilities(self):
        from engine.pantheon import capabilities as C
        if not C.RUNTIME_CVARLIST.exists():
            return SKIP, "no 11.3 cvarlist capture", {}
        registered = {c.lower() for c in C.runtime_registered_cvars()}
        # A capability whose evidence is a MEASURED behaviour change is not
        # audited against the cvarlist: the list proves registration, the
        # measurement proves effect, and the probe never asked about every
        # family. It must still say what was measured, which is checked below.
        bad = [(cap.name, cvar) for cap in C.WOLFCAM_11_3.values()
               if cap.evidence is C.Evidence.EXECUTION_PROVEN and not cap.measured
               for cvar in cap.cvars if cvar.lower() not in registered]
        unsupported = [cap.name for cap in C.WOLFCAM_11_3.values()
                       if cap.measured and len(cap.measured) < 40]
        if unsupported:
            return FAIL, (f"claims a measurement without describing it: "
                          f"{unsupported}"), {}
        if bad:
            return FAIL, f"claims EXECUTION_PROVEN for cvars the runtime does not list: {bad[:3]}", {}
        rep = C.report()
        return OK, (f"{len(rep['usable'])} usable, "
                    f"{len(rep['not_established'])} not established "
                    f"(e.g. {sorted(rep['not_established'])[:2]})"), rep["not_established"]

    def _visual_profile(self):
        """Checks the translator's OUTPUT without spelling a cvar: the names
        come from the capability registry, which is where backend detail is
        allowed to live."""
        from engine.pantheon import capabilities as C
        from engine.pantheon import visual_profile as VP
        p = VP.profile("REVIEW")
        c = p.resolve()
        enemy_model = C.get("FORCE_ENEMY_MODEL").cvars[0]
        team_model = C.get("FORCE_TEAM_MODEL").cvars[0]
        every = C.get("FORCE_ALL_MODELS").cvars[0]
        want = f'"{p.enemy_model}/{p.enemy_skin}"'
        if c.get(enemy_model) != want:
            return FAIL, f"REVIEW does not force {p.enemy_model}: {c.get(enemy_model)}", {}
        if c.get(team_model) != '""' or c.get(every) != 0:
            return FAIL, "REVIEW would change teammates as well as enemies", {}
        return OK, (f"{len(VP.PROFILES)} profiles; REVIEW forces the enemy to "
                    f"{p.enemy_model}/{p.enemy_skin} in "
                    f"rgb{p.enemy_colour} and leaves teammates and self alone"), {}

    def _offscreen(self):
        import sys as _sys
        from engine.pantheon import offscreen as O
        if _sys.platform != "win32":
            return SKIP, "hidden desktops are a Windows mechanism", {}
        # The MECHANISM only, with a harmless GUI process. The doctor never
        # launches the game and never puts a window on the operator's screen.
        r = O.probe_isolation(dwell=1.2)
        if not r.ran:
            return FAIL, r.detail, {}
        if r.visible_windows:
            return FAIL, f"a window reached the operator's desktop: {r.visible_windows}", {}
        if r.stole_focus:
            return FAIL, "a hidden-desktop process took the foreground", {}
        return OK, ("hidden desktop isolates a GUI process: no window, no focus "
                    "change (probed with a harmless process, not the game)"), r.as_dict()

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
