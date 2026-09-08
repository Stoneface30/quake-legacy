# Projectile evidence reconciliation — Frag 5979 vs Frag 4121

*2026-09-01. Directive §1–6. Every number below comes from a query actually
run against `creative_suite/database/frag_recognition.db` (read-only).*

## Summary

There was no contradiction in the data, and nothing in the recognition
output needed correcting. The `~300 ms / 318.6 u` direct rocket cited
alongside Frag 5979 **belongs to a different frag**: Frag 4121. The two are
both on asylum, both ROCKET, both `DIRECT_CONFIRMED`, and come from
different demos — which is how they came to be conflated.

Frag 5979 really is point-blank. The preview pipeline was right to refuse to
build a projectile camera on it.

## The two events

| | Frag 5979 | Frag 4121 |
|---|---|---|
| demo date | 2011-12-20 | 2011-08-05 |
| `server_time_ms` | 553 075 | 826 600 |
| flight | **25 ms** | **300 ms** |
| distance | **38.7 u** | **318.6 u** |
| points in path | 2 | 24 |
| launch-match residual | 22.0 u / 31.8 ms | 16.4 u / 18.2 ms |
| geometry | `DIRECT_CONFIRMED` | `DIRECT_CONFIRMED` |
| usable for a camera | **no** | **yes** |

Frag 4121 matches the cited evidence on every field, including the residuals
that were never quoted. It is the event project memory records as the
canonical "#1 direct rocket". Frag 5979 is a separate, closer-range kill.

**The earlier 300 ms figure was not wrong — it was about the other frag.**
It is recorded here rather than quietly dropped.

## Why Frag 5979 cannot carry a projectile camera

Its cached path is two points, 25 ms apart, 38.7 u of travel: launch and
impact, with nothing in between. A camera flown along that arc has no arc to
fly. It fails three of the contract's criteria at once — sampling, duration
and displacement.

## The `launch.t == impact.t` rows: quantization, not corruption

An audit of all 4 391 cached paths found 256 whose `launch.t` and `impact.t`
are identical, which initially looked like a lost launch timestamp.

It is not. **All 256 have a point-series span of exactly 25 ms** — one
server snapshot tick, the shortest flight the server clock can express. A
projectile that launches and lands inside a single tick cannot resolve to two
different tick values. The remaining 4 135 paths agree exactly between the
two sources, and **zero paths disagree**.

```
paths examined                          4391
scalar flight == series span (healthy)  4135
scalar flight != series span             0
scalar flight == 0                       256   <- all span exactly 25 ms
```

No extractor fix is warranted, and no data was rewritten.

## What was actually wrong

The selector in `director_preview.py` computed flight from the
`launch.t`/`impact.t` **scalars**:

```python
flight_ms = int(impact.get("t", 0)) - int(launch.get("t", 0))
return flight_ms >= 200
```

This produced correct results on today's corpus — the audit above confirms
zero paths were misjudged — but it is correct only by luck. It reads the
quantized scalars rather than the point series that is the primary evidence,
so any future extractor that populates the scalars differently would silently
change which frags get cameras.

## The contract now in force

`projectile_evidence()` measures from the **point series** and returns typed
rejection reasons (`too_few_points`, `flight_too_short`,
`displacement_too_small`, `non_positive_flight`, `malformed_points`,
`non_finite_coords`, `no_path`). The scalars are reported for diagnosis but
are never load-bearing.

| criterion | threshold | why |
|---|---|---|
| points | ≥ 8 | enough samples for a smooth Catmull-Rom retarget |
| flight | ≥ 200 ms | below this there is no arc to move a camera along |
| displacement | ≥ 64 u | a path that never leaves the muzzle films nothing |
| flight sign | > 0 | a non-positive span is malformed, not short |
| coordinates | finite | NaN/inf would propagate into the compiled camera |

Pinned by `creative_suite/tests/test_projectile_evidence.py` (19 tests): the
contract on synthetic paths, both real frags' measurements, and the two
corpus-wide invariants (equal-timestamp rows are all one tick; scalars and
series never disagree). The corpus tests skip when the database is absent.

## Noted in passing, not fixed

`creative_suite/frontend/frags.js:83` derives the map name by slicing the
demo filename positionally and stripping a hard-coded nickname prefix. This
is the same positional-parse defect already recorded against demos named
`CA-<player>-<map>-<date>`, where the map is misread as a date fragment. The
authoritative source is `demos.map_name`. Left alone here because changing it
is a behavior change outside this directive's scope.
