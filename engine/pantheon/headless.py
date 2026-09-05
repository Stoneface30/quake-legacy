"""The headless PANTHEON performance loop.

    trace    = extract_performance(demo, actor, start_ms, end_ms)
    compiled = compile_performance(trace, cast=..., retarget=...)
    back     = reextract(compiled)
    report   = compare(trace, back[...])

Seconds, no game process. `run()` does all four and times each step. Only a
report whose `semantic_fidelity == "PASS"` is allowed to reach a render
backend, and that hand-off happens in `engine.pantheon.backends`, not here.

CHARACTER != PERFORMANCE. A trace says how a body moved, aimed and fought.
The `cast` says which character performs it -- model, skin, team -- and is a
`roster.PresenterProfile` or a bare (model, skin) pair. Anarki can perform a
trace recorded from anyone; no historical identity travels with it.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from engine.pantheon import performance as P
from engine.pantheon.compare import PerformanceDiff, Tolerances, compare
from engine.pantheon.frame_truth import FrameTruth
from engine.pantheon.performance import PerformanceTrace
from engine.pantheon.retarget import Retarget
from engine.pantheon.scenario import RoundScenario, Team, Weapon

Vec3 = tuple[float, float, float]
BASE_MS = 1000                 # the compiler's first snapshot time
DEFAULT_T0 = 0.6               # synthetic seconds before the window opens
OUT = Path("G:/QUAKE_LEGACY/creative_suite/generated/pantheon/headless")

# obituary MOD -> the weapon slot that produced it, from the parser's table
def _weapon_for_mod(mod: int | None) -> Weapon:
    from engine.parser.demo_parse import _MOD_NAMES
    name = _MOD_NAMES.get(mod or -1, "")
    table = {"ROCKET": Weapon.ROCKET, "GRENADE": Weapon.GRENADE,
             "PLASMA": Weapon.PLASMA, "RAILGUN": Weapon.RAIL,
             "LIGHTNING": Weapon.LIGHTNING, "SHOTGUN": Weapon.SHOTGUN,
             "MACHINEGUN": Weapon.MACHINEGUN, "GAUNTLET": Weapon.GAUNTLET}
    for key, w in table.items():
        if name.startswith(key):
            return w
    return Weapon.ROCKET


# ── extract ────────────────────────────────────────────────────────────────

def extract_performance(demo: Path, actor: int | str, start_ms: int,
                        end_ms: int, *, parsed=None) -> PerformanceTrace:
    """Everything the demo observed about `actor` in the window.

    `actor` is a client slot, or "POV" for the recorder himself (whose tracks
    come from the playerstate rather than an entity). Works for any client the
    recorder's snapshots carried; where they did not, the trace has a gap and
    says so.
    """
    demo = Path(demo)
    parsed = parsed or P._parse_with_anims(demo)
    if actor == "POV":
        client = P.recorder_client(parsed[0])
        if client is None:
            raise ValueError(f"{demo.name}: no playerstate client -- no POV")
    else:
        client = int(actor)
    return P.extract_performance(demo, start_ms, end_ms, client, parsed=parsed)


def parse(demo: Path):
    """Parse once, reuse across several extractions from the same demo."""
    return P._parse_with_anims(Path(demo))


def team_of(parsed, client: int) -> Team:
    """The team the demo's configstrings gave this client."""
    out = parsed[0]
    players = out.get("players") or {}
    p = players.get(client) or players.get(str(client)) or {}
    t = str(p.get("team", "")).upper()
    return Team.BLUE if t in ("BLUE", "2") else Team.RED


def context_windows(parsed, lo: int, hi: int, *, exclude: Iterable[int] = (),
                    min_samples: int = 4) -> dict[str, tuple[int, int, int]]:
    """CONTEXT ACTOR POLICY: every other client the recorder observed in the
    window is performed from his own trace; nobody is fabricated to match a
    frame. Fewer than `min_samples` samples is noise, not an actor."""
    out = parsed[0]
    seen: dict[int, int] = {}
    for e in out["entities"]:
        c = e["client_num"]
        if c is not None and lo <= e["server_time_ms"] <= hi:
            seen[c] = seen.get(c, 0) + 1
    ex = set(exclude)
    return {f"CTX{c}": (c, lo, hi) for c, n in sorted(seen.items())
            if c not in ex and n >= min_samples}


# ── compile ────────────────────────────────────────────────────────────────

@dataclass
class CastMember:
    name: str
    team: Team
    model: str = "sarge"
    skin: str = "default"

    @classmethod
    def coerce(cls, name: str, spec, default_team: Team) -> "CastMember":
        if isinstance(spec, CastMember):
            return spec
        if spec is None:
            return cls(name, default_team)
        if hasattr(spec, "model") and hasattr(spec, "skin"):      # PresenterProfile
            return cls(name, default_team, spec.model, spec.skin)
        if isinstance(spec, (tuple, list)) and len(spec) >= 2:
            team = spec[2] if len(spec) > 2 else default_team
            return cls(name, team, spec[0], spec[1])
        raise TypeError(f"cast[{name!r}]: expected PresenterProfile, "
                        f"(model, skin[, team]) or CastMember, got {spec!r}")


@dataclass
class CompiledPerformance:
    scenario: RoundScenario
    demo: object                              # dm73_write.DemoWriter
    frame_truth: FrameTruth
    traces: dict[str, PerformanceTrace]
    clients: dict[str, int]
    t0: dict[str, float]
    duration: float
    retarget: Retarget
    time_offset_ms: int                       # repro.t == real.t + this
    path: Path | None = None
    intentional: set[str] = field(default_factory=set)   # declared, not judged

    def save(self, path: Path) -> Path:
        self.path = self.demo.save(path)
        return self.path

    def window(self, name: str) -> tuple[int, int]:
        tr = self.traces[name]
        return tr.start_ms + self.time_offset_ms, tr.end_ms + self.time_offset_ms


def compile_performance(traces: PerformanceTrace | Mapping[str, PerformanceTrace],
                        *, cast: Mapping[str, object] | None = None,
                        retarget: Retarget | None = None,
                        t0: float = DEFAULT_T0,
                        observer: Vec3 | None = None,
                        observer_yaw: float | None = None,
                        hostname: str = "PANTHEON PERFORMANCE",
                        kills: bool = True) -> CompiledPerformance:
    """Recorded traces -> a RoundScenario -> a synthetic demo + FrameTruth.

    All traces share one clock: the earliest `start_ms` lands at `t0`
    seconds into the demo and every other trace keeps its real offset from
    it, so two players recorded together stay together.
    """
    if isinstance(traces, PerformanceTrace):
        traces = {"PERF": traces}
    if not traces:
        raise ValueError("compile_performance needs at least one trace")
    rt = retarget or Retarget.exact_world()
    cast = dict(cast or {})
    names = list(traces)
    maps = {tr.map for tr in traces.values()}
    if len(maps) != 1:
        raise ValueError(f"traces span several maps: {sorted(maps)}")
    (map_name,) = maps
    min_start = min(tr.start_ms for tr in traces.values())
    max_end = max(tr.end_ms for tr in traces.values())

    scn = RoundScenario.clan_arena(map_name=map_name, hostname=hostname)
    first = traces[names[0]].transform[0].origin if traces[names[0]].transform else (0.0, 0.0, 0.0)
    first = rt.place(first)
    if observer is None:
        observer = (first[0] - 260.0, first[1] - 260.0, first[2] + 60.0)
    if observer_yaw is None:
        import math
        observer_yaw = math.degrees(math.atan2(first[1] - observer[1],
                                               first[0] - observer[0])) % 360
    scn.observer(observer, yaw=observer_yaw, team=Team.BLUE, name="POV")

    members: dict[str, CastMember] = {}
    actors = {}
    t0s: dict[str, float] = {}
    for i, name in enumerate(names):
        default_team = Team.RED if i == 0 else Team.BLUE
        m = CastMember.coerce(name, cast.get(name), default_team)
        members[name] = m
        a = scn.actor(name, m.team).appearance(m.model, m.skin)
        tr = traces[name]
        t0s[name] = t0 + (tr.start_ms - min_start) / 1000.0
        a.perform(tr, t0=t0s[name], **rt.perform_kwargs())
        a._recorded_client = tr.client        # so impacts can name their victim
        actors[name] = a

    # kills: an obituary in a trace whose victim is another cast member.
    # A RECORDED obituary (a temp-entity event with its code) is replayed
    # verbatim by perform(); the round is credited without a second entity.
    by_client = {traces[n].client: n for n in names}
    intentional: set[str] = set()
    if kills:
        for name in names:
            for ev in traces[name].of_kind("obituary"):
                victim = by_client.get(ev.other_client)
                when = round(t0s[name] + (ev.t - traces[name].start_ms) / 1000.0, 3)
                if victim is None or victim == name:
                    if ev.code is None:
                        # not replayed, no body to kill: a declared difference
                        intentional.add("obituary")
                    continue
                if ev.code is not None:
                    actors[name].credit_kill(actors[victim], t=when)
                else:
                    actors[name].kill(actors[victim], mod=_weapon_for_mod(ev.weapon), t=when)

    duration = t0 + (max_end - min_start) / 1000.0 + 0.3
    demo = scn.compile(duration=duration)
    ft = FrameTruth.from_scenario(scn, duration=duration)
    ft.provenance = "SYNTHETIC_PERFORMANCE"
    return CompiledPerformance(
        scenario=scn, demo=demo, frame_truth=ft, traces=dict(traces),
        clients={n: actors[n].client for n in names}, t0=t0s,
        duration=duration, retarget=rt,
        time_offset_ms=BASE_MS + int(round(t0 * 1000)) - min_start,
        intentional=intentional)


# ── re-extract and compare ─────────────────────────────────────────────────

def reextract(compiled: CompiledPerformance, path: Path | None = None
              ) -> dict[str, PerformanceTrace]:
    """Read the synthetic demo back with the SAME extractor, one trace per
    cast member, over each member's own window."""
    path = path or compiled.path
    if path is None:
        raise ValueError("save the compiled demo first, or pass a path")
    parsed = P._parse_with_anims(Path(path))
    out = {}
    for name in compiled.traces:
        lo, hi = compiled.window(name)
        out[name] = P.extract_performance(Path(path), lo, hi,
                                          compiled.clients[name], parsed=parsed)
    return out


@dataclass
class HeadlessResult:
    traces: dict[str, PerformanceTrace]
    compiled: CompiledPerformance
    reextracted: dict[str, PerformanceTrace]
    diffs: dict[str, PerformanceDiff]
    timings_ms: dict[str, float] = field(default_factory=dict)

    @property
    def semantic_fidelity(self) -> str:
        return "FAIL" if any(d.semantic_fidelity == "FAIL"
                             for d in self.diffs.values()) else "PASS"

    def as_dict(self) -> dict:
        return {"semantic_fidelity": self.semantic_fidelity,
                "timings_ms": self.timings_ms,
                "synthetic_demo": str(self.compiled.path),
                "diffs": {k: v.as_dict() for k, v in self.diffs.items()}}


def run(demo: Path, windows: Mapping[str, tuple[int | str, int, int]], *,
        cast: Mapping[str, object] | None = None,
        retarget: Retarget | None = None,
        tol: Tolerances = Tolerances(),
        intentional: Sequence[str] = (),
        context: bool = False,
        out_dir: Path = OUT, label: str = "headless") -> HeadlessResult:
    """extract -> compile -> reextract -> compare, timed, for a set of
    `name -> (actor, start_ms, end_ms)` windows on one demo.

    `context=True` adds every other client the recorder observed across the
    union of the windows, each performed from his own trace on the team the
    demo gave him (context actor policy)."""
    demo = Path(demo)
    timings: dict[str, float] = {}

    t = time.perf_counter()
    parsed = parse(demo)
    timings["parse"] = round((time.perf_counter() - t) * 1000, 1)

    t = time.perf_counter()
    windows = dict(windows)
    cast = dict(cast or {})
    if context:
        lo = min(w[1] for w in windows.values())
        hi = max(w[2] for w in windows.values())
        named = {P.recorder_client(parsed[0]) if a == "POV" else int(a)
                 for a, _, _ in windows.values()}
        for name, (c, a, b) in context_windows(parsed, lo, hi, exclude=named).items():
            windows[name] = (c, a, b)
            cast.setdefault(name, CastMember(name, team_of(parsed, c)))
    traces = {name: extract_performance(demo, actor, lo, hi, parsed=parsed)
              for name, (actor, lo, hi) in windows.items()}
    timings["extract"] = round((time.perf_counter() - t) * 1000, 1)

    t = time.perf_counter()
    compiled = compile_performance(traces, cast=cast, retarget=retarget)
    timings["compile"] = round((time.perf_counter() - t) * 1000, 1)

    t = time.perf_counter()
    out_dir.mkdir(parents=True, exist_ok=True)
    compiled.save(out_dir / f"{label}.dm_73")
    compiled.frame_truth.save(out_dir / f"{label}.frametruth.json")
    timings["write"] = round((time.perf_counter() - t) * 1000, 1)

    t = time.perf_counter()
    back = reextract(compiled)
    timings["reextract"] = round((time.perf_counter() - t) * 1000, 1)

    t = time.perf_counter()
    declared = set(intentional) | compiled.intentional
    diffs = {name: compare(traces[name], back[name], retarget=compiled.retarget,
                           tol=tol, intentional=declared)
             for name in traces}
    timings["compare"] = round((time.perf_counter() - t) * 1000, 1)
    timings["total_excluding_parse"] = round(
        sum(v for k, v in timings.items() if k != "parse"), 1)

    res = HeadlessResult(traces, compiled, back, diffs, timings)
    for name, d in diffs.items():
        d.save(out_dir / f"{label}.{name}.diff.json")
    return res
