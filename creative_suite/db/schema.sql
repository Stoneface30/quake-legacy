CREATE TABLE IF NOT EXISTS assets (
  id              INTEGER PRIMARY KEY,
  category        TEXT NOT NULL,
  subcategory     TEXT,
  source_pk3      TEXT NOT NULL,
  internal_path   TEXT NOT NULL,
  checksum        TEXT NOT NULL,
  extracted_path  TEXT,
  width           INTEGER,
  height          INTEGER,
  thumbnail_path  TEXT,
  UNIQUE (source_pk3, internal_path)
);

CREATE TABLE IF NOT EXISTS variants (
  id              INTEGER PRIMARY KEY,
  asset_id        INTEGER NOT NULL REFERENCES assets(id),
  user_prompt     TEXT,
  final_prompt    TEXT NOT NULL,
  seed            INTEGER,
  comfy_job_id    TEXT,
  png_path        TEXT NOT NULL,
  thumbnail_path  TEXT,
  width           INTEGER,
  height          INTEGER,
  status          TEXT NOT NULL,
  approved_at     DATETIME,
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_variants_asset_status ON variants(asset_id, status);

CREATE TABLE IF NOT EXISTS pack_builds (
  id              INTEGER PRIMARY KEY,
  pack_slug       TEXT NOT NULL,
  pk3_path        TEXT NOT NULL,
  variant_count   INTEGER NOT NULL,
  sha256          TEXT NOT NULL,
  built_at        DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS annotations (
  id              TEXT PRIMARY KEY,
  part            INTEGER NOT NULL,
  mp4_time        REAL NOT NULL,
  description     TEXT NOT NULL,
  avi_effect      TEXT,
  dream_effect    TEXT,
  tags            TEXT,
  clip_index      INTEGER,
  clip_filename   TEXT,
  demo_hint       TEXT,
  demo_file       TEXT,
  servertime_ms   INTEGER,
  created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_annotations_part ON annotations(part);
CREATE INDEX IF NOT EXISTS idx_annotations_tags ON annotations(tags);

CREATE TABLE IF NOT EXISTS clip_durations (
  avi_path        TEXT PRIMARY KEY,
  duration_s      REAL NOT NULL,
  probed_at       DATETIME DEFAULT CURRENT_TIMESTAMP
);
