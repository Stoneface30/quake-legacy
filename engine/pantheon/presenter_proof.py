"""DIEGETIC_PRESENTER_PROOF_01 — Crash introduces the game, from inside it.

WHAT THIS PROVES, in one short scene: a named Quake character stands in
Campgrounds, turns to the camera, speaks in his OWN recorded voice, walks,
introduces a second character who gestures and answers in a synthesised voice,
and then that second character hides behind a wall and XRAY finds him.

It deliberately teaches NOTHING about Clan Arena. The grammar has to work
before it carries a lesson.

VOICE PROVENANCE IS VISIBLE IN THE SCRIPT. Four of the five spoken lines are
real Quake Live tutorial recordings -- Crash already said them. Only the two
lines Crash never recorded are synthesised.

    python -m engine.pantheon.presenter_proof
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from engine.pantheon.frame_truth import FrameTruth
from engine.pantheon.navigation import NavigationTruth
from engine.pantheon.presenter import Stage
from engine.pantheon.scenario import RoundScenario, Team, Weapon
from engine.pantheon.voice import GameVoiceBank

NAV_CACHE = Path(".tmp/nav_campgrounds.json")
TRANSCRIPTS = Path(".tmp/voice/crash_transcripts.json")
TTS = Path(".tmp/voice/tts")

# The guide is Crash wearing his own trainer skin -- the character Quake Live
# actually casts as its teacher. `models/players/crash/{head,upper,lower}_
# trainer.skin` ship in pak00.
GUIDE_MODEL, GUIDE_SKIN = "crash", "trainer"
ENEMY_MODEL, ENEMY_SKIN = "keel", "bright"
# The `bright` skin family is tinted by the player's c1 colour index, so two
# different models pinned at the same c1 render as the same flat green -- which
# is exactly what the first capture showed. Guide and enemy get separate
# indices so the audience can tell who is speaking without a nameplate.
GUIDE_C1, ENEMY_C1 = "1", "3"

DURATION = 26.0
XRAY_FROM = 20.5          # when the reveal beat starts


def build(out_dir: Path, *, map_name: str = "campgrounds"):
    nav = NavigationTruth.for_map(map_name, cache=NAV_CACHE)
    bank = GameVoiceBank.from_transcripts(TRANSCRIPTS)
    route = nav.route()
    leg = route.thinned()
    wall = nav.wall_separated_pair()

    # The camera stands where a person would stand to be talked to: back along
    # the route, far enough that a whole body is in frame.
    guide_spot = leg[2]
    eye = min((p for p in leg if math.dist(p, guide_spot) > 130),
              key=lambda p: abs(math.dist(p, guide_spot) - 240), default=leg[-1])

    scn = RoundScenario.clan_arena(map_name=map_name,
                                   hostname="PANTHEON DIEGETIC PRESENTER")
    stage = Stage(scn, camera_at=eye, looking_at=guide_spot)

    guide = stage.presenter("CRASH", Team.RED, model=GUIDE_MODEL,
                            skin=GUIDE_SKIN, profile="GUIDE",
                            c1=GUIDE_C1, c2=GUIDE_C1)
    enemy = stage.presenter("KEEL", Team.BLUE, model=ENEMY_MODEL,
                            skin=ENEMY_SKIN, profile="KEEL",
                            c1=ENEMY_C1, c2=ENEMY_C1)

    # Keel starts beside the guide, then goes behind the wall at the end.
    enemy_spot = leg[4] if len(leg) > 4 else leg[-1]
    guide.stand_at(guide_spot, facing=eye, t=0.0)
    enemy.stand_at(enemy_spot, facing=eye, t=0.0)

    # ── SHOT 1: the guide introduces himself, in his own voice ──────────
    t = 1.0
    t = guide.say_line(bank.find_one("welcome"), t=t)          # real Crash
    t = guide.say_line(bank.find_one("my name"), t=t + 0.35)   # real Crash
    guide.hold(until=t + 0.4)

    # ── SHOT 2: he walks, and names the place ───────────────────────────
    walk_from, walk_to_ = t + 0.4, t + 3.4
    guide.walk_to(leg[2:5], during=(walk_from, walk_to_))
    t = guide.say_line(bank.find_one("fighting arenas"), t=walk_from + 0.5)
    guide.hold(until=t + 0.3)

    # ── SHOT 3: the enemy greets the camera ─────────────────────────────
    t += 0.5
    guide.look_at(enemy, t=t - 0.2)
    enemy.gesture(t=t)
    t = enemy.say_synth("Hello. I am the enemy.", TTS / "keel_hello.wav", t=t + 0.3)
    enemy.hold(until=t + 0.3)

    # ── SHOT 4: what the enemy is FOR ───────────────────────────────────
    t += 0.4
    t = guide.say_line(bank.find_one("main objective"), t=t)   # real Crash
    guide.hold(until=t + 0.3)

    # ── SHOT 5: the enemy hides, and XRAY finds him ─────────────────────
    hide_from = t + 0.3
    if wall:
        # a real wall-separated position, mined from where players walked
        enemy.walk_to([enemy_spot, wall[1]], during=(hide_from, hide_from + 2.2))
    t = guide.say_synth("Keep an eye on him.", TTS / "guide_watch.wav",
                        t=hide_from + 2.4)
    guide.hold(until=DURATION - 1.0)
    enemy.hold(until=DURATION - 1.0)

    out_dir.mkdir(parents=True, exist_ok=True)
    demo = scn.compile(duration=DURATION).save(
        out_dir / "DIEGETIC_PRESENTER_PROOF_01.dm_73")
    truth = FrameTruth.from_scenario(scn, duration=DURATION)
    truth.save(out_dir / "DIEGETIC_PRESENTER_PROOF_01.frametruth.json")

    track = stage.dialogue_track()
    for cue in track:
        c = next(c for c in stage.cues if c.start_t == cue["start_t"])
        pan, dist = stage.pan_and_distance(c, truth)
        cue["pan"], cue["distance"] = round(pan, 3), round(dist, 3)
    (out_dir / "DIEGETIC_PRESENTER_PROOF_01.dialogue.json").write_text(
        json.dumps({"duration_s": DURATION, "xray_from": XRAY_FROM,
                    "cues": track}, indent=1), encoding="utf-8")
    return demo, stage, truth, track


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=Path(".tmp/synthetic"))
    args = ap.parse_args()
    demo, stage, truth, track = build(args.out)
    print(f"demo  : {demo}  ({demo.stat().st_size:,} bytes)")
    print(f"truth : {len(truth.frames)} frames\n")
    print("dialogue track:")
    for c in track:
        kind = "GAME " if c["source_kind"] == "GAME_ASSET" else "SYNTH"
        print(f"  {c['start_t']:5.2f}-{c['end_t']:5.2f}s [{kind}] "
              f"{c['actor_id']:6s} pan={c['pan']:+.2f} \"{c['text'][:58]}\"")
    return 0


if __name__ == "__main__":                     # pragma: no cover - CLI
    raise SystemExit(main())
