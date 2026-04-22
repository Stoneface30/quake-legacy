-- creative_suite/database/nle_schema.sql
-- NLE Studio DB schema — studio_nle.db
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS clip_arrangements (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    part        INTEGER NOT NULL,
    position    INTEGER NOT NULL,
    role        TEXT    NOT NULL DEFAULT 'body',   -- intro | body | outro
    clip_path   TEXT    NOT NULL,
    tier        TEXT    NOT NULL DEFAULT 'T2',     -- T1 | T2 | T3
    is_fl       INTEGER NOT NULL DEFAULT 0,
    pair_path   TEXT,
    duration_s  REAL,                              -- populated at import via ffprobe; NULL if unknown
    updated_at  REAL    NOT NULL DEFAULT (unixepoch('now','subsecond'))
);

CREATE TABLE IF NOT EXISTS clip_effects (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    arrangement_id  INTEGER NOT NULL REFERENCES clip_arrangements(id) ON DELETE CASCADE,
    effect_type     TEXT    NOT NULL,  -- slowmo|speedup|shine_on_kill|audio_reverb|audio_bass_drop|zoom|vignette|audio_silence_dip
    params          TEXT    NOT NULL DEFAULT '{}',  -- JSON blob
    position        INTEGER NOT NULL DEFAULT 0,
    enabled         INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS music_assignments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    part            INTEGER NOT NULL,
    role            TEXT    NOT NULL,   -- intro | main_{n} | outro
    track_filename  TEXT    NOT NULL,
    artist          TEXT,
    title           TEXT,
    bpm             REAL,
    duration_s      REAL,
    transition_in   TEXT DEFAULT '{}',   -- JSON
    transition_out  TEXT DEFAULT '{}',   -- JSON
    chain_score     REAL DEFAULT 0.0,
    position        INTEGER NOT NULL DEFAULT 0,
    UNIQUE(part, role)
);

CREATE TABLE IF NOT EXISTS audio_fx (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    part        INTEGER NOT NULL,
    trigger     TEXT    NOT NULL,   -- song_transition|frag_kill|frag_railgun|frag_rocket
    effect_type TEXT    NOT NULL,   -- sweep_up|sweep_down|bass_drop|reverb_tail|filter_open|audio_silence_dip
    params      TEXT    NOT NULL DEFAULT '{}',
    enabled     INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_arr_part_pos ON clip_arrangements(part, position);
CREATE INDEX IF NOT EXISTS idx_fx_arr       ON clip_effects(arrangement_id);
CREATE INDEX IF NOT EXISTS idx_music_part   ON music_assignments(part, position);
CREATE INDEX IF NOT EXISTS idx_audio_fx_part ON audio_fx(part);
