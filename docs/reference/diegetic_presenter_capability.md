# Diegetic presenter — what the engine gives us, and what it does not

The narrator lives inside Quake. This is what that actually costs, measured.

## 1. Character identity is demo-authored — PROVEN

`\model\keel/bright` in the client's `CS_PLAYERS + clientNum` configstring
selects the character from the demo file itself. No playback-time override.

**Proof.** Two demos identical but for the model key, captured with
`cg_enemyModel ""` and `cg_enemyHeadModel ""` so the override cannot be doing
the work: `keel/bright` renders the bulky helmeted Keel silhouette,
`sarge/default` renders Sarge. Frames:
`docs/visual-record/2026-09-05/green_keel_synthetic_proof_01.png`.

`cg_ignoreClientHeadModel` defaults to `2` (`cg_main.c:2165`), which for a
protocol-QL demo makes the head follow `model` — so the one key covers head,
torso and legs.

`bright` is a real shipped skin, confirmed two ways: from inside `pak00.pk3`
itself, and from a per-entry manifest
(`docs/research/steam-pak-manifest-2026-04-17.json` in the creative-suite-v2
worktree, 9,285 entries matching the live pak exactly). The same manifest shows
`bright` is a **Quake Live addition** -- Q3A's `pak0.pk3` carries only
blue/default/red for keel. Contents:
`models/players/keel/{upper,lower,head}_bright.skin` exist with real contents,
and `scripts/models_players.shader:3205` defines `models/players/keel/bright`
with an `rgbGen entity` stage.

## 2. Green is a TINT, not part of the model — and it is the default

The green comes from `cg_enemyHeadColor` / `cg_enemyTorsoColor` /
`cg_enemyLegsColor`, which default to **`0x2a8000`** (`cg_main.c:2101-2103`).
They land in `shaderRGBA`, and the `bright` shader's `rgbGen entity` stage is
what makes the model take the tint at all. The DEFAULT skin
(`models/players/keel/keel`) has no entity stage and would not tint.

So: **model = demo-authored, colour = playback-time.** There is no
configstring key for player colour -- `c1`/`c2` are parsed and never applied.
A fully demo-baked colour would need a custom whole-model shader in a
`zzz_*.pk3` (ENG-2), since a skin name not ending in `.skin` becomes one
shader across every surface (`tr_image.c:2238`).

## 3. Gesture — one animation, and no pointing

`TORSO_GESTURE = 6` (`animNumber_t`, `bg_public.h:1195-1248`), held for
`TIMER_GESTURE = 34*66+50 = 2294 ms` (`bg_local.h:35`). Re-issuing it requires
flipping `ANIM_TOGGLEBIT` (128) or the engine treats it as the same animation
and does nothing -- the same toggle rule as events.

**There is no pointing animation.** `TORSO_FOLLOWME`, `TORSO_GETFLAG`,
`TORSO_PATROL`, `TORSO_AFFIRMATIVE`, `TORSO_NEGATIVE` exist in the enum, but
`CG_ParseAnimationFile` (`cg_players.c:222-232`) memcpy's them from
`TORSO_GESTURE` when a model's cfg ends early -- which is the norm for stock
models. Expect them to render identically.

**Register: `CUSTOM_POINT_GESTURE = UNSUPPORTED_NATIVE`.** A guide can greet,
turn to the camera, turn to another player and walk. "Raises an arm and
indicates that wall" is not in the MD3 vocabulary and is the specific thing
that routes to Blender as a character-performance backend.

**GESTURE_PROOF_01 -- visually confirmed.** Keel at t=1.0 s (idle) against
t=2.6 s and t=3.4 s (inside the gesture window opened at 2.0 s): the arm goes
from down-across-the-body to raised and out. Measured, the silhouette widens
from a 48 px bounding box to 59 px, aspect 0.38 -> 0.49, while green pixel
count stays flat at ~2,415 -- the body did not move or change size, it changed
pose. Frames: `docs/visual-record/2026-09-05/gesture_proof_01_torso_gesture.png`.

Caveat: no `animation.cfg` exists on disk -- the pak00 extraction kept PNGs
only -- so frame ranges are unverified. The 2294 ms timer is a source
constant, not a reading of any model's cfg.

## 4. Voice — the brief's assumption was wrong

**Piper is NOT installed.** Searched for binaries, voices and modules across
every interpreter: zero hits. Do not plan against it.

What is actually here:

| tool | role | status |
|---|---|---|
| **Kokoro-82M** | TTS | installed, weights on disk (327 MB), **broken at import** -- an `accelerate`/`bitsandbytes` circular import in system Py311. One voice: `bm_george`. |
| **Windows SAPI5** | TTS | working, 3 voices. Dated, usable as fallback. |
| **faster-whisper 1.2.0** | ASR / word timing | working offline, verified live |
| ffmpeg 8.1 | processing | `rubberband` (pitch + formant), `afir` (convolution reverb), `acrusher`, full EQ/dynamics |

**TTS synthesises speech; ASR transcribes it.** Whisper cannot say a sentence.
It can give word-level timing for an existing file -- verified on a real game
asset, `welcome_02.wav` -> `Welcome(0.00-0.44) to(0.44-0.92) Quake(0.92-1.24)
Live!(1.24-1.94)`. That is what drives subtitles and mouth timing.

`G:\QUAKE_LEGACY\WOLF WHISPERER\` is the WolfcamQL automation tool, **not**
OpenAI Whisper. The name collision is coincidental.

## 5. The best narrator voice is already in the game, and unextracted

Quake player models have **no speech** -- 13 files each: taunt, pain, death,
jump, gasp, fall. Same schema for all 26 models; they differ in timbre only.

But `pak00.pk3` contains `sound/vo/crash_new/` -- **40 files of the QL tutorial
trainer speaking complete instructional sentences**, 1.5-8 s each. Plus
`sound/vo/` with 107 announcer lines (`fight`, countdown, `red_wins`...).
**None of it has been extracted** -- `raw/sound/` has no `vo/` directory.

That is the single highest-value action for the presenter, and it is pure
read-only extraction against the pak (ENG-4 respected).

---

## Three engine traps that each cost a filmed take (2026-09-05)

All three are silent. Every one of them ended with a process that exited
cleanly and produced either nothing or the wrong thing, with no error text
anywhere in `qconsole.log`.

### 1. `MAX_CONSOLE_LINES` eats `+demo`

`Com_ParseCommandLine` (qcommon/common.c) stops recording `+` groups once it
holds **32**, and returns without a word. The launch line was eight built-in
`+set` groups, plus the master profile's fourteen, plus thirteen shot cvars —
so `+demo` fell off the end. The engine booted to the main menu, never ran
`cgamepostinit.cfg`, and exited `rc=0` after ~300s with no AVI.

- **Grade:** EXECUTION_PROVEN — reproduced, then fixed and re-proven.
- **Fix:** shot cvars go into `capture.cfg` (exec'd from `cgamepostinit`, no
  ceiling), never onto the command line. `shot.py::render` also refuses to
  launch a command line with more than `MAX_CONSOLE_LINES` groups.

### 2. SDL's driver probe fails, and the answer is a quarter-resolution film

```
SDL_Init( SDL_INIT_VIDEO ) FAILED (No available video device)
^1GLimp_StartDriverAndSetMode() failed, reverting to safe values
GLimp_Shutdown: mode -1 lastMode -999      <- r_mode -1 WAS set
...setting mode 11: 856 480
```

The requested `r_mode -1` / 1920x1080 was correct and was applied; the driver
probe failed first, and "safe values" silently replaced the resolution. The
capture then ran to completion and wrote a perfectly valid **856x480** AVI.

- **Fix:** launch with `SDL_VIDEODRIVER=windib` in the environment. First
  attempt then succeeds and the film is 1920x1080.
- **Watch for:** any capture whose AVI probes at 856x480 hit this.

### 3. A stale `q3config.cfg` overrode demo-authored identity

The master capture profile clears `cg_enemyModel` / `cg_teamModel` and sets
`cg_forceModel 0`. It does **not** clear wolfcam's per-part override family,
and the staged `q3config.cfg` still carried, from some earlier session:

```
seta cg_enemyHeadModel "keel/bright"
seta cg_enemyLegsSkin  "bright"
seta cg_enemyTorsoSkin "bright"
seta cg_enemyHeadSkin  "bright"
```

Crash and Keel therefore rendered as the same flat green figure. Nothing was
wrong with the demo: the client was overriding the skins the file authored.

- **Falsified on the way:** the `c1` / `c2` player colour indices were the
  first suspect. Filming Crash at `c1=1` against Keel at `c1=3` changed
  nothing — colour indices are not the tint source here.
- **Fix:** `VisualProfile.cvars()` clears the whole enemy/team model+skin
  family. Crash then renders in his red-and-white trainer skin, visibly a
  different character from Keel. `keel/bright` staying green is correct: the
  `bright` skin family IS the flat green one, and that is what was authored.

**Delivered:** `DIEGETIC_PRESENTER_PROOF_01.mp4`, 1920x1080, 60fps, 19.70s,
six dialogue cues (four real Crash tutorial recordings, two synthesised),
panned from FrameTruth positions on the scenario clock.
Reproduce with `python -m engine.pantheon.presenter_proof` then
`python -m engine.pantheon.presenter_film`.
