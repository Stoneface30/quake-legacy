"""Read real Clan Arena rounds as an executable specification.

WHY. The synthetic writer had been learning the protocol one guessed field at
a time, and a guess that both the writer and the reader agree on is invisible:
the invented entity indices passed every round-trip test and rendered nothing.
The corpus already contains 4,292 demos of the engine doing it correctly. A
real round is a worked example, so the cheapest way to learn what a player
entity must carry is to watch one that the engine already drew.

WHAT THIS PRODUCES. A `CARoundTrace` per round: the configstring transitions
that express round start / alive counts / round win / reset, the event
timeline, and -- the part the synthetic side is missing -- a FIELD PROFILE of
real player entities, showing which entity fields actually vary while a player
idles, runs, fires and dies.

Read-only. Nothing here writes to a cache or a demo.

NAMES NEVER LEAVE THIS MODULE. A CA demo's server text is chat, and chat
carries opponent nicknames verbatim. The first run of this extractor wrote
them into JSON that was committed to a public repository. Traces are now
redacted by default -- server text is reduced to its kind and length, and the
demo is identified by a hash rather than by a filename that contains the
recorder's handle. `--identifying` restores the raw form for local work and
writes it somewhere that is gitignored.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

# A committed fixture may contain normalized anonymous ids (RED_1, BLUE_2) and
# nothing else that identifies a person. Server text has no safe kind: chat,
# tchat, print and cp all carry nicknames, so the default output drops the text
# channel entirely and keeps only its shape.
SAFE_TEXT_KINDS: frozenset[str] = frozenset()

# Writing identifying output into a directory git tracks is the mistake that
# already happened once. `--identifying` refuses to target one.
TRACKED_ROOTS = ("docs/", "creative_suite/", "engine/")

import engine.parser.demo_parse as dp
from engine.parser.demo_parse import DM73Parser

from engine.pantheon.store import data_root as _data_root
# The data root (HL-9), never a drive letter: a rebuild into a separate build
# root must not read the live corpus behind its back.
FRAGS_DB = _data_root() / "creative_suite" / "database" / "frags_rebuilt.db"

# The configstrings Clan Arena expresses its round state through. Indices from
# the format deep dive §3; meanings are confirmed here against real value
# sequences rather than assumed.
CS_SCORES1, CS_SCORES2 = 6, 7
CS_WARMUP = 5
CS_LEVEL_START_TIME = 13
CS_ROUND_STATUS = 661
CS_ROUND_TIME = 662
CS_RED_PLAYERS_LEFT = 663
CS_BLUE_PLAYERS_LEFT = 664
CS_ROUND_WINNERS = 705

ROUND_STATE_CS = (CS_SCORES1, CS_SCORES2, CS_WARMUP, CS_ROUND_STATUS,
                  CS_ROUND_TIME, CS_RED_PLAYERS_LEFT, CS_BLUE_PLAYERS_LEFT,
                  CS_ROUND_WINNERS)

MAX_CLIENTS = 64


@dataclass
class CARoundTrace:
    """One real round, normalised. Every entry traces to demo evidence."""
    round_num: int
    start_ms: int | None
    end_ms: int | None
    configstrings: list[dict] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    server_text: list[dict] = field(default_factory=list)

    def alive_transitions(self) -> list[dict]:
        """How the CA alive counters actually move during the round."""
        out = []
        for c in self.configstrings:
            if c["cs"] in (CS_RED_PLAYERS_LEFT, CS_BLUE_PLAYERS_LEFT):
                out.append({"t": c["t"],
                            "team": "RED" if c["cs"] == CS_RED_PLAYERS_LEFT
                                    else "BLUE",
                            "left": c["value"]})
        return out

    def as_dict(self) -> dict:
        return {"round": self.round_num, "start_ms": self.start_ms,
                "end_ms": self.end_ms,
                "duration_s": (None if self.start_ms is None or self.end_ms is None
                               else round((self.end_ms - self.start_ms) / 1000, 1)),
                "configstrings": self.configstrings,
                "alive_transitions": self.alive_transitions(),
                "events": self.events, "server_text": self.server_text}


@dataclass
class PlayerFieldProfile:
    """Which entity fields a REAL rendered player actually uses.

    `changes` counts how often a field's value moved between snapshots, which
    is what separates a static requirement (solid, eType) from an animated one
    (legsAnim, torsoAnim). `values` keeps the observed set for the small
    enumerated fields so synthetic animation can reuse real values instead of
    inventing counters.
    """
    present: Counter = field(default_factory=Counter)
    changes: Counter = field(default_factory=Counter)
    values: dict[int, Counter] = field(default_factory=lambda: defaultdict(Counter))
    samples: int = 0

    def observe(self, prev: dict | None, cur: dict) -> None:
        self.samples += 1
        for idx, val in cur.items():
            self.present[idx] += 1
            if len(self.values[idx]) < 64:
                self.values[idx][round(val, 1) if isinstance(val, float) else val] += 1
            if prev is not None and prev.get(idx) != val:
                self.changes[idx] += 1

    def report(self) -> list[dict]:
        out = []
        for idx in sorted(self.present):
            vals = self.values[idx]
            out.append({
                "field": idx,
                "present_pct": round(100 * self.present[idx] / max(1, self.samples), 1),
                "change_pct": round(100 * self.changes[idx] / max(1, self.samples), 1),
                "distinct_values": len(vals),
                "top_values": [v for v, _ in vals.most_common(6)],
            })
        return out


def _redact(text_rows: list[dict], keep: bool) -> list[dict]:
    """Chat is the nickname channel. Keep its shape, drop its content."""
    if keep:
        return text_rows
    # No `text` key at all. A redaction marker in a `text` field invites a
    # later change to "just put it back for debugging"; a schema with no text
    # channel does not.
    return [{"server_time_ms": r["server_time_ms"], "kind": r["kind"],
             "chars": len(r.get("text", "")), "round": r.get("round")}
            for r in text_rows]


def _demo_id(path: Path, keep: bool) -> str:
    """A stable id that is not the filename -- QL demo names embed the
    recorder's handle."""
    if keep:
        return path.name
    import hashlib
    return "demo-" + hashlib.sha256(path.name.encode()).hexdigest()[:16]


def trace_demo(path: Path, *, max_rounds: int = 6,
               identifying: bool = False) -> dict[str, Any]:
    """Parse one demo and pull out round traces plus the player field profile."""
    parser = DM73Parser(path)
    cs_log: list[dict] = []
    profile = PlayerFieldProfile()
    prev_states: dict[int, dict] = {}

    orig_cs = parser._absorb_cs

    def cs_hook(idx: int, val: str) -> None:
        if idx in ROUND_STATE_CS:
            cs_log.append({"t": parser._last_server_time, "cs": idx,
                           "value": val})
        orig_cs(idx, val)

    parser._absorb_cs = cs_hook

    orig_snap = parser._parse_snapshot

    def snap_hook(s, events, snapshots):
        orig_snap(s, events, snapshots)
        for num, st in parser._entity_states.items():
            if num < MAX_CLIENTS and st.get(dp._F_ETYPE) == 1:
                profile.observe(prev_states.get(num), dict(st))
                prev_states[num] = dict(st)

    parser._parse_snapshot = snap_hook
    out = parser.parse()

    rounds = out["rounds"][:max_rounds]
    traces: list[CARoundTrace] = []
    for r in rounds:
        lo = r["start_ms"] or 0
        hi = r["end_ms"] if r["end_ms"] is not None else 10 ** 12
        t = CARoundTrace(r["round"], r["start_ms"], r["end_ms"])
        t.configstrings = [c for c in cs_log if lo <= c["t"] <= hi]
        t.events = [{"t": e["server_time_ms"], "type": e["type"],
                     "killer": e.get("killer_client"),
                     "victim": e.get("victim_client"),
                     "weapon": e.get("weapon_name")}
                    for e in out["events"] if lo <= e["server_time_ms"] <= hi]
        t.server_text = _redact(
            [x for x in out["server_text"] if lo <= x["server_time_ms"] <= hi],
            identifying)
        traces.append(t)

    return {
        "demo": _demo_id(Path(path), identifying),
        "map": out["map"],
        "gametype": out["gametype"],
        "packet_errors": out["packet_errors"],
        "n_rounds": len(out["rounds"]),
        "n_events": out["event_count"],
        "rounds": [t.as_dict() for t in traces],
        "player_field_profile": profile.report(),
        "profile_samples": profile.samples,
    }


def pick_reference_demos(limit: int = 6) -> list[tuple[str, str]]:
    """Reference demos, chosen for round variety rather than for being good.

    Wants: complete rounds with a start and an end, several deaths so alive
    counters actually move, and a full roster so 4v4 structure appears.
    """
    con = sqlite3.connect(f"file:{FRAGS_DB.as_posix()}?mode=ro", uri=True)
    rows = con.execute(
        """select name, path from demos
           where gametype='CA' and rounds between 8 and 40
             and players >= 8 and accepted_frags >= 10
           order by accepted_frags desc limit ?""", (limit,)).fetchall()
    con.close()
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=Path("docs/reference/ca_rounds"))
    ap.add_argument("--demos", type=int, default=5)
    ap.add_argument("--rounds", type=int, default=6)
    ap.add_argument("--identifying", action="store_true",
                    help="keep chat text and demo filenames. Local use only -- "
                         "the output must never be committed.")
    args = ap.parse_args()
    if args.identifying:
        rel = args.out.resolve().as_posix()
        repo = Path(__file__).resolve().parents[2].as_posix()
        inside = rel.startswith(repo)
        tracked = any(rel.startswith(f"{repo}/{r}") for r in TRACKED_ROOTS)
        if inside and tracked:
            raise SystemExit(
                f"refusing --identifying into a tracked path ({args.out}). "
                "Identifying output goes somewhere git does not follow.")
    args.out.mkdir(parents=True, exist_ok=True)

    merged = PlayerFieldProfile()
    summaries = []
    for name, path in pick_reference_demos(args.demos):
        try:
            tr = trace_demo(Path(path), max_rounds=args.rounds,
                            identifying=args.identifying)
        except Exception as exc:
            print(f"  {_demo_id(Path(path), args.identifying)[:44]:44s} FAILED {type(exc).__name__}: {exc}")
            continue
        dest = args.out / (tr["demo"] + ".json")
        dest.write_text(json.dumps(tr, indent=1), encoding="utf-8")
        alive = sum(len(r["alive_transitions"]) for r in tr["rounds"])
        kills = sum(1 for r in tr["rounds"] for e in r["events"]
                    if e["type"] == "obituary")
        print(f"  {tr['demo'][:44]:44s} map={tr['map']:<14} rounds={tr['n_rounds']:3d} "
              f"traced={len(tr['rounds'])} kills={kills:3d} alive_moves={alive:3d} "
              f"errors={tr['packet_errors']}")
        summaries.append({"demo": tr["demo"], "map": tr["map"],
                          "rounds": tr["n_rounds"], "traced": len(tr["rounds"]),
                          "kills": kills, "alive_moves": alive,
                          "file": str(dest)})
    print(f"\nwrote {len(summaries)} traces to {args.out}")
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
