# The playable roster — all 26

Generated, not remembered: `python scripts/roster_inventory.py` writes
`docs/pantheon_world/roster.json` from the installed paks
(`bin.pk3`, `pak00.pk3`). Re-run it rather than trusting this table if the
install changes.

**Playable** means checkable: `lower.md3` + `upper.md3` + `head.md3` +
`animation.cfg`, because that is what cgame needs to assemble a body. All 26
character directories qualify; none were rejected.

## Unique characters — 26, with 199 usable skins

| character | skins | character | skins |
|---|---|---|---|
| anarki | 7 | major | 8 (`daemia`) |
| biker | 10 (`hossman`, `slammer`, `stroggo`) | mynx | 7 |
| bitterman | 7 | orbb | 7 |
| bones | 8 (`bones`) | ranger | 7 (`wrack`) |
| crash | 8 (`trainer`) | razor | 9 (`id`, `patriot`) |
| doom | 8 (`phobos`) | santa | 7 |
| grunt | 8 (`stripe`) | sarge | 9 (`krusade`, `roderic`) |
| hunter | 8 (`harpy`) | slash | 8 (`yuriko`) |
| james | 7 | sorlag | 7 |
| janet | 7 | tankjr | 7 |
| keel | 7 | uriel | 7 |
| klesk | 8 (`flisk`) | visor | 8 (`gorre`) |
| lucy | 8 (`angel`) | xaero | 7 |

Named skins in brackets are the character-specific ones; every character also
carries `default`, `blue`, `red`, `bright`, `sport`, `sport_blue`,
`sport_red` (ranger has no plain `sport` — the inventory checks that all three
body parts declare a skin before calling it usable, which is how that gap
surfaced).

## The three things kept apart

* **UNIQUE CHARACTER** — a `models/players/<name>` directory. 26 of them.
* **MODEL VARIANT** — there are none. `lower_1.md3` / `lower_2.md3` are Q3
  **LOD levels**, not alternates, and the renderer picks them by distance.
* **SKIN VARIANT** — `<part>_<skin>.skin`. A skin counts only when all three
  parts declare it, because a player wears one skin name across the body.

## Rules for the Hall

* **Identity is preserved.** Keel is Keel, Sorlag is Sorlag. Do not paint the
  roster blue and white — blue/white is the *architecture*'s language
  (`TEMPLE_V1.md`). Team-neutral `default` skins unless a shot argues
  otherwise.
* **Orbb cannot gesture.** His animation set is effectively a single frame for
  the upper body; never give him a gesture beat.
* **Character is not performance** (HL-5). A plinth pose is a
  `PresenterProfile` (model + skin) joined to a pose at compile time; the same
  authored idle can be worn by any of the 26.
* **Anchors, not hardcoded transforms.** Each character gets a named anchor in
  the Temple and is placed through `RoundScenario` / `RenderFrame`, never by a
  literal in the renderer.
