# Project review — 2026-09-05

## Evidence and scope

Reviewed this working checkout, recent commits through `bb23f2d4`, local memory,
the supplied research text, application/export code, and tests. The ChatGPT
share URL timed out; the supplied text is an excerpt, so this is not a claim
to have read the entire shared conversation. Existing edits were preserved.

The frozen V1 manifest is present and reports 68 episodes, 1,075 rendered
sources, one damaged source, zero duplicates and zero unexplained missing
sources. Those are manifest records, not a new decode audit. V1 was untouched.

## Repairs

| Problem | Change | Evidence |
|---|---|---|
| Windows liveness checks could terminate the lock holder or pytest parent | Shared non-destructive process query used by review proxy, director preview and batch capture | A synthetic child survives observation; lock and director suites complete |
| Failed proxy jobs silently requeued on every poll | FAILED remains visible until explicit retry; existing explicit frag requests retain retry behavior | Isolated queue regression |
| Pending scene URL replaced a playable frag proxy | Separate scene status polling, ready-only upgrade, timeout/error/retry display | 390×844 browser test with real synthetic video |
| Repeated verdict taps wrote twice; failed saves advanced | Serialized submissions, HTTP status checks, note/item captured before awaits | Repeated-tap, failed-save and note-preservation browser checks |
| Scene votes followed unrelated queue positions | Advance through remaining scene events and reuse ready scene media | Three votes advance through the scene and then to event four |
| Old async metadata could overwrite current item | Navigation guards on scene, dossier, usage, round and round-note responses | Browser sequencing checks and code review |
| Export overwrite deleted the entire manifest and old media before recapture succeeded | Stage capture and manifest; replace matching row, preserve unrelated rows, rollback media on manifest replacement failure | Export failure/subset/duplicate regressions |
| General `/media` mount shadowed `/media/phase1`; preview files had no matching URL | Specific mounts first; explicit `/media/preview` route matching generated preview directory | Static-file response assertions |
| Annotation offset was 15s while renderer uses 5s + 8s | Set app offset to 13s; align clip resolver tests | Config, API and render-duration contract tests |
| Inline comments broke generated-asset ignore patterns; SQLite journals were exposed to accidental staging | Correct patterns; ignore runtime databases, journals and local test folders | `git check-ignore` |
| README startup referred to nonexistent requirements and the wrong import path | Install from pyproject and launch the package factory from repo root | Import/compile checks |

No production capture batch, database rebuild, publishing, commit, push, or
merge was performed. Test media and verdicts are synthetic. The live phone
service was not restarted or used to submit test verdicts.

## Verification

- Broad suite: **2,589 passed, 3 skipped**, 912 warnings, 347.82s.
- Final focused repair suites: **152 passed**; config/clip offset follow-up:
  **7 passed**; proxy/liveness follow-up: **10 passed**. These overlap the broad
  suite and must not be added together as a unique total.
- Liveness + proxy + director verification: **64 passed** in 320.68s.
- Mobile browser: synthetic API, encoded synthetic MP4, 390×844 viewport;
  repeated taps, note preservation, failed-save retention, queued scene
  fallback, READY upgrade, scene reuse, FAILED state and retry all pass;
  no uncaught page errors. This proves client behavior under controlled
  responses, not real Wolfcam completion or phone tunnel performance.
- Python compilation succeeds for changed production modules.
- New `process_liveness.py`: strict Pyright **0 errors, 0 warnings**.
- Repository-wide Windows Pyright: **28,086 errors, 7 warnings** over 647
  files at the review snapshot. Most are missing/unknown annotations and
  members. The project is not globally type-clean. The initial WSL check
  could not resolve the Windows environment correctly and is not the
  authoritative count.

Browser reproduction: `scripts/check_review_mobile.cjs`. Supply an existing
Playwright module path via `PLAYWRIGHT_MODULE`, a compatible cached browser
via `PLAYWRIGHT_CHROMIUM_EXECUTABLE`, and a synthetic MP4 via
`REVIEW_TEST_VIDEO`; `REVIEW_SCREENSHOT` controls the screenshot destination.
The script never reaches a production API. Runtime logs are local under
`.tmp/review-20260905/`.

Visual proof: [mobile reviewer](../visual-record/2026-09-05/reviewer_mobile_regression.png).

## Remaining limits

1. Refresh/restart of the actual reviewer service and a real phone acceptance
   test remain necessary before calling the live service safe to review.
   Mobile transcoding still occurs on demand inside the media request.
2. Legacy Cinema Tier A's non-mock worker does not resolve a real demo/window
   or write its capture config. Its mock route and output delivery are tested;
   real capture is incomplete. It also needs subprocess output draining and
   checked FFmpeg completion when that worker is completed.
3. Capture lock ownership is still based on PID files; acquisition is not a
   cross-process atomic lock. The new liveness query fixes destructive
   observation, not every concurrency concern.
4. Public-repo hygiene needs a separate tracked-content/history audit. Ignore
   rules do not remove already tracked sensitive content or generated media.
5. Older C++ scaffold and universal cross-platform readiness claims are not
   supported by the checkout. Current parser implementation is Python.
6. Existing `CaptureJob` and `WolfcamJob` types are backend-specific. No shared
   multi-backend ShotSpec / FrameTruth pipeline was found.
7. `RoundScenario`, its synthetic demo compiler and `ca_explainer_v1.dm_73`
   were not found in the inspected source/output locations. Blender was not
   found on PATH or the checked standard installation paths. The other
   Claude session's working directory is needed to reconcile these results.

## Research corrections and next work

All three follow-ups requested by the user are specified in
[the integration blueprint](../superpowers/specs/2026-09-05-render-integration.md).

The BSP importer's own README currently states Blender **2.93–4.2** support
and approximate shader conversion. Do not assume compatibility with an
arbitrary newer Blender or identical historical beauty output.
[Importer source](https://github.com/SomaZ/Blender_BSP_Importer).

Cryptomatte supplies masks for rendered surfaces; a fully occluded player
needs a separate visibility/player render pass for through-wall XRAY. This
is a pipeline requirement, not a feature automatically delivered by a mask.

Use local target-engine registrations to verify enemy-conditioned FX before
claiming a shipped binary supports a requested pass. Modern Wolfcam source
documentation alone is not evidence of the installed capture binary.

The Windows liveness finding follows Python's documented Windows semantics:
signals other than console control events use TerminateProcess.
[Python os.kill](https://docs.python.org/3/library/os.html#os.kill),
[Windows process wait](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject).
