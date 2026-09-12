"""Trait rules v3 -- every trait re-derived from the recorder's calibration notes.

Each entry: (group, new_policy, new_rule, why_from_notes).
Policies:
  HERO     -- can carry a round on its own.
  SUPPORT  -- modifier only: raises a hero moment, never makes one.
  LANE:x   -- leaves round scoring; feeds its own compilation lane
              (TELEFRAG, BLOOPER, TRANSITION, EFFECT, INSTAGIB).
  BASE     -- not a trait: the plain kill value every frag already has.
  RETIRE   -- removed.

GLOBAL rules apply to every trait before its own rule (see GLOBAL below).
Nothing here changes a detector until the recorder validates the page.
"""

GLOBAL = [
    ("G1 Recorder only",
     "Every trait requires killer == the demo's recorder AND the recorder in "
     "the game (team RED/BLUE/FREE, not SPECTATOR) at that tick.",
     "'not me' x6 (DIRECT_ROCKET, LG_HIGH_ACCURACY, MULTI_WEAPON_CHAIN, "
     "VERTICAL_ACTION, MULTIKILL_QUAD, MULTIKILL_PENTA 'was I even in this "
     "game?'); HERO_THEN_DEATH 'I am just speccing someone'; GAUNTLET_KILL "
     "'me getting gauntlet' x3."),
    ("G2 Gametype lanes",
     "CA is the main lane. CTF-instagib, TDM, DUEL, FFA, CTF are separate "
     "lanes, never mixed with CA ranking. TDM and FFA are discounted.",
     "'CTF Instagib so dedicated category', 'TDM' x7 (all DROP/DISCOUNT), "
     "'its duel' DROP, 'FFA gameplay pointless'."),
    ("G3 A moment needs my kill",
     "No-kill traits never make a moment. They may only attach to a round "
     "that already has a recorder kill, or go to the BLOOPER lane.",
     "'Nothing happen' x6, 'no kill here', 'shot need to do something, if "
     "just shot and die its useless'."),
    ("G4 Melee and telefrag are not aim",
     "Aim/flick/sweep/HP/rocket-jump traits exclude GAUNTLET and TELEFRAG "
     "kills. Telefrags go to the TELEFRAG lane.",
     "'just a gauntlet frag' x3 on AGGRESSIVE_TRACKING_SWEEP/EXTREME_FLICK/"
     "CLEAN_FLICK; 'just a telefrag' on FLICK_SHOT, CRITICAL_HP_FRAG, "
     "ROCKET_JUMP_ENTRY."),
    ("G5 Series beat singles",
     "Consecutive recorder kills in one round multiply: a moment's value "
     "grows with each extra kill inside 6 s (rails, rockets, shafts).",
     "'serie' x9, 'double kill are excellent', '3 rail in a row', '4 frag "
     "is excellent', 'rail in a row are excellent!'."),
    ("G6 Whole round",
     "Clips are whole rounds (countdown -> my death / round end). Already "
     "done in round-first V2; kept.",
     "'need all round', 'cut too soon', 'can only see 3 frags', 'full round "
     "should be easier', 'need more of the round' x5."),
    ("G7 The v2 detectors must run on the whole corpus",
     "The v2 detectors (flick, LG, projectile, visibility, dodge, health) "
     "only ever labelled 2,560 frags; the Sep-8 v4 rescan rewrote the "
     "other 34,047 without them. The full rescan runs all enrichment "
     "stages first, then classification.",
     "Your highest-rated traits (TINY_GAP_SHOT, PIXEL_SHOT_GEO, DODGE_HERO, "
     "LG_HIGH_PRESSURE, NEAR_DIRECT...) show 0 rounds in round scoring."),
    ("G8 LG is about accuracy",
     "LG traits use LG-only accuracy for the engagement (beam contact ticks "
     "/ fire ticks), not the scoreboard total. 35% = SUPPORT, 45% = HERO.",
     "'High LG accuracy is excellent, 35% is good, 45% is HUGE'; 'lg acc "
     "should be the point' x2."),
    ("G9 Saved-by-me demos",
     "The small demos are moments I cut and saved myself. The source moment "
     "in the full demo gets SAVED_BY_RECORDER (strong prior + ground "
     "truth). Moments that exist only in a small demo are scanned as "
     "single-action units, not rounds.",
     "Your instruction: small demos are records of one action, not full "
     "rounds."),
    ("G10 Clanwar tag",
     "New trait CLANWAR_MATCH from clan tags / team names in the "
     "configstrings; its own lane and a round bonus.",
     "'big teamfight, maybe its a clanwar so should get clanwar tag'."),
]

R = {
 # ── aim ──────────────────────────────────────────────────────────────────
 "FLICK_SHOT": ("aim", "SUPPORT",
   "Old view-speed flick (>=220 deg/s). Excludes gauntlet/telefrag (G4). "
   "Superseded as a hero by CLEAN_FLICK / EXTREME_FLICK.",
   "MED/LOW: 'normal rocket frag', 'just a telefrag'. 2,312 hits = too loose."),
 "CLEAN_FLICK": ("aim", "HERO",
   ">=50 deg in <=300 ms, <=1 reversal, humanly possible. Excludes "
   "gauntlet/telefrag.", "HIGH/MED, but a gauntlet kill misfired."),
 "EXTREME_FLICK": ("aim", "HERO",
   ">=90 deg, <=350 ms, >=350 deg/s, clean. Excludes gauntlet.",
   "HIGH x3; 'just a gaun' is the one misfire."),
 "RAIL_FLICK": ("aim", "HERO",
   "Rail + EXTREME_FLICK tier only (>=90 deg); CA lane. Instagib goes to the "
   "INSTAGIB lane.", "'big flick' GOLDEN; 'CTF insta just one frag is nothing'."),
 "AGGRESSIVE_TRACKING_SWEEP": ("aim", "SUPPORT",
   ">=80 deg over >=400 ms. Excludes gauntlet. Modifier only.",
   "'just a gaunlet frag' x2; 'good but need the rest'."),
 "LARGE_AIM_TRANSITION": ("aim", "HERO", "Unchanged (>=120 deg transition).",
   "GOLDEN 'air rocket reflex', HIGH 'good combo'."),
 "HIGH_SPEED_AIM_TRANSITION": ("aim", "HERO",
   "Unchanged, plus the series multiplier (G5).",
   "GOLDEN x2: '3 rail in a row and the last one is a huge 360'."),
 "TARGET_TRANSFER": ("aim", "HERO", "Unchanged; the whole round fixes the cut.",
   "HIGH x3; 'shaft series but cut too soon'."),
 "LG_TRANSFER": ("aim", "HERO", "LG->LG transfer AND engagement LG accuracy >=35% (G8).",
   "H/M/G; 'good lg high acc should be the trait for lightning gun'."),
 "SNAP_ON_ARRIVAL": ("aim", "HERO", "Unchanged.", "HIGH/HIGH/MED: 'nice prediction rocket'."),
 "REACTION_SHOT": ("aim", "HERO", "Unchanged (LOS open <=250 ms).",
   "GOLDEN x2: 'double kill are excellent', 'big shot'."),
 "REACTION_SHOT_CANDIDATE": ("aim", "HERO", "CA lane only; duel moves to the DUEL lane.",
   "GOLDEN x2; LOW 'Duel action'."),
 # ── precision ────────────────────────────────────────────────────────────
 "TINY_GAP_SHOT": ("precision", "HERO", "Unchanged (visible <=12%). Runs corpus-wide (G7).",
   "GOLDEN x3: 'this trait is excellent'. Top trait."),
 "PIXEL_SHOT_GEO": ("precision", "HERO", "Unchanged (visible <=25%, <=3 deg). Corpus-wide.",
   "GOLDEN 'nice pixel shot', HIGH."),
 "PIXEL_SHOT_CANDIDATE": ("precision", "SUPPORT", "Long rail before visibility proof; "
   "upgraded to PIXEL_SHOT_GEO when stage-2 confirms.", "Not rated; kept as a pointer."),
 "CORNER_PREFIRE_CONFIRMED": ("precision", "HERO", "Unchanged. Corpus-wide.",
   "GOLDEN 'big rail', HIGH 'nade spam on tele exit, nice to keep'."),
 "RAIL_FRAG": ("precision", "BASE", "Plain rail kill: base kill value, no trait bonus.",
   "MED 'normal rail'. 8,011 hits."),
 "DIRECT_ROCKET": ("precision", "BASE", "Plain direct rocket: base kill value.",
   "MED 'ok frag'; DROP 'TDM not me'. 3,258 hits."),
 "RAIL_CONSECUTIVE": ("precision", "HERO", "CA: >=3 rails within 6 s. 2 rails = SUPPORT. "
   "Instagib -> INSTAGIB lane.", "MED x2: 'CTF Instagib so dedicated category'."),
 "RAIL_AIR": ("precision", "SUPPORT", "Victim >=90 u above ground (meaningful air), "
   "not a hop.", "HIGH once, LOW, DROP."),
 "DIRECT_CONFIRMED_GEO": ("precision", "HERO", "Unchanged. Corpus-wide.",
   "HIGH 'nice gren to track', MED 'big long distance rocks'."),
 "NEAR_DIRECT": ("precision", "HERO", "Promoted from SUPPORT. Corpus-wide.",
   "GOLDEN x2: 'best nade ever, specific angle', 'real nice air'."),
 "AIR_ROCKET": ("precision", "HERO", "Unchanged.", "HIGH 'easy peasy', MED."),
 "AIR_ROCKET_GEO": ("precision", "HERO", "Unchanged (victim vz >=250). Corpus-wide.",
   "GOLDEN 'big big air rocket', HIGH x2."),
 "AIR_GRENADE": ("precision", "HERO", "Unchanged.", "HIGH x2 'real nice nade'."),
 "PREDICTION_CANDIDATE": ("precision", "HERO", "Unchanged; teleport-exit preshots included.",
   "GOLDEN x2: 'preshot rock in tp'."),
 "PREDICTION_TEMPORAL": ("precision", "HERO", "Unchanged; jump-pad targets included.",
   "GOLDEN 'the jump pad rocket', HIGH 'perfect rocket for fpv'."),
 "SPLIT_TICK_DOUBLE": ("precision", "HERO", "Recorder only; instagib -> INSTAGIB lane.",
   "GOLDEN x2: 'Doublerail!'."),
 "COLLATERAL_DAMAGE": ("precision", "HERO",
   "Only when ONE recorder splash kills TWO enemies (<=50 ms). A splash "
   "touch without a double kill = nothing.",
   "HIGH x2 'nice double rocket splash frag'; DROP 'just touch a guy with splash'; LOW 'just a rail'."),
 "POINT_BLANK": ("precision", "SUPPORT", "Unchanged.", "LOW 'panic kill', MED x2."),
 "SHOTGUN_SNIPE": ("precision", "RETIRE", "Removed.", "LOW x3."),
 "UPSHOT_KILL": ("precision", "HERO",
   "HERO only when LG/rocket on a victim launched by a jump pad or knockback "
   "(the 'bump'). A rail upshot = SUPPORT.",
   "GOLDEN 'shaft on the bump, these frags are excellent'; LOW x2 'normal rail frag'."),
 "PLUNGE_KILL": ("precision", "SUPPORT", "Unchanged.", "HIGH x2, MED."),
 "VERTICAL_ACTION": ("precision", "SUPPORT", "Recorder only (G1).",
   "DROP 'not me'; HIGH 'rocket through a tight corner'."),
 # ── movement / speed ─────────────────────────────────────────────────────
 "HIGH_SPEED_FRAG": ("movement", "SUPPORT", "p90 attacker speed; CA only.",
   "DROP 'TDM', MED 'need context'. 3,050 hits."),
 "VERY_FAST_FRAG": ("movement", "HERO", "Unchanged (p97).", "HIGH x2 'good owned 1v1'."),
 "EXTREME_SPEED": ("movement", "HERO", "Unchanged (p99).", "GOLDEN 'nice rocket fight'."),
 "HIGH_SPEED_AIR_FRAG": ("movement", "RETIRE", "Removed as a standalone.",
   "DROP x2 'nothing good here'."),
 "SPEED_TARGET_FRAG": ("movement", "SUPPORT", "Unchanged; CA only.", "MED; DISCOUNT 'TDM'."),
 "HIGH_SPEED_MULTIKILL": ("movement", "HERO", "Unchanged; instagib -> INSTAGIB lane.",
   "GOLDEN 'big', HIGH 'CTF instagib but nice serie'."),
 "STRAFE_CHAIN_FRAG": ("movement", "RETIRE", "Removed.", "LOW x2, DROP."),
 "ROCKET_JUMP_FRAG": ("movement", "SUPPORT",
   "Requires the recorder's own rocket fire <=300 ms before the vertical "
   "impulse (a jump pad is not a rocket jump).", "MED, LOW, DROP."),
 "ROCKET_JUMP_ENTRY": ("movement", "SUPPORT",
   "Same own-rocket requirement; excludes telefrag.",
   "MED 'telefrag' and MED 'low hp rail' = misfires."),
 "DODGE_AND_KILL": ("movement", "RETIRE",
   "Direction-change proxy removed; DODGE_TO_KILL replaces it.",
   "10,677 hits, 'cant see much'."),
 "ESCAPE_TURNAROUND": ("movement", "RETIRE", "Yaw proxy removed.", "MED once, 'seen' x2."),
 "DODGE_STRAFE": ("movement", "SUPPORT", "Unchanged.", "GOLDEN once, HIGH, MED."),
 "DODGE_TO_KILL": ("movement", "HERO", "Promoted: measured dodge then my kill <=2 s.",
   "GOLDEN x2: 'lg that stuck in air are super trait'."),
 "DODGE_HERO": ("movement", "HERO", "Promoted: top-2% dodge evidence. Corpus-wide.",
   "GOLDEN x2: 'the jump over the rocket'."),
 "RAIL_DODGE_HERO": ("movement", "SUPPORT", "Unchanged.", "HIGH once, LOW x2."),
 "PROJECTILE_DODGE_HERO": ("movement", "SUPPORT", "Unchanged; the kill carries it.",
   "Rated for the rocket kill, not the dodge."),
 "LG_DODGE_MASTER": ("movement", "HERO", "Promoted.", "HIGH x2 'these lg fights are excellent'."),
 "NEAR_MISS_RAIL": ("movement", "RETIRE", "Standalone removed; the data feeds DODGE_TO_KILL.",
   "'the near miss useless'."),
 "NEAR_MISS_ROCKET": ("movement", "RETIRE", "Same.", "'nothing about the dodge'."),
 "NEAR_MISS_GRENADE": ("movement", "RETIRE", "Same.", "'okay dodge from the enemy gren'."),
 # ── LG ───────────────────────────────────────────────────────────────────
 "LG_HIGH_ACCURACY": ("lg", "HERO",
   "Rebuilt: LG-only engagement accuracy. >=45% = HERO, >=35% = SUPPORT "
   "(was the whole-match scoreboard number).",
   "'35% accuracy is good 45% is HUGE'; DROP 'TDM not me'."),
 "LG_TRACKING": ("lg", "HERO",
   ">=1.0 s continuous contact and >=60 damage in the engagement. A "
   "finish-off tick = nothing. Victim lifted (vz>0) while tracked = HERO.",
   "GOLDEN 'lifting enemy with lg'; LOW 'bad lg frag just finishing'."),
 "LG_HIGH_PRESSURE": ("lg", "HERO", "Unchanged. Corpus-wide.", "HIGH x3 'big shaft!'."),
 "DAMAGE_BURST": ("lg", "HERO", "Promoted. Corpus-wide.", "HIGH x3 'big shaft'."),
 # ── multi-kill / combo ───────────────────────────────────────────────────
 "MULTIKILL_DOUBLE": ("multi", "HERO", "Unchanged + series multiplier (G5).",
   "GOLDEN 'big round from me'."),
 "MULTIKILL_TRIPLE": ("multi", "HERO", "Unchanged.", "HIGH x2."),
 "MULTIKILL_QUAD": ("multi", "HERO", "Recorder in-game check (G1).",
   "GOLDEN; DROP 'not mine'."),
 "MULTIKILL_PENTA": ("multi", "HERO", "Recorder in-game check (G1).",
   "'Its not me, was I even in this game?'."),
 "RAPID_MULTIKILL": ("multi", "HERO", "Unchanged.", "HIGH 'good serie'."),
 "MULTI_WEAPON_CHAIN": ("multi", "HERO", "Recorder only.", "HIGH 'triple kill!'; DROP 'TDM not me'."),
 "WEAPON_COMBO": ("multi", "HERO", "Unchanged; clanwar tag when detected (G10).",
   "GOLDEN 'big teamfight, clanwar'."),
 "COMBO_KILL": ("multi", "HERO", "Unchanged.", "GOLDEN 'ownage'."),
 "WEAPON_TRIPTYCH": ("multi", "HERO",
   "Fix: detector skipped the duplicate-observation filter (same kill "
   "counted from copies) -> best observation only, recorder only.",
   "GOLDEN '4 frag excellent'; 'its the same clip'; 'the trait that triggered it is not good'."),
 "FAST_WEAPON_SWITCH": ("multi", "SUPPORT", "Unchanged.", "GOLDEN once 'need more of the round'."),
 "WEAPON_SWITCH_FINISH": ("multi", "SUPPORT", "Unchanged.", "MED 'big shaft', DROP."),
 "POPUP_COMBO": ("multi", "SUPPORT", "Demoted to SUPPORT: needs victim air >=90 u.",
   "GOLDEN once; MED x2 'ok rail', 'action is shit'."),
 # ── round context ────────────────────────────────────────────────────────
 "CLUTCH_1V2": ("round", "HERO", "Unchanged.", "MED 'good 1v2', 'need all round'."),
 "CLUTCH_1V3": ("round", "HERO", "Unchanged; the whole round shows every frag.",
   "'can see only one frag' x2 -> fixed by round units."),
 "CLUTCH_1V4_PLUS": ("round", "HERO", "Unchanged. Corpus-wide.", "GOLDEN x2."),
 "CLUTCH_1VN": ("round", "RETIRE",
   "Merged into CLUTCH_1V2/1V3/1V4_PLUS (it fired on ANY kill while last "
   "alive).", "LOW 'just a rail kill', MED '2v2'. 2,833 hits."),
 "CLUTCH_ROUND_WIN": ("round", "HERO", "Unchanged.", "GOLDEN 'real nice 2 rail for the win'."),
 "LAST_MAN_STANDING": ("round", "SUPPORT + LANE:EFFECT",
   "Round window extended to include the LMS announcer; feeds the EFFECT lane.",
   "GOLDEN 'huge pixel rail'; 'need to hear the last man standing, awesome for transition'."),
 "ROUND_WINNING_FRAG": ("round", "SUPPORT + LANE:EFFECT",
   "Feeds the EFFECT lane (end-of-round rail sequences).",
   "'could be an effect when its end rail round'."),
 "ROUND_OPENING_FRAG": ("round", "SUPPORT", "Unchanged; the countdown feeds transitions.",
   "LOW 'teamfight', HIGH 'nice 1v1'."),
 "FIRST_BLOOD": ("round", "SUPPORT", "Unchanged.", "HIGH 'nice push', LOW."),
 "OUTNUMBERED_FRAG": ("round", "SUPPORT", "Unchanged.", "HIGH 'nice rail, need longer round'."),
 "TRADE_KILL": ("round", "SUPPORT", "Unchanged, lowest modifier.", "LOW x2, MED."),
 "REFRAG": ("round", "LANE:BLOOPER", "Leaves scoring; funny when a friend baits.",
   "LOW x3: 'refrag is not super nice in quake, maybe for funny moment'."),
 "REVENGE_FRAG": ("round", "RETIRE", "Removed.", "LOW x3: 'this trait is useless'."),
 "ECONOMY_KILL": ("round", "RETIRE", "Removed (fired with no kill of mine).",
   "DROP x3 'no kill here', LOW x2."),
 "INSTANT_TRADE": ("round", "LANE:BLOOPER", "Leaves scoring.",
   "'trait not defined at all, this look like shit', 'just me spamming'."),
 "KILL_THEN_DEATH_FAST": ("round", "LANE:TRANSITION", "Leaves scoring; kill->death cut material.",
   "LOW, DROP: 'rush in, kill one, get destroyed'."),
 "HERO_THEN_DEATH": ("round", "LANE:TRANSITION", "Recorder in-game check; transition material.",
   "LOW x3 'can be used for transition'; DROP 'I am just speccing'."),
 "FROM_THE_GRAVE": ("round", "LANE:TRANSITION",
   "Recorder must be the killer (detector was not recorder-scoped).",
   "'can be used as filler and death for transition'; DROP 'FFA pointless'."),
 "DIED_WITH_SHOT_IN_FLIGHT": ("round", "RETIRE", "Removed.", "DROP x2 'useless'."),
 "SHOT_DENIED": ("round", "RETIRE", "Removed.", "'whats the trait of this'."),
 "SHARED_FIREFIGHT": ("round", "RETIRE", "Removed.", "'trait is not good trigger'."),
 "CHAT_REACTION_NEARBY": ("round", "SUPPORT",
   "Only attached to a round where I killed the player who chatted, within "
   "10 s (the rage reaction). Alone = nothing.",
   "DROP x2 'nothing happen'; but 'him raging in the chat' made MID_TELEPORT_DENIAL GOLDEN."),
 # ── health ───────────────────────────────────────────────────────────────
 "LAST_HP_CANDIDATE": ("health", "SUPPORT + LANE:EFFECT", "<=5 HP; feeds a low-HP effect.",
   "GOLDEN/HIGH but for the shots; 'low hp effect'."),
 "LAST_HP_FRAG": ("health", "SUPPORT", "Unchanged.", "MED 'clutch 1v1', LOW 'just a rail'."),
 "CRITICAL_HP_FRAG": ("health", "SUPPORT", "Excludes telefrag.", "MED 'telefrag' misfire."),
 "LOW_HP_FRAG": ("health", "SUPPORT", "Unchanged.", "HIGH x2 'nice serie'."),
 "LOW_HEALTH_WIN": ("health", "SUPPORT", "Requires MY kill to be the round-winning one.",
   "'not me doing the winning frag'; DROP; LOW 'TDM'."),
 "HEAVY_DAMAGE_SURVIVED": ("health", "SUPPORT", "Unchanged.", "GOLDEN 'super pixel rail'."),
 "OVERKILL_BLOW": ("health", "SUPPORT", "Flavour only.", "MED x2, LOW."),
 "RECORDER_DOMINANT": ("health", "SUPPORT", "Unchanged, lowest modifier.", "LOW '1v1 when i bait him'."),
 "DAMAGE_DEALT_ROUND": ("health", "SUPPORT", "NEW: high damage in the round (recorder playerstate).",
   "'big round from me high damage + round win + kills'."),
 # ── melee / teleport / world ─────────────────────────────────────────────
 "GAUNTLET_KILL": ("misc", "SUPPORT", "Killer == recorder (it counted ME being gauntleted).",
   "LOW x2 'me getting gaunlet'."),
 "GAUNTLET_INTERRUPT": ("misc", "SUPPORT", "Killer == recorder.",
   "HIGH '2 hits and I walk up to him'; LOW 'me getting gaunlet'."),
 "TELEFRAG": ("misc", "LANE:TELEFRAG", "Own compilation lane; never a round hero.",
   "HIGH x3: 'for the telefrag compilation / filler'."),
 "MID_TELEPORT_DENIAL": ("misc", "HERO + LANE:EFFECT",
   "Unchanged; also feeds teleport / enemy-POV effects.",
   "GOLDEN x2: 'frags of them going out of teleport are real good'."),
 "ENVIRONMENTAL_DEATH": ("misc", "LANE:BLOOPER", "Recorder's own void/lava death, or my push.",
   "'Keep for blooper'; DROP 'dies before void'."),
 "SELF_DAMAGE_DEATH": ("misc", "LANE:BLOOPER", "Blooper lane; CA only.", "DROP 'its duel'."),
 "RING_OUT": ("misc", "RETIRE", "Removed.", "DROP x3."),
 "SAVED_BY_RECORDER": ("misc", "SUPPORT", "NEW (G9): I saved this moment as its own demo.",
   "Your small-demo instruction."),
 "CLANWAR_MATCH": ("misc", "LANE:CLANWAR", "NEW (G10).", "'should get clanwar tag'."),
}
