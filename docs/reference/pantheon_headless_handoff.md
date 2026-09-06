# PANTHEON headless — reviewer integration handoff

Branch `feature/pantheon-headless`, worktree
`.claude/worktrees/pantheon-headless`. This document says what to merge, what
overlaps, and who owns which behaviour when it does.

**Do not merge the reviewer branch from the headless side.** The reviewer owns
their own checkout and their own merge.

## Merge range

    git log --oneline 5a1f08ddb4d84134124d78e9158c56dbfc5f8c59..b6c13efd

280 commits from the common ancestor `5a1f08dd` to the tip. The reviewer
merges the branch, not a cherry-pick: the modules below depend on each other.

## What the branch brings

Every one of these is committed. Nothing required exists only as an untracked
file, and nothing about correctness depends on a database that lives outside
the repository.

| Module | What it owns |
|---|---|
| `engine/pantheon/offscreen.py` | PANTHEON_QUAKE_OFFSCREEN: the engine on a hidden Windows desktop, with the window, focus and pointer watched every run |
| `engine/pantheon/render_permit.py` | the ONE permit. `PANTHEON_RENDER=off\|auto\|on`; a running game always defers |
| `engine/pantheon/disk_policy.py` | the three thresholds: review write, render job, large build |
| `engine/pantheon/visual_profile.py` | film words to backend values, in one function |
| `engine/pantheon/capabilities.py` | what a backend can do and how we know |
| `engine/pantheon/visual_proof.py` | what a person judged, and when it expired |
| `engine/pantheon/effect_recipes.py` | the film grammar as semantics |
| `engine/pantheon/possibilities.py` | what a moment can carry, with reasons |
| `engine/pantheon/review_moment.py` | the one object the reviewer reads |
| `engine/pantheon/backend_planner.py` | which backend takes which pass |
| `engine/pantheon/choreography.py` | recipe plus moment becomes a plan |
| `engine/pantheon/engine_census.py` | asks the running client for its whole vocabulary |
| `engine/pantheon/engine_inventory.py` | 2,345 engine items, graded, zero unclassified |
| `engine/parser/protocol.py` | the protocol-73 registry |
| `engine/pantheon/defaults.py` | the versioned project profiles |
| `engine/pantheon/ideas.py`, `director_notes.py` | the director's 306 ideas and 28 original notes, verbatim |

## The green Keel proof is durable

`REVIEW_GREEN_KEEL` is VISUALLY_PROVEN for backend PANTHEON_QUAKE_OFFSCREEN,
profile REVIEW, engine wolfcamql-11.3.

    ENEMY = KEEL / BRIGHT / GREEN      TEAM = preserved      SELF = preserved

One demo, one serverTime, one camera, the VisualProfile as the only variable.
AUTHENTIC renders a slim blue actor; REVIEW renders a large unmistakable green
Keel. 49,509 strong-green pixels against 2 in the control, filmed offscreen
with no visible window and no stolen focus.

The artefacts are **committed** at `docs/visual-record/2026-09-06/green_keel/`
and their sha256 prefixes are recorded in the registry seed, so a changed file
is detectable rather than silently trusted. The registry database itself lives
under `PANTHEON_PERFORMANCE_STORE` and is NOT in the repository; the `SEED`
tuple in `visual_proof.py` is the committed authority and `doctor` rebuilds the
database from it on a fresh checkout.

The older memory saying the green enemy was closed PARTIAL is marked
SUPERSEDED_BY REVIEW_GREEN_KEEL, with its history kept.

## The four expected overlaps

### `engine/pantheon/render_permit.py` — headless wins

The reviewer's version resolves disk through `operator_health.free_gb()` with
a single floor and a `batch=` flag. The headless version resolves it through
`disk_policy`, which splits one floor into three: a review verdict is a few
bytes and must not be held to the space a capture needs, and an index build
needs far more than either.

**Take the headless file whole.** It already accepts `check(batch=True)` —
the reviewer's spelling, mapped to the large-build threshold — so their call
sites keep working unchanged. `operator_health` is not deleted; the permit
simply no longer asks it about disk.

### `creative_suite/engine/review_proxy.py` — both sides, split by concern

The reviewer owns the UI, the Option-A behaviour, the cache manifest, the job
states and everything about how a proxy is requested and served. The headless
branch changes exactly one thing inside it: **where the frames come from.**

Keep the reviewer's file and re-apply three headless changes:

1. `_film()` routes capture through `offscreen.capture` on the hidden desktop,
   with `CS_PROXY_WINDOW=1` as the explicit opt-out. There is no silent
   fallback to a window: if a hidden desktop cannot be created the job fails
   and says so.
2. The capture names the REVIEW master profile. Passing no profile does not
   mean "no profile" — it means the BATCH master, which once burned an
   opponent's name into a public clip.
3. `FFMPEG` resolves from the checkout that owns the data, not from the code,
   so the module works inside a git worktree.

Three columns were added to `review_proxies`: `backend`, `engine_version`,
`source_demo`. They are additive and nullable; a row from before the migration
reads NULL, which is the truth about it. **The cache key is unchanged**, so
every proxy already READY stays READY.

### `creative_suite/tests/test_render_permit.py` — merge both sets

Both sides test the same one permit and neither set is redundant. Take the
union. The headless file already contains the reviewer's batch semantics as
two tests written against `disk_policy`, so the reviewer's own
`operator_health`-based versions of those two can be dropped in favour of
them; every other reviewer test applies unchanged.

### `CLAUDE.md` — both rule sets, one authority each

Headless adds the HL-1..HL-8 hard rules. The reviewer's rules are unaffected
by them and none of the HL rules restates a CS or P1 rule. Concatenate; do not
merge sections. If a rule appears on both sides, the one that names a module
path is the authority and the other becomes a pointer to it.

## Conflict policy in one line

Where the two branches disagree about **the engine**, headless is the
authority. Where they disagree about **the reviewer's product** — its UI,
states, media cache, corpus and verdicts — the reviewer is the authority.

## What the reviewer inherits that is not yet finished

Stated plainly so nothing is discovered later:

- `XRAY_ACTOR` is NEEDS_VISUAL_CONFIRMATION. The pipeline runs end to end and
  the silhouettes draw; the colour was wrong until the packed-integer
  correction and has not been re-filmed since.
- Four registered engine switches are unproven as OUTPUT: the depth pass, the
  demo freeze recording frames, temporal blur, and chasing a projectile
  entity. Each needs one capture, not an argument.
- `review_db_write_safe` exists and has no caller. The reviewer owns the
  verdict-write path and should call it there.
- Seven capabilities in the proof registry are waiting on a human verdict.
