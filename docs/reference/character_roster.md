# The cast — Quake Live's character roster, as installed

Read from `pak00.pk3` on 2026-09-05 by `engine/pantheon/roster.py`. Machine
form: `character_roster.json`. Regenerate with
`python -c "from engine.pantheon.roster import save_inventory; save_inventory()"`.

**Why this exists.** PANTHEON does not have a mascot. The game ships
twenty-six characters, and every film, chapter or scene casts its presenter
from them. This document is the factual half of that decision — what ships.
The suitability column is a creative suggestion and says so.

## Factual inventory

Every model has `animation.cfg`, a `bright` skin, `red`/`blue`/`sport` team
skins, and thirteen native sounds: `taunt.wav`, `death1-3`, `pain25/50/75/100`,
`jump1`, `fall1`, `falling1`, `gasp`, `drown`. So every character has a native
voice **anchor** (its taunt and barks); only **Crash** has full sentences (the
trainer tutorial, 40 lines, transcribed and word-timed in an earlier sprint).

| model | sex | gesture frames | extra skins | can gesture |
|---|---|---:|---|---|
| anarki | m | 40 | — | yes |
| biker | m | 40 | hossman, slammer, stroggo | yes |
| bitterman | m | 40 | — | yes |
| bones | m | 40 | bones | yes |
| crash | f | 40 | **trainer** | yes |
| doom | m | 40 | phobos | yes |
| grunt | m | 40 | stripe | yes |
| hunter | f | 40 | harpy | yes |
| james | m | 26 | — | yes |
| janet | f | 26 | — | yes |
| keel | m | 40 | — | yes |
| klesk | n | 44 | flisk | yes |
| lucy | f | 40 | angel | yes |
| major | f | 37 | daemia | yes |
| mynx | f | 40 | — | yes |
| **orbb** | n | **1** | — | **no** |
| ranger | m | 40 | wrack | yes |
| razor | m | 40 | id, patriot | yes |
| santa | m | 40 | — | yes |
| sarge | m | 40 | krusade, roderic | yes |
| slash | f | 47 | yuriko | yes |
| sorlag | f | 41 | — | yes |
| tankjr | n | 40 | — | yes |
| uriel | m | 37 | — | yes |
| visor | m | 40 | gorre | yes |
| xaero | m | 33 | — | yes |

**Orbb cannot gesture.** His `TORSO_GESTURE` row is one frame — a still, not a
wave. Found by reading `animation.cfg` row 6 per model, not by assuming every
model matches Sarge. `PresenterProfile.gesture_ok()` reports it and the
instruction layer skips the gesture beat for him rather than playing a
one-frame pose.

## Visual identity rules (from PROOF B)

- The `cg_team*Color` / `cg_enemy*Color` family tints the **bright** skin and
  nothing else; `sarge/default` measured identically with it cleared and set.
- So a `bright` skin on a presenter is a *choice to be tintable*, and a
  `default` or named skin is a choice to keep the character's own look.
- Green Keel is `keel/bright` + the enemy half of the family, and it is a
  **role** (`ENEMY_DEMONSTRATOR`), not a brand. Crash, Anarki, Slash, Orbb keep
  their real skins.
- Historical actors are never re-skinned. Presenter identity comes from
  blocking, camera attention, looking at camera, walking during the freeze,
  gesture and dialogue.

## Suggested casting — creative, revisable

| role | character | skin | voice anchor | why |
|---|---|---|---|---|
| GUIDE | Crash | trainer | 40 real tutorial lines + taunt | the game's own teacher; the only full native voice |
| ENEMY_DEMONSTRATOR | Keel | bright | taunt + barks | big readable silhouette; "Hello. I'm the enemy." already lands |
| MOVEMENT | Anarki | default | taunt + barks | the hoverboard punk — the movement chapter's own face |
| TACTICAL | Slash | default | taunt + barks | sharp, energetic; 47-frame gesture, the longest in the roster |
| COMEDY | Orbb | default | taunt + barks | an eye on legs; **cannot gesture** — stage him with movement and camera instead |
| VETERAN | Sarge | default | taunt + barks | the default player everyone recognises |
| ARCHIVE | Ranger | default | taunt + barks | the original Quake protagonist; history's witness |

**Recommended for the three chapters currently planned:**

- **QUAKE PRESENTATION** — Crash. Her recorded tutorial lines *are* Quake
  explaining itself; nothing synthetic can match that provenance.
- **CLAN ARENA** — Slash presents, Keel is the enemy foil. Slash gives the
  chapter a different voice from the introduction; Keel stays the thing she
  points at.
- **ARCHIVE / LEGACY** — Ranger. The first Quake face introducing ten years of
  demos reads as intended.

Movement/technique segments later: Anarki. Comic beat: Orbb, without a
gesture.

## Voice coverage

`engine/pantheon/voice.PROFILES` now carries GUIDE, KEEL, ANARKI, SLASH, ORBB,
SARGE, RANGER. Each pairs the character's native anchor with a Kokoro voice
(`af_heart`, `am_michael`, `af_sky`, `am_adam`) and a processing chain; none of
them is an impression, and the chain is what keeps a synthetic line sitting
beside the real barks. Kokoro is working in the project venv (0.9.4) — the
earlier "broken at import" note was for the system interpreter.

Cast sheet: `PANTHEON_CAST_PROOF_01` — one demo, one mark, one camera, twelve
characters in sequence: idle, gesture, walk. Stills and the contact sheet live
in `docs/visual-record/2026-09-05/cast/`.
