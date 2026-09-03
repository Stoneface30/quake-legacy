# Netcode anomaly archive + forensic replay (2026-09-02)

Modules: `creative_suite/engine/netcode_anomaly.py` (`netcode-anomaly-v1.0.0`),
`creative_suite/engine/forensic_replay.py` (`forensic-replay-v1.0.0`).
Archive: `output/anomalies/netcode_anomalies_v1.jsonl` (JSON Lines, local, gitignored).

This is **not** a netcode project. Nothing here touches prediction, hit registration, damage
or a server. It preserves numerically interesting delivery situations with their evidence and
can turn one into a reproducible video that explains it.

## ANOMALY IS NOT BUG

Every record carries an assessment. Detectors may only assign
`EXPECTED_NETCODE_BEHAVIOR`, `CLIENT_OBSERVATION_LIMITATION`, `RECONSTRUCTION_DISAGREEMENT`
or `INSUFFICIENT_EVIDENCE`. `SUSPICIOUS`, `SUSPECTED_BUG` (needs a stated `reason`) and
`CONFIRMED_BUG` (needs `confirmed_by`) are human states; the constructor refuses them without
their fields. A projectile the client recorded for 25 ms and then lost is a
`CLIENT_OBSERVATION_GAP`; when the physics continuation lands on the recorded explosion it is an
excellent forensic case and **not** evidence of a Quake bug.

## Record fields

content_hash · server_time_ms (demo_us derived) · round_index · subject_client · target_client ·
entity_num · weapon_wp · event_weapon_wp · weapon_mod · event_type · recorded_before ·
recorded_after · expected_state · spatial_residual_u · temporal_residual_us · damage_evidence ·
snapshot_gap_us · provenance_classes · confidence · assessment · reason · confirmed_by ·
creative_utility · notes · detector_version. Unsupported fields stay `UNKNOWN` (None).
`anomaly_id` = sha256 of the evidence fields (notes and creative_utility excluded), so identical
evidence in the same recording gives the same id and the same numbers in another recording do
not. Synthetic provenance (`CINEMATIC_SYNTHETIC`) cannot enter a record.

## Taxonomy

Vocabulary: NETCODE_HIT_DISAGREEMENT, PREDICTION_CORRECTION_SPIKE, REMOTE_TELEPORT, SNAPSHOT_GAP,
DAMAGE_WITHOUT_EXPECTED_CONTACT, CONTACT_WITHOUT_DAMAGE, PROJECTILE_VISUAL_DISAGREEMENT,
REWIND_LIMIT_EDGE, SPLASH_FALLOFF_EDGE, PLAYERSTATE_ENTITYSTATE_DISAGREEMENT,
PROJECTILE_RECONSTRUCTION_DISAGREEMENT, CLIENT_OBSERVATION_GAP, PROJECTILE_TERMINATION_DISAGREEMENT,
REMOTE_STATE_DISCONTINUITY.

Detectors exist for six only (`DETECTED_TYPES`): `from_projectile` (gap / reconstruction /
termination), `snapshot_gaps`, `remote_discontinuities` (REMOTE_TELEPORT with a teleport event
nearby → expected; otherwise REMOTE_STATE_DISCONTINUITY → insufficient evidence). The rest are
reserved names; nothing populates them yet.

## Truth layers stay separate

RECORDED GAME EVENT · RECORDED SNAPSHOT STATE · PHYSICS_RECONSTRUCTED · EVENT_CONSTRAINED ·
DELIVERED VISUAL · DELIVERED GAME AUDIO · CINEMATIC_SYNTHETIC. An anomaly compares layers
(`recorded_before` / `expected_state` / `recorded_after`) and never merges them; the path's
`provenance_segments` say which stretch is which.

## Code spaces (measured)

Samples and entity-sourced `missile_hit`/`missile_miss` events carry **WP_** (4 GL, 5 RL, 8 PG).
**MOD_** is obituaries only. A playerstate-sourced event's `weapon` is the recorder's held weapon,
never the missile's (`event_weapon_is_missile`). A missing delta-coded `pos_z` means unchanged
(`merge_delta_pos`).

## Forensic replay

`ForensicReplayRecipe` — anchors in demo_us (context before, OBSERVATION ENDS, anomaly end,
context after), exact rational slow rate, freeze duration, layers, camera (SIDE / TOP /
PROJECTILE, all `CINEMATIC_CLEAN`), audio policy (game audio by default, no music). Its
`time_segments()` are `scene_recipe.TimeSegment`s: normal → freeze → slow → normal, contiguous,
no temporal debt. `ForensicManifest` records anomaly id + hash, content hash, source event,
reconstruction version, BSP hash (sha256 of the pak entry), physics constants, provenance
segments, camera, TimeMap, layers, recipe hash, output sha256. `render_forensic_replay` draws
schematic frames (recorded = solid yellow discs; reconstructed = dashed blue; bounces; predicted
terminal; recorded explosion + splash radius; compact numeric overlay) and encodes with the
project ffmpeg. It opens no database and changes no moment state: rendering never marks
VALIDATED / ASSIGNED / USED. `forensic_sheet` adds the forensic lanes to the diagnostic sheet.
Domains: `FORENSIC_REFERENCE` (this) vs `CINEMATIC_INTERPRETATION` (future, authored); the
recipe refuses the latter.

Rendering is on demand, one case at a time. Detection and indexing are cheap; videos are not.

## Creative Opportunity Graph

`opportunity_graph.anomaly_fields(anomaly, forensic_replay_available=…)` fills
`anomaly_available`, `anomaly_type`, `anomaly_assessment`, `anomaly_id`,
`forensic_replay_available`, `observation_gap_us`, `anomaly_residual_u`, `creative_utility`.
Searchable material for a technical interlude, a tribute, a glitch treatment; never a placement.

## First proof — Frag 28557 (trinity, grenade)

Recorded 2 samples (25 ms) → OBSERVATION ENDS → 2,476 ms reconstructed, 5 BSP bounces →
FUSE at 2,500 ms → recorded explosion **5.7 u** from the predicted point →
`CLIENT_OBSERVATION_GAP` / `CLIENT_OBSERVATION_LIMITATION` / `EXACT_DETERMINISTIC`.
Replay: `docs/visual-record/2026-09-02/forensic_replay_frag28557.mp4` (13.4 s, 1280×720,
normal → freeze 1.5 s → ¼ speed → normal) with sidecar `.forensic.json`; frames contact sheet
`forensic_replay_frag28557_frames.png`; sheet `forensic_sheet_frag28557.png`.
The same occurrence exists in a trimmed demo (Frag 33576): one case, not two.

## Second proof — Frag 24326 (rocket), cheap

Recorded prefix 2 samples (25 ms, 999 u/s) → OBSERVATION ENDS → 1,100 ms reconstructed →
the missile entity re-appears at the hit tick with its trajectory base reset to the impact point
(recorded contact) **49.0 u** from the continuation → cut at 1,125 ms, `DYNAMIC_CONTACT`,
`DETERMINISTIC_UNTIL_UNOBSERVED_DYNAMIC_CONTACT`, anomaly `CLIENT_OBSERVATION_GAP` /
`CLIENT_OBSERVATION_LIMITATION`. The victim's collision was not observed; the victim's death
position lies 11.6 u from the recorded hit.
Replay: `docs/visual-record/2026-09-02/forensic_replay_frag24326.mp4` (7.5 s).

**Pitfall recorded:** feeding the re-observation into the continuation as an input gives a
0.0 u residual by construction. `from_projectile` now refuses that shape (a recorded run after
a derived run → `INSUFFICIENT_EVIDENCE` with a note); propagate the prefix only.
