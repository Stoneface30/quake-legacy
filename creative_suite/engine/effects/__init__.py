"""Effect engines for the render pipeline (Rules P1-Q / P1-E).

`event_localized` builds the per-clip slow filter used by render_part_v6, but it
only fires when a clip carries an explicit `slow=` override, and the override
files are essentially empty (Part 4: 1 `slow=` line across 120 clips). That is
why finished Parts had no visible effects.

`speed_ramp` applies a three-stage ramp to EVERY frag automatically -- dead time
compressed, money shot slowed -- with no hand-authored overrides required.
"""
from creative_suite.engine.effects import event_localized, speed_ramp
from creative_suite.engine.effects.speed_ramp import (
    SpeedPlan,
    build_filter,
    fit_to_duration,
    snap_to_beat,
)

__all__ = [
    "event_localized",
    "speed_ramp",
    "SpeedPlan",
    "build_filter",
    "fit_to_duration",
    "snap_to_beat",
]
