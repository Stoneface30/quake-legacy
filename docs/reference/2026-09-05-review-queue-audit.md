# Reviewer, queues, export and proof audit

Scope: current checkout including today's repairs. No live user verdicts,
production captures or batch work. Evidence levels below are deliberately
separate: source reading, isolated executable reproduction, browser simulation,
and actual game-frame proof are not interchangeable.

## Q1 — ARCHITECTURAL BLOCKER / CORRECTNESS BUG: capture ownership is not exclusive

`review_proxy.py:279` uses a PID file. At `:290` it only defers to a *different*
live PID. Two workers inside the server process both acquire it successfully.
`director_preview.py:1786` runs its own queue and calls that same helper at
`:1793`; review_proxy has another worker. `api/_render_worker.py` is another
queue authority, not the global engine scheduler.

**Isolated executable proof:** with LOCK_PATH patched to an external temporary
directory, call `_try_acquire_lock()` twice without releasing. Both return
`True`. No engine or production lock was touched. File existence followed by
write is also not atomic between processes.

**Impact:** the single-capture contract is not enforced across these workers.
One worker can remove the shared PID marker while another still captures.
Today's Windows liveness fix prevents killing the owner; it does not solve
this ownership failure.

**Smallest next proof:** run two synthetic workers through the real lock
boundary; assert maximum concurrent entry is exactly one, including same-PID
threads and different processes. Then make every capture consumer use the
same owner-token lock/scheduler. No batch render needed.

## Q2 — PRODUCTION UX BLOCKER: queue selection does not cancel queued work

`api/review.py:179–198` claims work from a stale selection is abandoned, but
the key is checked only while enqueueing. The queued job at
`engine/review_proxy.py:257–261` has no selection key, and the worker consumes
all queued jobs without consulting the current selection.

The queue endpoint prefetches 12 individual proxies. Scene media requests add
a separate, wider-window proxy; the cache key includes start/end times.
Ready-scene playback reuse does not eliminate those individual capture jobs.
The claim that one scene asset avoids all per-frag captures is not established.

**Smallest next proof:** enqueue selection A, switch to B while a synthetic
worker is busy, then inspect actual dequeued job IDs. Only the current
foreground request and explicitly retained work may continue. Assert shared
scene events schedule one scene capture rather than N redundant windows.

## Q3 — PRODUCTION UX BLOCKER: client repair is not live acceptance

Today's browser script proves double-tap serialization, successful advancement,
failure retention, scene READY upgrade, reuse, and retry using synthetic API
responses and an encoded test video. It does not run the actual queue, tunnel,
mobile transcoder, Wolfcam or real endpoint persistence as one system.

`request_proxy.py` is not a module; the actual implementation is
`engine/review_proxy.py:235–239`: persisted in-flight rows are retained when
*any* worker thread is alive. After a restart, starting another job can make
the new worker alive while an older persisted job has no in-memory owner.
Explicit retry can still retain that orphan. Client timeout makes this
visible but does not repair durable ownership.

`frontend/review.html:799–809` restores page offset but ignores the saved
`last_item_id`. Queue loading resets idx to zero and requests the default
queue rather than `unreviewed_only`; “resumed where you stopped” overstates
exact resume semantics. In-session scene advancement is now tested; resume
and next-unreviewed semantics still need their own production-path proof.

**Smallest next proof:** isolated TEST database plus the real API/worker,
at 390px: three votes, delayed scene readiness, failed render, server restart,
new job, retry old job, refresh at the fourth item. Assert real persistence
and no production identity writes. Only then repeat on the actual phone.

## Q4 — CORRECTNESS BUG: a retryable HTTP save is not idempotent

The client now serializes taps and checks success. The server still has no
request ID: `review_corpus.py:838–869` upserts the current verdict but appends
a log row every call. If the database commit succeeds and the response is
lost, retrying adds a duplicate log event. Client double-tap protection is
not exactly-once persistence.

**Smallest next proof:** commit a TEST verdict, drop its response, retry the
same request identity, and assert one history event and the preserved note.

## Q5 — FALSELY CLAIMED / NOT PROVEN: legacy Cinema Tier A is not real capture

`api/_preview_job.py:47–53` says it builds a config but neither writes it nor
resolves the actual demo/time window. It launches `+exec preview.cfg` without
the resolved demo. Its captured PIPE is not drained before `wait`, and the
FFmpeg return code is not checked before emitting done (`:82–96`).

Today's media mount repair makes generated preview files reachable. The mock
preview test proves delivery and SSE shape, not this real capture path.

**Smallest next proof:** use the common capture adapter with one approved
source window; record the generated config, process exit status, ffprobe
validation and actual frame. Until then label this legacy path incomplete.

## Q6 — Export and V1: concrete strengths, bounded guarantees

- Public capture resolves the semantic intent in `public_clip_export.py:169`
  and `:461`. Calling it merely a one-off profile branch would be inaccurate.
  Source/profile safety gates exist. Actual identity-free pixels for every
  supported POV/effect combination remain a separate acceptance requirement.
- Export duplicate IDs and destructive subset overwrite were reproduced and
  repaired with staging/rollback tests. That is process-level failure safety,
  not a claim of multi-file crash-atomic commit or multi-writer serialization.
- `review_proxy.py:219–221` validates raw demo source provenance before cache
  use. No new V1 fallback was established by this audit. Keep V1-isolation
  regressions; do not invent a regression from the existence of the separate
  legacy AVI pipeline.
- A tracked-extension scan found zero tracked `.dm_73`, `.avi`, `.mp4`, `.db`,
  SQLite WAL/SHM or `.env` files. This is **not** a historical secret audit or
  proof that text/screenshots contain no identities.

## What changed versus the beginning of the review

The initial destructive Windows PID probes, failed-job polling loop,
double-tap/failed-save advancement, scene URL race, export overwrite and
preview route defects were repaired and regression-tested before the user
paused further implementation for this audit. Remaining findings above are
not silently bundled into another architecture expansion.

Whole-suite success (2,589 passed, 3 skipped) is evidence of test behavior,
not certification of the end-to-end film pipeline or live phone service.
