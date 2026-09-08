# Astra truth audit — refreshed current checkout

2026-09-05. Refreshed through commit `430645e0` plus current working files after the user reported concurrent implementation. This supersedes the first `bb23f2d4` audit snapshot. Read-only source audit: no production database writes, captures, mining, installations, service changes or new implementation. The coordinating auditor read aggregate database records separately; those observations are attributed below. Proposed tests are not claims of execution.

The new code materially improves annotation delivery. It also makes actions reviewable before every consumer understands the ACTION namespace. That boundary, promotion identity, and human migration are the immediate production risks.

## Current evidence and attachment history

The supplied attachment, lines 1–2300, requests a versioned full-corpus rebuild and explicitly supersedes earlier restrictions on remining. Its requirements include preserving every human decision, testing mapping before cutover, distinguishing absence from negative truth, sharing protocol definitions, rebuilding canonical occurrences and scenes, and extracting broader non-kill/aim signals. Historical counts in that brief are baselines, not acceptance targets. Near the end of this range it reports a separate visual proof of model/skin/tint authority and a correction for latched capture cvars. It explicitly leaves later instruction-layer proofs unfinished. This is historical task context and reported results; it is not independent proof of current mining correctness.

The coordinating auditor reports current read-only epoch records: **4,292 distinct hashes, 6,445 raw copies, zero newly discovered hashes; 77,951 action rows; 1,292,062 aim rows; 4,292 action runs and 4,292 aim runs with zero recorded errors; both miner versions `1.0.0`; promotion stage records both tables PROMOTED.** These prove stored counts/status, not a new raw-byte inventory or independently validated labels. The implied duplicate raw-file count is 2,153. The reported 5,553 high-confidence own no-kill actions remains a queue-classification claim subject to findings 1–4; I did not independently recount that filtered subset.

## 1. CORRECTNESS BUG — ACTION IDs become unrelated kill IDs in ActionTruth

`review_corpus._action_item()` constructs `ACTION:<action_id>` and sets `source_id=action_id` (`creative_suite/engine/review_corpus.py:1703`–1704). The module correctly states that ACTION and USER_FRAG are separate namespaces (lines 1643–1646).

`action_truth.for_item()` resolves that review item and immediately assigns `occ_id = it.source_id` (`creative_suite/engine/action_truth.py:213`–216), without inspecting item type. It queries `kill_occurrences_v1` using that integer (lines 218–224), then computes the kill's stack, geometry, movement and round. `/dossier/{item_id}` forwards arbitrary item IDs directly to this path (`creative_suite/api/review.py:776`–784).

Therefore an action with ID 41 and an unrelated kill occurrence with ID 41 can return the kill's entire dossier under the action's item ID. If no kill has that integer, it instead reports unavailable. This is source-established namespace confusion; no private examples were fetched. Human migration has a parallel namespace risk: it treats every human_reviews.source_id as a kill occurrence (`human_migration.py:42`–47, 96–112).

**Smallest proof:** isolated fixtures with ACTION:41 and USER_FRAG:41 on different maps/times. Resolve both through the real dossier API and require correct entity identity or an explicit unsupported-action result. Then verify an ACTION review against the action identity, never a coincidental kill ID.

## 2. ARCHITECTURAL BLOCKER — promotion and migration do not preserve review identity

`mining_epoch.promote()` excludes action_id/aim_id from inserted columns (`creative_suite/engine/mining_epoch.py:256`), deletes destination rows (line 273), and reinserts into AUTOINCREMENT tables. ACTION review IDs are those destination action IDs. The coordinating auditor reproduced with disposable SQLite databases that promoting the same one-row epoch twice changes its destination action_id from 1 to 2. Counts remain unchanged while review targets move.

Promotion opens and commits a separate destination transaction for each table (lines 248, 260, 280). No human-migration or completion gate is called. One table may commit while the next refuses or fails. Its status check compares miner row versions, not EPOCH_VERSION (lines 265–267). Thus the comment promising an atomic versioned rebuild exceeds the implementation.

`human_migration.check()` gives a different nonempty fingerprint at the same ID the status CHANGED_ID_SAME_EVENT (`human_migration.py:143`–146), although its own detail says the ID resolves to a different kill. BLOCKING excludes that status (line 37). The coordinating auditor's disposable repro returns blocked=False for kill-A changing to kill-B at the same ID. Its default before/after database is also the same current file (lines 120–124): that proves present self-consistency, not preservation through a past operation.

**Smallest proof:** require a same-ID/different-fingerprint change to block; repeat the same promotion twice with saved ACTION verdicts; inject failure on the second table and require both tables plus all human references to retain the previous epoch. Include notes, chosen POV, production usage and all namespaces in mapping; production_usage is absent from HUMAN_TABLES.

These are not hypothetical pre-cutover cautions: epoch records indicate promotion has already occurred. They justify preserving the current stores and auditing mapping before any repeat promotion, not automatically rolling back live data.

## 3. CORRECTNESS BUG — action labels assert more than the observations establish

The new miner's missing-team comment says absence is not enmity, but `is_enemy()` returns every other client when the recorder's team is absent (`engine/parser/mine_action_moments.py:215`–222). Static whole-demo team rows also ignore team changes.

`TRUE_NO_KILL_ACTION` is set whenever no nearby **recorder** kill is found (lines 255–260, 287–292). Other players can die within the action and it remains “true no kill”; the review module labels this family “nobody died” (`review_corpus.py:1641`). A recorder kill *before* the action can conversely mark it FRAG_BUILDUP_CONTEXT because the search includes t−4500ms. `nearest_round()` selects the next kill's round, not an observed round interval (miner lines 231–235).

HIGH confidence means only that the recorder supplied at least half of counted shots (lines 250–273). No relation connects those shots to the victims' pain. A sustained LG stream can dominate a teammate's single damaging rocket even when the recorder never hits those targets. A percentile calibration of shot share estimates rarity, not attribution precision. `PROJECTILE_NEAR_MISS` similarly comes from three missile misses and zero missile hits (lines 297–298), without a proximity check or projectile-owner check. These labels feed the live default queue through HIGH plus ends_in_kill=0 (`review_corpus.py:1675`–1682).

**Smallest proof:** fixtures for unknown team, teammate kill during the action, recorder kill before the action, unrelated high-rate recorder fire, and distant missile misses. The output must preserve observed counts while withholding unsupported enemy, no-kill, buildup, near-miss and ownership claims. No additional mining is required to falsify these semantics.

## 4. CORRECTNESS BUG — resumability can preserve stale results and skip failed demos

Both miners consider any run row with the current version “done,” including runs with errors (`mine_action_moments.py:319`–323; `mine_aim_events.py:276`–280). A failed demo is therefore silently omitted on retry unless state/version is manually changed.

Both writers use INSERT OR REPLACE for newly detected rows and never remove obsolete rows for the reprocessed demo (`mine_action_moments.py:304`–316; `mine_aim_events.py:258`–273). A changed detector that finds fewer events leaves the old events behind; an error can leave old successful output paired with a new failed run. Replacement also regenerates AUTOINCREMENT IDs. Version changes are not sufficient to make stale events disappear.

Input scope is not the freshly hashed inventory: action mining iterates previously scanned demos with *any* enrichment run, ignoring its semantic version/error (`mine_action_moments.py:155`–163); aim mining iterates scanned hashes that have a path in the older rebuilt database (`mine_aim_events.py:133`–142). `mining_epoch.current_semantic_hashes()` exists (line 100), but these miners do not call it. Thus the 4,292 current zero-error records do not establish that future resumptions or newly discovered demos obey the promised version-aware full-corpus contract.

**Smallest proof:** one failed current-version run must retry; remine a demo from two events to one and require the removed event to disappear without changing surviving identity; change semantic version and require rederivation; add a raw-inventory demo missing from scanned_demos and require an explicit pending/failure result rather than omission.

## 5. FALSELY CLAIMED OR NOT PROVEN — aim calibration does not establish player-aim semantics

Stillness segmentation and measured thresholds are real additions (`engine/parser/mine_aim_events.py:145`–212 and lines 72–83). They fix the earlier “one gesture per demo” approach described in the source. However extraction discards snapshot client_num and all semantic discontinuity markers, retaining only time/yaw/pitch (lines 228–240). A spectator-follow change below MAX_STEP_DEG is indistinguishable from hand movement. Camera resets/round restarts are likewise not explicit segment boundaries.

The parser normalizes **both** pitch and yaw modulo 360 (`engine/parser/demo_parse.py:1065`, 1084–1085). The gesture code wraps yaw but directly subtracts pitch (`mine_aim_events.py:162`–163, 185–187). A small pitch movement across 0/360 is treated as a huge discontinuity and discarded. The same physical aim path can therefore segment differently across the coordinate boundary.

TRACKING is assigned from duration>=800ms and peak speed below the flick threshold (lines 249–250), with no target relation. It currently means prolonged slow view movement, not demonstrated tracking of an opponent. MICRO_CORRECTION also describes low net displacement after >=25 degrees of total travel, not necessarily a small corrective aim movement.

**Smallest proof:** replay identical angular paths across equivalent pitch representations, camera-client changes and round resets; require invariant geometry and explicit observer segmentation. Compare a slow turn toward an empty wall with actual target tracking; absent target evidence must remain a view-motion descriptor. Distribution percentiles alone cannot certify those labels.

## 6. ARCHITECTURAL BLOCKER — the factual gate still accepts uncertainty as fact

The refreshed contract still marks OBSERVED and DERIVED factual (`production_contract.py:55`) and only treats None as unavailable (lines 214–220). The earlier pure in-memory probe showed UNKNOWN weapon text accepted as OBSERVED/factual, an empty alive curve as DERIVED/factual, and a numeric accuracy with AMBIGUOUS confidence as DERIVED/factual. The relevant implementation remains unchanged; the probe did not query databases.

A concrete same-tick ownership bug also remains: ActionTruth joins recognition attributes by content_hash+server_time_ms with LIMIT 1, without actor/victim/weapon (`action_truth.py:227`–231). Concurrent kills can share metrics. `action_stats.py:161`–174 counts all victim pain against one weapon's recorder shots; earlier pain from another weapon can become HIGH confirmed accuracy (lines 225–231). Sharing that result with the dossier or contract does not validate it.

**Smallest proof:** require unsupported or ambiguous claim types to fail eligibility even with numeric values; add two same-tick occurrences with different victims and reverse insertion order; add previous-weapon pain followed by one missed and one lethal rail. Test identity and evidence, not equality between adapters over the same query.

## 7. DUPLICATED AUTHORITY — rounds and observation membership remain independently reconstructed

ActionTruth still uses `round_story` (`action_truth.py:241`), whose round start/end are the first/last observed kills (`round_story.py:150`–151, 229), and whose alive counts use whole-demo team membership minus observed deaths (lines 138–140, 185–210). Its event.time_in_round_ms is time since the first kill (`action_truth.py:255`), not the round-start configstring. Another RoundContext builder reads round-state, team changes and outcomes (`round_context.py:182`–200); these authorities remain separate.

Scene still filters canonical occurrences through only their globally selected best observation (`scene.py:165`–172). Changing the preferred camera can remove an occurrence from a demo's scene despite another observation proving it belongs there. The new production resolver repeats that dependency (`production_contract.py:603`–609).

**Smallest proof:** a round with first kill 20 seconds after start, a team change, and an occurrence observed in two demos. Review and planning must agree on round timing/identity; switching preferred POV must not change historical membership. Keep canonical event identity distinct from observation membership.

## 8. FALSELY CLAIMED OR NOT PROVEN — independent parser recall remains weaker than claimed

`engine/parser/score_oracle.py:90`–102 decodes both score updates and obituaries with DM73Parser and matches every score update to the nearest obituary of any client. It does not consume matches or account for score-delta multiplicity, yet prints implied detector recall (lines 135–137). `protocol_profiles.py:168`–170 cites that result as 100% recall corroboration. One surviving obituary can satisfy several nearby score increments.

The duplicated netfield tables at `demo_parse.py:475`–482 and `protocol_profiles.py:90`–110 appear consistent in the inspected portions; this is a drift risk, not a finding that the current table is wrong. A round trip against a synthetic writer sharing these constants cannot independently certify them.

**Smallest proof:** one score delta of three with only one obituary must fail a recall assertion. Then compare exact anonymized event tuples against independently decoded raw fixtures, including same-tick kills, slot zero, event-toggle bits and multiple service messages per packet.

## Corrections to the earlier audit and limits

The original event-note loss finding is **resolved in current source**: Scene now loads event_annotations and preserves provenance (`scene.py:244`–272); the contract rejects non-human event-note provenance (`production_contract.py:518`–524). The new `build_choreography_input_for_scene()` resolves every verdict-bearing event and loads notes/tags/POV counts (lines 619–654), and a real director endpoint calls it (`creative_suite/api/director.py:128`–136). `test_note_reaches_production.py:130`–145 now exercises storage-to-input rather than only a preannotated fixture. No rerun of that suite was performed here. A full ChoreographyPlan consumer still was not located, but calling the bridge entirely unwired is now wrong.

The older `input_for_item()` still passes only one truth for a scene (`production_contract.py:553`); the new scene entrypoint is the materially stronger API. API availability is not proof of a finished film planner.

The launcher now redirects the formerly missed tag/workshop modules and forces TEST provenance on their writes (`scripts/review_test_instance.py:63`–117). Its comment records the earlier accidental HUMAN_USER writes and manual cleanup; that is reported history, not independent verification that production is clean. The coordinating auditor separately covers remaining explicit-live-path and SQLite-copy isolation defects. Do not infer preservation from equal counts or from current TEST wrappers.

RoundScenario/compiler reconciliation belongs to the parallel synthetic/capture audit. The original main-checkout absence finding must not be generalized to the concurrently updated prologue worktree. Do not build a duplicate compiler until that work has been located and audited.

Recommended order: preserve a consistent current snapshot; prove namespaced target identity and human mapping; make repeat promotion idempotent and atomic; then falsify action/aim semantics on small isolated fixtures. Additional production batches and backend expansion are SAFE TO DEFER. The current counts show that work ran; they do not certify what each mined row means.
