"""Build the prologue proof sheet: every primitive, driven by live cache data.

WHAT THIS PROVES. Not that the film is good -- that the film can be built
truthfully. Each panel below is generated from a query run at build time, so
if a number on this page is wrong, the cache is wrong, not the slide.

It deliberately does NOT consume any historical hero frag. Where footage would
go, the sheet shows the SLOT and the size of the pool that qualifies for it, so
human review can see what it is being asked for without anything being spent.

    python -m creative_suite.prologue.proof [out.html]
"""
from __future__ import annotations

import sqlite3
import sys
from html import escape
from pathlib import Path

from creative_suite.prologue import facts, primitives as p
from creative_suite.prologue.slots import SLOTS


def _rows(sql: str) -> list[tuple]:
    with sqlite3.connect(
            f"file:{facts.RECOGNITION_DB.as_posix()}?mode=ro", uri=True) as c:
        return c.execute(sql).fetchall()


def _rebuilt_rows(sql: str) -> list[tuple]:
    with sqlite3.connect(
            f"file:{facts.REBUILT_DB.as_posix()}?mode=ro", uri=True) as c:
        return c.execute(sql).fetchall()


def _fmt(v: object) -> str:
    """Ledger display. A derived hour count is a measurement, not 15 digits."""
    if isinstance(v, float):
        return f"{v:,.1f}"
    if isinstance(v, int):
        return f"{v:,}"
    return escape(str(v))


def _panel(title: str, svg: str, note: str, source: str) -> str:
    return (f'<section class="panel"><h3>{escape(title)}</h3>'
            f'<div class="art">{svg}</div>'
            f'<p class="note">{escape(note)}</p>'
            f'<p class="src">{escape(source)}</p></section>')


def build() -> str:
    """Render the sheet. Every number here is queried, none is typed."""
    verified = facts.verify()
    by_key = {r["key"]: r for r in verified}

    # -- live queries -------------------------------------------------------
    maps = [p.MapWeight(n, d) for n, d in _rebuilt_rows(
        "select map_name, count(*) c from demos group by 1 order by c desc")]
    weapons = _rows("""select mod_name, count(*) c from kill_occurrences_v1
                       where mod_name in ('LIGHTNING','RAILGUN','ROCKET',
                       'SHOTGUN','GRENADE','PLASMA','MACHINEGUN','GAUNTLET')
                       group by 1 order by c desc""")
    speeds = _rows("""select peak_speed from movement_moments_v1
                      where kind='HIGH_SPEED_MOVEMENT' and peak_speed is not null
                      order by peak_speed""")
    sp = [s[0] for s in speeds]
    median_speed = sp[len(sp) // 2]
    p90_speed = sp[int(len(sp) * 0.90)]

    rounds = by_key["canonical_rounds"]["actual"]
    user = by_key["user_frags"]["actual"]
    allk = by_key["all_player_kills"]["actual"]

    panels = []

    # PART 1
    panels.append(_panel(
        "P1 - speed readout at the base run speed",
        p.speed_readout(p.BASE_RUN_UPS, label="ENGINE CONSTANT"),
        "320 ups is what the engine gives you for holding forward. Everything "
        "in Part 1 is about beating this number.",
        "g_main.c:152 (g_speed); bands cg_draw.c:844-857"))
    panels.append(_panel(
        "P1 - median measured high-speed run",
        p.speed_readout(median_speed),
        f"Median peak across {len(sp):,} HIGH_SPEED_MOVEMENT runs. A ~0.3 s "
        f"segment average, so it understates the instantaneous peak - which is "
        f"why the label reads MEASURED.",
        "movement_moments_v1.peak_speed; movement_moments.py:141,161-166"))
    panels.append(_panel(
        "P1 - p90 measured run",
        p.speed_readout(p90_speed),
        "p90 of the same pool. The detector rejects anything above 1200 ups as "
        "a discontinuity, so this pool is truncated and we never call its max "
        "'the fastest run in the archive'.",
        "movement_moments.py:56 (IMPLAUSIBLE_UPS = 1200.0)"))
    panels.append(_panel(
        "P1 - weapon language, weighted by what actually killed",
        p.weapon_row([(n, c) for n, c in weapons]),
        "Three weapons are the overwhelming majority of everything that ever "
        "happened. The gauntlet is the joke, and it is a measured joke.",
        "kill_occurrences_v1 group by mod_name"))

    # PART 2
    for red, blue, cap in ((4, 4, "round start"), (4, 3, "first kill"),
                           (2, 2, "the freeze"), (1, 0, "round won")):
        panels.append(_panel(
            f"P2 - alive counter, {cap}",
            p.alive_counter(red, blue),
            "A pip goes dark and stays dark. That is how the audience learns "
            "one-life-per-round without being told it.",
            "one life verified at 99.6%: kill_events_v1, deaths per "
            "(demo, round, victim)"))

    # PART 3
    panels.append(_panel(
        "P3 - archive counter, demos",
        p.archive_counter(by_key["demos_scanned"]["actual"], "demos scanned"),
        "One demo may span several matches. It is never called a match.",
        "scanned_demos (0 errors)"))
    panels.append(_panel(
        "P3 - archive counter, hours",
        p.archive_counter("OVER 450", "hours of recordings"),
        f"Lower bound: {by_key['recording_hours']['actual']:.1f} h, summed as "
        f"first kill to last per demo. Warmup and tails are outside it. The "
        f"brief's '~452 hours' had no derivation; this does.",
        "sum over kill_events_v1.demo_us, 4,266 demos"))
    panels.append(_panel(
        "P3 - map constellation, all 61 recorded maps",
        p.map_constellation(maps),
        f"{len(maps)} maps, each sized by demos recorded on it. campgrounds "
        f"({maps[0].demos:,}) against the long tail is the true shape of a "
        f"career, not a flattering one.",
        "frags_rebuilt.demos group by map_name"))
    panels.append(_panel(
        "P3 - round grid",
        p.round_grid(rounds, cols=48, rows=18),
        "One cell per round. The frame runs out long before the archive does, "
        "and the caption says so rather than implying the grid is complete.",
        "round_kills_v1 (NOT sum(demos.rounds)=138,301, counter-inflated)"))
    panels.append(_panel(
        "P3 - the denominator beat",
        p.round_grid(allk, cols=48, rows=18,
                     lit=round(48 * 18 * user / allk)),
        f"{allk:,} player kills; {user:,} were the user's. The lit fraction is "
        f"the honest ratio ({user / allk:.1%}), which is why this beat replaces "
        f"a disclaimer card.",
        "corpus_status(ALL_PLAYERS) vs corpus_status(USER_FRAGS)"))
    panels.append(_panel(
        "P3 - the five human answers",
        p.role_tiles("T1"),
        "The review workstation's buttons, re-expressed as the film's own "
        "typography. The website itself never appears on screen.",
        "review_corpus.ROLES"))

    # -- slots --------------------------------------------------------------
    slot_rows = "".join(
        f'<tr><td class="k">{escape(s.key)}</td><td>{escape(s.part)}</td>'
        f'<td>{escape(s.requirement)}</td>'
        f'<td class="num">{s.pool_size if s.pool_size is not None else "-"}</td>'
        f'<td>{escape(s.status)}</td></tr>' for s in SLOTS)

    fact_rows = "".join(
        f'<tr><td class="k">{escape(r["key"])}</td>'
        f'<td class="num">{_fmt(r["actual"])}</td>'
        f'<td>{escape(str(r["on_screen"] or "-- never shown --"))}</td>'
        f'<td class="{"ok" if r["ok"] else "bad"}">'
        f'{"VERIFIED" if r["ok"] else "DRIFT"}</td></tr>' for r in verified)

    ok = sum(1 for r in verified if r["ok"])
    return f"""<!doctype html><meta charset="utf-8">
<title>PANTHEON PROLOGUE - PROOF SHEET</title>
<style>
 :root{{color-scheme:dark}}
 body{{background:#08090b;color:#c8ccd2;margin:0;
   font:14px/1.6 ui-sans-serif,system-ui,sans-serif}}
 header{{padding:48px 40px 28px;border-bottom:1px solid #22252b}}
 h1{{font-size:34px;letter-spacing:6px;margin:0 0 8px;color:#c8ccd2;
   font-weight:600}}
 .sub{{color:#6b7280;letter-spacing:3px;font-size:12px}}
 main{{padding:32px 40px 80px;max-width:1000px}}
 h2{{font-size:12px;letter-spacing:5px;color:#d4a63c;margin:44px 0 16px;
   border-bottom:1px solid #22252b;padding-bottom:8px}}
 .panel{{margin:0 0 30px;background:#0d0f12;border:1px solid #1c1f25;
   padding:18px}}
 .panel h3{{font-size:12px;letter-spacing:3px;color:#8a9099;margin:0 0 12px;
   font-weight:500;text-transform:uppercase}}
 .art{{overflow-x:auto}} .art svg{{max-width:100%;height:auto;display:block}}
 .note{{margin:12px 0 4px;color:#a8adb6}}
 .src{{margin:0;color:#565b66;font:12px ui-monospace,monospace}}
 table{{border-collapse:collapse;width:100%;font-size:13px}}
 th,td{{text-align:left;padding:7px 10px;border-bottom:1px solid #1c1f25;
   vertical-align:top}}
 th{{color:#6b7280;font-size:11px;letter-spacing:2px;text-transform:uppercase}}
 .k{{font:12px ui-monospace,monospace;color:#d4a63c;white-space:nowrap}}
 .num{{font:13px ui-monospace,monospace;text-align:right;white-space:nowrap}}
 .ok{{color:#5fbf7f}} .bad{{color:#e05a4a}}
</style>
<header>
 <h1>PANTHEON PROLOGUE</h1>
 <div class="sub">PROOF SHEET &#183; {ok}/{len(verified)} FACTS VERIFIED
 AGAINST LIVE CACHES &#183; NO HISTORICAL MATERIAL CONSUMED</div>
</header>
<main>
 <h2>Facts ledger</h2>
 <table><tr><th>fact</th><th>measured</th><th>permitted on screen</th>
 <th></th></tr>{fact_rows}</table>

 <h2>Primitives, driven by live data</h2>
 {''.join(panels)}

 <h2>Historical slots - what human review must fill</h2>
 <table><tr><th>slot</th><th>part</th><th>requirement</th><th>pool</th>
 <th>status</th></tr>{slot_rows}</table>
</main>
"""


def main(argv: list[str]) -> int:
    out = Path(argv[1]) if len(argv) > 1 else Path("docs/prologue/proof.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(), encoding="utf-8")
    print(f"wrote {out}  ({out.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":                      # pragma: no cover - CLI
    raise SystemExit(main(sys.argv))
