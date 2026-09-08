# CLAN ARENA EXPLAINER — BUILD PLAN

**Supersedes PROLOGUE_PROOF_01.** That build was rejected, correctly: abstract
2D graphics instead of the game, gameplay cut to 0.26–0.52 s so it read as
flashing, an "XRAY" caption over a shot containing no x-ray, and Quake and
Clan Arena merged into one piece when they must be separate.

## THE TWO DECISIONS

1. **The demo is synthesised** — `.dm_73` bytes written from scratch, not
   recorded and not borrowed from the archive.
2. **X-ray is out of this pass.** It is not a stock cvar and approximating it
   is what went wrong last time. It returns as its own piece of work.

## THE DELIVERABLES ARE SEPARATE FILES

| # | Deliverable | Built from |
|---|---|---|
| **A** | **WHAT IS CLAN ARENA** | the synthetic demo, wolfcam camera path, overlays |
| **B** | **WHAT IS QUAKE / FAST ARENA FPS** | separate, later, its own pass |
| **C** | THE ARCHIVE / PANTHEON | separate, later |

Nothing is assembled into a combined prologue until A and B are each accepted
on their own.

---

## STAGE 1 — THE DEMO WRITER  ·  *bit layer and gamestate DONE*

`engine/parser/dm73_write.py`.

**Done and proven:**
- Huffman encoder. The reader's tree is **static** — `receive()` never calls
  `add_ref()` — so encoding is a precomputed code table, byte-exact with the
  reader by construction. All 256 symbols and every bit width 1–32 round-trip.
- `BitWriter`: the mirror of `_Bits`, including the `n & 7` raw/symbol split.
- File container: `[seq][len][payload]`, messages terminated by `svc_EOF`.
- `svc_gamestate` with configstrings, and `svc_serverCommand`.
- **A written demo parsed by the project's own `DM73Parser`**: map
  `campgrounds`, gametype `CA`, 8 players on correct teams, 0 packet errors.

**Remaining:**
- `svc_snapshot`: serverTime, areamask, `MSG_WriteDeltaPlayerstate`,
  packet entities terminated by 1023. **Read `areamaskLen + 1` bytes** — the
  known desync that silently dropped 73.6% of every demo.
- Entity/playerstate delta encoders validated field-by-field against the
  reader's tables (they are imported, not restated).
- `EV_OBITUARY` events so the round has real kills:
  `event & ~0x300 == EV_OBITUARY`, killer in `otherEntityNum2`, victim in
  `otherEntityNum`, MOD in `eventParm`.
- CA round configstrings: `CS_ROUND_STATUS 661`, `CS_ROUND_TIME 662`
  (−1 ends the round), `CS_RED/BLUE_PLAYERS_LEFT 663/664`, `CS_SCORES1/2 6/7`.

**Gate:** round-trip every field, then **WolfcamQL plays the file**. Until the
engine plays it, it is not a demo.

## STAGE 2 — THE ROUND

A scene description compiled to the demo: 8 players, real positions over time,
one clean elimination sequence 4v4 → 4v3 → 3v3 → 2v2 → 1v0.

Choreographed so the camera can always see the action, since the whole point
is a round we control rather than one we found.

**Provenance:** every event carries `SYNTHETIC_EXPLAINER`. It never enters
career totals, the review queue, or any frag corpus. Already enforced by test.

## STAGE 3 — THE CAMERA

WolfcamQL's own spline camera, verified present:
`addcamerapoint` / `clearcamerapoints` / `playcamera` / `savecamera` /
`loadcamera`, plus `freecam`, `chase`, `view`
(`docs/reference/wolfcam-commands.md` §3).

A path that establishes the arena from above, descends into the first
engagement, holds through the exchanges, and rises for the last kill. Captured
through the existing V2 path. **`cg_draw2D 1` must be set** or overlays and the
speed readout are suppressed — the finding from the speedometer test.

## STAGE 4 — THE OVERLAYS

Composited **on the real footage**, tracking real world positions projected to
screen: arrows pointing at the players being discussed, alive counts, labels
that follow a player, the round state. Not a diagram beside the game — marks
on the game.

Positions come from the same demo, so the overlay and the picture cannot
disagree.

## STAGE 5 — THE CUT

Cut lengths governed by what a viewer needs to read. **No cut below ~1 s** in
an explainer. Speed comes from structure and contrast, never from shortening
everything.

---

## WHAT CARRIES FORWARD FROM THE REJECTED BUILD

Kept: the verified facts ledger, `name_guard` (a real defect it caught — the
V2 proxies burn opponent names into the picture), the shot-manifest discipline,
and the render/audit plumbing.

Discarded: every abstract 2D shot, the sub-second burst, and the fake x-ray.
