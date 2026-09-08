# Demo mining audit — 2026-09-08

The concern is justified: established Quake tooling supports substantially more reliable baseline mining than the current fragmented extraction approach. The priority is a validated decoded-state foundation, followed by broad reusable feature extraction. Increasing score coverage alone will not fix the correctness issues below.

Scope: attached status report, root checkout `demo-v2-mining` at `c563fda9`, relevant code in `.claude/worktrees/pantheon-headless`, local run logs and read-only database queries, and upstream primary sources. No demo extraction, capture batch, production-code modification, commit, or publication was performed. Counts are observations of stored data, not an accuracy certification. Working copies and databases may continue changing.

## Claim-by-claim review

| Attached statement | Verdict and evidence |
|---|---|
| 36,607 frags | Confirmed in `frag_recognition.db.recognized_frags`. These are recognition rows for recorder frags, not necessarily every death in every recording. |
| Health reached 11.1% | Confirmed: 4,051 of 36,607 rows contain `attributes.health_at_frag`, or 11.066%. This measures non-null coverage, not correctness. |
| 45.3% is the health ceiling | Incorrect interpretation. The extractor comment describes measured coverage in a widened processed subset. It does not establish a mathematical or protocol limit. |
| 11.1% is near the design ceiling | Describes saturation of the current restrictive selection, not all recoverable health. Current candidate query finds 4,017 eligible rows, only four missing HP. Previously enriched rows outside that selection explain why total HP rows exceed current candidates. |
| Candidates are CA clutches or MAIN_CA score >=10 | Supported by `extract_health_armor.py` candidate query. This is application policy. Basic telemetry need not be selected by an editorial score. |
| 605 candidate demos versus 2,844 | Historical 605 not independently reproduced. Current recognition metadata contains 2,844 v2 demos; health metadata records 607 successful v3 demos. Different stages count different populations. |
| Rescan wiped attributes while health completion stayed marked | Supported failure mechanism: recognition `store()` deletes and reinserts frag rows and their attribute JSON; health has a separate versioned completion table. Stable completion metadata can survive loss of the actual enrichment. |
| Bumped extractor to v3 and fixed script imports | Supported in the `pantheon-headless` worktree: repository path setup, store import and version 3 are present. Root checkout still has version 2. Reviewing only the root would wrongly reject this claim. The version bump is a recovery measure, not dependency invalidation. |
| 1,700 health events updated, zero failures | Close to persistent current metadata: successful v3 rows total 1,702 events across 607 demos. The exact historical terminal result was not preserved in an independently verified artifact. Successful execution does not validate health semantics. |
| Prefer health-bearing exemplars; 62/107 cards; 21/71 score >=10; median 5 | Historical picker/card statistics not independently reproduced. Do not present them as verified current results. Selection preference can improve displayed completeness but also bias examples toward already processed data. |
| Lower MIN_SCORE to get missing health | Partly correct: it broadens the high-score candidate branch, subject to the remaining group restrictions and actual observation availability. It cannot guarantee HP on every card. The advertised `--all` flag sets `ALL_FRAGS`, but the reviewed candidate query does not use it. |
| Rescan processed 2,592 existing demos, added none | Log confirms 2,592 scheduled, not a fresh inventory audit. Its adjacent numbers do not reconcile: 2,810 size-eligible minus 252 already processed is 2,558. No before/after source-hash inventory established “nothing new to add.” |
| 16 shapes and 56,834 detections | Confirmed stored totals, across 3,257 hashes. Neither count measures precision or recall. Multiple shapes can refer to one action. |
| 48,989 fight rounds | Confirmed in `match_format_v1`, across 4,107 hashes. This is a derived table count. |
| 42,926 outcomes, 91.3% with a winner | Confirmed: 39,200 non-null winners / 42,926 = 91.318%, across 4,207 hashes. Winner availability is not winner accuracy. |
| Shapes, rosters and outcomes key on hash + time, so all are current | Partly wrong. Shapes include hash/time/shape/actor/victim; rosters and outcomes use hash plus round identity. These avoid frag-ID churn, but stable keys do not validate freshness, round semantics or upstream parser versions. Shapes read a separate `kill_events_v1` source. |
| 71 current traits; 20 doubts | The attached counts and question set were not independently reproduced as a frozen review manifest. Taxonomy breadth does not establish detector validity. |
| 16 shapes need a per-player velocity extractor that does not exist | Too broad. The parser already exports entity and playerstate velocity fields and the recognizer consumes them. A reliable persisted trajectory dataset or particular shape detector may still be absent; that is different from unavailable format knowledge. Exact availability remains observation-dependent. |
| All three scripts use 5s/5s | Not established for the unnamed scripts. Worktree public export uses 5/5; other reviewed paths use 5/3, 4/3 or 3/3. The window is not a universal shared contract. |
| 49 clips queued, about 100 minutes | Log confirms queued 49. Only six READY records were present in the reviewed log. Neither completion, runtime estimate nor frame alignment is proven. |
| 97.8% exact timestamp agreement across independent extractions | No supporting comparison artifact located. The population, matching keys, independence and remaining 2.2% are unestablished. Even genuine agreement on server time does not validate game-clock conversion or captured video placement. |
| Therefore excess lead-in must be Wolfcam capture error | Unsupported root-cause conclusion. Time-domain conversion, chosen event, round/gamestate context, seek settling and first captured frame all need checking. |

## Correctness findings that matter before wider mining

### 1. Snapshot reference reconstruction — high priority

Root `engine/parser/demo_parse.py:555` reads the message sequence, but dispatch does not receive it. At line 784, the snapshot delta distance is used only to distinguish zero from nonzero. Entity and playerstate fields are merged into the latest accumulated state.

Wolfcam selects the specific historical snapshot at `messageNum - deltaNum`, then decodes both state streams against it. These are not equivalent: a value changed in an intervening snapshot must revert to the older reference value when omitted from a later delta against that older reference. The reviewed worktree retains the same approach.

The structural defect is confirmed by source comparison. How many actual corpus rows it affects remains unmeasured; this review does not claim the whole corpus is corrupt. Zero decoder exceptions cannot establish semantic correctness.

Sources: [Wolfcam snapshot reconstruction](https://github.com/brugal/wolfcamql/blob/master/code/client/cl_parse.c#L410), [original id Software implementation](https://github.com/id-Software/Quake-III-Arena/blob/master/code/client/cl_parse.c).

### 2. Changed-entity rows are not complete snapshots

At `demo_parse.py:849`, unchanged deltas are skipped; entity rows are appended only for encountered changed entities. The comment promising every player each snapshot overstates the export. Downstream `frag_recognition.py` explicitly acknowledges that gaps may mean no state change or no visibility.

Reconstruct the active entity set first, including unchanged states, and represent actual disappearance separately. Preserve trajectory type, reference time, sample time and discontinuities. A baseline definition is also not proof that an entity is active; the parser's full-update initialization currently conflates those concepts internally.

### 3. Health fields require identity, signedness and age checks

`extract_health_armor.py` takes the latest earlier snapshot up to ten seconds old, discarding its client and round identity. A decoded health number can therefore belong to a followed player after a POV switch or a different round context. Store source client, sample time, age and observation method with every derived value.

Current HP values range from 0 to 65,535, with 11 nonpositive and 23 above 200. Values above 200 are not automatically impossible in every game context, but 65,535 requires signedness/sentinel validation: the Python `readshort()` returns unsigned values whereas the engine's short decoder sign-extends. The worktree retains unsigned decoding. This is especially relevant to negative death health and apparent health recovery.

POV playerstate has health/armor; ordinary entitystate does not universally carry exact health for every player. Teammate status commands or pain events can provide additional evidence where recorded, with different freshness and coverage. [Wolfcam health fallback documentation](https://github.com/brugal/wolfcamql/blob/master/README-wolfcam.txt).

### 4. Weapon constants disagree across layers

`frag_classify.py:49` declares gauntlet=1, machinegun=2, shotgun=3. The correct order is shotgun=1, gauntlet=2, machinegun=3, already used by `demo_parse.py`. This is not just a misleading comment: `frag_recognition.py:59` imports `W_SHOTGUN` and line 768 uses it to gate reaction candidates, admitting MOD 3 and excluding MOD 1 from the shotgun side of that condition. The affected corpus count was not measured.

Use one protocol-aware constants source. [Wolfcam means-of-death enum](https://github.com/brugal/wolfcamql/blob/master/code/game/bg_public.h#L1214).

### 5. Extraction is repeatedly parsing and selectively persisting

Health, aim, view time series, projectiles, dodge, LG and semantic-event jobs each invoke `DM73Parser`. The expensive decoding is reused as code, but decoded facts are not consistently reused as data. Independent resume flags and wholesale attribute replacement create the reported loss/recovery cycle.

The score >=10 gate also creates a feedback loop: a candidate may need health evidence to earn a context score, yet fail the score needed to request health. Choosing different exemplars conceals missing telemetry instead of recovering it for the examples under review.

## What established tools already provide

UberDemoTools supports dm_73, frag sequences, mid-air rocket/BFG frags, multi-frag rails and flick rails. Its custom parsing API exposes decoded snapshots, player/entity state, changed/removed entities, commands and protocol-aware constants. It can serve as a competing decoder or independent validation reference while Python retains the project's taxonomy, scoring and review workflow. These are existing capabilities, not a proposed AI invention. [UDT project](https://github.com/mightycow/uberdemotools), [custom parsing API](https://github.com/mightycow/uberdemotools/blob/develop/CUSTOM_PARSING.md).

The configured root `creative_suite/tools/uberdemotools` directory contains a README, not the advertised executable. This does not establish that UDT is absent everywhere on the machine; resolve actual available binaries before planning integration. Benchmark on identical approved fixtures before making speed claims.

Known source code provides the mechanics, but it cannot recreate observations never recorded. Snapshot visibility filtering means a known obituary need not come with a complete victim or projectile trajectory. Multiple genuine recordings of the same match can improve coverage when correctly aligned. Inferred movement and cinematic reconstruction must remain separate from measured facts. [Snapshot visibility](https://github.com/id-Software/Quake-III-Arena/blob/master/code/server/sv_snapshot.c), [broadcast obituary creation](https://github.com/id-Software/Quake-III-Arena/blob/master/code/game/g_combat.c).

Player velocity fields are established, but trajectory semantics matter. A trajectory helper can return zero for interpolation even when trDelta was populated; validate protocol semantics instead of blindly substituting one helper. Estimated velocity from observed positions requires visibility-gap and teleport guards. [Trajectory and playerstate conversion](https://github.com/id-Software/Quake-III-Arena/blob/master/code/game/bg_misc.c).

UDT uses server time. Wolfcam `seekclock` uses game clock. An explicit conversion and captured-frame anchor are essential. [UDT time formats](https://github.com/mightycow/uberdemotools#time-formats), [Wolfcam seeking](https://github.com/brugal/wolfcamql/blob/master/README-wolfcam.txt).

## Recommended order

1. Certify a small approved stratified sample against UDT/Wolfcam: obituary identity/weapon/time, full snapshot reference handling, signed health, round identity and movement. Include older recordings, POV changes, visibility gaps, teleports and nonadjacent delta references. Report disagreements, not just agreement percentage.
2. Resolve the confirmed parser and constant defects before expanding derived classifications. Measure impact and invalidate affected derivatives by dependency version rather than manually bumping unrelated completion flags.
3. Build one reusable decoded evidence layer keyed by demo hash, gamestate/segment, server time, subject and event identity. Preserve all supported events, commands and observable state once. Keep protocol facts separate from derived editorial attributes.
4. Derive health, movement, air time, direct/splash status, weapon chains, multikills and CA clutch context for all eligible observed frags without score-gating inexpensive telemetry. Apply creative ranking afterwards. Keep missing, stale, inferred and exact values distinct.
5. Freeze review exemplars and attach missing evidence to those same events. Report totals, selected candidates, processed cases, successful observations and independently validated accuracy as separate denominators.
6. Validate one 5/5 capture using the actual first video frame and obituary anchor before a batch. Consolidate the capture-window contract, including multi-kill and clutch context.

This is a review and proposed sequence, not an implementation or a request to approve a batch. The practical upgrade is broader, reusable deterministic extraction with stronger provenance, while the creative scoring remains yours to define and validate.
