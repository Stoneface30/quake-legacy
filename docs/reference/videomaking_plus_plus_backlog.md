# VIDEOMAKING++ — creative backlog (director's notes, preserved verbatim in spirit)

*2026-09-01. The director's original notes plus a 20-family synthesis. This
is a BACKLOG, not a plan: nothing here is scheduled. It exists so the ideas
survive review cycles and so PANDORA work can cite a source. No opponent
names appear here; the director's own clan brand (pTn) is intentional.*

## Camera vocabulary the UI will expose

The director decides camera per moment in the UI; the technical side is
automated; trims are set by hand before generation. What matters most is
the **anchoring point**, not the mode name.

| mode | anchor | exists today |
|---|---|---|
| FPV — shooter's eye | the player | yes (`FPV`) |
| Chase — behind + above | the player | yes (`CHASE`), geometry-limited |
| Side — perpendicular | the player or the shot | no |
| Orbit — around impact | the impact point | yes (`ORBIT`), currently a *fallback*; as a chosen "around impact" tail it is a legitimate angle |
| Projectile follow — rides the shot | the projectile | yes (`PROJECTILE`) |
| Top down — plan view | the arena | no |
| Freecam — unconstrained | none | yes (`FREECAM`) |

Review finding (canary V3B): cutting back to FPV before impact reads as
messy and harsh. A cinematic view that keeps the **shooter visible** through
the impact is preferred over a return to first person.

## Sync rule (director)

Music sync belongs mostly to **kills**, to **music slow-downs / build-ups**,
and to **high-speed movement** (rocket jumps, doors, teleports). The
canary showed a fast track (161 BPM) puts too many beats under a single
frag; the preferred track synced on a **voice entry**, with the slow leading
into a musical **high** — "not on high/slow/beat" was the correction.

## Director's original ideas

- New/live textures, live texture change, live morphing for transitions —
  a rocket and the whole background shift into the next scene; seamless.
- Slow-mo a death, then fly into the eye / into the rocket.
- **1 vs X**: when chased and winning, show all enemies coming; pause with an
  enemy count; or the map disappears → reappears with enemies revealed one
  by one and the count; decrement (−1, or something fancy) on each kill.
  Same idea when chasing several enemies down.
- Change texture / skin / effect during a clip: a countdown on a texture
  before a frag; anything that can pop out inside the demo.
- Morph to a different style live, during a slow-mo, or on a frag.
  Change model / skin / textures when low HP.
- Direct grenade contact → generate the model doing a chest control or a
  headbutt, like football.
- Only show "you are the only one left standing" when the round is actually
  **won** — otherwise it is anticlimactic.
- A kill followed by my own death: avoid it, show it only when the round is
  won, or use it — my death's blood can start the next clip.
- Full pTn rounds (2–4 clan-mates vs a recognisable stack) are a distinct
  content class: regroup, focus, strategy — excellent for action, POV,
  effects. Keep full round wins even without highlight frags.
- Great kill then killed: freeze on the killer, keep him, swap the clip to
  one with a similar position/weapon, continue.
- Map construction for intros: wire → texture → details in layers; a
  database of these works everywhere.
- Picture-in-picture as texture: ad banners; one grows to replace the
  scene as the camera follows.
- Chat bubbles as effect/transition; the chat itself (rage, insults, gg) as
  meme transitions. Log and index chat so it can be searched by time.
- Weaker skills become valuable by **grouping**: same position, same
  weapon, same place, same enemy → 10/20 clips in a row for tempo and
  music resync. Same for the rocket jump I did a thousand times.
- High-speed runs and rocket jumps that fly through the map, and going
  through doors → transitions.
- Telefrags and gauntlet frags → effects and transitions.
- mme transitions/effects for different styles.
- Reference: a clan-mate's transition-heavy videos on YouTube
  (`https://www.youtube.com/watch?v=artB2MbT6E8`).

## Twenty creative families (synthesis)

1. **Combat-state cinematography** — 1vX as a story state; sequential
   enemy reveal 4→3→2→1; decrement on kills; never resolve triumphantly on
   a lost round.
2. **World transformation** — countdown on textures, pTn/Nauru material
   passes, low-HP world treatment, impact emissive pulses, wire → untextured
   → textured → detailed, environment becoming the next map. Shader
   remapping is the realistic path.
3. **Player/weapon transformation** — low-HP presentation, hero-moment
   morphs, enemy classes visually separated in a reveal; later,
   presentation-only model/animation overrides without touching replay truth.
4. **Physical comedy / impossible replay** — the grenade chest-control
   gag: a semantic one-off recipe for a rare event, built from real
   impact location/velocity.
5. **Subject-preserving match transitions** — freeze on the killer, find
   another scene with a player in the same screen position/weapon/pose,
   swap the world underneath, continue.
6. **Object wipes / occlusion cuts** — rocket fills frame → next rocket
   emerges; player crosses camera → world changes; door closes → different
   map opens; weapon passes frame → next scene.
7. **Depth transitions** — foreground vanishes, then player, then
   background (or reverse); `mme_saveDepth` is already proven.
8. **Portal / impossible space** — fly into an exhaust, an eye, a
   teleporter, a gib cloud, a rail impact, a decal, an ad board, a barrel,
   a chat bubble, and emerge elsewhere.
9. **PIP as world geometry** — ad boards/monitors showing another scene;
   camera approaches until it is full-screen. Newer Wolfcam multi-videoMap
   work is a donor reference.
10. **Death as transition material** — blood/gib cloud as a wipe; red
    screen becomes the next map's red; killer silhouette becomes the next
    player. Solves "great kill then I die" — the death is the mechanism.
11. **Chat as cinematic content** — parsed, timed, indexed; bubbles, 3D
    world text, wall texture, wipe, meme insert — only when temporally and
    contextually connected.
12. **Clan/team-story sequences** — full pTn rounds; camera may leave FPV
    because the team geometry is the subject.
13. **Rhythmic motif montages** — pools of visually compatible moments
    (same doorway, jump, swing, target position, enemy, camera vector) cut
    4/8/16 to a musical pattern. Weak footage becomes valuable, not filler.
14. **Movement bridges** — rocket jump begins in map A, lands in map B;
    door A → exit B; teleporter A → another match; strafe → whip cut. The
    archive's scale is the advantage.
15. **Weapon-specific transition libraries** — telefrag → portal; gauntlet
    → brutal match cut; rail → line becomes geometry; LG → beam becomes a
    spline; rocket → projectile bridge; grenade → bounce becomes rhythm.
16. **Freeze decomposition** — freeze before the moment; isolate player and
    enemies; world disappears; rebuild geometry → opponents → trajectories
    → labels/count → resume.
17. **Time echoes / multi-exposure** — ghosts of previous positions during
    a dodge, flick, jump or LG track; Wolfcam trail hooks make it plausible.
18. **Map construction intros** — wire → geometry → texture → detail →
    lighting, each stage on a musical event; camera enters the finished map
    and play starts without a conventional cut.
19. **Health/state-reactive world** — low HP strips colour, alters
    materials, exposes wireframe, pulses surfaces; snaps back on recovery.
    SUBTLE by default, HERO only for exceptional scenes.
20. **Music-reactive world events** — semantic, not a spectrum visualiser:
    ACCENT → texture pulse; BUILD → layers assemble; DROP → scene swap;
    silence → world disappears; LG tick train → restrained response; kill →
    full texture/light returns. This is where Music Intelligence and
    PANDORA meet.

## Standing constraints these must respect

Replay movement truth is authoritative; presentation only. Every effect has
OFF / SUBTLE / HERO. Effects bind to recognised events, never wall-clock.
Nothing overwrites an original asset. Everything reproducible from a recipe.
