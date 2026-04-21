"""One-shot: create pipelines/ dirs + initialize assets.db schema."""
import sqlite3
from pathlib import Path

PHOTOREAL = Path(__file__).parent / "photoreal"

for pipe in ["upscale_only", "tile_d35", "tile_d50", "tile_d60", "tile_d70", "tile_d80"]:
    (PHOTOREAL / "pipelines" / pipe).mkdir(parents=True, exist_ok=True)
    print(f"  mkdir pipelines/{pipe}/")

DB = PHOTOREAL / "assets.db"
conn = sqlite3.connect(str(DB))
conn.executescript("""
CREATE TABLE IF NOT EXISTS assets (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    rel_path  TEXT    NOT NULL UNIQUE,
    category  TEXT    NOT NULL,
    route     TEXT    NOT NULL,
    width     INTEGER,
    height    INTEGER,
    sha256    TEXT
);
CREATE TABLE IF NOT EXISTS renders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id    INTEGER NOT NULL REFERENCES assets(id),
    pipeline    TEXT    NOT NULL,
    denoise     REAL,
    style       TEXT,
    output_path TEXT    NOT NULL UNIQUE,
    created_at  TEXT    DEFAULT (datetime('now')),
    status      TEXT    DEFAULT 'ok'
);
CREATE INDEX IF NOT EXISTS idx_renders_asset    ON renders(asset_id);
CREATE INDEX IF NOT EXISTS idx_assets_category  ON assets(category);
""")
conn.commit()
n_a = conn.execute("SELECT count(*) FROM assets").fetchone()[0]
n_r = conn.execute("SELECT count(*) FROM renders").fetchone()[0]
print(f"  assets.db OK — {n_a} assets, {n_r} renders")
conn.close()
