# Fragmovie Effect Research — Classic Technique Mining

*Research pass 2026-08-30 (demo-v2-mining). Purpose: expand the effect-recipe vocabulary of the
programmable fragmovie engine beyond the already-planned set (orbit, projectile follow/POV,
reverse track, bullet-time arc, chase cam, side track, vertical orbit, top-down, enemy POV cut,
freeze, time ramps, pixel-replay zoom, flick replay + arc viz, enemy-count markers, low-HP
pulse/heartbeat, speed FOV, feed stacking, world-space text/logos, trajectory ghosts, impact
rings). Everything below is NEW relative to that list.*

Sources consulted: q3mme command reference and forum ([entdark/q3mme cmds.txt](https://github.com/entdark/q3mme/blob/master/cmds.txt),
[q3mme.proboards motion blur tutorial](https://q3mme.proboards.com/thread/18)),
WolfcamQL docs and community tutorial ([brugal/wolfcamql README](https://github.com/brugal/wolfcamql/blob/master/README-wolfcam.txt),
[ESR WolfcamQL Complete Tutorial](https://www.esreality.com/post/2525022/wolfcamql-complete-tutorial/),
[Maverick's cvar list](http://kitteh.maverickservers.com/cvarlist/)),
classic movie reception threads ([Get Quaked 3 — igmdb](https://www.igmdb.org/?m=51),
[GQ3 polycount thread](https://polycount.com/discussion/39668/get-quaked-3-frag-video),
[AnnihilatioN by own-age — ESR](https://www.esreality.com/post/420974/annihilation-by-own-age/),
[ESR "Your Top 3 Quake frag / Defrag movies"](https://www.esreality.com/post/2775835/your-top-3-quake-frag-defrag-movies/)),
FX scripting ([wolfcam q3mme.fx](https://github.com/brugal/wolfcamql/blob/master/package-files/wolfcam-ql/scripts/q3mme.fx),
[QLFF fx-script editing guide](https://qlff.board-directory.net/t1-how-to-enable-the-q3mme-fx-script-included-with-wolfcam-and-start-editing-it)),
DeFRaG recam culture ([DeFRaG — Wikipedia](https://en.wikipedia.org/wiki/DeFRaG),
[q3df.org DemoCams wiki](https://www.q3df.org/wiki?p=138),
[q3df.org Replay-script editing wiki](https://www.q3df.org/wiki?p=173)),
transition-craft threads ([teamfortress.tv "Good transitions to use in frag movies?"](https://www.teamfortress.tv/30189/good-transitions-to-use-in-frag-movies),
[ESR Moviemaking Interview Series](https://www.esreality.com/post/2919989/moviemaking-interview-series/)),
film-language reference for match-cut taxonomy ([StudioBinder match cuts guide](https://www.studiobinder.com/blog/match-cuts-creative-transitions-examples/)).

Execution legend — **ENGINE** = wolfcamql/q3mme camera+cvar scripting at capture time ·
**DATA** = needs our dm73 parser and/or BSP tooling to compute · **POST** = ffmpeg/NLE pass in
`creative_suite/engine/`.

---

## 1. New Effect / Technique Ideas

### Camera & staging

#### 1. Visor / surface reflection shot
- **Looks like:** the incoming rocket (or rail beam) is seen reflected in a shiny surface — the
  victim's visor, a glass/metal wall — a beat before it lands. GQ3's most-quoted single shot is a
  long-distance midair rocket "reflected in the doomguy's visor just before it nailed him"
  ([polycount thread](https://polycount.com/discussion/39668/get-quaked-3-frag-video)).
- **Execute:** ENGINE + POST. Freecam framed tight on the victim's head/shiny geometry
  (`/follow victim`, freecam, dof on face); the "reflection" is a post composite — render the
  killer-POV pass, warp/darken it, and mask it into the visor region (static head = trivial
  planar mask; our parser gives exact victim head position + view angles for the framing).
- **Suits:** air rocket, pixel rail — long-flight-time projectiles only.

#### 2. Map fly-through establishing shot (chapter opener)
- **Looks like:** slow spline cruise through the empty (or ambient) map — the classic Q3
  fragmovie chapter opener; nearly every own-age-era movie opens map segments this way, and
  DeFRaG "recams" made the roaming-camera map tour a genre convention
  ([DeFRaG](https://en.wikipedia.org/wiki/DeFRaG)).
- **Execute:** ENGINE. q3mme `camera` catmullrom spline over 10–20 s at low speed, wide fov,
  ambient game audio only. Our BSP tooling can auto-generate collision-free spline waypoints
  through the map's main atrium — a *programmable* flythrough per map, seeded from the arena
  where the next frag chain happens.
- **Suits:** section intros/outros; pairs with T3 filler slots.

#### 3. Dolly zoom (Vertigo shot)
- **Looks like:** the victim stays the same size while the world stretches behind them —
  signature "oh no" moment. Fits the moment an LG victim realizes they're trapped.
- **Execute:** ENGINE. q3mme camera keypoints support fov animation: dolly the camera backward
  along the killer→victim axis while ramping fov down (or forward + fov up), keeping the
  target's screen size constant. Our parser supplies both entity positions to compute the exact
  dolly/fov pairing (screen-height-constant equation), so this is a closed-form recipe.
- **Suits:** clutch 1vX (the "cornered" beat), LG tracking.

#### 4. Rack-focus pull (killer ↔ victim)
- **Looks like:** foreground killer sharp / background victim blurred, then focus snaps to the
  victim at the moment of the hit. Pure film language, fully in-engine.
- **Execute:** ENGINE. q3mme `dof` keypoints with target-based focusing (`dof target` on a
  player, focus + radius animatable per keypoint —
  [cmds.txt](https://github.com/entdark/q3mme/blob/master/cmds.txt)). Recipe: dof keypoint A
  focused on killer, keypoint B at impact-time focused on victim.
- **Suits:** pixel rail (distance = big focus delta), air rocket.

#### 5. Whip-pan transition
- **Looks like:** camera whips 180°+ in 4–6 frames with heavy motion blur; the next clip
  begins mid-whip in the same direction — the two clips read as one continuous move. A staple of
  the own3d-era editors, done in-engine rather than in After Effects.
- **Execute:** ENGINE + POST. End clip A with a fast angular camera keypoint pair; start clip B
  the same way mirrored; mme blurFrames makes the smear ([motion blur
  tutorial](https://q3mme.proboards.com/thread/18)); the cut hides in the blur. Our render
  pipeline just needs a `whip_out` / `whip_in` flag on adjacent clips.
- **Suits:** multikill (between kills), high-speed movement chains.

#### 6. One-take frag chain (long take)
- **Looks like:** a single unbroken freecam shot flows through 2–4 frags with NO cut — the
  camera swims from one victim to the next. AnnihilatioN's reputation rests on cinematography of
  exactly this patience ([ESR](https://www.esreality.com/post/420974/annihilation-by-own-age/)).
- **Execute:** ENGINE + DATA. Needs the parser to find frag clusters (2+ obituaries within
  ~8 s and within camera-travel range) — then one q3mme spline is authored across the whole
  window with timescale dips at each kill. This is a *frag-mining query*, not just a camera.
- **Suits:** multikill, clutch 1vX round ends.

#### 7. POV dive-in (tactical-to-personal transition)
- **Looks like:** top-down overview showing the whole arena and enemy dots, then the camera
  plunges vertically and forward-tilts until it lands exactly in the player's eyes — cut to
  first person, fight starts. Distinct from a plain top-down: it's the *transition* that sells it.
- **Execute:** ENGINE + DATA. Camera spline from overhead point to the player's head position +
  view angles at time T (parser gives ps.origin + viewangles); final keypoint matches FP fov;
  hard cut to the FP capture at spline end. BSP ceiling height clamps the start altitude.
- **Suits:** clutch 1vX openers, round-start storytelling.

#### 8. Platform / door dolly mount
- **Looks like:** camera rides a moving map element — a lift, bouncing on a jump-pad arc, a
  rotating object — as the fight happens around it. In-world "crane shots" with zero rig.
- **Execute:** ENGINE + DATA. Parser tracks mover entities (func_plat/func_door origins per
  snapshot); generate camera keypoints locked to mover origin + offset. Feels physical because
  it *is* physical.
- **Suits:** high-speed movement, map-personality b-roll.

#### 9. Through-frame foreground composition
- **Looks like:** the frag is framed through a doorway, grate, or teleporter arch, with the
  near edge softly defocused — depth-composed shots instead of floating void cameras. What
  separates "camera in space" from cinematography.
- **Execute:** ENGINE + DATA. BSP tooling finds portal/doorframe geometry between camera and
  action; place camera 32–64u behind the frame, dof radius high, focus on the fight. This is
  automatable: pick camera positions where a *portal polygon* intersects the killer→victim
  sightline.
- **Suits:** pixel rail, LG tracking duels.

#### 10. Dutch-angle roll keyframes
- **Looks like:** camera rolls 5–15° during aggression peaks, returning level on the kill.
  Classic movies used subtle roll in flythroughs; q3mme camera angles are fully keyframable
  (quaternion angle interpolation — [cmds.txt](https://github.com/entdark/q3mme/blob/master/cmds.txt)).
- **Execute:** ENGINE. Roll component on camera keypoints; rule: never exceed ~15°, always
  resolve to 0° on the beat of the kill.
- **Suits:** high-speed movement, multikill runs.

#### 11. LG-shaft axis cam
- **Looks like:** camera sits almost on the beam axis behind the killer's shoulder, so the LG
  shaft reads as a solid light-bridge to the victim; small orbital drift makes the beam "bend."
- **Execute:** ENGINE + DATA. Parser gives attacker viewangles + both origins → camera placed
  on the beam line + 20u lateral offset, tracking the victim. Only worth it on high-accuracy
  segments (accuracy from our LG-band scoring, FT-2).
- **Suits:** LG tracking exclusively.

### Time & playback

#### 12. Resurrection cut (time-reversed footage)
- **Looks like:** gibs fly *backwards* and reassemble into a standing player — used as a
  chapter transition or "meanwhile" device. Distinct from the reverse camera *track* already
  planned: this reverses the *footage*.
- **Execute:** POST (ffmpeg `reverse`); capture a death at high fps first. Best with heavy gibs
  enabled (wolfcam supports Q3-style bleeding/gibs —
  [ESR tutorial](https://www.esreality.com/post/2525022/wolfcamql-complete-tutorial/)).
- **Suits:** transitions, outro stingers.

#### 13. Round hyperlapse
- **Looks like:** an entire CA round compressed to 15–20 s at 6–10× speed under a smooth
  camera path — the "how the round unfolded" recap before or after the clutch clip plays at
  normal speed. (Speedrun-community DNA: DeFRaG movies condensed runs the same way.)
- **Execute:** ENGINE. q3mme `line speed` / wolfcam timescale >1 with a slow spline; capture is
  timescale-aware so blur accumulates naturally. Parser marks round start/end times.
- **Suits:** clutch 1vX context-setting.

#### 14. Frame-hold stutter (beat-locked freeze pulses)
- **Looks like:** playback freezes for 2–4 frames on each beat during a rapid kill chain —
  a rhythmic "pump" that old-school editors did with duplicated frames, NOT the modern
  zoom-shake spam. Reads as confidence, not chaos.
- **Execute:** POST. ffmpeg select/loop on beat timestamps from `partNN_beats.json`; cap at
  3 pulses per clip (grammar rule: stutter is seasoning).
- **Suits:** multikill, LG tracking bursts.

#### 15. Pre-kill dead-air hold
- **Looks like:** the *opposite* of compressing dead time: for the biggest frag of the Part,
  hold 2–3 s of uncut quiet — footsteps, item hum — before the action. Classic movies earned
  their peaks with silence; the drop hits harder from stillness.
- **Execute:** ENGINE (just don't trim) + editing rule. This is an exception flag to P1-Q-AUTO
  speed-ramping: `hold_head=1` on climax clips, synced so the music break covers the quiet.
- **Suits:** the single T1 climax frag per Part; air rocket setups.

### Game-state storytelling

#### 16. Item-cycle narrative overlay
- **Looks like:** a minimal world-space marker on the red-armor / mega spawn point with a
  countdown; the clutch player routes through the item *exactly* as it spawns. Explains WHY the
  1vX was winnable — stack storytelling beyond enemy counts.
- **Execute:** DATA + POST. Parser reads item pickup events + respawn cycle; BSP gives the
  spawner's world position; project to screen space per-frame (we have camera matrices from our
  own spline) and composite a small counter in post. Old-school styling: bitmap font, no glow.
- **Suits:** clutch 1vX.

#### 17. Delayed obituary reveal
- **Looks like:** HUD kill feed suppressed during the slow-mo; when time snaps back to 1×, all
  three obituary lines print at once with their sounds stacked. The *information* is edited, not
  just the pictures.
- **Execute:** ENGINE (capture with feed hidden via wolfcam HUD cvars) + POST (composite the
  feed lines back at chosen times — parser has exact obituary text/weapon/time).
- **Suits:** multikill.

#### 18. Announcer-as-stinger editing
- **Looks like:** QL announcer samples ("IMPRESSIVE", "EXCELLENT", "HUMILIATION") pulled out of
  the game mix and placed ON musical hits, sometimes replacing a snare. The announcer *is* the
  hype man — a QL-native trick no generic editor has.
- **Execute:** DATA + POST. P1-DD sound-template matching already recognizes these events;
  extract clean samples from pak00, mute the in-clip instance, re-place on the beat grid in the
  music mix (single fixed music level preserved per P1-G — the stinger rides the game-audio bus).
- **Suits:** pixel rail (IMPRESSIVE), multikill (EXCELLENT), gauntlet (HUMILIATION).

#### 19. Clock-pressure outro
- **Looks like:** final frag of a round with the game clock burned large; cuts accelerate as
  the clock runs down, last kill lands as it hits zero (or as the round-end horn fires).
- **Execute:** ENGINE + DATA. Parser has server_time + round timer; render clock as a stylized
  overlay (post) or keep wolfcam's HUD clock; cut lengths scripted to shrink geometrically.
- **Suits:** clutch 1vX round-enders.

#### 20. Gib-follow shot
- **Looks like:** after the kill, the camera abandons the players and follows one gib chunk
  arcing across the map, landing as the music resolves. Morbid punctuation; very Q3.
- **Execute:** ENGINE. Gibs are client-side particles — not in the demo — so this is a freecam
  improvisation: enable max gibs, replay the death repeatedly, hand- or script-tune a ballistic
  camera arc from the death point (simple projectile math, gravity 800). Doesn't need to match a
  specific gib perfectly; any plausible arc reads correctly.
- **Suits:** air rocket, rail finishers.

### Look & material (in-engine art direction)

#### 21. Per-section FX-script reskin
- **Looks like:** each music section gets a signature palette — e.g. the rail beam recolored to
  the PANTHEON gold, rocket trails thickened, impact sparks doubled — via q3mme fx scripting,
  not post grading. Wolfcam ships the q3mme.fx system: isolate `weapon/rocket/impact` etc. and
  edit shaders, emitters, even screen *vibration* per event
  ([q3mme.fx](https://github.com/brugal/wolfcamql/blob/master/package-files/wolfcam-ql/scripts/q3mme.fx),
  [QLFF guide](https://qlff.board-directory.net/t1-how-to-enable-the-q3mme-fx-script-included-with-wolfcam-and-start-editing-it)).
- **Execute:** ENGINE. Generate `zzz_partNN_section.fx` variants from templates; swap
  `cg_fxfile` per capture batch. This makes "recipes" cover *materials*, not just cameras.
- **Suits:** all classes; chapter identity.

#### 22. FX-script impact camera shake
- **Looks like:** brief screen vibration when a rocket lands near the camera — physicality
  without post shake. The fx system exposes a vibration property per event.
- **Execute:** ENGINE. Add `vibrate` to rocket/grenade impact events in the fx script, scaled
  by distance. Grammar rule: only on third-person shots, never on FP (FP already has kick).
- **Suits:** air rocket, grenade direct.

#### 23. Retro-crunch picture pass
- **Looks like:** one chapter deliberately shot at `r_picmip 5`+, vertex light, low sky detail —
  the 1999-LAN look — then snapped back to the clean pass. Old-school authenticity as a *device*
  rather than a limitation.
- **Execute:** ENGINE. Pure cvar preset per capture; cheap A/B. (Contrast chapter against the
  photoreal-textured `zzz_*.pk3` chapters from Phase 5 for a "then vs now" arc.)
- **Suits:** nostalgia interludes, first chapter of a Part.

#### 24. Noir lighting pass (silhouette duel)
- **Looks like:** gamma/overbright crushed so players read as silhouettes against bright sky or
  lava glow; LG and rail beams become the only light sources. Wolfcam exposes the full r_*
  lighting stack ([cvar list](http://kitteh.maverickservers.com/cvarlist/)).
- **Execute:** ENGINE. Preset: `r_gamma` low, `r_mapOverBrightBits 0`, `r_vertexLight 1`,
  fullbright models off; pick arenas with strong backlight (BSP light-grid query can rank
  candidate camera azimuths that put the sky behind the fight).
- **Suits:** LG tracking duels, rail duels.

#### 25. Teleporter wipe
- **Looks like:** the clip transition rides a telein/teleout event — player enters the portal,
  the teleport flash whites the frame, next clip begins on the flash. A wipe the *game* provides.
- **Execute:** DATA + editing rule. P1-DD already templates `telein/teleout` sounds; parser
  flags EV_PLAYER_TELEPORT events; the clip-cutter prefers cutting exactly on the flash frame.
- **Suits:** movement chains, connecting same-map frags.

#### 26. Ambient b-roll library (map idle shots)
- **Looks like:** 3–6 s locked-off or slow-drift shots of map *life* — flame jets, fog,
  bouncing jump-pad shimmer, the space skybox drift — used as breathers between kill runs.
  Classic movies breathed; modern edits don't.
- **Execute:** ENGINE + DATA. Batch job: for each map in the corpus, auto-capture N ambient
  shots from BSP-derived vantage points (fx-emitting entities are in the entity lump —
  misc_model, fx entities, light styles). Builds a reusable T3-style stock library per map.
- **Suits:** pacing infrastructure; intro/outro pools (feeds P1-B).

---

## 2. TRANSITIONS Catalogue — Scene-to-Scene

The era's craft consensus, verbatim from the community threads: *"Knowing where to cut is far
more important than knowing what transition to use"* and transitions *"really shouldn't be
noticeable to the average viewer on the first viewing"*
([teamfortress.tv thread](https://www.teamfortress.tv/30189/good-transitions-to-use-in-frag-movies)).
Every entry below therefore earns its place by *hiding* the seam or *meaning* something —
never by decorating it. Whip-pan (idea 5), resurrection cut (idea 12) and teleporter wipe
(idea 25) from Section 1 also belong to this catalogue; they are not repeated.

### T1. Motion match cut
- **What:** cut between two clips where the on-screen motion vector continues across the seam —
  strafe-jump arcing left→ next clip opens on a leftward rocket flying the same screen path.
  Classic "match on action" ([StudioBinder taxonomy](https://www.studiobinder.com/blog/match-cuts-creative-transitions-examples/)),
  and the single most invisible cut available.
- **Execute:** DATA + POST. Our parser knows every entity velocity; a matcher scores candidate
  clip pairs by (screen-space motion direction at tail of A) · (motion at head of B) using our
  own camera matrices. Cut on the frame where directions align within ~20°.
- **When:** joining unrelated frags inside one music section; the workhorse mid-chapter cut.

### T2. Geometry match cut
- **What:** frame A ends composed on a strong map shape (arch, jump-pad disc, portal ring);
  frame B opens on a similar shape on another map, same screen position/scale — the "graphic
  match" ([StudioBinder](https://www.studiobinder.com/blog/match-cuts-creative-transitions-examples/)).
- **Execute:** DATA. BSP tooling classifies landmark geometry (patches, discs, arches) per map
  with world-space bounding shapes; the camera recipe for clip B's opening keypoint is solved to
  place the landmark at clip A's closing screen rect.
- **When:** chapter/map changes — makes the map switch feel authored rather than shuffled.

### T3. Rocket-flight bridge
- **What:** camera leaves scene A riding a rocket (projectile follow already planned), flies
  through darkness/sky/fog, and "arrives" as a different rocket entering scene B — one apparent
  projectile connecting two frags. The fragmovie version of the recam cam2cam bridge
  ([q3df DemoCams — automated cam2cam transitions](https://www.q3df.org/wiki?p=138)).
- **Execute:** ENGINE + DATA. Capture A's projectile-follow tail and B's projectile-follow head
  with matched fov/roll; parser picks rocket pairs with similar flight azimuth; the seam hides
  in a 2–4 frame pass through unlit BSP or skybox (BSP query finds where the trail crosses a
  dark volume). Fallback: 0.2 s dip through motion-blurred smoke in post.
- **When:** the showpiece transition — once per Part, into a climax air-rocket.

### T4. Kill-cam whip pan (kill → next victim)
- **What:** on kill A the camera whips off the corpse in the direction of the *next* clip's
  victim; the cut lands mid-blur and the whip completes onto victim B. Whip-pan (idea 5)
  specialized into a narrative device: the camera "hunts" the next target.
- **Execute:** ENGINE. Two fast angle keypoints at A-tail and B-head, same angular direction,
  mme blurFrames smearing both sides ([q3mme blur tutorial](https://q3mme.proboards.com/thread/18)).
- **When:** multikill chains and back-to-back same-map frags; max 2–3 per chapter or it
  becomes seasickness.

### T5. Map fly-through bridge
- **What:** after frag A, the camera lifts and cruises the map spline (idea 2) — but instead of
  fading out, the cruise *ends by descending into frag B's arena* as the fight starts. B-roll
  that is secretly a transition; DeFRaG recams made this roaming-camera connective tissue a
  convention ([DeFRaG](https://en.wikipedia.org/wiki/DeFRaG)).
- **Execute:** ENGINE + DATA. Spline from A's death point to B's engagement zone through
  BSP-validated corridors; timescale slightly >1 during the cruise so it stays under ~6 s.
- **When:** same-map frag pairs separated by downtime; break/verse music sections only.

### T6. Speed-sync cut (timescale handoff)
- **What:** clip A ramps *down* into slow-mo and the cut lands while slow; clip B opens equally
  slow and ramps *up* — the tempo curve is continuous across the seam even though the scene
  changed. The audience feels one gesture, not two clips.
- **Execute:** ENGINE + POST. Both sides captured with matching timescale ramps (or ramped in
  post via our speed_ramp module); rule: cut at the *bottom* of the ramp, on a music downbeat.
- **When:** drop sections; pairing two T1-class frags without demoting either.

### T7. Teleporter pass-through (extended teleporter wipe)
- **What:** stronger form of idea 25: the camera *follows the player into* the teleporter; the
  telein flash whites the frame; scene B opens on a *different* demo's teleporter exit flash —
  the game's own wipe used to travel between demos, maps, even years.
- **Execute:** DATA. Parser indexes EV_PLAYER_TELEPORT events corpus-wide (with map + portal
  entity); the clip-cutter pairs an entry event with any exit event; cut on the white frame.
- **When:** chapter openers, "10 years of demos" montage moments; inherently earns a smile.

### T8. Sound-bridge cut (audio leads picture)
- **What:** the audio of clip B (rocket launch, LG hum, announcer) starts 0.3–0.7 s *before*
  the picture cuts — the classic sound bridge / audio match
  ([StudioBinder](https://www.studiobinder.com/blog/match-cuts-creative-transitions-examples/)).
  Old-school movies did this constantly with the rail charge whine.
- **Execute:** POST. Trivial in our split audio/video graphs (P1-BB): offset B's game-audio bus
  ahead of its video by a lead time. Parser tells us which event sound opens B.
- **When:** everywhere — the cheapest large upgrade to perceived editing quality; default-on
  candidate for hard cuts between clips whose head event is recognized (P1-DD).

### T9. Frag-feed carry (HUD continuity cut)
- **What:** the kill feed / obituary line from clip A stays on screen across the cut into
  clip B and expires naturally there — HUD continuity papering over a scene change. The
  information layer says "same story continuing."
- **Execute:** DATA + POST. We composite obituary lines ourselves (idea 17 infrastructure), so
  persistence across a cut is a compositor rule, not an engine trick.
- **When:** rapid montage segments where clips are 2–4 s each; keeps velocity readable.

### T10. Item-orb match dissolve
- **What:** clip A ends framed on a spinning item (mega, RA); ≤0.4 s dissolve to clip B opening
  framed on the same item type on another map — the era-legal crossfade given a *reason*.
  Community norm: dissolves stay fast (0.10–0.25 s) or they ghost
  ([teamfortress.tv](https://www.teamfortress.tv/30189/good-transitions-to-use-in-frag-movies)).
- **Execute:** DATA. BSP entity lump gives item positions; closing/opening camera keypoints
  frame the item at the same screen rect; xfade ≤0.4 s per P1-H.
- **When:** the only sanctioned dissolve besides plain ≤0.4 s seam xfades; use when tempo drops.

### T11. Corpse-to-spawn time cut
- **What:** hold 8–10 frames on victim A's corpse, hard cut to the *same player model*
  respawning/standing in clip B — death→rebirth ellipsis. Reads as storytelling, costs nothing.
- **Execute:** DATA. Parser matches victim model/skin across clips; the cutter prefers a B clip
  whose opening frames contain that model idle or spawning.
- **When:** between rounds of the same CA match; outro de-escalation sequences.

### T12. Speed-portal wipe (foreground occlusion cut)
- **What:** a foreground object (pillar, doorway edge, passing rocket smoke) sweeps across the
  lens and the cut hides inside the 2–3 fully-occluded frames — the film "wipe by natural
  object." The in-engine version of what modern editors fake with luma masks.
- **Execute:** ENGINE + DATA. BSP query finds pillar/doorframe faces near the camera path; the
  closing keypoints deliberately drag the lens past the occluder; clip B starts behind a similar
  occluder moving the same direction.
- **When:** movement chains and chase-cam sequences; invisible when done right, so unlimited use.

### Transition usage rules (era norms)
1. **Default is the hard cut.** Everything above is an exception with a trigger condition —
   the baseline joint between clips remains a straight cut on the beat grid
   ([teamfortress.tv](https://www.teamfortress.tv/30189/good-transitions-to-use-in-frag-movies): straight cuts "work excellently with proper clip ordering").
2. **One vocabulary per movie.** Pick ≤4 of these per Part and repeat them; a different
   transition every seam reads as a plugin demo reel. ("Using dozens makes videos look
   unfocused" — same thread.)
3. **Crossfade norms of the era:** dissolves exist but stay ≤0.4 s (P1-H) and need a visual
   reason (T10). Fade-to-black lives only at chapter boundaries, never inside one.
4. **Banned:** film burns beyond one ironic use, fire fades ("so overused it's annoying" —
   era consensus), spinning/3D page transitions, flash-frame strobes, lens-dirt overlays.
5. **The seam serves the music.** Showpiece transitions (T3, T5, T7) land on phrase
   boundaries; invisible transitions (T1, T8, T12) can land anywhere the beat grid allows.
6. **Escalation mapping:** verse → T1/T8/T12 (invisible), build → T4/T6 (kinetic),
   drop → hard cuts + effects, break → T5/T10/T11 (breathing), chapter change → T2/T3/T7.

---

## 3. Classic Fragmovie Grammar — Actionable Rules

Distilled from the reception threads on the canon movies (GQ3, AnnihilatioN, Memorial, the ESR
top-3 thread) and era tutorials.

**Pacing**
1. **Chapters, not playlists.** Canon movies are built in 3–6 chapters, each with its own map
   focus, music track, and look. Chapter boundary = flythrough or b-roll + music change. Our
   three-track P1-R contract already maps to this; extend it with a per-chapter look preset
   (fx file + cvar preset, ideas 21/23/24).
2. **One climax per chapter.** Exactly one frag gets the full treatment (multi-angle, dead-air
   hold, dolly zoom). Everything else plays fast. When everything is emphasized, nothing is.
3. **Escalate WITHIN a chapter, reset BETWEEN chapters.** Kill density and effect density rise
   toward the chapter's end; the next chapter opens calm.
4. **Breathe.** ≥10% of a chapter's runtime is non-frag material (flythrough, b-roll, victim
   wandering). GQ3 spent 13 months and 1500+ demos partly on connective tissue
   ([igmdb](https://www.igmdb.org/?m=51)).

**Kill-sync**
5. **The kill lands on the beat; the SETUP is what gets stretched.** Old-school sync shifts
   when a clip *starts* and bends time in the approach so the impact frame hits the downbeat —
   never trimming the frag itself (this is exactly our P1-S/P1-Z doctrine; the research confirms
   it as period-authentic).
6. **Sync density follows the music.** Verse: cut on bars. Build: cut on beats. Drop: cut on
   beats + effects on the kill. Break: one long take, no cuts. (Matches P1-CC section shapes.)
7. **In-game sound survives.** The mix always keeps hit sounds, rail whine, announcer under the
   music. A muted-game-audio movie reads as a slideshow. Announcer hits doubling as stingers
   (idea 18) is period-correct.

**Intro/outro**
8. **Intros are short and map-anchored:** logo → map flythrough → first frag inside 30–40 s.
   Multi-minute 3D-logo intros were mocked even in 2004.
9. **Outros de-escalate:** slowest song, FL slow-mo b-roll, credits over gameplay — never over
   black (consistent with P1-Y).
10. **Name plates, not stat walls.** Player intro = a one-line plate over their first clip,
    bitmap font, ≤2 s. (For our archive: pTn tag styling; public exports keep names anonymized
    per repo rules.)

**Authentic vs cringe**
11. **In-engine beats post-plugin.** The canon look is q3mme motion blur, dof, fov and fx
    scripting — not After Effects glows, twixtor artifacts, or 3D camera projection. If wolfcam
    can do it, do it in wolfcam.
12. **No zoom-punch spam, no flash-transition spam, no lens dirt, no letterbox-for-drama.**
    The permitted transition set stays tiny: hard cut, whip-pan, teleporter wipe, ≤0.4 s xfade
    (P1-H).
13. **Effects need a reason.** Every slow-mo answers "what should the viewer study in this
    frame?" — the pixel gap of a rail, the air time of a rocket. Unmotivated slow-mo is filler.
14. **The HUD is a character.** Old-school movies show real HP/armor/clock when it tells the
    story (low-HP clutch, timer pressure) and hide it for pure-cinema shots. Toggling per shot
    is the grammar; leaving it always-on or always-off is laziness.
15. **Music: one fixed level, action bends to it** (P1-G v6) — also period-authentic: classic
    editors cut picture to the track and never ducked the song.

---

## 4. Feasibility Table

| # | Effect | In-engine (wolfcam/q3mme) | Needs parser/BSP data | Post-production |
|---|--------|---------------------------|-----------------------|-----------------|
| 1 | Visor reflection shot | camera/dof framing | victim head pos + angles | reflection composite |
| 2 | Map fly-through opener | camera spline capture | BSP waypoint autogen (optional) | — |
| 3 | Dolly zoom | camera + fov keyframes | killer/victim positions for math | — |
| 4 | Rack-focus pull | dof target keypoints | kill timestamps | — |
| 5 | Whip-pan transition | fast angle keys + mme blur | — | cut alignment |
| 6 | One-take frag chain | long spline + timescale | frag-cluster mining query | — |
| 7 | POV dive-in | spline → FP handoff | ps.origin/viewangles at cut | hard-cut assembly |
| 8 | Platform dolly mount | camera keys | mover entity tracks | — |
| 9 | Through-frame composition | camera + dof | BSP portal/doorframe query | — |
| 10 | Dutch-angle roll | camera roll keys | — | — |
| 11 | LG-shaft axis cam | camera keys | attacker angles + origins, LG accuracy | — |
| 12 | Resurrection cut | high-fps death capture | death event times | ffmpeg reverse |
| 13 | Round hyperlapse | timescale >1 + spline | round start/end times | — |
| 14 | Frame-hold stutter | — | beat grid (beats.json) | ffmpeg frame hold |
| 15 | Pre-kill dead-air hold | (capture as-is) | climax-frag selection | trim-exception flag |
| 16 | Item-cycle overlay | — | pickup events, spawn cycle, BSP item pos, camera matrix | overlay composite |
| 17 | Delayed obituary reveal | HUD-off capture | obituary text/weapon/time | feed composite |
| 18 | Announcer stingers | — | P1-DD event recognition | audio placement |
| 19 | Clock-pressure outro | HUD clock capture | server_time / round timer | stylized clock option |
| 20 | Gib-follow shot | gib cvars + freecam arc | death point/time | — |
| 21 | Per-section FX reskin | fx-script variants + cg_fxfile | — | — |
| 22 | FX impact shake | fx `vibrate` property | — | — |
| 23 | Retro-crunch pass | picmip/vertexlight preset | — | — |
| 24 | Noir lighting pass | r_gamma/overbright preset | BSP light/sky azimuth ranking (optional) | — |
| 25 | Teleporter wipe | — | EV_PLAYER_TELEPORT flags | cut-on-flash rule |
| 26 | Ambient b-roll library | batch ambient capture | BSP entity-lump vantage autogen | — |

### Transitions feasibility

| # | Transition | In-engine (wolfcam/q3mme) | Needs parser/BSP data | Post-production | Difficulty |
|---|-----------|---------------------------|-----------------------|-----------------|------------|
| T1 | Motion match cut | — | velocity vectors + camera matrices, pair scoring | frame-accurate cut | Medium |
| T2 | Geometry match cut | opening keypoint solve | BSP landmark classifier | — | Hard |
| T3 | Rocket-flight bridge | projectile-follow captures | rocket-pair mining, dark-volume query | optional smoke dip | Hard |
| T4 | Kill-cam whip pan | fast angle keys + mme blur | next-victim position | cut alignment | Easy |
| T5 | Map fly-through bridge | spline + timescale | BSP corridor pathing, engagement zones | — | Medium |
| T6 | Speed-sync cut | timescale ramps | beat grid | speed_ramp matching | Easy |
| T7 | Teleporter pass-through | follow-cam into portal | corpus-wide EV_PLAYER_TELEPORT index | cut-on-flash | Medium |
| T8 | Sound-bridge cut | — | head-event recognition (P1-DD) | audio-lead offset (P1-BB graphs) | Easy |
| T9 | Frag-feed carry | HUD-off capture | obituary data | feed compositor rule | Easy |
| T10 | Item-orb match dissolve | framing keypoints | BSP item positions | ≤0.4 s xfade | Medium |
| T11 | Corpse-to-spawn cut | — | model/skin matching across clips | hard cut | Easy |
| T12 | Speed-portal wipe | camera path past occluder | BSP occluder-face query | — | Medium |

---

*Cross-references: P1-G/P1-H/P1-S/P1-Z/P1-CC (render rules these ideas must respect),
`docs/reference/wolfcam-commands.md` (FT-4 command inventory),
`docs/reference/effects-catalog.md` (existing planned effect set),
`docs/reference/highlight-criteria.md` (frag classes).*
