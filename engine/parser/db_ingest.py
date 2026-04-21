"""engine/parser/db_ingest.py

Write a parsed DM73 stream dict (from DM73Parser.parse()) into frags.db.

Tables written:
  demos            — one row per demo (idempotent on filename)
  demo_events      — all game events (obituaries, weapon fires, pickups, etc.)
  demo_rounds      — round timeline
  demo_player_stats — per-demo kill/death aggregates
  player_snapshots  — per-snapshot observed-player state (position/velocity/angles)
  players           — cross-demo player registry (upsert on canonical name)
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

_DEFAULT_DB = (
    Path(__file__).parent.parent.parent
    / 'creative_suite' / 'database' / 'frags.db'
)
_SCHEMA = (
    Path(__file__).parent.parent.parent
    / 'creative_suite' / 'database' / 'schema.sql'
)

_COLOR_RE = re.compile(r'\^\d')


def _strip_colors(name: str) -> str:
    return _COLOR_RE.sub('', name).strip().lower()


def _ensure_schema(con: sqlite3.Connection) -> None:
    sql = _SCHEMA.read_text(encoding='utf-8')
    con.executescript(sql)
    con.commit()


def ingest(stream: dict, db_path: Path = _DEFAULT_DB) -> int:
    """Write parsed stream dict to frags.db. Returns demo_id."""
    con = sqlite3.connect(str(db_path))
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA foreign_keys=ON')
    _ensure_schema(con)
    try:
        demo_id = _write_demo(con, stream)
        _write_players(con, stream)
        _write_rounds(con, demo_id, stream)
        _write_events(con, demo_id, stream)
        _write_player_stats(con, demo_id, stream)
        _write_snapshots(con, demo_id, stream)
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
    return demo_id


# ── writers ────────────────────────────────────────────────────────────────────

def _write_demo(con: sqlite3.Connection, stream: dict) -> int:
    filename = stream['demo']
    cur = con.execute(
        'SELECT id FROM demos WHERE filename = ?', (filename,)
    )
    row = cur.fetchone()
    if row:
        demo_id = row[0]
        # Refresh metadata
        con.execute(
            'UPDATE demos SET map_name=?, game_type=?, parser=? WHERE id=?',
            (stream['map'], stream['gametype'], 'dm73-python', demo_id),
        )
    else:
        cur = con.execute(
            'INSERT INTO demos (filename, map_name, game_type, parser)'
            ' VALUES (?, ?, ?, ?)',
            (filename, stream['map'], stream['gametype'], 'dm73-python'),
        )
        demo_id = cur.lastrowid
    return demo_id


def _write_players(con: sqlite3.Connection, stream: dict) -> None:
    for _client, info in stream.get('players', {}).items():
        raw_name  = info.get('name', '')
        canonical = _strip_colors(raw_name)
        if not canonical:
            continue
        cur = con.execute(
            'SELECT id, aliases FROM players WHERE canonical_name = ?', (canonical,)
        )
        row = cur.fetchone()
        if row:
            player_id, aliases_json = row
            aliases: list = json.loads(aliases_json) if aliases_json else []
            if raw_name not in aliases:
                aliases.append(raw_name)
                con.execute(
                    'UPDATE players SET aliases=? WHERE id=?',
                    (json.dumps(aliases), player_id),
                )
        else:
            con.execute(
                'INSERT INTO players (canonical_name, aliases, first_seen_demo)'
                ' VALUES (?, ?, ?)',
                (canonical, json.dumps([raw_name]), stream['demo']),
            )


def _write_rounds(con: sqlite3.Connection, demo_id: int, stream: dict) -> None:
    # Delete existing rounds for this demo (re-ingest safe)
    con.execute('DELETE FROM demo_rounds WHERE demo_id = ?', (demo_id,))
    rows = [
        (demo_id, r['round'], r['start_ms'], r.get('end_ms'))
        for r in stream.get('rounds', [])
    ]
    con.executemany(
        'INSERT INTO demo_rounds (demo_id, round_num, start_ms, end_ms)'
        ' VALUES (?, ?, ?, ?)',
        rows,
    )


def _write_events(con: sqlite3.Connection, demo_id: int, stream: dict) -> None:
    con.execute('DELETE FROM demo_events WHERE demo_id = ?', (demo_id,))
    rows = []
    for ev in stream.get('events', []):
        rows.append((
            demo_id,
            ev.get('server_time_ms'),
            ev.get('round'),
            ev.get('type'),
            ev.get('event_code'),
            ev.get('entity_num'),
            ev.get('client_num'),
            ev.get('victim_client'),
            ev.get('killer_client'),
            ev.get('weapon'),
            ev.get('weapon_name'),
            ev.get('event_parm'),
            ev.get('pos_x'),
            ev.get('pos_y'),
            ev.get('pos_z'),
        ))
    con.executemany(
        'INSERT INTO demo_events'
        ' (demo_id, server_time_ms, round_num, event_type, event_code,'
        '  entity_num, client_num, victim_client, killer_client,'
        '  weapon, weapon_name, event_parm, pos_x, pos_y, pos_z)'
        ' VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
        rows,
    )


def _write_player_stats(con: sqlite3.Connection, demo_id: int, stream: dict) -> None:
    con.execute('DELETE FROM demo_player_stats WHERE demo_id = ?', (demo_id,))
    rows = []
    for s in stream.get('player_stats', []):
        rows.append((
            demo_id,
            s['client_num'],
            s['player_name'],
            s['team'],
            s['kills'],
            s['deaths'],
            s['suicides'],
            json.dumps(s['kills_by_weapon']),
            json.dumps(s['deaths_by_weapon']),
        ))
    con.executemany(
        'INSERT INTO demo_player_stats'
        ' (demo_id, client_num, player_name, team, kills, deaths, suicides,'
        '  kills_by_weapon, deaths_by_weapon)'
        ' VALUES (?,?,?,?,?,?,?,?,?)',
        rows,
    )


def _write_snapshots(con: sqlite3.Connection, demo_id: int, stream: dict) -> None:
    con.execute('DELETE FROM player_snapshots WHERE demo_id = ?', (demo_id,))
    rows = []
    for snap in stream.get('snapshots', []):
        rows.append((
            demo_id,
            snap.get('server_time_ms'),
            snap.get('round_num'),
            snap.get('client_num'),
            snap.get('origin_x'),
            snap.get('origin_y'),
            snap.get('origin_z'),
            snap.get('vel_x'),
            snap.get('vel_y'),
            snap.get('vel_z'),
            snap.get('angle_pitch'),
            snap.get('angle_yaw'),
            snap.get('weapon'),
            snap.get('speed'),
        ))
    con.executemany(
        'INSERT INTO player_snapshots'
        ' (demo_id, server_time_ms, round_num, client_num,'
        '  origin_x, origin_y, origin_z, vel_x, vel_y, vel_z,'
        '  angle_pitch, angle_yaw, weapon, speed)'
        ' VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
        rows,
    )
