-- QUAKE LEGACY — Unified Database Schema
-- Shared across all phases. All phases read and write here.
-- knowledge.db = cross-phase learning store

-- ─── Phase 2: Demo Intelligence ───────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS demos (
    id          INTEGER PRIMARY KEY,
    filename    TEXT NOT NULL UNIQUE,
    map_name    TEXT,
    game_type   INTEGER,       -- GT_FFA=0, GT_DUEL=1, GT_CA=4, etc.
    duration_ms INTEGER,
    parsed_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    parser      TEXT           -- 'UDT' or 'qldemo-python'
);

CREATE TABLE IF NOT EXISTS frags (
    id              INTEGER PRIMARY KEY,
    demo_id         INTEGER REFERENCES demos(id),
    frag_time_ms    INTEGER NOT NULL,   -- absolute server_time in ms
    pre_roll_ms     INTEGER DEFAULT 5000,
    post_roll_ms    INTEGER DEFAULT 2000,
    weapon          TEXT,               -- MOD_RAILGUN, MOD_ROCKET, etc.
    is_airshot      BOOLEAN DEFAULT FALSE,
    is_multikill    BOOLEAN DEFAULT FALSE,
    kill_streak     INTEGER DEFAULT 1,
    distance_units  REAL,               -- killer-victim distance (units)
    victim_z_vel    REAL,               -- victim Z velocity at frag time
    -- Phase 3 AI scores (filled later)
    ai_score        REAL,               -- 0.0-1.0 AI rating
    pattern_tags    TEXT,               -- JSON array: ["airshot","multikill","combo"]
    -- Human review
    tier            INTEGER,            -- 1=best, 2=good, 3=ok (human-assigned)
    reviewed        BOOLEAN DEFAULT FALSE,
    approved        BOOLEAN DEFAULT FALSE,
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS rendered_clips (
    id              INTEGER PRIMARY KEY,
    frag_id         INTEGER REFERENCES frags(id),
    avi_path        TEXT,
    camera_type     TEXT,               -- firstperson/freelook/spline
    wolfcamql_cfg   TEXT,               -- the gamestart.cfg content used
    rendered_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_size_mb    REAL
);

-- ─── Phase 1: Clip Assembly Learning ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS assembled_parts (
    id              INTEGER PRIMARY KEY,
    part_number     INTEGER NOT NULL,
    output_path     TEXT,
    clip_count      INTEGER,
    duration_s      REAL,
    file_size_mb    REAL,
    grade_preset    TEXT,               -- JSON of grade settings used
    approved        BOOLEAN DEFAULT FALSE,
    assembled_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ─── Cross-Phase Knowledge Store ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS knowledge (
    id          INTEGER PRIMARY KEY,
    phase       INTEGER,                -- 1, 2, or 3
    category    TEXT,                   -- 'grade', 'camera', 'pattern', 'clip_length'
    key         TEXT NOT NULL,
    value       TEXT NOT NULL,          -- JSON
    confidence  REAL DEFAULT 1.0,
    learned_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Examples of cross-phase knowledge entries:
-- phase=1, category='grade', key='optimal_contrast', value='1.42'
-- phase=2, category='clip_length', key='preferred_pre_roll_ms', value='4500'
-- phase=2, category='pattern', key='approval_rate_airshot', value='0.87'
-- phase=3, category='camera', key='best_angle_for_railgun', value='"wide_reveal"'

-- ─── Phase 3: Camera Library ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS camera_paths (
    id          INTEGER PRIMARY KEY,
    map_name    TEXT NOT NULL,
    camera_type TEXT,                   -- overview/follow/bullet_cam/rail_reveal
    trigger_zone TEXT,                  -- JSON: {x, y, z, radius}
    wolfcam_file TEXT,                  -- path to .camera file
    approval_count INTEGER DEFAULT 0,  -- times human approved clips using this
    rejection_count INTEGER DEFAULT 0
);

-- ─── Phase 2+: Full Demo Event Dataset ───────────────────────────────────────

-- Every meaningful game event from every parsed demo
CREATE TABLE IF NOT EXISTS demo_events (
    id              INTEGER PRIMARY KEY,
    demo_id         INTEGER REFERENCES demos(id),
    server_time_ms  INTEGER NOT NULL,
    round_num       INTEGER,
    event_type      TEXT NOT NULL,     -- 'obituary','change_weapon','fire_weapon','pickup', etc.
    event_code      INTEGER,           -- raw EV_* integer
    entity_num      INTEGER,           -- entity that carried the event
    client_num      INTEGER,           -- primary actor (killer for obituary, shooter for fire, etc.)
    victim_client   INTEGER,           -- obituary only
    killer_client   INTEGER,           -- obituary only
    weapon          INTEGER,           -- MOD_* or weapon slot
    weapon_name     TEXT,
    event_parm      INTEGER,           -- raw eventParm (item index, etc.)
    pos_x           REAL,              -- position of event entity at event time
    pos_y           REAL,
    pos_z           REAL
);

-- Round timeline — one row per round per demo
CREATE TABLE IF NOT EXISTS demo_rounds (
    id          INTEGER PRIMARY KEY,
    demo_id     INTEGER REFERENCES demos(id),
    round_num   INTEGER NOT NULL,
    start_ms    INTEGER,
    end_ms      INTEGER
);

-- Per-demo per-player aggregate stats (kills, deaths, weapon breakdown)
CREATE TABLE IF NOT EXISTS demo_player_stats (
    id               INTEGER PRIMARY KEY,
    demo_id          INTEGER REFERENCES demos(id),
    client_num       INTEGER NOT NULL,
    player_name      TEXT,
    team             TEXT,
    kills            INTEGER DEFAULT 0,
    deaths           INTEGER DEFAULT 0,
    suicides         INTEGER DEFAULT 0,
    kills_by_weapon  TEXT,             -- JSON {"RAILGUN":5,"ROCKET":3,...}
    deaths_by_weapon TEXT              -- JSON
);

-- Per-snapshot observed-player state (position, velocity, look direction, weapon)
-- Populated from the playerstate in each snapshot (not entity state)
CREATE TABLE IF NOT EXISTS player_snapshots (
    id              INTEGER PRIMARY KEY,
    demo_id         INTEGER REFERENCES demos(id),
    server_time_ms  INTEGER NOT NULL,
    round_num       INTEGER,
    client_num      INTEGER,           -- from ps.clientNum
    origin_x        REAL,
    origin_y        REAL,
    origin_z        REAL,
    vel_x           REAL,
    vel_y           REAL,
    vel_z           REAL,
    angle_pitch     REAL,              -- ps.viewangles[0]
    angle_yaw       REAL,              -- ps.viewangles[1]
    weapon          INTEGER,           -- ps.weapon slot
    speed           REAL               -- sqrt(vx^2+vy^2+vz^2) — pre-computed
);

-- Cross-demo player registry (for FT-5 nickname dictionary)
CREATE TABLE IF NOT EXISTS players (
    id              INTEGER PRIMARY KEY,
    canonical_name  TEXT NOT NULL,     -- strip color codes, lowercase
    aliases         TEXT,              -- JSON array of all seen raw name strings
    first_seen_demo TEXT
);

-- ─── Indexes ─────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_frags_demo      ON frags(demo_id);
CREATE INDEX IF NOT EXISTS idx_frags_weapon    ON frags(weapon);
CREATE INDEX IF NOT EXISTS idx_frags_approved  ON frags(approved);
CREATE INDEX IF NOT EXISTS idx_knowledge_key   ON knowledge(phase, category, key);
CREATE INDEX IF NOT EXISTS idx_demo_events_demo ON demo_events(demo_id, server_time_ms);
CREATE INDEX IF NOT EXISTS idx_demo_events_type ON demo_events(event_type, demo_id);
CREATE INDEX IF NOT EXISTS idx_demo_events_client ON demo_events(client_num, demo_id);
CREATE INDEX IF NOT EXISTS idx_player_snapshots_demo ON player_snapshots(demo_id, server_time_ms);
CREATE INDEX IF NOT EXISTS idx_demo_player_stats_demo ON demo_player_stats(demo_id);
