# Astra audit: game truth, scene identity and directing intent

Audit date: 2026-09-05. Source baseline: checkout whose latest commit is `bb23f2d4`, including existing working changes. Scope: parser semantics and proof, ActionTruth, Scene, production contract, annotations, choreography and local synthetic-demo evidence. No implementation was changed; no production database was opened, capture launched, dependency installed or production test run. One pure in-memory contract probe was executed with Python bytecode writes disabled. This report is the only audit artifact written by this reviewer.

The central problem is that sharing an object is being treated as proof that the object is true. The dossier adapter does share ActionTruth, which is useful. The executable boundary still admits uncertain facts, loses real annotations, and does not feed a ChoreographyPlan. These gaps should be falsified with small isolated fixtures before additional render backends are built.

## 1. CORRECTNESS BUG — persisted event direction never enters the live bridge

**Evidence.** `/scene_note` persists notes in `scene_event_notes` at `creative_suite/api/review.py:724`; its reader is at line 703. A source search finds that table only in those API handlers. `SceneEvent.annotation` defaults to an empty string at `creative_suite/engine/scene.py:89`. `build_scene()` creates movement events without annotations at line 215 and merges verdict metadata at lines 235–239 without copying even the frag review's `note`. `production_contract.input_for_item()` builds that Scene at line 509; `choreography_input()` copies only its existing event annotation at lines 480–484.

The advertised proof bypasses the missing adapter: `creative_suite/tests/test_production_contract.py:45` and line 48 construct already-annotated SceneEvents in memory. The purported end-to-end test at line 247 calls the converter directly, never either persistence API or `input_for_item()`. Consequently the test can pass while both jump-pad and frag directing notes disappear on the real path.

**Consequence.** The director can save “music buildup here” successfully and the planning input receives no instruction. This is a source-traced defect, not a measured claim about existing production notes.

**Smallest proof.** In isolated stores, persist one frag note and one movement note through the real save path, then resolve the same item through `input_for_item()`. Require byte-identical text and event IDs. Also require a machine-provenance event note to be withheld: unlike round notes, the current event conversion has no provenance check (`production_contract.py:475` versus line 480), and `SceneEvent` does not retain note provenance.

## 2. CORRECTNESS BUG — simultaneous kills can borrow another occurrence's metrics

**Evidence.** `creative_suite/engine/action_truth.py:218` resolves a canonical occurrence and its best observation. Its recognition lookup at lines 227–231 then discards occurrence identity and selects `recognized_frags` using only `content_hash`, `server_time_ms`, and `LIMIT 1`. It does not constrain victim, weapon or actor. The same module states that canonical identity is the occurrence ID at lines 202–204. The recorder-only scope of `recognized_frags` is documented at `engine/parser/derive_kill_events.py:3`–7.

The selected attributes supply stack, damage, geometry, movement and traits (`action_truth.py:271`, line 277, line 284 and line 289). Stack is protected by the actor-POV flag; damage, geometry and movement are not protected by a matching occurrence assertion.

**Consequence.** Two kills on one server tick can receive the first matching row's victim geometry or weapon metrics. A foreign actor's kill on the same tick as the recorder's kill can inherit recorder-kill attributes even though its own stack is correctly withheld. `dossier == action_truth` still passes because both expose the same mistaken association (`creative_suite/tests/test_dossier.py:95`–101).

**Smallest proof.** Insert two anonymized same-demo, same-time occurrences with different victims and visibly different geometry, plus the recorder's recognition row. Resolve both and require exact metric ownership or UNKNOWN. Reverse recognition insertion order; neither result may change. This is a statically identified join ambiguity; its frequency in the private corpus was not measured.

## 3. ARCHITECTURAL BLOCKER — provenance class is being used as a factual eligibility gate

**Evidence.** `production_contract.py:55` permits both OBSERVED and DERIVED to support on-screen factual claims. `provenance_of()` at lines 214–215 checks only `value is not None`; `is_factual()` at lines 218–220 never checks confidence, coverage, ambiguity or the assumption behind a derivation. The dictionary classifies `round.alive_curve` DERIVED (line 145), `action.accuracy_pct` DERIVED (line 109), and `movement.victim_air_height` OBSERVED (line 129).

Air height actually comes from `z - recent_floor`, not an observed height-above-current-ground field (`engine/parser/frag_recognition.py:275`–278). A recent floor can be the wrong reference over a ledge. That distinction is erased by the contract table.

**Executed proof, no databases.** Calling the existing contract functions on in-memory inputs produced:

```text
event.weapon='UNKNOWN'                     OBSERVED  factual=True
round.alive_curve=[]                        DERIVED   factual=True
action.accuracy_pct=66.7, confidence=AMBIGUOUS DERIVED   factual=True
```

These results do not demonstrate a shipped false title; no production consumer of this contract was found. They demonstrate that the proposed protective gate does not enforce the stated uncertainty policy. UNKNOWN string values already exist in the game-domain vocabulary; requiring None only is not a complete domain boundary.

**Smallest proof.** Build a table of permitted claim types with unavailable, ambiguous, partial-observation and assumption-violating fixtures. Require claim eligibility to reject each while still allowing an explicit lower bound or hypothesis to be displayed as such. Provenance, value availability and permission to assert a particular claim need separate checks.

## 4. DUPLICATED AUTHORITY — two round models disagree about boundaries and evidence

**Evidence.** ActionTruth takes its round from `round_story.round_context()` (`action_truth.py:241`). That path uses the first and last observed kill as `start_ms` and `end_ms` (`round_story.py:150`–151, line 229), uses whole-demo `player_teams_v1` for team sizes (line 138, lines 185–190), and subtracts observed deaths (lines 200–210). There is no game-mode check or measured completeness predicate before producing the alive curve. `event.time_in_round_ms` then subtracts this first-kill time (`action_truth.py:255`), although its field name implies round-clock time. Its first kill is always time zero, even if the round began much earlier.

A separate `creative_suite/engine/round_context.py:182` computes a RoundContext from round outcomes, team changes and round-state configstrings (lines 188–200); it has explicit victory gates at lines 125–142. The two models do not share a round identity/boundary resolver, and the latter builder has only test call sites in the searched Python tree.

Scene independently repeats first/last-kill grouping (`scene.py:161`–177). Its query accepts an occurrence only when that occurrence's globally selected best observation belongs to the chosen demo. Thus changing which observation is considered best can remove a real event from this demo's scene, even when this demo observed it. A canonical occurrence identity is not the same thing as an observation-membership relation.

**Consequence.** “Round duration,” round-clock offsets, starting team counts and scene completeness are not governed by one authority. The comment that alive counts are DERIVED does not make an unverified one-life/complete-roster assumption safe for factual clutch graphics.

**Smallest proof.** Use one round whose first kill occurs 20 seconds after its round-start configstring, one client who changes team, and an occurrence with observations in two demos. Require the review and production round IDs/times/counts to agree; changing the preferred observation must not change scene membership. Do not merge the models by name alone: preserve the stronger outcome and team-timeline evidence.

## 5. CORRECTNESS BUG — slow-weapon “confirmed accuracy” is not shot attribution

**Evidence.** `action_stats.py:152` counts recorder shots of the obituary weapon. Lines 161–165 count all pain on the victim in the entire window, without relating a pain event to a particular shot or weapon. Lines 169–174 only test whether any other entity fired in the window. With no such event, lines 225–231 report the capped pain count as confirmed hits with HIGH confidence and the statement that only the user was firing at this target. No target trace or per-shot matching supports that sentence.

For example, the recorder can damage the victim with another weapon, switch to rail, miss once and then kill once. Earlier victim pain is included in the rail numerator; two pain events plus two rail shots report 100% with HIGH confidence although only one rail shot hit. Pain throttling and partial observation can also suppress counts. Restricting weapon fire rate does not establish attribution or observation completeness.

**Proof weakness.** `test_dossier.py:25` asserts the allowable weapon set; the killing-hit test at lines 29–34 searches for a source-code substring. Neither falsifies wrong weapon attribution. Sharing the result with the production contract simply promotes the same error into DERIVED factual data.

**Smallest proof.** Feed an isolated semantic-event ledger containing earlier machinegun pain, one missed rail and one lethal rail; expect at most the obituary-confirmed lower bound unless extra hit attribution evidence exists. Add a missing-pain case. Test shot-to-hit evidence, not membership in `ATTRIBUTABLE`. No real accuracy percentages were audited here.

## 6. MISSING CAPABILITY — ChoreographyInput is a partial adapter, not a consumed planning boundary

**Evidence.** `production_contract.input_for_item()` at line 513 passes exactly `[truth]`, although ChoreographyInput promises one classified reference per scene occurrence at lines 423–428. A four-frag scene therefore gets one ActionTruthRef. Tests explicitly construct this incomplete shape and only assert that occurrence 101 resolves (`test_production_contract.py:321`–328); they never require every scene occurrence to resolve.

A repository Python-reference search found no production caller of `production_contract`, `ChoreographyInput`, `choreography_input` or `input_for_item` outside the contract itself. `ChoreographyPlan` exists (`choreography.py:183`) but carries slot timing and elements; there is no located function translating this input into a plan and preserving evidence/note references. The bridge's own source rightly says it does not plan (`production_contract.py:430`–434). That separation is sound; the missing next adapter is material.

**Consequence.** The wording “ChoreographyPlan consumes all three” in `docs/reference/pantheon_capabilities.md:42`–43 is not supported by a wired production path. The narrower statement that an in-memory conversion API exists is supported.

**Smallest proof.** A single four-frag scene, one movement event and one human note must resolve all occurrence references and produce a deterministic plan with an explicit disposition for each instruction: applied, unsupported, or awaiting a creative decision. The proof can stop at plan serialization; it does not require a renderer or a full batch.

## 7. FALSELY CLAIMED OR NOT PROVEN — the scoreboard oracle cannot establish detector recall

**Evidence.** `engine/parser/score_oracle.py:90` obtains both scoreboard data and obituaries through `DM73Parser`. Its matching loop at lines 98–102 matches each scoreboard update to the nearest obituary of any client and does not consume the matched obituary. It ignores the delta's magnitude, killer identity and victim. Lines 135–137 nevertheless print “implied detector recall.” `protocol_profiles.py:168`–170 cites this as 100% recall corroboration.

One surviving obituary can satisfy several nearby increments. A score jump of three counts as one match. Shared packet-dispatch omissions can affect both streams. The scoreboard itself is useful corroborating evidence, and the oracle's header appropriately warns that CA score need not equal frags (lines 17–19); its printed recall percentage exceeds what its executable matching proves.

Parser field tables are additionally duplicated in `demo_parse.py:475`–482 and `protocol_profiles.py:90`–110; event IDs are independently restated at `demo_parse.py:56`–90. They appear consistent in the inspected portions. This is a drift risk, not evidence that the current protocol is wrong. `engine/parser/tests/test_demo_parse_events.py:7`–12 checks local tables and a source substring; it is not independent byte-level decoding evidence.

**Smallest proof.** Run the oracle logic against a synthetic scoreboard update with delta three and only one nearby obituary: a recall claim must fail. Then use a tiny externally decoded, anonymized fixture set, checking exact event tuples and missing/extra events, not plausible totals. Keep slot-zero, toggle-bit masking, multiple service messages per packet, and same-tick kills in that set. A compiler/parser round trip sharing constants is useful serialization coverage but cannot certify game semantics by itself.

## Synthetic compiler: scoped absence, not a universal nonexistence claim

`RoundScenario`, a compiler for it, and `ca_explainer_v1.dm_73` were not found in the searched local source/output filenames or source-text references beyond documentation. Two local image artifacts exist: `docs/visual-record/2026-09-05/synthetic_demo_static_camera_0ups.jpg` and `synthetic_demo_playback_proof_01.png`. Their existence does not identify the compiler source or make its implementation auditable here. The “synthetic demo builder” in `engine/parser/tests/test_extract_dodge_events.py:63` creates Python dictionaries of decoded snapshots; it does not emit dm_73 bytes.

Classification: **FALSELY CLAIMED OR NOT PROVEN** for any assertion that this checkout contains an audited synthetic compiler. Another session or checkout may contain it. The smallest next proof is a source-directory/commit handoff, generated demo digest and exact invocation. Then audit the authoring schema separately from protocol encoding and compare decoded event tuples against an independently specified scenario. Do not create a replacement compiler before locating that work.

## What is supported, and what can wait

The dossier really is a thin adapter (`dossier.py:19`–21). Missing stack is explicitly withheld and foreign-camera health is not relabelled (`action_truth.py:68`–76). Round victory gating rejects UNKNOWN in the separate round-context module (`round_context.py:125`–130). These are valuable foundations, not end-to-end truth proof.

Broader backend work and cosmetic schema cleanup are **SAFE TO DEFER** until findings 1–7 have discriminating proofs. Do not respond by building a second truth model. Resolve canonical occurrence-to-observation membership, temporal round identity, uncertainty and note provenance inside the existing boundaries first. The runtime probe here proves only the contract behavior stated above; all other findings are source traces or proposed falsifications, not newly measured production failures.
