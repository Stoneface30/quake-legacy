"""Render every Part, then extra episodes while unspent T1 clips remain.

User direction 2026-08-29:
    "generate all the parts with intro outro (use POV for intros) if not
     available use T3/T2 frags, same rules for all the parts, if extra t1 left
     generate extra parts ... also please review so all the parts have
     different music never 2 of the same"

Rules enforced here:
  - Every Part uses the SAME pipeline and the same rules.
  - Intro: frags whose folder is tagged "intro" lead the cut (POV-led). When a
    Part has none, selection falls through to its ordinary T1/T2 ordering and
    the T3 tail still closes it.
  - Music uniqueness is by CONTENT HASH across every video ever rendered
    (highlight_ledger.claim_song), not by filename -- four pairs of slot files
    in this library are the same song under different names.
  - Extra episodes: after a Part ships, any Part still holding unspent T1 frags
    gets another episode, until T1 is exhausted or nothing further fits.
  - Clips are only burned after a render succeeds, so a failure never loses them.

    python hl_all.py                 # parts 4-12, then extra episodes
    python hl_all.py --parts 4 5 6   # a subset
    python hl_all.py --max-episodes 3
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from creative_suite.engine import highlight_ledger as L  # noqa: E402
from creative_suite.engine.config import Config  # noqa: E402
from creative_suite.engine.render_highlight import collect_frags  # noqa: E402

# Keep going while ANY selectable clip is unspent. One clip left is still a
# clip that must ship -- the coverage invariant is "every selected T1/T2 source
# appears exactly once", not "each Part fits in N episodes".
MIN_CLIPS_FOR_EXTRA = 1


def clips_left(part: int, cfg: Config) -> tuple[int, int]:
    """(T1, T2) still unspent for this Part."""
    frags = collect_frags(part, cfg)
    rem = L.remaining(part, frags)
    return (sum(1 for f in rem if f.tier == "T1"),
            sum(1 for f in rem if f.tier == "T2"))


def t1_left(part: int, cfg: Config) -> int:
    """Total unspent T1+T2. Named for the caller; counts BOTH tiers.

    Previously this counted T1 only, so a Part stopped generating episodes the
    moment its T1 ran out -- silently stranding every remaining T2 clip.
    """
    a, b = clips_left(part, cfg)
    return a + b


def render(part: int, episode: int, minutes: float) -> tuple[bool, float, Path]:
    suffix = "" if episode == 1 else f"_ep{episode}"
    out = ROOT / "output" / f"Part{part}_highlight{suffix}.mp4"
    log = ROOT / "output" / f"hl_p{part}e{episode}.log"
    print(f"\n===== Part {part} episode {episode} -> {out.name} =====", flush=True)
    t0 = time.time()
    with log.open("w", encoding="utf-8", errors="replace") as fh:
        p = subprocess.run(
            [sys.executable, "-u", "-m",
             "creative_suite.engine.render_highlight",
             "--part", str(part), "--minutes", str(minutes),
             "--out", str(out)],
            cwd=str(ROOT), stdout=fh, stderr=subprocess.STDOUT)
    dt = (time.time() - t0) / 60
    ok = p.returncode == 0 and out.exists()
    print(f"Part {part} ep{episode}: {'OK' if ok else 'FAILED'}  {dt:.1f} min",
          flush=True)
    return ok, dt, out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", type=int, nargs="*", default=list(range(4, 13)))
    ap.add_argument("--minutes", type=float, default=5.0)
    ap.add_argument("--max-episodes", type=int, default=4)
    a = ap.parse_args()

    cfg = Config()
    results: list[tuple[int, int, bool, float]] = []

    for ep in range(1, a.max_episodes + 1):
        wave = []
        for part in a.parts:
            if ep == 1:
                wave.append(part)
            elif t1_left(part, cfg) >= MIN_CLIPS_FOR_EXTRA:
                wave.append(part)
        if not wave:
            print(f"\n[all] every Part has exhausted its T1+T2 clips "
                  f"-- stopping at episode {ep - 1}", flush=True)
            break

        print(f"\n########## EPISODE {ep}: parts {wave} ##########", flush=True)
        for part in wave:
            t1, t2 = clips_left(part, cfg)
            print(f"[all] Part {part}: {t1} T1 + {t2} T2 unspent", flush=True)
            ok, dt, _ = render(part, ep, a.minutes)
            results.append((part, ep, ok, dt))

    print("\n" + "=" * 62 + "\n[all] SUMMARY\n" + "=" * 62, flush=True)
    for part, ep, ok, dt in results:
        print(f"  Part {part:2d} ep{ep}  {'OK    ' if ok else 'FAILED'} "
              f"{dt:6.1f} min", flush=True)

    print("\n[all] coverage:", flush=True)
    for part in a.parts:
        frags = collect_frags(part, cfg)
        cov = L.coverage(part, frags)
        t1, t2 = clips_left(part, cfg)
        ok = "OK" if (t1 + t2) == 0 else f"INCOMPLETE ({t1} T1 + {t2} T2 left)"
        print(f"  Part {part:2d}: {cov.used}/{cov.total} shipped "
              f"({cov.pct:.0f}%), {cov.episodes} episode(s)  {ok}", flush=True)

    songs = L.used_songs()
    print(f"\n[all] {len(songs)} distinct songs claimed (no reuse):", flush=True)
    for h, label in sorted(songs.items(), key=lambda kv: kv[1]):
        print(f"  {label}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
