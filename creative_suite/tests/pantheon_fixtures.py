"""Hand-built PerformanceTraces in the exact shape the extractor produces.

No demo on disk is needed for the headless unit tests: these traces carry
a jump-pad launch, an airborne stretch, a rocket fired mid-air with its
missile samples, an impact and an obituary, so every headless stage has
something real-shaped to chew on.
"""
from __future__ import annotations

import math

from engine.pantheon.performance import (ActionEvent, AimSample, AnimSample,
                                         PerformanceTrace, ProjectileSample,
                                         TransformSample, WeaponSample)

START = 500_000
STEP = 25


def jumppad_rocket_trace(n: int = 60, start: int = START, client: int = 5,
                         victim: int = 1) -> PerformanceTrace:
    """RUN -> JUMP_PAD (i=10) -> AIRBORNE -> FLICK + FIRE ROCKET (i=18)
    -> PROJECTILE (i=18..29) -> MISSILE_HIT (i=30) -> OBITUARY (i=30) -> LAND (i=34)."""
    tr = PerformanceTrace(demo_hash="fixture", map="campgrounds", gametype="CA",
                          client=client, start_ms=start, end_ms=start + STEP * (n - 1))
    air = range(10, 34)
    for i in range(n):
        t = start + STEP * i
        z = 24.0 + (60.0 * math.sin(math.pi * (i - 10) / 24) if i in air else 0.0)
        o = (100.0 + 8.0 * i, 50.0 - 3.0 * i, z)
        vz = 990.0 if i == 10 else (400.0 - 40.0 * (i - 10) if i in air else 0.0)
        v = (320.0, -120.0, vz)
        tr.transform.append(TransformSample(t, o, v, math.hypot(v[0], v[1]),
                                            i in air, 1023 if i in air else 1022))
        yaw = 30.0 + (4.5 * i if i < 15 else 4.5 * 15 + 40.0 * min(1.0, (i - 15) / 2.0))
        prev_yaw = tr.aim[-1].yaw if tr.aim else yaw
        rate = ((yaw - prev_yaw + 180) % 360 - 180) / (STEP / 1000.0)
        tr.aim.append(AimSample(t, yaw % 360.0, -12.0 + 0.5 * i, round(rate, 1), 0.0))
        legs = 18 if i in air else (19 if i in (34, 35) else 15)
        tr.animation.append(AnimSample(t, legs, 7 if 18 <= i <= 22 else 11, i % 2 == 0, False))
    tr.weapon.append(WeaponSample(start, 5))
    for i in range(18, 30):
        t = start + STEP * i
        tr.projectiles.append(ProjectileSample(t, 200, 5, (300.0 + 22.0 * i, -20.0, 90.0),
                                               (900.0, 0.0, 0.0)))
    p = lambda i: tr.transform[i].origin
    tr.events = [
        ActionEvent(start + STEP * 10, "jump_pad", None, p(10), None, 0),
        ActionEvent(start + STEP * 18, "fire_weapon", 5, p(18), None, None),
        ActionEvent(start + STEP * 30, "missile_hit", 5, (300.0 + 22.0 * 30, -20.0, 90.0),
                    None, 0),
        ActionEvent(start + STEP * 30, "obituary", 6, (960.0, -20.0, 90.0), victim, None),
    ]
    return tr


def victim_trace(n: int = 60, start: int = START, client: int = 1,
                 gap: tuple[int, int] = (20, 40)) -> PerformanceTrace:
    """A standing victim the recorder loses sight of between samples
    gap[0]..gap[1]: an OBSERVATION GAP, which must stay a gap."""
    tr = PerformanceTrace(demo_hash="fixture", map="campgrounds", gametype="CA",
                          client=client, start_ms=start, end_ms=start + STEP * (n - 1))
    for i in range(n):
        if gap[0] <= i < gap[1]:
            continue
        t = start + STEP * i
        o = (960.0, -20.0 + 2.0 * i, 60.0)
        tr.transform.append(TransformSample(t, o, (0.0, 80.0, 0.0), 80.0, False, 1022))
        tr.aim.append(AimSample(t, 210.0, 0.0, 0.0, 0.0))
        tr.animation.append(AnimSample(t, 15, 11, False, False))
    tr.weapon.append(WeaponSample(start, 7))
    tr.events = [ActionEvent(start + STEP * 30, "pain", None, (960.0, 40.0, 60.0), None, 25)]
    return tr
