# Checker refresh — current Claude handoffs

Read-only review, 2026-09-05. This supersedes project-wide absence claims in the earlier audit: the intro implementation also lives in `.claude/worktrees/pantheon-prologue`. Earlier test totals predate this work and do not certify it.

## Confirmed coverage records

Read-only SQLite queries against `creative_suite/database/mining_epoch.db` found:

- Inventory: 4,292 distinct hashes, 6,445 copies, zero entries marked new.
- Actions: 77,951 rows; 4,292 run records, zero recorded errors, version `action-moments-v1.0.0`.
- Aim: 1,292,062 rows; 4,292 run records, zero recorded errors, version `aim-events-v1.0.0`.
- Promotion stage records both tables as PROMOTED.

These corroborate the saved inventory and completion claims. This checker did not independently rehash the corpus or establish that every extracted event is correctly attributed.

## Immediate findings

1. **CORRECTNESS BUG — changed historical identity passes migration.** `creative_suite/engine/human_migration.py:143` labels a different fingerprint at the same ID `CHANGED_ID_SAME_EVENT`; that status is absent from BLOCKING. A disposable before/after SQLite fixture with `kill-A` becoming `kill-B` returned `blocked: false`. Reject changed fingerprints; only a separately proven identity mapping can establish the same event at another ID. Comparing the live database with itself cannot prove preservation against an earlier state. `production_usage` is also absent from the protected target enumeration.

2. **CORRECTNESS BUG — promotion renumbers action review targets.** `creative_suite/engine/mining_epoch.py:256` removes action/aim IDs from INSERT; line 273 deletes existing rows without preserving identity. Disposable fixture: promoting the same source action twice assigned destination IDs 1 then 2. `review_corpus.py:1703` uses that ID in the public ACTION review key. Preserve stable semantic keys and existing human bindings across repeat promotion. Promotion also commits each table separately, without invoking the human migration guard; the function does not implement the module's advertised atomic epoch contract.

3. **CORRECTNESS BUG — ACTION dossier crosses into kill identity.** `_action_item` uses action ID as `source_id`, while `action_truth.for_item` treats `source_id` as a kill occurrence ID without checking item type. The dossier endpoint calls this path. An action and unrelated kill sharing the same integer can be confused. Dispatch explicitly by namespace; an unsupported action dossier must remain unavailable rather than return kill truth.

4. **CORRECTNESS BUG — test isolation can select the live database.** `scripts/review_test_instance.py:41` accepts any `--db`; `assert_isolated` only verifies modules equal that supplied path. Reject the resolved live path and aliases before opening it. Lines 49–53 separately copy a potentially changing SQLite database, WAL and SHM; use a consistent SQLite backup instead. The expanded module list is useful but cannot itself prove complete isolation.

5. **FALSELY CLAIMED / NOT PROVEN — HIGH action confidence is not hit attribution.** In `engine/parser/mine_action_moments.py`, missing recorder team falls back to treating other clients as enemies despite the opposite comment. Shot share does not establish who caused pain, and linking only recorder kills does not prove nobody died. Keep observed activity separate from inferred ownership and no-kill semantics. Population percentiles calibrate rarity, not semantic accuracy.

6. **CORRECTNESS BUG — pass acceptance does not ensure that pass renders.** The prologue worktree contains executable ShotSpec and synthetic FrameTruth code. Its ShotSpec renderer checks pass support but does not consistently translate requested pass kinds into capture commands and output collection. A requested depth or actor-XRAY pass must either produce the corresponding verified artifact or fail explicitly; a beauty AVI cannot satisfy it.

## Intro evidence correction

The separate prologue worktree contains `engine/pantheon/shot.py`, `frame_truth.py`, presenter/instruction modules, roster code, and native proof media. The earlier claim that these are absent project-wide is withdrawn. Proof B and existing presenter experiments do not establish completion of the newest separate-presenter Proof C contract. That requires preserving historical actors while a distinct presenter moves through edit time, plus validated cast pixels and output provenance.

## Next implementation brief

Reviewer session: fix findings 1–4 first, using disposable databases and a repeat-promotion identity test. Then correct ACTION attribution and aim-observation semantics; retain existing extraction results as candidates until validated. Do not reparse the corpus solely to fix these derived-layer issues. Reconcile existing human records against a preserved snapshot without automatically deleting or remapping them.

PANTHEON PROLOGUE INTRODUCTION: continue the already-scoped cast sheet and Proof C. Close pass-intent/output mismatches before claiming rendered passes. Supply artifact paths, effective engine settings and historical-state comparisons; keep presenter truth explicitly separate. No new architecture expansion is needed to make those claims reviewable.

No production tables, human records, captures, or implementation files were changed by this refresh. See the refreshed Astra truth and render reports for further source detail.
