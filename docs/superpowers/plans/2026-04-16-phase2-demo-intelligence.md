# Phase 2 — Demo Intelligence Engine

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Parse all 948+ `.dm_73` Quake Live demo files into a SQLite frag database, build a human review dashboard to rate/approve frags, and automate WolfcamQL batch rendering of approved frags to AVI clips.

**Architecture:** Three independent sub-systems wired together through the shared `frags.db` SQLite database. (1) Parser: UDT_json.exe + qldemo-python extract every EV_OBITUARY kill event into the database. (2) Review: Streamlit dashboard reads frags, lets user rate/approve/reject. (3) Renderer: batch_renderer writes gamestart.cfg, launches wolfcamql.exe per approved frag, polls process exit. All three sub-systems are independently testable. No sub-system calls another directly — they share only the database.

**Tech Stack:** Python 3.11+, SQLite3 (stdlib), Streamlit 1.30+, tqdm, subprocess (no shell=True anywhere)

**Key constants (from wolfcamql source `bg_public.h`):**
- `EV_OBITUARY = 58`
- `EV_EVENT_BITS = 0x00000300` (bits 8 and 9)
- Detection: `entity.event & ~0x300 == 58`
- Fields: `entity.otherEntityNum` = victim slot, `entity.otherEntityNum2` = killer slot, `entity.eventParm` = MOD_* weapon
- Configstring 0: server info (key `\mapname\`)
- Configstrings 529+N: player slot N name (key `\n\`)
- Air shot threshold: `victim.velocity[2] > 200` at frag snapshot

**Source paths:**
- Demos: `G:\QUAKE_LEGACY\WOLF WHISPERER\WolfcamQL\wolfcam-ql\demos\` (948 `.dm_73` files)
- WolfcamQL exe: `G:\QUAKE_LEGACY\WOLF WHISPERER\WolfcamQL\wolfcamql.exe`
- WolfcamQL home: `G:\QUAKE_LEGACY\WOLF WHISPERER\WolfcamQL\wolfcam-ql\`
- UDT source: `G:\QUAKE_LEGACY\tools\quake-source\uberdemotools\` (must download binary)
- qldemo-python: `G:\QUAKE_LEGACY\tools\quake-source\qldemo-python\`
- Database: `G:\QUAKE_LEGACY\database\frags.db`
- Schema: `G:\QUAKE_LEGACY\database\schema.sql`

---

## File Map

```
phase2/
  __init__.py
  config.py              <- all Phase 2 paths and constants
  verify_env.py          <- pre-flight checker (tools, db, demo dir)
  parser/
    __init__.py
    udt_wrapper.py       <- run UDT_json.exe, parse JSON output per demo
    demo_parser.py       <- qldemo-python driver: iterate snapshots, extract configstrings
    frag_detector.py     <- EV_OBITUARY scan, air shot calc, multi-kill grouping
  database/
    __init__.py
    db.py                <- SQLite connection, insert_demo(), insert_frag(), query functions
    migrations.py        <- run schema.sql on first init (idempotent)
  renderer/
    __init__.py
    batch_renderer.py    <- write gamestart.cfg, launch wolfcamql, poll exit
    cap_cfg.py           <- generate cap.cfg (recording settings)
  review/
    __init__.py
    dashboard.py         <- Streamlit app: browse frags, rate/approve/reject
  re/
    README.md            <- Ghidra analysis notes for WolfWhisperer.exe

tests/
  phase2/
    __init__.py
    conftest.py          <- shared fixtures: temp DB, sample demo path, mock entities
    test_udt_wrapper.py
    test_frag_detector.py
    test_db.py
    test_batch_renderer.py
```

---

## Human Review Gates

| Gate | When | What to do |
|---|---|---|
| P2-1 | After Task 4, before full parse | Run parser on 10 sample demos. Review DB output. Confirm frag count/fields look right. |
| P2-2 | After Task 6, before any render | Open Streamlit dashboard. Rate frags. Must approve at least 10 before batch render. |
| P2-3 | After first 10 renders complete | Watch 10 AVI clips. Confirm timing, camera, file size. Approve before full batch. |

---

## Task 0: Package Init Files and Environment Setup

**Files:**
- Create: `tests/phase2/__init__.py`
- Create: `phase2/__init__.py`
- Create: `phase2/parser/__init__.py`
- Create: `phase2/database/__init__.py`
- Create: `phase2/renderer/__init__.py`
- Create: `phase2/review/__init__.py`
- Create: `phase2/re/README.md`

- [ ] **Step 1: Create directory structure**

```bash
cd G:/QUAKE_LEGACY
mkdir -p phase2/parser phase2/database phase2/renderer phase2/review phase2/re
mkdir -p tests/phase2
```

- [ ] **Step 2: Create all init files**

```bash
touch phase2/__init__.py
touch phase2/parser/__init__.py
touch phase2/database/__init__.py
touch phase2/renderer/__init__.py
touch phase2/review/__init__.py
touch tests/phase2/__init__.py
```

On Windows (Git Bash):
```bash
echo "" > phase2/__init__.py
echo "" > phase2/parser/__init__.py
echo "" > phase2/database/__init__.py
echo "" > phase2/renderer/__init__.py
echo "" > phase2/review/__init__.py
echo "" > tests/phase2/__init__.py
```

- [ ] **Step 3: Install Python dependencies**

```bash
pip install streamlit tqdm
```

Phase 2 requires only stdlib + streamlit + tqdm. qldemo-python uses a C extension (huffman) that must be compiled.

- [ ] **Step 4: Build qldemo-python huffman C extension**

```bash
cd "G:/QUAKE_LEGACY/tools/quake-source/qldemo-python"
python setup.py build_ext --inplace
```

Expected: creates `huffman.pyd` (Windows) or `huffman.so` (Linux) in the `qldemo-python/` directory.

If `setup.py` fails (Python 3.11 distutils removed), use:
```bash
pip install setuptools
python setup.py build_ext --inplace
```

If it still fails, install via pip directly pointing at the source:
```bash
pip install -e "G:/QUAKE_LEGACY/tools/quake-source/qldemo-python"
```

- [ ] **Step 5: Download UDT_json.exe binary**

UDT source is present but the binary must be downloaded separately:
1. Go to: https://udt.playmorepromode.com
2. Download the Windows x64 command-line tools zip (filename contains `_con_x64`)
3. Extract all `.exe` files to: `G:\QUAKE_LEGACY\tools\uberdemotools\`
4. Verify: `G:\QUAKE_LEGACY\tools\uberdemotools\UDT_json.exe` exists

- [ ] **Step 6: Commit**

```bash
git add phase2/ tests/phase2/
git commit -m "feat(phase2): add package structure and init files"
```

---

## Task 1: Config Module

**Files:**
- Create: `phase2/config.py`
- Create: `tests/phase2/conftest.py`

- [ ] **Step 1: Write failing test**

Create `tests/phase2/conftest.py`:

```python
"""Shared fixtures for Phase 2 tests."""
import pytest
import sqlite3
from pathlib import Path

# Absolute path to the project root — required for all test paths
ROOT = Path(__file__).parent.parent.parent  # tests/phase2/../../ = G:/QUAKE_LEGACY

# Sample demo: use first .dm_73 in the demos directory (must exist)
DEMOS_DIR = ROOT / "WOLF WHISPERER" / "WolfcamQL" / "wolfcam-ql" / "demos"


@pytest.fixture
def cfg():
    from phase2.config import Config
    return Config()


@pytest.fixture
def tmp_db(tmp_path):
    """Create an in-memory-backed temp SQLite database with schema applied."""
    from phase2.database.migrations import init_db
    db_path = tmp_path / "test_frags.db"
    init_db(db_path)
    return db_path


@pytest.fixture
def sample_demo_path():
    """Return path to the first real .dm_73 demo file for integration tests."""
    demos = sorted(DEMOS_DIR.glob("*.dm_73"))
    if not demos:
        pytest.skip(f"No .dm_73 files found in {DEMOS_DIR}")
    return demos[0]


@pytest.fixture
def mock_entity():
    """Return a mock entity dict matching EV_OBITUARY structure."""
    return {
        "number": 5,
        "event": 58,          # EV_OBITUARY, no extra bits set
        "eventParm": 10,       # MOD_RAILGUN
        "otherEntityNum": 3,   # victim slot
        "otherEntityNum2": 1,  # killer slot
        "pos": {
            "trBase": [100.0, 200.0, 50.0],
            "trDelta": [0.0, 0.0, 300.0],   # victim moving upward = airshot candidate
        },
    }
```

- [ ] **Step 2: Write config test**

Create `tests/phase2/test_config.py`:

```python
from phase2.config import Config
from pathlib import Path


def test_config_demos_dir_exists(cfg):
    assert cfg.demos_dir.exists(), f"Demos dir not found: {cfg.demos_dir}"


def test_config_demo_count(cfg):
    demos = list(cfg.demos_dir.glob("*.dm_73"))
    assert len(demos) > 100, f"Expected 100+ demos, found {len(demos)}"


def test_config_wolfcamql_exe_exists(cfg):
    assert cfg.wolfcamql_exe.exists(), f"wolfcamql.exe not found: {cfg.wolfcamql_exe}"


def test_config_db_path_is_absolute(cfg):
    assert cfg.db_path.is_absolute()
    assert cfg.db_path.name == "frags.db"


def test_config_udt_json_path(cfg):
    # UDT binary may not exist yet — just check the path is configured
    assert cfg.udt_json_exe.name == "UDT_json.exe"


def test_config_ms_to_clock():
    from phase2.config import ms_to_clock
    assert ms_to_clock(0) == "0:00"
    assert ms_to_clock(65000) == "1:05"
    assert ms_to_clock(3600000) == "60:00"
    assert ms_to_clock(90500) == "1:30"
```

- [ ] **Step 3: Run failing test**

```bash
cd G:/QUAKE_LEGACY
pytest tests/phase2/test_config.py -v
```

Expected: ImportError (module doesn't exist yet).

- [ ] **Step 4: Implement config.py**

Create `phase2/config.py`:

```python
"""Central configuration for Phase 2 — Demo Intelligence Engine."""
from pathlib import Path

# Project root: one level up from phase2/
ROOT = Path(__file__).parent.parent


def ms_to_clock(ms: int) -> str:
    """Convert milliseconds to WolfcamQL seekclock format: M:SS (no zero-pad on minutes)."""
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"


class Config:
    """All Phase 2 paths and constants. Explicit __init__ — no class-level mutables."""

    def __init__(self):
        # ── Demo source ───────────────────────────────────────────
        self.demos_dir: Path = (
            ROOT / "WOLF WHISPERER" / "WolfcamQL" / "wolfcam-ql" / "demos"
        )

        # ── WolfcamQL ─────────────────────────────────────────────
        self.wolfcamql_exe: Path = (
            ROOT / "WOLF WHISPERER" / "WolfcamQL" / "wolfcamql.exe"
        )
        self.wolfcamql_home: Path = (
            ROOT / "WOLF WHISPERER" / "WolfcamQL" / "wolfcam-ql"
        )

        # ── UberDemoTools ─────────────────────────────────────────
        self.udt_json_exe: Path = ROOT / "tools" / "uberdemotools" / "UDT_json.exe"

        # ── qldemo-python ─────────────────────────────────────────
        self.qldemo_python_dir: Path = (
            ROOT / "tools" / "quake-source" / "qldemo-python"
        )

        # ── Database ──────────────────────────────────────────────
        self.db_path: Path = ROOT / "database" / "frags.db"
        self.schema_path: Path = ROOT / "database" / "schema.sql"

        # ── Rendered clips output ─────────────────────────────────
        self.clips_output_dir: Path = ROOT / "output" / "phase2_clips"
        self.clips_output_dir.mkdir(parents=True, exist_ok=True)

        # ── Frag timing defaults (milliseconds) ───────────────────
        self.pre_roll_ms: int = 5000    # 5s before the kill
        self.post_roll_ms: int = 2000   # 2s after the kill

        # ── EV_OBITUARY detection constants (from bg_public.h) ────
        self.EV_OBITUARY: int = 58
        self.EV_EVENT_BITS: int = 0x00000300   # bits 8+9, mask these off

        # ── Air shot threshold ────────────────────────────────────
        self.airshot_z_velocity: float = 200.0  # units/s upward Z at frag time

        # ── Multi-kill window ─────────────────────────────────────
        self.multikill_window_ms: int = 3000    # kills within 3s = multi-kill

        # ── MOD_* weapon name map (from constants.py) ─────────────
        self.mod_names: dict = {
            0: "MOD_UNKNOWN",
            1: "MOD_SHOTGUN",
            2: "MOD_GAUNTLET",
            3: "MOD_MACHINEGUN",
            4: "MOD_GRENADE",
            5: "MOD_GRENADE_SPLASH",
            6: "MOD_ROCKET",
            7: "MOD_ROCKET_SPLASH",
            8: "MOD_PLASMA",
            9: "MOD_PLASMA_SPLASH",
            10: "MOD_RAILGUN",
            11: "MOD_LIGHTNING",
            12: "MOD_BFG",
            13: "MOD_BFG_SPLASH",
            14: "MOD_WATER",
            15: "MOD_SLIME",
            16: "MOD_LAVA",
            17: "MOD_CRUSH",
            18: "MOD_TELEFRAG",
            19: "MOD_FALLING",
            20: "MOD_SUICIDE",
            21: "MOD_TARGET_LASER",
            22: "MOD_TRIGGER_HURT",
            23: "MOD_GRAPPLE",
        }

    def weapon_name(self, mod_id: int) -> str:
        """Return MOD_* string for a weapon ID."""
        return self.mod_names.get(mod_id, f"MOD_UNKNOWN_{mod_id}")

    def demo_list(self) -> list:
        """Return sorted list of all .dm_73 files in demos_dir."""
        return sorted(self.demos_dir.glob("*.dm_73"))
```

- [ ] **Step 5: Run test to confirm it passes**

```bash
pytest tests/phase2/test_config.py -v
```

Expected: all 6 tests PASS (UDT test passes even if binary not downloaded yet — it only checks path config).

- [ ] **Step 6: Commit**

```bash
git add phase2/config.py tests/phase2/conftest.py tests/phase2/test_config.py
git commit -m "feat(phase2): add Config module with paths, constants, and ms_to_clock"
```

---

## Task 2: Database — Migrations and CRUD

**Files:**
- Create: `phase2/database/migrations.py`
- Create: `phase2/database/db.py`
- Create: `tests/phase2/test_db.py`

- [ ] **Step 1: Write failing test**

Create `tests/phase2/test_db.py`:

```python
import pytest
import sqlite3
from pathlib import Path
from phase2.database.db import (
    insert_demo, insert_frag, get_frags_for_review,
    mark_frag_approved, mark_frag_rejected, get_demo_by_filename,
    get_frag_by_id, count_frags,
)


def test_insert_demo_returns_id(tmp_db):
    conn = sqlite3.connect(tmp_db)
    demo_id = insert_demo(conn, filename="test.dm_73", map_name="campgrounds",
                          game_type=0, duration_ms=120000, parser="test")
    conn.close()
    assert isinstance(demo_id, int)
    assert demo_id > 0


def test_insert_demo_duplicate_returns_existing_id(tmp_db):
    conn = sqlite3.connect(tmp_db)
    id1 = insert_demo(conn, filename="same.dm_73", map_name="arena", game_type=0,
                      duration_ms=60000, parser="test")
    id2 = insert_demo(conn, filename="same.dm_73", map_name="arena", game_type=0,
                      duration_ms=60000, parser="test")
    conn.close()
    assert id1 == id2


def test_insert_frag_returns_id(tmp_db):
    conn = sqlite3.connect(tmp_db)
    demo_id = insert_demo(conn, filename="frag_test.dm_73", map_name="purgatory",
                          game_type=0, duration_ms=90000, parser="test")
    frag_id = insert_frag(conn, demo_id=demo_id, frag_time_ms=30000,
                          weapon="MOD_RAILGUN", is_airshot=True,
                          is_multikill=False, kill_streak=1,
                          distance_units=850.0, victim_z_vel=310.0)
    conn.close()
    assert isinstance(frag_id, int)
    assert frag_id > 0


def test_get_frags_for_review_returns_unapproved(tmp_db):
    conn = sqlite3.connect(tmp_db)
    demo_id = insert_demo(conn, filename="review_test.dm_73", map_name="asylum",
                          game_type=0, duration_ms=90000, parser="test")
    insert_frag(conn, demo_id=demo_id, frag_time_ms=10000, weapon="MOD_ROCKET",
                is_airshot=False, is_multikill=False, kill_streak=1,
                distance_units=300.0, victim_z_vel=0.0)
    frags = get_frags_for_review(conn, limit=50)
    conn.close()
    assert len(frags) == 1
    assert frags[0]["weapon"] == "MOD_ROCKET"
    assert frags[0]["reviewed"] == 0


def test_mark_frag_approved(tmp_db):
    conn = sqlite3.connect(tmp_db)
    demo_id = insert_demo(conn, filename="approve_test.dm_73", map_name="qzendo3",
                          game_type=0, duration_ms=90000, parser="test")
    frag_id = insert_frag(conn, demo_id=demo_id, frag_time_ms=15000,
                          weapon="MOD_RAILGUN", is_airshot=True,
                          is_multikill=False, kill_streak=1,
                          distance_units=1200.0, victim_z_vel=400.0)
    mark_frag_approved(conn, frag_id, tier=1, notes="clean air rail")
    frag = get_frag_by_id(conn, frag_id)
    conn.close()
    assert frag["approved"] == 1
    assert frag["reviewed"] == 1
    assert frag["tier"] == 1
    assert frag["notes"] == "clean air rail"


def test_mark_frag_rejected(tmp_db):
    conn = sqlite3.connect(tmp_db)
    demo_id = insert_demo(conn, filename="reject_test.dm_73", map_name="qzendo3",
                          game_type=0, duration_ms=90000, parser="test")
    frag_id = insert_frag(conn, demo_id=demo_id, frag_time_ms=20000,
                          weapon="MOD_MACHINEGUN", is_airshot=False,
                          is_multikill=False, kill_streak=1,
                          distance_units=50.0, victim_z_vel=0.0)
    mark_frag_rejected(conn, frag_id, notes="boring mg kill")
    frag = get_frag_by_id(conn, frag_id)
    conn.close()
    assert frag["approved"] == 0
    assert frag["reviewed"] == 1


def test_count_frags(tmp_db):
    conn = sqlite3.connect(tmp_db)
    demo_id = insert_demo(conn, filename="count_test.dm_73", map_name="qzendo3",
                          game_type=0, duration_ms=90000, parser="test")
    for i in range(5):
        insert_frag(conn, demo_id=demo_id, frag_time_ms=i * 5000,
                    weapon="MOD_RAILGUN", is_airshot=False,
                    is_multikill=False, kill_streak=1,
                    distance_units=500.0, victim_z_vel=0.0)
    total = count_frags(conn)
    conn.close()
    assert total == 5
```

- [ ] **Step 2: Run failing test**

```bash
pytest tests/phase2/test_db.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement migrations.py**

Create `phase2/database/migrations.py`:

```python
"""
Run schema.sql to initialize the database.
Idempotent — safe to call on an existing database (uses CREATE TABLE IF NOT EXISTS).
"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
DEFAULT_SCHEMA = ROOT / "database" / "schema.sql"


def init_db(db_path: Path, schema_path: Path = DEFAULT_SCHEMA) -> None:
    """
    Initialize the SQLite database at db_path using schema.sql.
    Creates the database file if it does not exist.
    Safe to call on an already-initialized database.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")

    schema_sql = schema_path.read_text(encoding="utf-8")
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()

    print(f"Database initialized: {db_path}")


if __name__ == "__main__":
    from phase2.config import Config
    cfg = Config()
    init_db(cfg.db_path, cfg.schema_path)
```

- [ ] **Step 4: Implement db.py**

Create `phase2/database/db.py`:

```python
"""
SQLite CRUD functions for the Phase 2 frag database.
All functions take a sqlite3.Connection — callers manage connections.
Row factory is set to sqlite3.Row for dict-like access.
"""
import sqlite3
from pathlib import Path
from typing import Optional, List


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Open and configure a SQLite connection. Sets row_factory for dict-like rows."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # safe concurrent reads
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def insert_demo(
    conn: sqlite3.Connection,
    filename: str,
    map_name: Optional[str],
    game_type: Optional[int],
    duration_ms: Optional[int],
    parser: str,
) -> int:
    """
    Insert a demo record. Returns existing id if filename already in DB (idempotent).
    """
    # Check for existing
    row = conn.execute(
        "SELECT id FROM demos WHERE filename = ?", (filename,)
    ).fetchone()
    if row:
        return row["id"]

    cur = conn.execute(
        """INSERT INTO demos (filename, map_name, game_type, duration_ms, parser)
           VALUES (?, ?, ?, ?, ?)""",
        (filename, map_name, game_type, duration_ms, parser),
    )
    conn.commit()
    return cur.lastrowid


def insert_frag(
    conn: sqlite3.Connection,
    demo_id: int,
    frag_time_ms: int,
    weapon: str,
    is_airshot: bool,
    is_multikill: bool,
    kill_streak: int,
    distance_units: float,
    victim_z_vel: float,
    pre_roll_ms: int = 5000,
    post_roll_ms: int = 2000,
) -> int:
    """Insert a frag record. Returns new frag id."""
    cur = conn.execute(
        """INSERT INTO frags
           (demo_id, frag_time_ms, pre_roll_ms, post_roll_ms, weapon,
            is_airshot, is_multikill, kill_streak, distance_units, victim_z_vel)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (demo_id, frag_time_ms, pre_roll_ms, post_roll_ms, weapon,
         int(is_airshot), int(is_multikill), kill_streak,
         distance_units, victim_z_vel),
    )
    conn.commit()
    return cur.lastrowid


def get_frags_for_review(
    conn: sqlite3.Connection,
    limit: int = 100,
    weapon_filter: Optional[str] = None,
    airshot_only: bool = False,
    multikill_only: bool = False,
) -> List[sqlite3.Row]:
    """
    Return unreviewed frags with their demo filename joined.
    Optional filters: weapon, airshot_only, multikill_only.
    """
    where_clauses = ["f.reviewed = 0"]
    params = []

    if weapon_filter:
        where_clauses.append("f.weapon = ?")
        params.append(weapon_filter)
    if airshot_only:
        where_clauses.append("f.is_airshot = 1")
    if multikill_only:
        where_clauses.append("f.is_multikill = 1")

    where_sql = " AND ".join(where_clauses)
    params.append(limit)

    rows = conn.execute(
        f"""SELECT f.*, d.filename, d.map_name
            FROM frags f
            JOIN demos d ON f.demo_id = d.id
            WHERE {where_sql}
            ORDER BY f.is_airshot DESC, f.kill_streak DESC, f.frag_time_ms ASC
            LIMIT ?""",
        params,
    ).fetchall()
    return [dict(r) for r in rows]


def get_approved_frags(conn: sqlite3.Connection) -> List[dict]:
    """Return all approved frags with demo filename for rendering."""
    rows = conn.execute(
        """SELECT f.*, d.filename, d.map_name
           FROM frags f
           JOIN demos d ON f.demo_id = d.id
           WHERE f.approved = 1
           ORDER BY f.tier ASC, f.kill_streak DESC""",
    ).fetchall()
    return [dict(r) for r in rows]


def get_frag_by_id(conn: sqlite3.Connection, frag_id: int) -> Optional[dict]:
    """Return a single frag by id, or None."""
    row = conn.execute(
        "SELECT * FROM frags WHERE id = ?", (frag_id,)
    ).fetchone()
    return dict(row) if row else None


def get_demo_by_filename(conn: sqlite3.Connection, filename: str) -> Optional[dict]:
    """Return demo record by filename, or None."""
    row = conn.execute(
        "SELECT * FROM demos WHERE filename = ?", (filename,)
    ).fetchone()
    return dict(row) if row else None


def mark_frag_approved(
    conn: sqlite3.Connection,
    frag_id: int,
    tier: int = 2,
    notes: str = "",
) -> None:
    """Mark a frag as reviewed and approved with optional tier and notes."""
    conn.execute(
        """UPDATE frags
           SET reviewed = 1, approved = 1, tier = ?, notes = ?
           WHERE id = ?""",
        (tier, notes, frag_id),
    )
    conn.commit()


def mark_frag_rejected(
    conn: sqlite3.Connection,
    frag_id: int,
    notes: str = "",
) -> None:
    """Mark a frag as reviewed and rejected."""
    conn.execute(
        """UPDATE frags
           SET reviewed = 1, approved = 0, notes = ?
           WHERE id = ?""",
        (notes, frag_id),
    )
    conn.commit()


def count_frags(
    conn: sqlite3.Connection,
    approved_only: bool = False,
    reviewed_only: bool = False,
) -> int:
    """Count frags in the database with optional filters."""
    if approved_only:
        return conn.execute("SELECT COUNT(*) FROM frags WHERE approved = 1").fetchone()[0]
    if reviewed_only:
        return conn.execute("SELECT COUNT(*) FROM frags WHERE reviewed = 1").fetchone()[0]
    return conn.execute("SELECT COUNT(*) FROM frags").fetchone()[0]


def count_demos(conn: sqlite3.Connection) -> int:
    """Count parsed demos."""
    return conn.execute("SELECT COUNT(*) FROM demos").fetchone()[0]
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/phase2/test_db.py -v
```

Expected: all 7 tests PASS.

- [ ] **Step 6: Initialize the production database**

```bash
python phase2/database/migrations.py
```

Expected: `G:\QUAKE_LEGACY\database\frags.db` created with schema.

- [ ] **Step 7: Commit**

```bash
git add phase2/database/migrations.py phase2/database/db.py tests/phase2/test_db.py
git commit -m "feat(phase2): add SQLite database layer with migrations and CRUD"
```

---

## Task 3: Frag Detector — EV_OBITUARY Extraction Logic

**Files:**
- Create: `phase2/parser/frag_detector.py`
- Create: `tests/phase2/test_frag_detector.py`

This module contains all the detection logic as pure functions with no I/O. Input: list of entity dicts + snapshot server_time. Output: list of frag dicts. This makes it fully unit-testable without real demo files.

- [ ] **Step 1: Write failing test**

Create `tests/phase2/test_frag_detector.py`:

```python
import pytest
from phase2.parser.frag_detector import (
    is_obituary_event,
    extract_frag_from_entity,
    detect_airshot,
    group_multikillers,
    Frag,
)


def test_is_obituary_basic():
    # EV_OBITUARY = 58, no extra bits
    assert is_obituary_event(58) is True


def test_is_obituary_with_event_bits():
    # event bits set (0x100 or 0x200) — should still detect as obituary
    assert is_obituary_event(58 | 0x100) is True
    assert is_obituary_event(58 | 0x200) is True
    assert is_obituary_event(58 | 0x300) is True


def test_is_obituary_false_for_other_events():
    assert is_obituary_event(0) is False
    assert is_obituary_event(10) is False
    assert is_obituary_event(57) is False
    assert is_obituary_event(59) is False


def test_extract_frag_from_entity_basic(mock_entity):
    frag = extract_frag_from_entity(
        entity=mock_entity,
        server_time=30000,
        weapon_name="MOD_RAILGUN",
    )
    assert isinstance(frag, Frag)
    assert frag.frag_time_ms == 30000
    assert frag.weapon == "MOD_RAILGUN"
    assert frag.killer_slot == 1
    assert frag.victim_slot == 3


def test_detect_airshot_true_when_z_high(mock_entity):
    # victim_z_vel = 300 > 200 threshold
    result = detect_airshot(victim_z_vel=300.0, threshold=200.0)
    assert result is True


def test_detect_airshot_false_when_z_low():
    result = detect_airshot(victim_z_vel=50.0, threshold=200.0)
    assert result is False


def test_detect_airshot_false_when_z_negative():
    # Falling victim is not an air shot
    result = detect_airshot(victim_z_vel=-100.0, threshold=200.0)
    assert result is False


def test_group_multikillers_detects_multikill():
    """Two kills by same slot within 3000ms = multi-kill."""
    frags = [
        Frag(frag_time_ms=10000, killer_slot=1, victim_slot=2,
             weapon="MOD_RAILGUN", victim_z_vel=0.0),
        Frag(frag_time_ms=11500, killer_slot=1, victim_slot=3,
             weapon="MOD_RAILGUN", victim_z_vel=0.0),
        Frag(frag_time_ms=20000, killer_slot=2, victim_slot=1,
             weapon="MOD_ROCKET", victim_z_vel=0.0),
    ]
    result = group_multikillers(frags, window_ms=3000)
    # First two frags are multi-kills by slot 1
    assert result[0].is_multikill is True
    assert result[1].is_multikill is True
    # Third frag is solo — not a multi-kill
    assert result[2].is_multikill is False


def test_group_multikillers_streak_count():
    """Kill streak increments for same killer within window."""
    frags = [
        Frag(frag_time_ms=5000, killer_slot=1, victim_slot=2,
             weapon="MOD_RAILGUN", victim_z_vel=0.0),
        Frag(frag_time_ms=6000, killer_slot=1, victim_slot=3,
             weapon="MOD_RAILGUN", victim_z_vel=0.0),
        Frag(frag_time_ms=7000, killer_slot=1, victim_slot=4,
             weapon="MOD_RAILGUN", victim_z_vel=0.0),
    ]
    result = group_multikillers(frags, window_ms=3000)
    assert result[2].kill_streak == 3


def test_group_multikillers_resets_after_window():
    """Kills outside the window don't count toward streak."""
    frags = [
        Frag(frag_time_ms=1000, killer_slot=1, victim_slot=2,
             weapon="MOD_RAILGUN", victim_z_vel=0.0),
        Frag(frag_time_ms=10000, killer_slot=1, victim_slot=3,
             weapon="MOD_RAILGUN", victim_z_vel=0.0),  # 9s later — reset
    ]
    result = group_multikillers(frags, window_ms=3000)
    assert result[0].is_multikill is False
    assert result[1].is_multikill is False
    assert result[1].kill_streak == 1
```

- [ ] **Step 2: Run failing test**

```bash
pytest tests/phase2/test_frag_detector.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement frag_detector.py**

Create `phase2/parser/frag_detector.py`:

```python
"""
Frag detection logic — pure functions, no I/O.

All inputs are plain Python dicts/values matching qldemo-python's flattened
entity representation. Outputs are Frag dataclass instances.

EV_OBITUARY detection:
  event & ~EV_EVENT_BITS == EV_OBITUARY
  where EV_OBITUARY = 58, EV_EVENT_BITS = 0x300

Fields from entity:
  entity["event"]            -> raw event value (may have EV_EVENT_BITS set)
  entity["eventParm"]        -> MOD_* weapon id
  entity["otherEntityNum"]   -> victim client slot
  entity["otherEntityNum2"]  -> killer client slot
  entity["pos"]["trDelta"]   -> [vx, vy, vz] velocity components
"""
from dataclasses import dataclass, field
from typing import List, Optional

EV_OBITUARY = 58
EV_EVENT_BITS = 0x00000300


@dataclass
class Frag:
    """A single kill event extracted from a demo snapshot."""
    frag_time_ms: int
    killer_slot: int
    victim_slot: int
    weapon: str
    victim_z_vel: float

    # Computed after extraction
    is_airshot: bool = False
    is_multikill: bool = False
    kill_streak: int = 1

    # Optional metadata (filled by demo_parser after configstring lookup)
    killer_name: str = ""
    victim_name: str = ""
    demo_filename: str = ""
    map_name: str = ""


def is_obituary_event(raw_event: int) -> bool:
    """
    Return True if raw_event is an EV_OBITUARY (with or without EV_EVENT_BITS).

    The engine sets bits 8 and 9 of entity.event to differentiate repeated events.
    We mask them off before comparing.
    """
    return (raw_event & ~EV_EVENT_BITS) == EV_OBITUARY


def extract_frag_from_entity(
    entity: dict,
    server_time: int,
    weapon_name: str,
) -> Frag:
    """
    Extract a Frag from a raw entity dict at a given server_time.

    Args:
        entity:      Flattened entity dict from qldemo snapshot
        server_time: Snapshot server_time in milliseconds
        weapon_name: MOD_* string for entity["eventParm"]

    Returns: Frag with basic fields populated (is_airshot/is_multikill set later)
    """
    # Z velocity comes from pos.trDelta[2]
    try:
        z_vel = float(entity.get("pos", {}).get("trDelta", [0, 0, 0])[2])
    except (IndexError, TypeError, ValueError):
        z_vel = 0.0

    return Frag(
        frag_time_ms=server_time,
        killer_slot=entity.get("otherEntityNum2", 0),
        victim_slot=entity.get("otherEntityNum", 0),
        weapon=weapon_name,
        victim_z_vel=z_vel,
    )


def detect_airshot(victim_z_vel: float, threshold: float = 200.0) -> bool:
    """
    Return True if the victim was airborne (positive Z velocity above threshold).

    Only upward Z motion counts — negative Z means falling, which can be legitimate
    ground movement on inclines and should not be counted as an air shot.
    """
    return victim_z_vel > threshold


def group_multikillers(frags: List[Frag], window_ms: int = 3000) -> List[Frag]:
    """
    Scan sorted frag list and annotate is_multikill and kill_streak.

    Algorithm:
      - Maintain a dict: killer_slot -> list of recent kill timestamps
      - For each frag, remove kills from that killer's list older than window_ms
      - If list is non-empty after pruning -> current frag is part of a multi-kill streak
      - kill_streak = length of current window (including this kill)
      - is_multikill = kill_streak >= 2

    Input must be sorted by frag_time_ms ascending (demo_parser guarantees this).
    Returns the same list with is_multikill and kill_streak mutated in place.
    """
    # killer_slot -> [frag_time_ms, ...]
    killer_windows: dict = {}

    for frag in frags:
        slot = frag.killer_slot
        now = frag.frag_time_ms

        if slot not in killer_windows:
            killer_windows[slot] = []

        # Remove stale kills outside the window
        killer_windows[slot] = [
            t for t in killer_windows[slot] if now - t <= window_ms
        ]

        # Current kill streak = previous kills in window + this one
        streak = len(killer_windows[slot]) + 1
        frag.kill_streak = streak
        frag.is_multikill = streak >= 2

        # Record this kill
        killer_windows[slot].append(now)

    return frags
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/phase2/test_frag_detector.py -v
```

Expected: all 10 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add phase2/parser/frag_detector.py tests/phase2/test_frag_detector.py
git commit -m "feat(phase2): add EV_OBITUARY frag detector with airshot and multi-kill logic"
```

---

## Task 4: Demo Parser — qldemo-python Driver

**Files:**
- Create: `phase2/parser/demo_parser.py`
- Create: `phase2/parser/udt_wrapper.py`

This task implements two independent parsers. `demo_parser.py` uses qldemo-python for custom extraction (gives us Z velocity). `udt_wrapper.py` uses UDT_json.exe for fast batch parsing. The database ingestion pipeline uses `demo_parser.py` as primary and falls back to `udt_wrapper.py` when qldemo-python fails (corrupted demos, etc).

- [ ] **Step 1: Implement demo_parser.py**

Create `phase2/parser/demo_parser.py`:

```python
"""
Parse a single .dm_73 demo using qldemo-python.

Extracts:
  - map_name, game_type, duration_ms from configstrings + snapshots
  - All EV_OBITUARY kill events as Frag objects with Z velocity

qldemo-python import path: add qldemo-python dir to sys.path before import.
The huffman C extension must be compiled (see Task 0 Step 4).
"""
import sys
from pathlib import Path
from typing import List, Optional, Tuple

ROOT = Path(__file__).parent.parent.parent
QLDEMO_DIR = ROOT / "tools" / "quake-source" / "qldemo-python"

# Add qldemo-python to path so its C extension is found
if str(QLDEMO_DIR) not in sys.path:
    sys.path.insert(0, str(QLDEMO_DIR))

from phase2.config import Config
from phase2.parser.frag_detector import (
    is_obituary_event, extract_frag_from_entity,
    detect_airshot, group_multikillers, Frag,
)


def _parse_keyvalue_string(cs: str) -> dict:
    """
    Parse a Quake configstring of the form \\key\\value\\key\\value into a dict.
    Strips leading backslash if present.
    """
    cs = cs.strip()
    if cs.startswith("\\"):
        cs = cs[1:]
    parts = cs.split("\\")
    result = {}
    for i in range(0, len(parts) - 1, 2):
        result[parts[i]] = parts[i + 1]
    return result


def _get_map_name(configstrings: dict) -> Optional[str]:
    """Extract mapname from configstring index 0 (CS_SERVERINFO)."""
    cs0 = configstrings.get(0, "")
    if not cs0:
        return None
    kv = _parse_keyvalue_string(cs0)
    return kv.get("mapname")


def _get_player_names(configstrings: dict) -> dict:
    """
    Build slot -> player_name dict from configstrings 529-593 (CS_PLAYERS range).
    Each configstring is \\n\\PlayerName\\t\\teamnum\\...
    """
    players = {}
    for cs_idx, cs_val in configstrings.items():
        if 529 <= cs_idx <= 593:
            slot = cs_idx - 529
            kv = _parse_keyvalue_string(cs_val)
            name = kv.get("n", "")
            if name:
                players[slot] = name
    return players


def parse_demo(demo_path: Path, cfg: Config) -> Tuple[dict, List[Frag]]:
    """
    Parse a .dm_73 demo file using qldemo-python.

    Returns:
        (demo_info dict, list of Frag objects)

    demo_info keys: filename, map_name, game_type, duration_ms, parser

    Raises:
        ImportError: if huffman C extension not compiled
        RuntimeError: if demo is unreadable/corrupted
    """
    try:
        from qldemo import QLDemo
    except ImportError as e:
        raise ImportError(
            f"qldemo-python not available. Compile huffman extension first.\n"
            f"Run: cd {QLDEMO_DIR} && python setup.py build_ext --inplace\n"
            f"Original error: {e}"
        )

    raw_frags: List[Frag] = []
    last_server_time = 0
    configstrings = {}

    try:
        demo = QLDemo(str(demo_path))
        for packet in demo:
            if packet is None:
                continue

            # Accumulate configstrings from GameState packets
            if hasattr(packet, "configstrings"):
                configstrings.update(packet.configstrings)

            # Process snapshots
            if hasattr(packet, "serverTime"):
                server_time = packet.serverTime
                last_server_time = max(last_server_time, server_time)

                # Scan all entities in this snapshot for EV_OBITUARY
                entities = getattr(packet, "entities", [])
                for entity in entities:
                    entity_dict = entity.flatten() if hasattr(entity, "flatten") else entity

                    raw_event = entity_dict.get("event", 0)
                    if not is_obituary_event(raw_event):
                        continue

                    # Suicide check: killer == victim (skip these)
                    killer_slot = entity_dict.get("otherEntityNum2", 0)
                    victim_slot = entity_dict.get("otherEntityNum", 0)
                    if killer_slot == victim_slot:
                        continue

                    weapon_id = entity_dict.get("eventParm", 0)
                    weapon_name = cfg.weapon_name(weapon_id)

                    frag = extract_frag_from_entity(
                        entity=entity_dict,
                        server_time=server_time,
                        weapon_name=weapon_name,
                    )
                    frag.is_airshot = detect_airshot(
                        frag.victim_z_vel, cfg.airshot_z_velocity
                    )
                    frag.demo_filename = demo_path.name
                    raw_frags.append(frag)

    except StopIteration:
        pass  # Normal end of demo stream
    except Exception as e:
        raise RuntimeError(f"Failed to parse {demo_path.name}: {e}") from e

    # Annotate multi-kills (requires sorted order — already chronological)
    frags = group_multikillers(raw_frags, cfg.multikill_window_ms)

    # Resolve player names from configstrings
    player_names = _get_player_names(configstrings)
    for frag in frags:
        frag.killer_name = player_names.get(frag.killer_slot, f"slot{frag.killer_slot}")
        frag.victim_name = player_names.get(frag.victim_slot, f"slot{frag.victim_slot}")

    map_name = _get_map_name(configstrings)

    demo_info = {
        "filename": demo_path.name,
        "map_name": map_name,
        "game_type": None,   # can extend: parse g_gametype from CS_SERVERINFO
        "duration_ms": last_server_time,
        "parser": "qldemo-python",
    }

    return demo_info, frags
```

- [ ] **Step 2: Implement udt_wrapper.py**

Create `phase2/parser/udt_wrapper.py`:

```python
"""
Wrapper for UDT_json.exe — fast batch demo parsing via UberDemoTools.

UDT_json.exe extracts frags and metadata for a demo to a JSON file.
This module handles invoking the binary and parsing its output.

Usage:
    wrapper = UDTWrapper(cfg)
    demo_info, frags = wrapper.parse(demo_path)

UDT_json.exe command:
    UDT_json.exe -a=frags <demo_path>

Output: creates <demo_path>.json next to the demo, or in a specified output dir.
The JSON has a top-level array. Each element represents one cut point (frag event).
"""
import json
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional

from phase2.config import Config
from phase2.parser.frag_detector import Frag


# UDT JSON output field names (from UberDemoTools documentation)
# These are the keys in each frag entry from UDT_json -a=frags
_UDT_WEAPON_MAP = {
    "Gauntlet": "MOD_GAUNTLET",
    "MachineGun": "MOD_MACHINEGUN",
    "Shotgun": "MOD_SHOTGUN",
    "GrenadeLauncher": "MOD_GRENADE",
    "RocketLauncher": "MOD_ROCKET",
    "LightningGun": "MOD_LIGHTNING",
    "Railgun": "MOD_RAILGUN",
    "PlasmaGun": "MOD_PLASMA",
    "BFG": "MOD_BFG",
    "GrapplingHook": "MOD_GRAPPLE",
    "HeavyMachineGun": "MOD_MACHINEGUN",
    "NailGun": "MOD_MACHINEGUN",
    "ProximityLauncher": "MOD_GRENADE",
    "ChainGun": "MOD_MACHINEGUN",
}


class UDTWrapper:
    """Wraps UDT_json.exe to parse .dm_73 demos."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._check_binary()

    def _check_binary(self):
        if not self.cfg.udt_json_exe.exists():
            raise FileNotFoundError(
                f"UDT_json.exe not found: {self.cfg.udt_json_exe}\n"
                f"Download from: https://udt.playmorepromode.com\n"
                f"Extract to: {self.cfg.udt_json_exe.parent}"
            )

    def parse(self, demo_path: Path) -> Tuple[dict, List[Frag]]:
        """
        Run UDT_json.exe on demo_path, parse the JSON output.

        Returns:
            (demo_info dict, list of Frag objects)

        Raises:
            FileNotFoundError: UDT binary missing
            RuntimeError: UDT returned non-zero or output not found
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            # UDT_json writes <demo_name>.json to the output dir
            cmd = [
                str(self.cfg.udt_json_exe),
                f"-a=frags",
                f"-o={tmp_dir}",
                str(demo_path),
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"UDT_json.exe failed for {demo_path.name}:\n"
                    f"stdout: {result.stdout[:500]}\n"
                    f"stderr: {result.stderr[:500]}"
                )

            # Find the output JSON
            json_files = list(Path(tmp_dir).glob("*.json"))
            if not json_files:
                raise RuntimeError(
                    f"UDT_json.exe produced no JSON for {demo_path.name}"
                )

            raw = json.loads(json_files[0].read_text(encoding="utf-8"))

        return self._parse_udt_json(demo_path.name, raw)

    def _parse_udt_json(
        self, filename: str, raw: dict
    ) -> Tuple[dict, List[Frag]]:
        """Convert UDT JSON output to (demo_info, [Frag]) tuple."""
        # UDT JSON top-level structure varies by version.
        # Typical: {"demoFilePath": ..., "fragEvents": [...]}
        frag_events = raw.get("fragEvents", [])

        frags: List[Frag] = []
        for event in frag_events:
            # UDT uses "serverTimeMs" for the kill timestamp
            server_time = event.get("serverTimeMs", 0)
            # UDT uses "meanOfDeath" string for weapon
            udt_weapon = event.get("meanOfDeath", "unknown")
            weapon = _UDT_WEAPON_MAP.get(udt_weapon, f"MOD_{udt_weapon.upper()}")

            # UDT does not directly expose Z velocity — set to 0 (no airshot from UDT)
            frag = Frag(
                frag_time_ms=server_time,
                killer_slot=event.get("attackerClientIndex", 0),
                victim_slot=event.get("targetClientIndex", 0),
                weapon=weapon,
                victim_z_vel=0.0,   # UDT limitation: no Z vel in frag events
                killer_name=event.get("attackerName", ""),
                victim_name=event.get("targetName", ""),
                demo_filename=filename,
            )
            frags.append(frag)

        # Sort by time, then annotate multi-kills
        frags.sort(key=lambda f: f.frag_time_ms)
        from phase2.parser.frag_detector import group_multikillers
        frags = group_multikillers(frags, self.cfg.multikill_window_ms)

        demo_info = {
            "filename": filename,
            "map_name": raw.get("mapName"),
            "game_type": raw.get("gameType"),
            "duration_ms": raw.get("durationMs"),
            "parser": "UDT",
        }

        return demo_info, frags
```

- [ ] **Step 3: Write integration test for demo_parser**

These tests require the huffman extension to be built. They are marked as integration tests and skipped if the extension is missing.

Create `tests/phase2/test_udt_wrapper.py`:

```python
"""
Tests for the demo parser modules.
Integration tests require: huffman C extension built, real .dm_73 files present.
Unit tests run without any external dependencies.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


# ── Unit tests: no real demo or binary needed ─────────────────────────────────

def test_udt_weapon_map_covers_common_weapons():
    """The UDT weapon name map must cover the weapons we care about."""
    from phase2.parser.udt_wrapper import _UDT_WEAPON_MAP
    assert "Railgun" in _UDT_WEAPON_MAP
    assert "RocketLauncher" in _UDT_WEAPON_MAP
    assert "LightningGun" in _UDT_WEAPON_MAP
    assert _UDT_WEAPON_MAP["Railgun"] == "MOD_RAILGUN"


def test_udt_wrapper_raises_if_binary_missing(cfg, tmp_path):
    """UDTWrapper raises FileNotFoundError if UDT binary not at configured path."""
    from phase2.parser.udt_wrapper import UDTWrapper
    # Temporarily redirect udt_json_exe to a nonexistent path
    cfg.udt_json_exe = tmp_path / "nonexistent" / "UDT_json.exe"
    with pytest.raises(FileNotFoundError, match="UDT_json.exe not found"):
        UDTWrapper(cfg)


def test_parse_udt_json_parses_frag_events(cfg):
    """UDTWrapper._parse_udt_json correctly parses a synthetic UDT JSON structure."""
    from phase2.parser.udt_wrapper import UDTWrapper

    # Mock the binary check so we can test parsing without the binary
    with patch.object(UDTWrapper, "_check_binary"):
        wrapper = UDTWrapper(cfg)

    fake_udt_json = {
        "mapName": "campgrounds",
        "gameType": 0,
        "durationMs": 120000,
        "fragEvents": [
            {
                "serverTimeMs": 30000,
                "meanOfDeath": "Railgun",
                "attackerClientIndex": 1,
                "targetClientIndex": 2,
                "attackerName": "Hunter",
                "targetName": "Ranger",
            },
            {
                "serverTimeMs": 31500,
                "meanOfDeath": "Railgun",
                "attackerClientIndex": 1,
                "targetClientIndex": 3,
                "attackerName": "Hunter",
                "targetName": "Keel",
            },
        ],
    }

    demo_info, frags = wrapper._parse_udt_json("test.dm_73", fake_udt_json)

    assert demo_info["map_name"] == "campgrounds"
    assert demo_info["parser"] == "UDT"
    assert len(frags) == 2
    assert frags[0].weapon == "MOD_RAILGUN"
    assert frags[0].killer_name == "Hunter"
    # Both frags by same killer within 3s = multi-kill
    assert frags[1].is_multikill is True


# ── Integration tests: require real .dm_73 and huffman extension ──────────────

@pytest.mark.integration
def test_demo_parser_parses_real_demo(sample_demo_path, cfg):
    """Parse a real .dm_73 demo and verify basic output structure."""
    pytest.importorskip("qldemo",
        reason="qldemo huffman extension not compiled — run setup.py build_ext --inplace")

    from phase2.parser.demo_parser import parse_demo

    demo_info, frags = parse_demo(sample_demo_path, cfg)

    assert demo_info["filename"] == sample_demo_path.name
    assert demo_info["parser"] == "qldemo-python"
    assert isinstance(demo_info["duration_ms"], int)
    assert demo_info["duration_ms"] > 0
    # Most demos have at least 1 kill
    assert isinstance(frags, list)
    print(f"\n  Demo: {sample_demo_path.name}")
    print(f"  Map: {demo_info['map_name']}")
    print(f"  Duration: {demo_info['duration_ms'] / 1000:.1f}s")
    print(f"  Frags: {len(frags)}")
    if frags:
        f = frags[0]
        print(f"  First frag: {f.weapon} at {f.frag_time_ms}ms "
              f"(airshot={f.is_airshot}, multikill={f.is_multikill})")
```

- [ ] **Step 4: Run unit tests (integration tests require real demo)**

```bash
pytest tests/phase2/test_udt_wrapper.py -v -m "not integration"
```

Expected: 3 unit tests PASS.

Run integration test only if huffman extension is compiled:
```bash
pytest tests/phase2/test_udt_wrapper.py -v -m "integration"
```

- [ ] **Step 5: Commit**

```bash
git add phase2/parser/demo_parser.py phase2/parser/udt_wrapper.py tests/phase2/test_udt_wrapper.py
git commit -m "feat(phase2): add qldemo-python and UDT demo parser drivers"
```

---

## Task 5: Parse Pipeline — Ingest All Demos into Database

**Files:**
- Create: `phase2/parse_pipeline.py`

This is the main orchestrator for demo ingestion. It loops all 948 demos, parses each, writes to the database. Designed to be resumable (skips demos already in DB by filename).

- [ ] **Step 1: Implement parse_pipeline.py**

Create `phase2/parse_pipeline.py`:

```python
"""
Phase 2A: Parse all .dm_73 demos and populate frags.db.

Usage:
    # Parse 10 demos (for Gate P2-1 human review)
    python phase2/parse_pipeline.py --limit 10

    # Parse all demos
    python phase2/parse_pipeline.py --all

    # Parse with UDT fallback if qldemo fails
    python phase2/parse_pipeline.py --all --fallback-udt

Design:
    - Skips demos already in the database (resumable)
    - Logs parse errors to output/phase2_parse_errors.txt (doesn't abort)
    - Prints progress with tqdm
    - Reports summary on completion
"""
import argparse
import sqlite3
import sys
import traceback
from pathlib import Path
from typing import List

from tqdm import tqdm

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from phase2.config import Config
from phase2.database.db import get_connection, insert_demo, insert_frag, count_demos, count_frags
from phase2.database.migrations import init_db


def parse_demo_safe(demo_path: Path, cfg: Config, use_udt_fallback: bool = False):
    """
    Parse a single demo. Returns (demo_info, frags) or raises on failure.
    Tries qldemo-python first; falls back to UDT_json if use_udt_fallback=True.
    """
    try:
        from phase2.parser.demo_parser import parse_demo
        return parse_demo(demo_path, cfg)
    except ImportError:
        if not use_udt_fallback:
            raise
        # qldemo-python unavailable — use UDT
    except RuntimeError:
        if not use_udt_fallback:
            raise

    # Fallback to UDT
    from phase2.parser.udt_wrapper import UDTWrapper
    wrapper = UDTWrapper(cfg)
    return wrapper.parse(demo_path)


def ingest_demo(conn: sqlite3.Connection, demo_path: Path, cfg: Config,
                use_udt_fallback: bool) -> int:
    """
    Parse a demo and write to database. Returns frag count inserted.
    Returns 0 if demo already in DB (skipped).
    """
    from phase2.database.db import get_demo_by_filename
    existing = get_demo_by_filename(conn, demo_path.name)
    if existing:
        return 0   # already parsed — skip

    demo_info, frags = parse_demo_safe(demo_path, cfg, use_udt_fallback)

    demo_id = insert_demo(
        conn,
        filename=demo_info["filename"],
        map_name=demo_info.get("map_name"),
        game_type=demo_info.get("game_type"),
        duration_ms=demo_info.get("duration_ms"),
        parser=demo_info["parser"],
    )

    inserted = 0
    for frag in frags:
        insert_frag(
            conn,
            demo_id=demo_id,
            frag_time_ms=frag.frag_time_ms,
            weapon=frag.weapon,
            is_airshot=frag.is_airshot,
            is_multikill=frag.is_multikill,
            kill_streak=frag.kill_streak,
            distance_units=0.0,    # not computed at parse stage
            victim_z_vel=frag.victim_z_vel,
            pre_roll_ms=cfg.pre_roll_ms,
            post_roll_ms=cfg.post_roll_ms,
        )
        inserted += 1

    return inserted


def run_pipeline(
    demo_paths: List[Path],
    cfg: Config,
    use_udt_fallback: bool = False,
) -> dict:
    """
    Parse all demos in demo_paths, write to database.
    Returns summary dict: {parsed, skipped, errors, total_frags}.
    """
    # Ensure DB is initialized
    init_db(cfg.db_path, cfg.schema_path)
    conn = get_connection(cfg.db_path)

    error_log = ROOT / "output" / "phase2_parse_errors.txt"
    error_log.parent.mkdir(exist_ok=True)

    stats = {"parsed": 0, "skipped": 0, "errors": 0, "total_frags": 0}
    error_lines = []

    for demo_path in tqdm(demo_paths, desc="Parsing demos", unit="demo"):
        try:
            frag_count = ingest_demo(conn, demo_path, cfg, use_udt_fallback)
            if frag_count == 0:
                stats["skipped"] += 1
            else:
                stats["parsed"] += 1
                stats["total_frags"] += frag_count
        except Exception as e:
            stats["errors"] += 1
            error_line = f"{demo_path.name}: {e}"
            error_lines.append(error_line)
            tqdm.write(f"  ERROR: {error_line}")

    conn.close()

    # Write error log
    if error_lines:
        with open(error_log, "w", encoding="utf-8") as f:
            f.write("\n".join(error_lines) + "\n")
        print(f"\nErrors written to: {error_log}")

    # Print summary
    total_in_db = count_frags(get_connection(cfg.db_path))
    print(f"\n{'='*50}")
    print(f"Parse pipeline complete:")
    print(f"  Parsed:       {stats['parsed']} demos")
    print(f"  Skipped:      {stats['skipped']} (already in DB)")
    print(f"  Errors:       {stats['errors']}")
    print(f"  Frags added:  {stats['total_frags']}")
    print(f"  Total in DB:  {total_in_db}")
    print(f"{'='*50}")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Phase 2A: Parse .dm_73 demos into frags.db"
    )
    parser.add_argument("--limit", type=int, default=None,
                        help="Only parse N demos (for Gate P2-1 sample review)")
    parser.add_argument("--all", action="store_true",
                        help="Parse all demos in demos_dir")
    parser.add_argument("--fallback-udt", action="store_true",
                        help="Fall back to UDT_json.exe when qldemo-python fails")
    args = parser.parse_args()

    cfg = Config()
    demo_paths = cfg.demo_list()

    if not demo_paths:
        print(f"No .dm_73 files found in: {cfg.demos_dir}")
        sys.exit(1)

    if args.limit:
        demo_paths = demo_paths[:args.limit]
        print(f"Limiting to {args.limit} demos (Gate P2-1 sample mode)")
    elif not args.all:
        print("Specify --limit N or --all")
        parser.print_help()
        sys.exit(0)

    print(f"Demos to parse: {len(demo_paths)}")
    print(f"Database: {cfg.db_path}")
    print(f"Parser: qldemo-python" + (" + UDT fallback" if args.fallback_udt else ""))
    print()

    run_pipeline(demo_paths, cfg, use_udt_fallback=args.fallback_udt)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run Gate P2-1 — parse 10 sample demos**

```bash
python phase2/parse_pipeline.py --limit 10
```

Expected output (approximate):
```
Demos to parse: 10
Database: G:\QUAKE_LEGACY\database\frags.db
Parser: qldemo-python
Parsing demos: 100%|████████████| 10/10 [00:05<00:00]
Parse pipeline complete:
  Parsed:       10 demos
  Skipped:      0 (already in DB)
  Errors:       0
  Frags added:  ~400-800 (depends on demos)
  Total in DB:  ~400-800
```

**⚠ HUMAN REVIEW GATE P2-1:** Before running the full parse, review the sample output:

```bash
# Quick DB inspection — see what was found
python -c "
import sqlite3
conn = sqlite3.connect('database/frags.db')
conn.row_factory = sqlite3.Row
print('Demos:')
for row in conn.execute('SELECT filename, map_name, duration_ms FROM demos LIMIT 10'):
    print(f'  {row[\"filename\"]} | map={row[\"map_name\"]} | dur={row[\"duration_ms\"]}ms')
print()
print('Sample frags:')
for row in conn.execute('SELECT f.frag_time_ms, f.weapon, f.is_airshot, f.kill_streak, d.filename FROM frags f JOIN demos d ON f.demo_id = d.id LIMIT 10'):
    print(f'  {row[\"filename\"]} | t={row[\"frag_time_ms\"]}ms | {row[\"weapon\"]} | air={row[\"is_airshot\"]} | streak={row[\"kill_streak\"]}')
print()
print(f'Total demos: {conn.execute(\"SELECT COUNT(*) FROM demos\").fetchone()[0]}')
print(f'Total frags: {conn.execute(\"SELECT COUNT(*) FROM frags\").fetchone()[0]}')
"
```

Check: do frags have reasonable timestamps? Are map names correct? Are weapons recognizable? Are kill streaks plausible (1-5 typically)?

If output looks good, proceed to full parse. If something is wrong (all 0 frags, garbled maps), debug before continuing.

- [ ] **Step 3: Run full parse (after Gate P2-1 approval)**

```bash
python phase2/parse_pipeline.py --all
```

This processes all 948 demos. Estimated time: 10-30 minutes depending on machine speed.

- [ ] **Step 4: Commit**

```bash
git add phase2/parse_pipeline.py
git commit -m "feat(phase2): add demo ingestion pipeline with resume and error logging"
```

---

## Task 6: Human Review Dashboard — Streamlit App

**Files:**
- Create: `phase2/review/dashboard.py`

- [ ] **Step 1: Write failing test (smoke test — just imports)**

Add to `tests/phase2/test_db.py` (at the bottom):

```python
def test_dashboard_importable():
    """Dashboard must be importable without running Streamlit."""
    import importlib
    # Should not raise
    spec = importlib.util.find_spec("phase2.review.dashboard")
    assert spec is not None
```

- [ ] **Step 2: Implement dashboard.py**

Create `phase2/review/dashboard.py`:

```python
"""
Phase 2 Human Review Dashboard — Streamlit app.

Launch with:
    streamlit run phase2/review/dashboard.py

Features:
    - Browse unreviewed frags (filterable by weapon, airshot, multikill)
    - View frag metadata (map, time, weapon, streak, distance)
    - See demo filename and WolfcamQL seekclock for manual preview
    - Approve (tier 1/2/3) or Reject with notes
    - Bulk approve by filter (e.g. "all rail air shots")
    - Progress bar: reviewed / total
"""
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from phase2.config import Config, ms_to_clock
from phase2.database.db import (
    get_connection, get_frags_for_review, get_approved_frags,
    mark_frag_approved, mark_frag_rejected, count_frags,
)

cfg = Config()


def get_conn():
    """Get a cached database connection (one per Streamlit session)."""
    if "conn" not in st.session_state:
        st.session_state.conn = get_connection(cfg.db_path)
    return st.session_state.conn


def render_frag_card(frag: dict, conn) -> None:
    """Render a single frag as a Streamlit card with approve/reject controls."""
    frag_id = frag["id"]

    # Compute seekclock for WolfcamQL manual preview
    start_ms = max(0, frag["frag_time_ms"] - frag.get("pre_roll_ms", 5000))
    end_ms = frag["frag_time_ms"] + frag.get("post_roll_ms", 2000)
    seekclock = ms_to_clock(start_ms)

    # Tags
    tags = []
    if frag.get("is_airshot"):
        tags.append("AIR SHOT")
    if frag.get("is_multikill"):
        tags.append(f"MULTI-KILL (x{frag.get('kill_streak', 1)})")
    tag_str = "  |  ".join(tags) if tags else "standard frag"

    with st.container():
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"### Frag #{frag_id}")
            st.markdown(f"**Map:** `{frag.get('map_name', 'unknown')}`")
            st.markdown(f"**Demo:** `{frag.get('filename', '')}`")
            st.markdown(f"**Weapon:** `{frag.get('weapon', '?')}`")
            st.markdown(f"**Tags:** {tag_str}")
            st.markdown(f"**Kill streak:** {frag.get('kill_streak', 1)}")
            st.markdown(
                f"**Frag time:** {ms_to_clock(frag['frag_time_ms'])} "
                f"({frag['frag_time_ms']}ms)"
            )
            st.markdown(f"**Victim Z vel:** {frag.get('victim_z_vel', 0):.1f} units/s")
            st.markdown(f"**Clip window:** `seekclock {seekclock}` → `at {ms_to_clock(end_ms)} quit`")
            st.code(
                f"seekclock {seekclock}\n"
                f"video avi name frag_{frag_id:04d}\n"
                f"at {ms_to_clock(end_ms)} quit",
                language="cfg",
            )

        with col2:
            st.markdown("**Rate this frag:**")
            tier = st.selectbox(
                "Tier", [1, 2, 3],
                index=1,
                key=f"tier_{frag_id}",
                help="1=best, 2=good, 3=ok",
            )
            notes = st.text_input(
                "Notes (optional)", key=f"notes_{frag_id}", value=""
            )

            if st.button("APPROVE", key=f"approve_{frag_id}", type="primary"):
                mark_frag_approved(conn, frag_id, tier=tier, notes=notes)
                st.success(f"Frag {frag_id} approved (tier {tier})")
                st.rerun()

            if st.button("REJECT", key=f"reject_{frag_id}"):
                mark_frag_rejected(conn, frag_id, notes=notes)
                st.warning(f"Frag {frag_id} rejected")
                st.rerun()

        st.divider()


def main():
    st.set_page_config(
        page_title="QUAKE LEGACY — Frag Review",
        page_icon=":fire:",
        layout="wide",
    )

    st.title("QUAKE LEGACY — Phase 2 Frag Review Dashboard")

    conn = get_conn()

    # ── Sidebar: filters and stats ────────────────────────────────────────────
    with st.sidebar:
        st.header("Filters")

        weapon_filter = st.selectbox(
            "Weapon",
            ["All", "MOD_RAILGUN", "MOD_ROCKET", "MOD_ROCKET_SPLASH",
             "MOD_LIGHTNING", "MOD_PLASMA", "MOD_GAUNTLET"],
        )
        airshot_only = st.checkbox("Air shots only")
        multikill_only = st.checkbox("Multi-kills only")
        page_size = st.slider("Frags per page", 5, 50, 20)

        st.divider()
        st.header("Database Stats")
        total = count_frags(conn)
        reviewed = count_frags(conn, reviewed_only=True)
        approved = count_frags(conn, approved_only=True)

        st.metric("Total frags", total)
        st.metric("Reviewed", reviewed)
        st.metric("Approved", approved)
        st.metric("Remaining", total - reviewed)

        if total > 0:
            pct = reviewed / total * 100
            st.progress(pct / 100, text=f"{pct:.1f}% reviewed")

        st.divider()

        # Bulk approve
        st.header("Bulk Actions")
        if st.button("Approve all current filters (tier 2)"):
            frags = get_frags_for_review(
                conn,
                limit=9999,
                weapon_filter=weapon_filter if weapon_filter != "All" else None,
                airshot_only=airshot_only,
                multikill_only=multikill_only,
            )
            for f in frags:
                mark_frag_approved(conn, f["id"], tier=2, notes="bulk approved")
            st.success(f"Bulk approved {len(frags)} frags")
            st.rerun()

    # ── Main: frag cards ──────────────────────────────────────────────────────
    frags = get_frags_for_review(
        conn,
        limit=page_size,
        weapon_filter=weapon_filter if weapon_filter != "All" else None,
        airshot_only=airshot_only,
        multikill_only=multikill_only,
    )

    if not frags:
        st.success("No unreviewed frags match current filters.")
        st.info("All done! Proceed to Task 7 (batch renderer).")
    else:
        st.subheader(f"Showing {len(frags)} unreviewed frags")
        for frag in frags:
            render_frag_card(frag, conn)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Launch dashboard**

```bash
streamlit run phase2/review/dashboard.py
```

Expected: browser opens at `http://localhost:8501` showing frag review UI.

**⚠ HUMAN REVIEW GATE P2-2:** Use the dashboard to rate and approve frags.

Minimum required before proceeding to batch render:
- At least 10 frags approved (more is better)
- Prioritize: airshot railguns (tier 1), multi-kills (tier 1-2), rockets (tier 2)
- Reject: suicide kills, machinegun/gauntlet unless exceptional
- Add notes for any frags you want to remember ("clean 180 air rail", "perfect quad")

When you have at least 10 approved frags, proceed to Task 7.

- [ ] **Step 4: Commit**

```bash
git add phase2/review/dashboard.py
git commit -m "feat(phase2): add Streamlit frag review dashboard with approve/reject and bulk actions"
```

---

## Task 7: Batch Renderer — WolfcamQL Automation

**Files:**
- Create: `phase2/renderer/cap_cfg.py`
- Create: `phase2/renderer/batch_renderer.py`
- Create: `tests/phase2/test_batch_renderer.py`

- [ ] **Step 1: Write failing test**

Create `tests/phase2/test_batch_renderer.py`:

```python
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from phase2.renderer.cap_cfg import generate_cap_cfg, CAP_CFG_CONTENT
from phase2.renderer.batch_renderer import (
    build_gamestart_cfg, FragRenderJob, render_frag,
)
from phase2.config import ms_to_clock


def test_ms_to_clock_basic():
    assert ms_to_clock(0) == "0:00"
    assert ms_to_clock(60000) == "1:00"
    assert ms_to_clock(65000) == "1:05"
    assert ms_to_clock(90500) == "1:30"


def test_ms_to_clock_large():
    assert ms_to_clock(3661000) == "61:01"


def test_build_gamestart_cfg_format():
    """gamestart.cfg must have seekclock, video avi, and at T quit."""
    cfg_content = build_gamestart_cfg(
        frag_time_ms=30000,
        clip_name="frag_0042",
        pre_roll_ms=5000,
        post_roll_ms=2000,
    )
    # start = 30000 - 5000 = 25000ms = 0:25
    assert "seekclock 0:25" in cfg_content
    # end = 30000 + 2000 = 32000ms = 0:32
    assert "at 0:32 quit" in cfg_content
    assert "video avi name frag_0042" in cfg_content


def test_build_gamestart_cfg_no_negative_start():
    """Start time must not go below 0 even if pre_roll > frag_time."""
    cfg_content = build_gamestart_cfg(
        frag_time_ms=2000,
        clip_name="early_frag",
        pre_roll_ms=5000,
        post_roll_ms=2000,
    )
    assert "seekclock 0:00" in cfg_content


def test_generate_cap_cfg_contains_required_cvars():
    content = generate_cap_cfg()
    assert "cl_aviFrameRate 60" in content
    assert "r_customWidth 1920" in content
    assert "r_customHeight 1080" in content
    assert "cg_draw2d 0" in content


def test_frag_render_job_construction():
    job = FragRenderJob(
        frag_id=42,
        demo_filename="Demo (100).dm_73",
        frag_time_ms=45000,
        pre_roll_ms=5000,
        post_roll_ms=2000,
    )
    assert job.clip_name == "frag_0042"
    assert job.frag_id == 42


def test_render_frag_writes_cfg_files(cfg, tmp_path):
    """render_frag writes gamestart.cfg and cap.cfg to wolfcam_home before launch."""
    job = FragRenderJob(
        frag_id=1,
        demo_filename="Demo (1).dm_73",
        frag_time_ms=30000,
        pre_roll_ms=5000,
        post_roll_ms=2000,
    )

    # Override paths to tmp_path
    cfg.wolfcamql_home = tmp_path
    cfg.wolfcamql_exe = tmp_path / "wolfcamql.exe"
    cfg.clips_output_dir = tmp_path / "clips"

    # Create a dummy wolfcamql.exe so existence check passes
    cfg.wolfcamql_exe.write_text("fake exe")
    cfg.clips_output_dir.mkdir()

    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process

        render_frag(job, cfg, timeout_seconds=5)

    # Verify cfg files were written
    gamestart = tmp_path / "gamestart.cfg"
    cap = tmp_path / "cap.cfg"
    assert gamestart.exists(), "gamestart.cfg must be written to wolfcam_home"
    assert cap.exists(), "cap.cfg must be written to wolfcam_home"
    assert "seekclock" in gamestart.read_text()
    assert "cl_aviFrameRate" in cap.read_text()

    # Verify wolfcamql was launched
    assert mock_popen.called
    launch_args = mock_popen.call_args[0][0]
    assert "+demo" in launch_args
    assert "Demo (1).dm_73" in launch_args
```

- [ ] **Step 2: Run failing test**

```bash
pytest tests/phase2/test_batch_renderer.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement cap_cfg.py**

Create `phase2/renderer/cap_cfg.py`:

```python
"""
Generate cap.cfg — WolfcamQL recording configuration.

cap.cfg is placed in wolfcam-ql/ (wolfcam_home) before each render.
It sets the recording parameters for the AVI output.
"""

CAP_CFG_CONTENT = """\
// QUAKE LEGACY — Phase 2 recording config
// Auto-generated by cap_cfg.py — do not edit manually

r_fullscreen 0
cl_aviFrameRate 60
cl_aviCodec uncompressed
cl_aviAllowLargeFiles 1
cg_draw2d 0
r_useFbo 1
r_customWidth 1920
r_customHeight 1080
s_useopenal 0
s_sdlWindowsForceDirectSound 1
mme_blurFrames 4
com_timescalesafe 1
"""


def generate_cap_cfg() -> str:
    """Return the cap.cfg content string."""
    return CAP_CFG_CONTENT


def write_cap_cfg(wolfcam_home: "Path") -> "Path":
    """Write cap.cfg to wolfcam_home directory. Returns path to written file."""
    from pathlib import Path
    out = Path(wolfcam_home) / "cap.cfg"
    out.write_text(CAP_CFG_CONTENT, encoding="utf-8")
    return out
```

- [ ] **Step 4: Implement batch_renderer.py**

Create `phase2/renderer/batch_renderer.py`:

```python
"""
Phase 2B: WolfcamQL batch renderer.

For each approved frag in the database:
  1. Write gamestart.cfg to wolfcam_home (seekclock, video, quit)
  2. Write cap.cfg to wolfcam_home (recording settings)
  3. Launch wolfcamql.exe +demo <demo> +exec cap.cfg
  4. Poll process exit (timeout_seconds)
  5. Move rendered AVI to clips_output_dir
  6. Insert rendered_clips record into database

Usage:
    # Render first 10 approved frags (Gate P2-3 sample)
    python phase2/renderer/batch_renderer.py --limit 10

    # Render all approved frags
    python phase2/renderer/batch_renderer.py --all
"""
import subprocess
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from tqdm import tqdm

from phase2.config import Config, ms_to_clock
from phase2.renderer.cap_cfg import write_cap_cfg


@dataclass
class FragRenderJob:
    """All data needed to render a single frag clip."""
    frag_id: int
    demo_filename: str
    frag_time_ms: int
    pre_roll_ms: int
    post_roll_ms: int

    @property
    def clip_name(self) -> str:
        """AVI clip filename stem (no extension)."""
        return f"frag_{self.frag_id:04d}"


def build_gamestart_cfg(
    frag_time_ms: int,
    clip_name: str,
    pre_roll_ms: int,
    post_roll_ms: int,
) -> str:
    """
    Generate gamestart.cfg content for a single frag clip.

    WolfcamQL executes this config when the demo starts playback.
    It seeks to the start time, begins AVI capture, then quits at end time.
    """
    start_ms = max(0, frag_time_ms - pre_roll_ms)
    end_ms = frag_time_ms + post_roll_ms

    return (
        f"// QUAKE LEGACY — auto-generated per-frag recording config\n"
        f"seekclock {ms_to_clock(start_ms)}\n"
        f"video avi name {clip_name}\n"
        f"at {ms_to_clock(end_ms)} quit\n"
    )


def render_frag(
    job: FragRenderJob,
    cfg: Config,
    timeout_seconds: int = 120,
) -> Optional[Path]:
    """
    Render a single frag clip with WolfcamQL.

    Writes gamestart.cfg and cap.cfg to wolfcam_home, then launches wolfcamql.exe.
    Polls until process exits or timeout_seconds exceeded.

    Returns path to rendered AVI, or None if render failed/timed out.

    Raises:
        FileNotFoundError: wolfcamql.exe not found at cfg.wolfcamql_exe
    """
    if not cfg.wolfcamql_exe.exists():
        raise FileNotFoundError(
            f"wolfcamql.exe not found: {cfg.wolfcamql_exe}\n"
            f"Expected at: {cfg.wolfcamql_exe}"
        )

    demo_path = cfg.demos_dir / job.demo_filename
    if not demo_path.exists():
        raise FileNotFoundError(f"Demo not found: {demo_path}")

    # Write recording configs to wolfcam_home
    gamestart_content = build_gamestart_cfg(
        frag_time_ms=job.frag_time_ms,
        clip_name=job.clip_name,
        pre_roll_ms=job.pre_roll_ms,
        post_roll_ms=job.post_roll_ms,
    )
    gamestart_path = cfg.wolfcamql_home / "gamestart.cfg"
    gamestart_path.write_text(gamestart_content, encoding="utf-8")
    write_cap_cfg(cfg.wolfcamql_home)

    # WolfcamQL renders AVI to wolfcam_home/videos/ by default
    videos_dir = cfg.wolfcamql_home / "videos"
    videos_dir.mkdir(exist_ok=True)
    expected_avi = videos_dir / f"{job.clip_name}.avi"

    # Launch WolfcamQL
    # +set fs_homepath: where wolfcamql writes files (must be wolfcam_home)
    # +exec cap.cfg: load recording settings on startup
    # +demo: play this demo immediately
    cmd = [
        str(cfg.wolfcamql_exe),
        "+set", "fs_homepath", str(cfg.wolfcamql_home),
        "+exec", "cap.cfg",
        "+demo", str(demo_path),
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Poll for process exit
    start_time = time.monotonic()
    while process.poll() is None:
        elapsed = time.monotonic() - start_time
        if elapsed > timeout_seconds:
            process.kill()
            print(f"  TIMEOUT: frag {job.frag_id} exceeded {timeout_seconds}s")
            return None
        time.sleep(0.5)

    # Check for AVI output
    if not expected_avi.exists():
        # WolfcamQL may write to a different location — search for it
        avi_candidates = list(videos_dir.glob(f"{job.clip_name}*.avi"))
        if avi_candidates:
            expected_avi = avi_candidates[0]
        else:
            print(f"  WARNING: No AVI found for frag {job.frag_id}")
            return None

    # Move AVI to clips_output_dir
    dest = cfg.clips_output_dir / expected_avi.name
    expected_avi.rename(dest)
    return dest


def get_render_jobs(conn: sqlite3.Connection, limit: Optional[int] = None) -> List[FragRenderJob]:
    """
    Query approved, unrendered frags from the database and build render jobs.
    """
    sql = """
        SELECT f.id, d.filename, f.frag_time_ms, f.pre_roll_ms, f.post_roll_ms
        FROM frags f
        JOIN demos d ON f.demo_id = d.id
        WHERE f.approved = 1
          AND f.id NOT IN (SELECT frag_id FROM rendered_clips)
        ORDER BY f.tier ASC, f.kill_streak DESC
    """
    if limit:
        sql += f" LIMIT {limit}"

    rows = conn.execute(sql).fetchall()
    return [
        FragRenderJob(
            frag_id=row[0],
            demo_filename=row[1],
            frag_time_ms=row[2],
            pre_roll_ms=row[3],
            post_roll_ms=row[4],
        )
        for row in rows
    ]


def record_rendered_clip(
    conn: sqlite3.Connection,
    frag_id: int,
    avi_path: Path,
    wolfcamql_cfg: str,
) -> None:
    """Insert a rendered_clips record into the database."""
    size_mb = avi_path.stat().st_size / 1024 / 1024 if avi_path.exists() else 0
    conn.execute(
        """INSERT INTO rendered_clips (frag_id, avi_path, camera_type, wolfcamql_cfg, file_size_mb)
           VALUES (?, ?, ?, ?, ?)""",
        (frag_id, str(avi_path), "firstperson", wolfcamql_cfg, size_mb),
    )
    conn.commit()


def run_batch(
    jobs: List[FragRenderJob],
    cfg: Config,
    conn: sqlite3.Connection,
    timeout_seconds: int = 120,
) -> dict:
    """
    Render all jobs sequentially. WolfcamQL is not parallelizable (single GPU).
    Returns stats dict: {rendered, failed, skipped}.
    """
    stats = {"rendered": 0, "failed": 0}

    for job in tqdm(jobs, desc="Rendering frags", unit="frag"):
        gamestart_cfg = build_gamestart_cfg(
            job.frag_time_ms, job.clip_name, job.pre_roll_ms, job.post_roll_ms
        )
        try:
            avi_path = render_frag(job, cfg, timeout_seconds=timeout_seconds)
            if avi_path:
                record_rendered_clip(conn, job.frag_id, avi_path, gamestart_cfg)
                stats["rendered"] += 1
                tqdm.write(f"  Rendered: {avi_path.name} ({avi_path.stat().st_size / 1024:.0f}KB)")
            else:
                stats["failed"] += 1
                tqdm.write(f"  FAILED: frag {job.frag_id}")
        except Exception as e:
            stats["failed"] += 1
            tqdm.write(f"  ERROR frag {job.frag_id}: {e}")

    print(f"\nBatch render complete:")
    print(f"  Rendered: {stats['rendered']}")
    print(f"  Failed:   {stats['failed']}")
    return stats


def main():
    import argparse
    import sys
    from phase2.database.db import get_connection
    from phase2.database.migrations import init_db

    parser = argparse.ArgumentParser(description="Phase 2B: WolfcamQL batch renderer")
    parser.add_argument("--limit", type=int, default=None,
                        help="Render only N frags (Gate P2-3 sample: use 10)")
    parser.add_argument("--all", action="store_true",
                        help="Render all approved unrendered frags")
    parser.add_argument("--timeout", type=int, default=120,
                        help="Per-frag timeout in seconds (default: 120)")
    args = parser.parse_args()

    cfg = Config()
    init_db(cfg.db_path, cfg.schema_path)
    conn = get_connection(cfg.db_path)

    jobs = get_render_jobs(conn, limit=args.limit if not args.all else None)
    if not jobs:
        print("No approved unrendered frags found.")
        print("Run dashboard (Task 6) and approve frags first.")
        sys.exit(0)

    print(f"Frags to render: {len(jobs)}")
    print(f"Output dir: {cfg.clips_output_dir}")
    print(f"WolfcamQL: {cfg.wolfcamql_exe}")
    print()

    if not args.limit and not args.all:
        print("Specify --limit N (Gate P2-3 sample) or --all")
        parser.print_help()
        sys.exit(0)

    run_batch(jobs, cfg, conn, timeout_seconds=args.timeout)
    conn.close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/phase2/test_batch_renderer.py -v
```

Expected: all 7 tests PASS.

- [ ] **Step 6: Gate P2-3 — Render 10 sample clips**

**⚠ HUMAN REVIEW GATE P2-3:**

First, render 10 clips:
```bash
python phase2/renderer/batch_renderer.py --limit 10
```

Expected: 10 AVI files in `G:\QUAKE_LEGACY\output\phase2_clips\`.

Watch each clip in your video player. Check:
- Clip starts ~5 seconds before the kill
- Clip ends ~2 seconds after the kill
- Camera is first-person (wolfcam default)
- Resolution is 1920x1080
- Frame rate is 60fps
- No garbled video or audio

If timing is wrong (off by seconds): adjust `pre_roll_ms` / `post_roll_ms` in `config.py`.
If resolution is wrong: check `cap.cfg` cvars.
If clips are empty (0 bytes): WolfcamQL may not be finding the demo — verify `demos_dir` path.

After approving the 10 sample clips, run full batch:
```bash
python phase2/renderer/batch_renderer.py --all
```

- [ ] **Step 7: Commit**

```bash
git add phase2/renderer/cap_cfg.py phase2/renderer/batch_renderer.py tests/phase2/test_batch_renderer.py
git commit -m "feat(phase2): add WolfcamQL batch renderer with gamestart.cfg automation"
```

---

## Task 8: Environment Verifier

**Files:**
- Create: `phase2/verify_env.py`

- [ ] **Step 1: Implement verify_env.py**

Create `phase2/verify_env.py`:

```python
"""
Phase 2 environment pre-flight check.
Run before starting any Phase 2 work to catch missing tools early.

Usage:
    python phase2/verify_env.py
"""
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent


def check(label: str, ok: bool, fix: str = "") -> bool:
    status = "OK" if ok else "FAIL"
    print(f"  [{status}] {label}")
    if not ok and fix:
        print(f"         FIX: {fix}")
    return ok


def main():
    print("QUAKE LEGACY — Phase 2 Environment Check\n")
    all_ok = True

    from phase2.config import Config
    cfg = Config()

    # Python version
    all_ok &= check(
        f"Python 3.11+ (current: {sys.version.split()[0]})",
        sys.version_info >= (3, 11),
        "Install Python 3.11+ from python.org",
    )

    # Demo directory
    demo_count = len(list(cfg.demos_dir.glob("*.dm_73")))
    all_ok &= check(
        f"Demos directory ({demo_count} .dm_73 files found)",
        demo_count > 0,
        f"Expected demos at: {cfg.demos_dir}",
    )

    # WolfcamQL
    all_ok &= check(
        f"WolfcamQL exe: {cfg.wolfcamql_exe}",
        cfg.wolfcamql_exe.exists(),
        f"WolfcamQL not found at: {cfg.wolfcamql_exe}",
    )

    # UDT_json
    all_ok &= check(
        f"UDT_json.exe: {cfg.udt_json_exe}",
        cfg.udt_json_exe.exists(),
        "Download from https://udt.playmorepromode.com and extract to tools/uberdemotools/",
    )

    # qldemo-python huffman extension
    try:
        qldemo_dir = str(cfg.qldemo_python_dir)
        if qldemo_dir not in sys.path:
            sys.path.insert(0, qldemo_dir)
        import huffman
        all_ok &= check("qldemo-python huffman extension", True)
    except ImportError:
        all_ok &= check(
            "qldemo-python huffman extension",
            False,
            f"cd {cfg.qldemo_python_dir} && python setup.py build_ext --inplace",
        )

    # Streamlit
    try:
        import streamlit
        all_ok &= check(f"Streamlit {streamlit.__version__}", True)
    except ImportError:
        all_ok &= check("Streamlit", False, "pip install streamlit")

    # tqdm
    try:
        import tqdm
        all_ok &= check("tqdm", True)
    except ImportError:
        all_ok &= check("tqdm", False, "pip install tqdm")

    # Database schema
    all_ok &= check(
        f"Schema SQL: {cfg.schema_path}",
        cfg.schema_path.exists(),
        f"Expected at: {cfg.schema_path}",
    )

    # Database (may not exist yet — just check parent dir)
    all_ok &= check(
        f"Database dir writable: {cfg.db_path.parent}",
        cfg.db_path.parent.exists(),
        f"Create directory: {cfg.db_path.parent}",
    )

    # Output dir
    all_ok &= check(
        f"Clips output dir: {cfg.clips_output_dir}",
        True,  # created by Config.__init__
    )

    print()
    if all_ok:
        print("All checks passed. Phase 2 ready.")
    else:
        print("Fix issues above before running Phase 2.")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run verifier**

```bash
python phase2/verify_env.py
```

Fix any failures before continuing.

- [ ] **Step 3: Commit**

```bash
git add phase2/verify_env.py
git commit -m "feat(phase2): add environment verifier for Phase 2 pre-flight checks"
```

---

## Task 9: WolfWhisperer Reverse Engineering Notes

**Files:**
- Create: `phase2/re/README.md`

- [ ] **Step 1: Create RE documentation**

Create `phase2/re/README.md`:

```markdown
# WolfWhisperer.exe — Reverse Engineering Notes

**Binary:** `G:\QUAKE_LEGACY\WOLF WHISPERER\WolfWhisperer.exe`
**Size:** 839KB
**Tool:** Ghidra (NSA, free — https://github.com/NationalSecurityAgency/ghidra)
**Ghidra install:** `G:\QUAKE_LEGACY\tools\ghidra\`

## Purpose

WolfWhisperer.exe is a GUI wrapper around wolfcamql.exe. It provides:
- Demo list browser
- FragForward button (sends `fragforward 8 5` console command to wolfcamql)
- options.ini state persistence

## Ghidra Analysis Setup

1. Launch Ghidra: `G:\QUAKE_LEGACY\tools\ghidra\ghidraRun.bat`
2. New project: `G:\QUAKE_LEGACY\WOLF WHISPERER\WolfWhisperer_RE\`
3. Import binary: File → Import File → `WolfWhisperer.exe`
4. Auto-analyze: accept all defaults, run analysis (~2 minutes for 839KB)

## Key Findings (fill in after Ghidra analysis)

### FragForward IPC Signal

- **wolfcamql console command:** `fragforward 8 5`
  - This is confirmed in wolfcamql source: `code/cgame/cg_event.c`
  - Parameters: `fragforward <seconds_ahead> <speed_multiplier>`
  - WolfWhisperer simply sends this string to the wolfcamql process stdin/IPC

- **WolfWhisperer IPC method:** [FILL IN — likely named pipe or stdin]
- **Named pipe name (if any):** [FILL IN from Ghidra strings view]

### options.ini Keys

File location: next to WolfWhisperer.exe or in AppData.
Keys observed: [FILL IN from Ghidra string extraction or live observation]

Example expected keys:
```ini
[WolfcamQL]
Path=C:\path\to\wolfcamql.exe
DemoDir=C:\path\to\demos

[Recording]
Width=1920
Height=1080
FPS=60
```

### Ghidra Analysis Steps

1. **String extraction:** Window → Defined Strings → search for "fragforward", "options.ini", "wolfcamql"
2. **Import table:** Window → Symbol Table → filter Imports → look for CreateProcess, CreateNamedPipe, WriteFile
3. **Main window proc:** Find WinMain or WndProc by looking at CreateWindowEx calls
4. **Button handler:** Find the FragForward button's WM_COMMAND handler

### fragforward in wolfcamql Source

Source: `G:\QUAKE_LEGACY\tools\quake-source\wolfcamql-src\code\cgame\`

From `cl_main.c` line 2078:
```c
if (((di.protocol == PROTOCOL_QL || di.protocol == 73 || di.protocol == 90)
     && event == EV_OBITUARY) ...
```

The `fragforward` console command in cgame scans forward in the demo stream
looking for the next EV_OBITUARY event, then seeks to N seconds before it.

### Conclusion for Phase 2

WolfWhisperer is not needed for Phase 2. Phase 2 directly writes `gamestart.cfg`
and launches wolfcamql.exe with `+demo` command-line argument, bypassing
WolfWhisperer entirely. WolfWhisperer is only useful for interactive manual
demo browsing and manual clip capture.

For Phase 3 (AI Cinematography), understanding WolfWhisperer's IPC may be
useful if we want to control wolfcamql interactively (e.g., for live camera
path preview). Document IPC findings here as they are discovered.
```

- [ ] **Step 2: Commit**

```bash
git add phase2/re/README.md
git commit -m "docs(phase2): add WolfWhisperer RE analysis notes and Ghidra setup guide"
```

---

## Task 10: Full Test Suite Run and Final Commit

- [ ] **Step 1: Run all Phase 2 tests**

```bash
pytest tests/phase2/ -v -m "not integration"
```

Expected output (approximate):
```
tests/phase2/test_config.py::test_config_demos_dir_exists PASSED
tests/phase2/test_config.py::test_config_demo_count PASSED
tests/phase2/test_config.py::test_config_wolfcamql_exe_exists PASSED
tests/phase2/test_config.py::test_config_db_path_is_absolute PASSED
tests/phase2/test_config.py::test_config_udt_json_path PASSED
tests/phase2/test_config.py::test_ms_to_clock PASSED
tests/phase2/test_db.py::test_insert_demo_returns_id PASSED
tests/phase2/test_db.py::test_insert_demo_duplicate_returns_existing_id PASSED
tests/phase2/test_db.py::test_insert_frag_returns_id PASSED
tests/phase2/test_db.py::test_get_frags_for_review_returns_unapproved PASSED
tests/phase2/test_db.py::test_mark_frag_approved PASSED
tests/phase2/test_db.py::test_mark_frag_rejected PASSED
tests/phase2/test_db.py::test_count_frags PASSED
tests/phase2/test_frag_detector.py::test_is_obituary_basic PASSED
tests/phase2/test_frag_detector.py::test_is_obituary_with_event_bits PASSED
tests/phase2/test_frag_detector.py::test_is_obituary_false_for_other_events PASSED
tests/phase2/test_frag_detector.py::test_extract_frag_from_entity_basic PASSED
tests/phase2/test_frag_detector.py::test_detect_airshot_true_when_z_high PASSED
tests/phase2/test_frag_detector.py::test_detect_airshot_false_when_z_low PASSED
tests/phase2/test_frag_detector.py::test_detect_airshot_false_when_z_negative PASSED
tests/phase2/test_frag_detector.py::test_group_multikillers_detects_multikill PASSED
tests/phase2/test_frag_detector.py::test_group_multikillers_streak_count PASSED
tests/phase2/test_frag_detector.py::test_group_multikillers_resets_after_window PASSED
tests/phase2/test_udt_wrapper.py::test_udt_weapon_map_covers_common_weapons PASSED
tests/phase2/test_udt_wrapper.py::test_udt_wrapper_raises_if_binary_missing PASSED
tests/phase2/test_udt_wrapper.py::test_parse_udt_json_parses_frag_events PASSED
tests/phase2/test_batch_renderer.py::test_ms_to_clock_basic PASSED
tests/phase2/test_batch_renderer.py::test_ms_to_clock_large PASSED
tests/phase2/test_batch_renderer.py::test_build_gamestart_cfg_format PASSED
tests/phase2/test_batch_renderer.py::test_build_gamestart_cfg_no_negative_start PASSED
tests/phase2/test_batch_renderer.py::test_generate_cap_cfg_contains_required_cvars PASSED
tests/phase2/test_batch_renderer.py::test_frag_render_job_construction PASSED
tests/phase2/test_batch_renderer.py::test_render_frag_writes_cfg_files PASSED
============================= 33 passed in Xs =============================
```

- [ ] **Step 2: Final commit**

```bash
git add phase2/ tests/phase2/ docs/
git commit -m "feat(phase2): complete Demo Intelligence Engine — parser, DB, dashboard, renderer"
```

---

## Quick Reference Commands

```bash
# Environment check
python phase2/verify_env.py

# Initialize database
python phase2/database/migrations.py

# Gate P2-1: Parse 10 sample demos for review
python phase2/parse_pipeline.py --limit 10

# Inspect DB after sample parse
python -c "
import sqlite3
conn = sqlite3.connect('database/frags.db')
conn.row_factory = sqlite3.Row
for row in conn.execute('SELECT f.weapon, f.is_airshot, f.kill_streak, d.map_name FROM frags f JOIN demos d ON f.demo_id=d.id LIMIT 20'):
    print(dict(row))
"

# Parse all demos (after Gate P2-1 approval)
python phase2/parse_pipeline.py --all

# Parse with UDT fallback (if qldemo-python fails on some demos)
python phase2/parse_pipeline.py --all --fallback-udt

# Gate P2-2: Open review dashboard
streamlit run phase2/review/dashboard.py

# Gate P2-3: Render 10 sample clips
python phase2/renderer/batch_renderer.py --limit 10

# Render all approved frags (after Gate P2-3 approval)
python phase2/renderer/batch_renderer.py --all

# Run all unit tests
pytest tests/phase2/ -v -m "not integration"

# Run integration tests (requires huffman extension + real demos)
pytest tests/phase2/ -v -m "integration"
```

---

## Human Review Summary

| Gate | Command | What to check | Proceed when |
|---|---|---|---|
| P2-1 | `python phase2/parse_pipeline.py --limit 10` then DB inspection | Map names correct? Frag timestamps reasonable (in seconds of demo)? Weapons recognized? Airshots plausible? | All 10 demos parsed, frags look correct |
| P2-2 | `streamlit run phase2/review/dashboard.py` | Rate each frag. Approve railgun air shots, multi-kills, rockets. Reject mundane kills. | At least 10 frags approved |
| P2-3 | `python phase2/renderer/batch_renderer.py --limit 10` | Watch 10 AVI clips. Timing correct? Resolution 1920x1080? No corruption? | All 10 clips look correct |
