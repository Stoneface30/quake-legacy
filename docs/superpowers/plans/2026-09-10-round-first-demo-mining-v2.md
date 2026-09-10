# Round-First Demo Mining V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a calibrated, weapon-aware, round-first mining pipeline that produces globally deduplicated CA review units and a prepare-only extraction manifest, while admitting only exceptional CTF Instagib sequences and excluding Duel/TDM.

**Architecture:** Preserve the existing frag recognizer as a deterministic evidence producer. Add versioned V2 calibration, authoritative round/life units, hierarchical scoring, canonical review projection, and immutable extraction-manifest modules backed by `mining_epoch.db`. Every media unit is identified independently of traits, so one reviewed round can appear in many virtual lanes without duplicate video or verdicts.

**Tech Stack:** Python 3.11, sqlite3, JSON/HTML, pytest, pyright; no new dependencies.

**Spec:** `docs/superpowers/specs/2026-09-10-round-first-demo-mining-v2-design.md`

## Global Constraints

- CA is the primary corpus. Duel, TDM and all non-CA/non-CTF-Instagib modes are rejected before scoring.
- CTF Instagib uses a separate mode-local score and produces only `CTF_INSTAGIB_HERO` or `REJECT`.
- CA starts at the observed five-second countdown and stops at the earliest of recorder death, authoritative round end or demo/gamestate end.
- A 750 ms completion tail is clamped before the next countdown, next round or gamestate end.
- Ambiguous round boundaries are `ROUND_BOUNDARY_UNCERTAIN` and cannot enter automatic capture.
- Canonical CA identity is `(content_hash, gamestate_id, authoritative_round_id, recorder_client, life_index)`.
- One canonical media unit is reviewed once; traits and weapon lanes are virtual projections sharing that verdict.
- Calibration targets are `GOLDEN=5`, `HIGH=4`, `MED=3`, `LOW=2`, `DISCOUNT=1`, `DROP=0`; missing verdicts do not fit weights.
- Strong calibrated traits lead scoring. Supporting traits cannot independently qualify a hero. Retired standalone traits contribute zero.
- Distinct CA moments combine as `e1 + 0.60*e2 + 0.35*e3`, then sequence, clutch/finish, editability and quality adjustments apply.
- Correlated traits attached to one event cannot stack as independent moments.
- Weapon percentiles are calculated within CA weapon lanes, never across modes.
- CTF rail presence alone is not Instagib evidence.
- Preparation never launches Wolfcam. Capture consumes a separately approved immutable manifest through the existing single-worker queue.
- Public artifacts contain no demo paths, filenames, player names, nicknames, Steam IDs or raw personal identifiers.
- Existing V1 tables and per-frag review remain readable; V2 uses new versioned tables.
- No `.dm_73`, video, database or environment file is committed.

---

### Task 1: Calibration V2 model and explicit trait registry

**Files:**
- Create: `engine/parser/calibration_v2.py`
- Create: `docs/reference/demo-mining-v2-traits.json`
- Create: `engine/parser/tests/test_calibration_v2.py`
- Create at runtime only: `output/demo_v2/calibration_v2/calibration_model.json`
- Create at runtime only: `output/demo_v2/calibration_v2/calibration_report.json`

**Interfaces:**
- Consumes: private Calibration V1 JSON with `answers[{trait,clip,worth?,verdict?}]`.
- Produces: `load_answers(path) -> list[CalibrationAnswer]`, `fit_trait_weights(answers, registry, prior_strength=8.0) -> CalibrationModel`, `write_model(model, output_dir) -> tuple[Path, Path]`.
- `CalibrationModel` exposes `calibration_hash`, `weight_for(trait)`, `policy_for(trait)` and canonical JSON.

- [ ] **Step 1: Add the checked-in trait registry**

Define JSON object keys `version`, `policies`, and `families`. Set hero policies for the families named in the spec, support policies for contextual facts, and retired policies for the explicit retired standalone list. Every known trait from Calibration V1 must have exactly one policy. The registry contains trait identifiers only, never clip IDs or comments.

- [ ] **Step 2: Write failing calibration tests**

Add literal fixtures proving:

```python
def test_targets_and_missing_verdicts():
    answers = load_answers(fixture_path)
    assert [a.target for a in answers] == [5, 0]

def test_regularization_prevents_three_samples_from_becoming_extreme():
    model = fit_trait_weights(three_golden_answers, registry, prior_strength=8.0)
    assert global_mean < model.weight_for("TINY_GAP_SHOT") < 5.0

def test_unknown_trait_is_rejected():
    with pytest.raises(ValueError, match="unregistered trait"):
        fit_trait_weights([unknown_answer], registry)

def test_input_order_does_not_change_calibration_hash():
    assert fit_trait_weights(a, registry).calibration_hash == fit_trait_weights(list(reversed(a)), registry).calibration_hash
```

The named break is silent use of unrated answers, unstable hashes, or overfitting tiny trait samples.

- [ ] **Step 3: Run the tests and verify RED**

Run: `E:/PersonalAI/venv/Scripts/python.exe -m pytest engine/parser/tests/test_calibration_v2.py -v`

Expected: import failure because `engine.parser.calibration_v2` does not exist.

- [ ] **Step 4: Implement deterministic loading and regularized weights**

Use immutable dataclasses:

```python
@dataclass(frozen=True)
class CalibrationAnswer:
    trait: str
    clip_id: str
    target: int
    comment: str

@dataclass(frozen=True)
class TraitWeight:
    trait: str
    policy: str
    rated_n: int
    raw_mean: float
    shrunk_mean: float
    adjustment: float
    confidence: float
```

Calculate `shrunk_mean = (sum_targets + prior_strength*global_mean)/(rated_n+prior_strength)`. Hero adjustments may be positive or negative around the global mean; support adjustments are capped so they cannot exceed the lowest hero contribution; retired adjustment is exactly zero. Hash canonical sorted answers without comments, the registry bytes, algorithm version and numeric configuration. Keep comments only in the private aggregate report.

- [ ] **Step 5: Generate and inspect aggregate Calibration V2 artifacts**

Run the module against `C:/Users/Stoneface/Downloads/calibration_answers.json`. Confirm the report says 333 answers, 295 rated answers, 106 traits and 277 unique clip IDs. Confirm no player names, clip comments or source paths appear in the checked-in registry.

- [ ] **Step 6: Verify GREEN and commit**

Run: `E:/PersonalAI/venv/Scripts/python.exe -m pytest engine/parser/tests/test_calibration_v2.py -v`

Commit exact source, registry and test files with message `feat: derive calibrated trait weights` and the required co-author trailer.

---

### Task 2: Authoritative V2 round and recorder-life units

**Files:**
- Modify: `engine/parser/demo_parse.py`
- Modify: `engine/parser/enrich_semantic_events.py`
- Create: `creative_suite/engine/round_units_v2.py`
- Create: `creative_suite/tests/test_round_units_v2.py`
- Modify: `creative_suite/engine/mining_epoch.py`

**Interfaces:**
- Consumes: versioned gamestate/configstring edges, kill events, recorder client, canonical source selection.
- Produces: `derive_round_states(rows) -> list[RoundStateV2]`, `resolve_ca_unit(round_state, recorder_deaths, demo_end_ms, tail_ms=750) -> CaptureUnit`, `canonical_ca_unit_id(...) -> str`, `build_ca_units(...) -> BuildStats`.
- Persists `round_units_v2` and `round_unit_events_v2` in `mining_epoch.db`.

- [ ] **Step 1: Write failing parser/enrichment tests for gamestate identity**

Add a synthetic two-gamestate fixture proving emitted state rows carry monotonically increasing `gamestate_id` and that round number 1 in each gamestate remains distinct.

The named break is merging rounds with the same visible number across map restarts or gamestate changes.

- [ ] **Step 2: Verify the gamestate test is RED**

Run the exact new test node with `-v`; expected failure is missing `gamestate_id`.

- [ ] **Step 3: Persist gamestate identity without changing V1 tables**

Add parser gamestate sequence tracking and a new `round_state_v2` table. Store `(content_hash,gamestate_id,server_time_ms,round,cs,value)` and a gamestate-end/demo-end fact. Do not reinterpret `round_state_v1`.

- [ ] **Step 4: Write failing pure boundary tests**

Cover these literal timelines:

```python
def test_death_ends_before_round_result_and_tail_stays_in_round():
    unit = resolve_ca_unit(state(countdown=1000, fight=6000, end=26000, next_countdown=28000), deaths=[20000], demo_end_ms=40000)
    assert (unit.start_ms, unit.raw_end_ms, unit.media_end_ms, unit.end_reason) == (1000, 20000, 20750, "RECORDER_DEATH")

def test_survivor_uses_round_end_and_tail_clamps_before_next_countdown():
    unit = resolve_ca_unit(state(countdown=1000, fight=6000, end=27900, next_countdown=28000), deaths=[], demo_end_ms=40000)
    assert unit.media_end_ms == 28000

def test_missing_or_contradictory_edges_are_quarantined():
    assert resolve_ca_unit(uncertain_state, [], 40000).reject_reason == "ROUND_BOUNDARY_UNCERTAIN"
```

Also prove no next fight/spawn lies within the media unit, recorder death matches client slot, demo-end partial units are explicit, and IDs differ across gamestate/life while remaining stable across trait changes.

- [ ] **Step 5: Verify boundary tests are RED**

Run: `E:/PersonalAI/venv/Scripts/python.exe -m pytest creative_suite/tests/test_round_units_v2.py -v`

- [ ] **Step 6: Implement the V2 state machine and pure resolver**

Treat CS661 announcement/countdown and CS662 positive/negative fight state as separate edges. Never use a kill span as an automatic capture boundary. The unit start is the observed countdown edge, not `fight_start-5000` arithmetic. Create canonical IDs as SHA-256 over a canonical JSON array containing the five identity fields, prefixed `CA2:`.

- [ ] **Step 7: Materialize V2 units and events**

Persist all selected event IDs, times, weapons, trait evidence and recorder ownership under one unit. Store boundary status and evidence JSON. Exclude uncertain units from eligibility but retain their diagnostic rows.

- [ ] **Step 8: Verify GREEN and commit**

Run the new tests plus `creative_suite/tests/test_round_and_lineage.py` and `creative_suite/tests/test_round_context.py`. Commit with message `feat: derive authoritative round capture units`.

---

### Task 3: Strong-trait event scoring and weapon-local round scoring

**Files:**
- Create: `creative_suite/engine/round_scoring_v2.py`
- Create: `creative_suite/tests/test_round_scoring_v2.py`
- Create: `creative_suite/tests/test_ctf_instagib_gate_v2.py`
- Modify: `creative_suite/engine/mining_epoch.py`

**Interfaces:**
- Consumes: `CaptureUnit`, unit events, `CalibrationModel`, mode evidence and data-quality facts.
- Produces: `score_event(event, model) -> EventScore`, `score_ca_unit(unit, events, model) -> RoundScore`, `weapon_lane(event) -> str`, `assign_weapon_percentiles(scores) -> list[RoundScore]`, `score_ctf_instagib(sequence, model, threshold) -> CtfScore`.
- Persists `calibration_models_v2` and `round_scores_v2` with full canonical breakdown.

- [ ] **Step 1: Write failing tests for trait policy and correlation collapse**

```python
def test_strong_trait_leads_event_score():
    assert score_event(hero_event, model).trait_total > score_event(plain_event, model).trait_total

def test_support_trait_cannot_promote_plain_frag():
    assert score_ca_unit(unit, [support_only_event], model).editorial_role != "HERO_ROUND"

def test_retired_trait_contributes_zero():
    assert contribution(score_event(retired_event, model), "CHAT_REACTION_NEARBY") == 0

def test_ten_correlated_labels_are_one_moment():
    assert score_ca_unit(unit, correlated_same_event, model).distinct_moment_count == 1
```

The named break is weak or duplicated labels outranking an actual strong frag.

- [ ] **Step 2: Write failing tests for the round formula and weapon pools**

Use literal event totals 100, 80, 40 and 20. Assert the direct moment subtotal is `100 + 0.60*80 + 0.35*40 == 162`, with the fourth event excluded. Assert an exceptional grenade is ranked within the grenade pool and CA rail scores do not affect its percentile.

- [ ] **Step 3: Write failing CTF and exclusion tests**

Prove:

- Duel and TDM are hard-rejected before scoring.
- CTF plus rail-only evidence is rejected.
- positively identified Instagib plus recorder-owned exceptional multi-rail can become `CTF_INSTAGIB_HERO` above its mode-local threshold.
- CTF scores never enter CA weapon percentiles.

- [ ] **Step 4: Verify all scoring tests are RED**

Run both new test modules with `-v`; expected import failure is the missing scoring module.

- [ ] **Step 5: Implement explainable event scores**

Collapse traits by `(event_key, family)` and select the strongest calibrated contribution in each family. Return ordered contribution records containing `kind`, `name`, `value`, `evidence_key` and `provenance`. Missing evidence contributes zero. Hard rejections are separate fields, never large negative magic numbers.

- [ ] **Step 6: Implement hierarchical CA scoring**

Sort distinct moment totals, apply the exact top-three formula, then add bounded sequence, clutch/finish and editability contributions. Choose the primary weapon lane from the highest calibrated event; expose other lanes as facets. Compute percentiles by `(mode,weapon_lane,scorer_version)`.

- [ ] **Step 7: Implement the separate CTF Instagib gate**

Require positive Instagib configuration/mode evidence, recorder ownership, an exceptional allowlisted feature, usable context/audio and a mode-local threshold. Return only `CTF_INSTAGIB_HERO` or `REJECT`.

- [ ] **Step 8: Persist reproducible scoring records**

Store scorer version, calibration hash, raw score, lane, lane percentile, editorial role, hard-reject reason and canonical breakdown JSON. Do not mutate `recognized_frags.highlight_score`.

- [ ] **Step 9: Verify GREEN and commit**

Run both new tests and `creative_suite/tests/test_score_architecture.py`. Commit with message `feat: score calibrated round stories`.

---

### Task 4: Canonical one-video review projection and Calibration V2 package

**Files:**
- Modify: `creative_suite/engine/review_corpus.py`
- Create: `creative_suite/engine/calibration_review_v2.py`
- Modify: `creative_suite/engine/review_proxy.py`
- Create: `creative_suite/tests/test_round_review_identity_v2.py`
- Create: `creative_suite/tests/test_calibration_review_v2.py`
- Modify: `creative_suite/tests/test_review_proxy_backend.py`
- Create at runtime only: `output/demo_v2/calibration_v2/index.html`
- Create at runtime only: `output/demo_v2/calibration_v2/review_manifest.json`

**Interfaces:**
- Consumes: eligible scored V2 units and their complete event/trait bundles.
- Produces: `round_v2_queue(filters, ...)`, `build_calibration_review_v2(...)`, `request_unit_proxy(unit, ...)`.
- Review `item_id` equals canonical unit ID; all virtual lanes resolve to that same ID.

- [ ] **Step 1: Write failing canonical review tests**

Create one unit with ten traits and three weapon facets. Query by two traits and two weapon lanes. Assert all results share one item ID, one proxy key and one human verdict. Add a second life and second gamestate with the same round number and assert neither collides.

- [ ] **Step 2: Write failing proxy-bound tests**

Assert `request_unit_proxy()` uses the exact pre-resolved unit bounds, includes boundary/parser/scorer version in its cache key, preserves the 750 ms tail, and refuses `ROUND_BOUNDARY_UNCERTAIN`. It must not call the legacy per-frag `capture_window()`.

- [ ] **Step 3: Verify RED**

Run the three named test files with `-v`; expected failures are missing V2 queue/package/proxy interfaces.

- [ ] **Step 4: Implement unit-level queueing**

Read materialized V2 units rather than grouping filtered frag rows. Apply gametype eligibility before weapon/trait filters. Filters select virtual views without changing the unit representative, score, bounds or verdict key. Return the complete ordered event/trait evidence bundle.

- [ ] **Step 5: Implement exact-bound V2 proxies**

Add a separate V2 proxy record keyed by canonical unit, source hash, exact bounds, capture profile and dependency versions. Preserve legacy frag proxies. Refuse uncertain/unapproved units before queue submission.

- [ ] **Step 6: Generate the information-gain Calibration V2 package**

Select globally unique units for top, boundary and known-false-positive examples per hero family and weapon. Include purposeful filler/transition examples. CTF Instagib appears in its own section. HTML cards show one video, all traits, weapon lanes, score breakdown and shared verdict state; dynamic user-derived strings use escaped text or DOM `textContent`.

- [ ] **Step 7: Verify GREEN and commit**

Run the new tests plus `creative_suite/tests/test_round_review_queue.py`, `test_review_stability.py`, and `test_review_media_lifecycle.py`. Commit with message `feat: review one canonical round once`.

---

### Task 5: Immutable prepare-only extraction manifest and hard gates

**Files:**
- Create: `creative_suite/engine/extraction_manifest_v2.py`
- Create: `creative_suite/tests/test_extraction_manifest_v2.py`
- Create: `creative_suite/tests/test_public_manifest_privacy_v2.py`
- Modify: `creative_suite/engine/capture_batch_run.py`
- Create at runtime only: `output/demo_v2/extraction_v2/manifest.json`
- Create at runtime only: `output/demo_v2/extraction_v2/manifest_summary.json`

**Interfaces:**
- Consumes: approved calibration hash, eligible scored units, exact bounds, source resolver and dependency versions.
- Produces: `prepare_manifest(units, approval, versions) -> ExtractionManifest`, `validate_manifest(manifest) -> list[GateFailure]`, `write_manifest_immutable(manifest, output_dir) -> Path`.
- Capture runner requires explicit `--manifest PATH --approved-hash SHA256`; no-argument invocation refuses V2 capture.

- [ ] **Step 1: Write failing gate and immutability tests**

Assert publication fails for excluded modes, non-hero CTF, unknown recorder, uncertain/cross-round boundary, next countdown inside the interval, duplicate unit IDs, missing time-conversion provenance, stale dependency versions, incomplete score breakdown and any public identifying/path field. Assert identical inputs produce byte-identical JSON and hash; changing an existing file is refused rather than overwritten.

- [ ] **Step 2: Write failing prepare-only capture tests**

Run the CLI handler against a synthetic approved manifest and a fake queue. Assert manifest preparation causes zero queue calls. Assert V2 capture without both explicit manifest and matching approval hash exits nonzero. Assert a matching approved manifest submits units through the existing single-worker interface in manifest order.

- [ ] **Step 3: Verify RED**

Run the two new test files and targeted capture-batch test with `-v`.

- [ ] **Step 4: Implement canonical private and public manifest views**

Keep source path/demo name in a local private resolver record. Public canonical rows contain unit ID, content hash, client slot, mode evidence, gamestate/round/life, bounds, anchors, offsets, weapons, trait evidence, score breakdown, role and dependency versions. Reject forbidden key names recursively.

- [ ] **Step 5: Implement immutable publication and approval hash**

Write canonical sorted JSON with a SHA-256 content hash. Use exclusive creation and refuse replacement. Record the approved calibration hash and manifest hash separately. Validation returns all failures without partially publishing.

- [ ] **Step 6: Put the hard gate in front of capture**

Require explicit V2 manifest path and exact approved hash. Validate every row again before queueing. Preserve current cancellation, cfg-injection and single-worker behavior. Do not change legacy capture commands unless necessary to prevent accidental V2 no-argument capture.

- [ ] **Step 7: Verify GREEN and commit**

Run new tests plus `creative_suite/tests/test_capture_guard.py`, `test_capture_truncation.py`, and `test_review_capture_determinism.py`. Commit with message `feat: gate round extraction manifests`.

---

### Task 6: Corpus dry run, Calibration V2 delivery and extraction-job preparation

**Files:**
- Modify only if verification exposes a defect: modules and tests from Tasks 1-5
- Create at runtime only: `output/demo_v2/calibration_v2/*`
- Create at runtime only: `output/demo_v2/extraction_v2/*`
- Create: `docs/reference/2026-09-10-round-first-v2-validation.md`
- Create: `docs/visual-record/2026-09-10/calibration_v2_review.png`
- Create: `docs/visual-record/2026-09-10/extraction_v2_summary.png`

**Interfaces:**
- Consumes: live read-only corpus databases and Calibration V1 input.
- Produces: Calibration V2 review package, validated prepare-only extraction manifest, aggregate validation report and screenshots. Produces no captured video.

- [ ] **Step 1: Run the pipeline in prepare-only mode**

Generate the calibration model, CA units, scores, Calibration V2 package and extraction manifest. Record counts at each gate: source demos, mode-eligible demos, authoritative rounds, recorder-life units, quarantined bounds, strong-trait units, editorial roles, deduplicated review units and manifest rows.

- [ ] **Step 2: Audit strong-trait scoring**

For each hero family and weapon lane, inspect top, threshold-boundary and false-positive examples. Confirm supporting/retired traits cannot independently create a hero and correlated labels do not multiply a single moment.

- [ ] **Step 3: Audit round boundaries without batch capture**

Select a stratified boundary sample covering recorder death, survivor round end, short round, last round, map restart and next-countdown proximity. Compare stored anchors and ensure every interval excludes the next round. Quarantine mismatches rather than widening windows.

- [ ] **Step 4: Verify CTF Instagib isolation**

Report positive Instagib evidence, exceptional feature and mode-local score for every accepted CTF row. Confirm zero Duel/TDM rows and zero ordinary CTF rails in the manifest.

- [ ] **Step 5: Capture the required visual records**

Use the existing Playwright runtime without installing packages. Screenshot the Calibration V2 summary and extraction-manifest gate report into the named visual-record paths.

- [ ] **Step 6: Run final verification**

Run all new tests, relevant existing round/review/capture tests, and the repository's resolved pyright executable over changed Python files. Require a complete test summary, no traceback/failure marker and clean `git diff --check`.

- [ ] **Step 7: Document measured results and commit**

Write only aggregate/anonymized counts and validation findings. Link private runtime artifacts by local path without committing them. Commit with message `docs: validate round-first mining v2`.

---

## Final Review and Handoff

- [ ] Generate one full branch review package from the merge base through HEAD.
- [ ] Run the required final code review and resolve all Critical/Important findings.
- [ ] Run `superpowers:verification-before-completion` against fresh test and pyright output.
- [ ] Run `superpowers:finishing-a-development-branch` and present integration options.
- [ ] Do not merge or push to a protected branch.
- [ ] Present Calibration V2 to the user before any full Wolfcam extraction batch.
