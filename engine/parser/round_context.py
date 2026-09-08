"""Round and team context for a kill: who was still alive, and what it decided.

Clan Arena has no respawn inside a round, so a round's obituaries ARE the
alive-count timeline: everyone on the roster starts the round alive and each
obituary removes exactly one player until one side is empty. That makes
"he was the last one left", "he closed the round" and "he was one against
three" observable facts rather than impressions -- but only once two things
established in the fixture audit are true:

  * rounds are reconstructed from CS_ROUND_STATUS/CS_ROUND_TIME with the
    trailing quote and newline normalised. The native round counter reports 27
    pseudo-rounds where this recording has 14, and every alive-count derived
    from those would be counting across round boundaries.

  * a round's window ends ONE SNAPSHOT after its end command, not at it. The
    command is logged against the previous snapshot, so the kill that decided
    the round lands 25ms later -- measured on 13 of 13 rounds in the fixture
    and independently on demo509's 14. Ending at the command drops the
    round-winning frag out of the round entirely.

Teams come from the configstring team field. Where that is missing the caller
gets nothing rather than a guess; a team inferred from proximity is how a
teammate becomes an opponent.
"""
from __future__ import annotations

import re

try:
    from engine.parser.protocol import ConfigString as _CS
    CS_ROUND_STATUS, CS_ROUND_TIME = _CS.ROUND_STATUS, _CS.ROUND_TIME
except Exception:                                                # noqa: BLE001
    CS_ROUND_STATUS, CS_ROUND_TIME = 661, 662

# One server frame. The round-end command is logged against the previous
# snapshot, so the terminal kill arrives in the next one.
END_COMMAND_GRACE_MS = 200      # generous; the measured lag is exactly 25

WORLD = 1022
TRADE_WINDOW_MS = 3000
AMBUSH_MAX_VISIBLE_MS = 1000


def _norm(v: str | None) -> str:
    """Configstring values keep a closing quote and a newline.

    int() on the raw value raises, and the historical handling of that was to
    skip the row, which is how a round boundary went missing.
    """
    return (v or "").replace('"', "").replace("\n", "").replace("\r", "").strip()


def reconstruct_rounds(parsed: dict) -> list[dict]:
    """Rounds from the round configstrings, not from the native counter."""
    announced: list[dict] = []
    ended: list[int] = []
    for r in parsed.get("round_results") or []:
        v = _norm(r.get("value"))
        cs = r.get("cs")
        if cs == CS_ROUND_STATUS:
            m = re.search(r"round\\(-?\d+)", v)
            st = re.search(r"time\\(-?\d+)", v)
            if m and int(m.group(1)) > 0:
                announced.append({
                    "round": int(m.group(1)),
                    "announced_ms": r.get("server_time_ms"),
                    "scheduled_start_ms": int(st.group(1)) if st else None,
                })
        elif cs == CS_ROUND_TIME:
            try:
                if int(v) < 0:
                    ended.append(r.get("server_time_ms"))
            except ValueError:
                continue

    seen, rounds = set(), []
    for a in announced:
        if a["round"] in seen:
            continue                    # a reliable command repeats; it is
            # not a new round, and counting repeats is what produced 27.
        seen.add(a["round"])
        rounds.append(a)
    rounds.sort(key=lambda r: r["round"])

    last_t = 0
    for s in parsed.get("snapshots") or []:
        t = s.get("server_time_ms")
        if t and t > last_t:
            last_t = t

    for i, r in enumerate(rounds):
        nxt = rounds[i + 1]["announced_ms"] if i + 1 < len(rounds) else last_t
        r["start_ms"] = r["scheduled_start_ms"] or r["announced_ms"]
        e = [x for x in ended if x and r["start_ms"] <= x <= (nxt or last_t)]
        r["end_command_ms"] = e[0] if e else None
        # Plus one snapshot. This is the whole point.
        r["end_ms"] = (e[0] + END_COMMAND_GRACE_MS) if e else (nxt or last_t)
        r["end_basis"] = ("ROUND_TIME_MINUS_ONE_PLUS_ONE_SNAPSHOT" if e
                          else "NO_END_SIGNAL__BOUNDED_BY_NEXT_ROUND_OR_EOF")
    return rounds


def teams_of(parsed: dict) -> dict[int, str]:
    """slot -> RED/BLUE. Slots with no team field are simply absent."""
    out = {}
    for k, v in (parsed.get("players") or {}).items():
        t = (v or {}).get("team")
        if t in ("RED", "BLUE"):
            try:
                out[int(k)] = t
            except (TypeError, ValueError):
                continue
    return out


def _obituaries(parsed: dict) -> list[dict]:
    return sorted(
        (e for e in (parsed.get("events") or []) if e.get("type") == "obituary"
         and e.get("server_time_ms") is not None),
        key=lambda e: e["server_time_ms"])


def build_context(parsed: dict, player: int | None) -> dict[int, dict]:
    """Per-kill-time context for `player`'s kills. Empty when teams are unknown.

    The alive count is exact for Clan Arena and would be wrong for any mode
    with respawns, so the caller must not reuse this on one.
    """
    teams = teams_of(parsed)
    if not teams or player is None or player not in teams:
        return {}
    rounds = reconstruct_rounds(parsed)
    if not rounds:
        return {}
    obits = _obituaries(parsed)

    my_team = teams[player]
    mates = {s for s, t in teams.items() if t == my_team}
    foes = {s for s, t in teams.items() if t != my_team}

    # who killed me, per round -- for revenge across rounds
    killed_me_by_round: dict[int, set[int]] = {}
    out: dict[int, dict] = {}

    for rd in rounds:
        lo, hi = rd["start_ms"], rd["end_ms"]
        in_round = [e for e in obits if lo <= e["server_time_ms"] <= hi]
        if not in_round:
            continue
        alive_mates, alive_foes = set(mates), set(foes)
        prev_deaths: list[dict] = []

        for e in in_round:
            k, v = e.get("killer_client"), e.get("victim_client")
            t = e["server_time_ms"]
            before_mates, before_foes = len(alive_mates), len(alive_foes)

            if k == player and v in alive_foes:
                # snapshot the state AT the kill, before applying it
                last = in_round[-1]["server_time_ms"] == t
                trade = any(
                    d["victim"] in mates and d["killer"] == v
                    and 0 <= t - d["t"] <= TRADE_WINDOW_MS
                    for d in prev_deaths)
                ctx = {
                    "round_index": rd["round"],
                    "round_start_ms": rd["start_ms"],
                    "round_end_ms": rd["end_ms"],
                    "round_end_basis": rd["end_basis"],
                    "team": my_team,
                    "alive_teammates_at_kill": before_mates,
                    "alive_opponents_at_kill": before_foes,
                    "opponents_left_after_kill": before_foes - 1,
                    "is_round_winning_frag": bool(before_foes == 1),
                    "is_first_blood": not prev_deaths,
                    "is_last_alive": before_mates == 1,
                    "outnumbered_by": max(0, before_foes - before_mates),
                    "is_trade_kill": trade,
                    "is_revenge": v in killed_me_by_round.get(rd["round"] - 1,
                                                              set()),
                    "is_terminal_kill_of_round": last,
                }
                out[t] = ctx

            if v in alive_mates:
                alive_mates.discard(v)
            elif v in alive_foes:
                alive_foes.discard(v)
            if v == player and k is not None and k != WORLD and k in foes:
                killed_me_by_round.setdefault(rd["round"], set()).add(k)
            prev_deaths.append({"t": t, "killer": k, "victim": v})

    return out
