"""5-minute beat-matched highlight renderer.

Written 2026-08-28 after the user reviewed the first full-length Parts and
rejected them:

    "volume from music need to stay SAME level ... the clip are literally just
     put next to each others with no transition no effect no slowmo ... you
     should beat match keeping the music pitch but slowing the frags and maybe
     accelerating the part with no action ... cut the length to 5 min and use
     all the TIER 1 frags in priority and fill with t2 ... dont split again the
     third view party and try to link then to the correct frag"

What the long pipeline got wrong, and what this does instead:

  MUSIC LEVEL   render_part_v6 crushed music to `music_volume = 0.08` (8%) and
                sidechain-ducked it, to satisfy an ebur128 gate demanding music
                >=12 LU below game peak. Here music sits at ONE CONSTANT level
                and is never ducked. Sync comes from the beat grid, not gain.

  PITCH         The music is never time-stretched or resampled, so it keeps its
                original pitch and tempo. The VIDEO bends to the beat grid.

  EFFECTS       v6 applied slow-mo only to clips carrying an explicit `slow=`
                override; Part 4 had exactly one such line across 120 clips.
                Here every frag gets an automatic speed ramp (see
                effects.speed_ramp): dead time compressed, money shot slowed.

  FL ANGLES     v6 expanded `FP > FL` pairs into separate standalone chunks, so
                third-person angles read as unrelated shots. Here an FL clip is
                only ever a slow replay appended to ITS OWN frag (Rule P1-K).

  SELECTION     All T1 frags first, alternated with T2, until the target length.

CLI:
    python -m creative_suite.engine.render_highlight --part 4 --minutes 5
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import re

from creative_suite.clips.parser import parse_clip_list
from creative_suite.engine import highlight_ledger
from creative_suite.engine import music_beatmatch, peak_guard
from creative_suite.engine.config import REPO_ROOT, Config
from creative_suite.engine.effects import speed_ramp

# Music sits at a constant, clearly audible level. This is deliberately far
# above v6's 0.08 -- the old value existed only to pass a loudness gate.
# "FL" anywhere in the stem marks a free-look / spectator angle. The old
# anchored pattern (FL\d*\)?\.avi$) missed real angles named
# "Demo101FL1-0000.avi", which were then treated as POV clips.
_FL_NAME = re.compile(r"FL\s*\d*", re.I)
# A folder tagged 'intro' holds the frag chosen to OPEN the video
# (user 2026-08-29: "the one labelled intro is the one to use for the intro").
_INTRO_NAME = re.compile(r"intro|outro", re.I)
# "Demo (152)" / "Demo152FL1" -> 152. The demo number is a frag's real identity;
# every angle of one kill shares it.
_DEMO_NUM = re.compile(r"Demo\s*\(?\s*(\d+)", re.I)


def demo_number(path) -> str | None:
    m = _DEMO_NUM.search(Path(path).name)
    return m.group(1) if m else None


def is_angle(path) -> bool:
    return bool(_FL_NAME.search(Path(path).stem))


def is_intro(path) -> bool:
    """True for intro/outro material, by filename OR containing folder."""
    q = Path(path)
    return bool(_INTRO_NAME.search(q.stem) or _INTRO_NAME.search(q.parent.name))

# The Quake console is drawn over the head of every capture
# (user 2026-08-28: "no console it always show").
# 1.20 s still let the console through on some captures (user 2026-08-29:
# "we can still see some consoles"). Brightness- and temporal-stability
# detectors both failed to discriminate it reliably on this corpus, so this is
# a blunt fixed trim. Revisit with a real overlay detector.
CONSOLE_TRIM_S = 2.00

# User 2026-08-29: "more game volume". Game is the foreground; music holds a
# fixed level under it (Rule P1-G v6 -- never ducked).
MUSIC_VOLUME = 1.24   # user 2026-08-29: "at least twice louder"
GAME_VOLUME = 2.90   # user 2026-08-31: "x2 in game volume"

# Visible seam. v6 used 0.40 s, which reads as a hard cut across 120 clips.
# User 2026-08-29: "more transition". Research ceiling is 0.10-0.25 s -- a
# transition the viewer notices on first viewing is the error, so 0.20 s.
XFADE_S = 0.35
# Overlap between the two songs so the change reads as a blend, not a cut.
MUSIC_XFADE_S = 6.0
# Output loudness target. TP is the hard safety property: every final render
# must measure <= -1.0 dBTP, so we aim at -1.5 for encoder margin.
TARGET_LUFS = -14.0
# Ask loudnorm for -2.0 dBTP so the finished file reliably lands under the
# -1.0 dBTP acceptance ceiling. Single-pass loudnorm targets true peak
# approximately, not exactly: measured across the first episodes it produced
# -2.10, -1.30, -1.00 and -0.80 dBTP against a -1.5 request, i.e. about +-0.7 dB
# of error. At -1.5 an episode can and did land at -0.80 and fail the gate --
# and since a retry renders the same clips with the same music it would fail
# again and strand the whole Part. -2.0 shifts the whole distribution below the
# ceiling with room to spare, at the cost of being marginally quieter.
TARGET_TP = -2.0
SAFE_TP_CEILING = -1.0   # acceptance threshold for a finished file
# -2 dBFS as a linear amplitude, for alimiter. Sits below the -1.0 dBTP
# acceptance ceiling so the finished file clears it with margin.
TP_LIMIT_LINEAR = 0.794

# Packing bounds, as fractions of the body target. Below the floor we keep
# adding unconditionally; above it a clip is only added when it still fits
# under the ceiling, otherwise it carries to the next episode. Soft packaging,
# never a reason to cut a frag.
BODY_SOFT_FLOOR = 0.88
BODY_HARD_CEIL = 1.08

MIN_FRAG_OUT_S = 2.5
# Raised for genuine multi-kill spans -- the user wants the WHOLE action, and
# find_action_span() legitimately returns 10 s+ on a multi-frag capture.
MAX_FRAG_OUT_S = 13.0

# Third-person leads INTO the POV, it does not replay after it. Research 2026-08-28
# (ESReality moviemaking interviews): mccormic -- "If you play something in third
# person first, then show the same thing in first person, that explains a lot to
# the viewer." No Quake source describes a killcam-style replay after the kill.
FL_LEADS_IN = True
FL_LEAD_PRE_S = 1.1
FL_LEAD_POST_S = 0.9
FL_LEAD_MAX_S = 3.0

# Slow-mo is a scarce accent, not a per-frag treatment. Per-frag slowmo is the
# most-mocked technique in the scene ("stop using slow motion every frag!!!!",
# "the slow-fast-slow-fast effect gets annoying"). Only every Nth frag, and only
# T1, gets the money-shot ramp; the rest play straight.
# User 2026-08-29 asked for more ("slowmo speed up nice"), so accent every 3rd
# T1 frag instead of every 4th. Still well short of per-frag slow-mo, which is
# the scene's most-mocked mistake.
SLOWMO_EVERY_N = 3
# User: "slowmo the short clips because frag are nice". A short capture is
# almost all money-shot, so it earns the accent regardless of cadence.
SHORT_CLIP_SLOWMO_S = 7.0
# An accent showcases one moment; a long multi-kill span plays straight instead.
SLOWMO_MAX_SPAN_S = 6.0
# Approach = dead time before the first shot. It is the ONLY region that may be
# sped up, and it is trimmed rather than rushed past this rate.
APPROACH_MAX_S = 4.0
APPROACH_MAX_RATE = 2.5
# A sliver off the tail so the hard cut-out transient never shows.
# User: "some are cut in the end". The tail trim was eating the last beat of
# a frag. Only the cut-out transient needs removing, so this is now minimal.
END_TRIM_S = 0.25   # FP tail stays 0.25 (user 2026-08-29)
# The console is drawn at the END of follow/spectator captures too
# (user 2026-08-29: "the console is always shown on the end of the Follow POV").
# Rule P1-L already put FL tail at 2.0 s; the highlight path was ignoring it.
FL_TAIL_TRIM_S = 0.90
# Was 2.00, which chopped nearly a second of real frag off angle clips
# (user: "some clips where chopped nearly 1 sec too"). Enough to clear the
# console at the end of a follow capture, not enough to eat the aftermath.
# Only a genuinely long clip has dead time worth compressing, and even then
# only its quiet lead-in -- never the action.
LONG_CLIP_S = 16.0
DEADTIME_RATE = 2.0        # lead-in only, never the action
OUTRO_FRAGS = 2            # T3 cinematic tail reserved for the close
# User 2026-08-29: intro/outro between 5 and 12 s.
INTRO_S = 8.0              # produced opener: brand + title over T2/T3

# SCRATCH REPLAY (user 2026-08-31: "i also love the kinda scratch effect with
# video like slowmo frag rollback then frag normal speed"). The money shot plays
# slowed, rewinds like a record being pulled back, then plays again at natural
# speed. It is a VARIATION, not a treatment: applied on a cadence to accented
# T1 shots only, because a rewind on every frag is the effect everyone
# overused in 2004.
SCRATCH_REWIND_RATE = 2.2  # how fast the rollback runs
SCRATCH_MIN_SRC_S = 5.0    # too short and the rewind has nothing to grab
SCRATCH_MIN_GAP = 3        # accented shots between one scratch and the next

# GRENADE INSET (user 2026-08-31: "FL view could be embeded for nade sometime
# that could create some variations"). A grenade play is the one case where the
# POV genuinely cannot show the whole story -- the shell leaves the screen and
# lands somewhere the shooter is not looking. Inset the follow camera so both
# are visible at once. Only on grenade shots that HAVE a second angle, and only
# when the shot is playing straight: overlaying a speed-ramped picture would
# put the two cameras on different clocks.
PIP_WIDTH_FRAC = 0.26      # inset width as a share of the frame
PIP_MARGIN_PX = 48
PIP_MIN_GAP = 4            # shots between one inset and the next
OUTRO_S = 10.0             # produced closer: mark + credits (was 14 s)
SLOW_PRE_S = 0.7
SLOW_POST_S = 1.1
# The action itself is capped by TRIMMING to the densest window, never by
# speeding it up.
ACTION_MAX_S = 8.0

# Transitions must be invisible, not absent. Kaneco: fades "0.10-0.25 max";
# eee: transitions "shouldnt be noticeable to the average viewer on the first
# viewing". The earlier 0.75 s dissolve smeared two rooms together.
SEAM_FADE_S = 0.18

# A highlight reel shows the approach into the kill and a short settle -- not
# the whole round. Without this window a clip whose peak lands late keeps a long
# uncompressible tail (only the approach is speed-ramped), and a single frag can
# swallow 25 s of a 5-minute reel.
# wolfcam /fragforward captures 5.0 s pre-kill / 3.0 s post, but that is a
# REVIEW window. Kaneco names both edges as the classic error: clips
# "ending too long after the frag, or starting too early into the frag".
SRC_PRE_PEAK_S = 3.4
SRC_POST_PEAK_S = 1.6


def _load_tail_table():
    """Per-clip measured end-trim, empty until tail_trim has been run."""
    try:
        from creative_suite.engine.tail_trim import load_table
        return load_table()
    except Exception:
        return {}


_TAIL_TABLE = _load_tail_table()


def source_window(peak: float, duration: float,
                  clip: Path | None = None) -> tuple[float, float]:
    """The playable range of a clip -- essentially ALL of it.

    HARD RULE (user 2026-08-29): "clips in video are already trimmed for the
    frags so stop fucking cutting the clips again."

    Each .avi in the corpus IS one frag, already cut by hand. Earlier versions
    ran onset detection and kept only the "densest action window", which threw
    away real frags inside multi-kill clips -- the direct cause of "you missing
    a lot of frags". There is nothing to select: the whole clip ships.

    The only trims left are the two the footage genuinely needs:
      head - the Quake console is drawn over the first moment of a capture
      tail - a hair off the end so the cut-out transient never lands on screen
    """
    # HEAD: nothing. User review 2026-08-31: "do not cut the start of the clips
    # ( we missing some frags )". The old rule took up to 2.0 s off the front of
    # every clip, which on a short capture is the run-up to the frag and
    # sometimes the frag itself. A console overlay for a moment is a far smaller
    # cost than a missing kill.
    #
    # TAIL: only where the capture genuinely ends badly. A first-person clip is
    # cut clean, so it keeps its full length; an FL (third-person) capture ends
    # on the console or the recorder stopping, so that one gets trimmed.
    head = 0.0

    # END trim, measured per clip rather than assumed. A hand-cut capture often
    # keeps rolling past the frag into the respawn or the next round -- measured
    # across the library the dead tail after the last game event runs a median
    # of 0.94 s and up to 3.2 s, which is the "1.3 second of next round" the
    # user reported. `tail_trim` finds the last rail / shaft / rocket / jump /
    # weapon-swap sound in each clip and cuts only what follows a 1.6 s
    # aftermath hold, so the impact, the kill feed and the beat after it all
    # survive. Clips with no recognised game audio are left alone.
    measured = _TAIL_TABLE.get(str(clip.resolve()).lower()) if clip else None
    if measured:
        tail_trim = measured
    else:
        # fallback: FL captures end on the console or the recorder stopping
        is_fl = bool(clip and is_angle(clip))
        tail_trim = min(FL_TAIL_TRIM_S, duration * 0.10) if is_fl else 0.0
    tail = max(head + 0.5, duration - tail_trim)
    return head, tail


@dataclass
class Frag:
    fp: Path
    tier: str
    fls: list[Path] = field(default_factory=list)
    duration: float = 0.0
    peak: float = 0.0
    out_duration: float = 0.0
    is_intro: bool = False      # folder tagged 'intro' -> opens the video
    slowmo_applied: bool = False   # whether the accent actually fired


# ── discovery ────────────────────────────────────────────────────────────────

def _tier_dirs(part: int, cfg: Config) -> dict[str, Path]:
    root = Path(getattr(cfg, "clips_root", REPO_ROOT / "QUAKE VIDEO"))
    return {t: root / t / f"Part{part}" for t in ("T1", "T2", "T3")}


def _index_clips(part: int, cfg: Config) -> dict[str, tuple[Path, str]]:
    """basename -> (path, tier). First tier that owns the name wins."""
    idx: dict[str, tuple[Path, str]] = {}
    for tier, d in _tier_dirs(part, cfg).items():
        if not d.is_dir():
            continue
        for f in d.rglob("*.avi"):
            idx.setdefault(f.name, (f, tier))
    return idx


def probe_duration(path: Path, cfg: Config) -> float:
    r = subprocess.run(
        [str(cfg.ffprobe_bin), "-v", "error", "-show_entries",
         "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, timeout=30,
    )
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


_SIG_CACHE: dict = {}


def _angle_signature(q: Path, cfg: Config):
    """A fingerprint of what an angle clip actually SHOWS.

    Byte identity only catches the same file exported twice. The corpus also
    holds the same recording re-encoded -- different size, different length,
    same footage -- and those play as the same angle twice in a row just as
    obviously. A couple of tiny grayscale frames pulled from fixed early
    timestamps survive re-encoding and are cheap enough to take per clip.

    Returns None when the clip cannot be decoded, which makes it its own group
    rather than silently collapsing it into someone else's.
    """
    try:
        st = q.stat()
    except OSError:
        return None
    ck = (str(q).lower(), st.st_size, int(st.st_mtime))
    if ck in _SIG_CACHE:
        return _SIG_CACHE[ck]
    h = hashlib.sha256()
    got = 0
    for t in (0.5, 2.0):
        r = subprocess.run(
            [str(cfg.ffmpeg_bin), "-v", "error", "-ss", str(t), "-i", str(q),
             "-frames:v", "1", "-vf", "scale=32:18,format=gray",
             "-f", "rawvideo", "-"],
            capture_output=True)
        if r.returncode == 0 and r.stdout:
            h.update(r.stdout)
            got += 1
    sig = h.hexdigest()[:16] if got else None
    _SIG_CACHE[ck] = sig
    return sig


def _dedupe_angles(paths, cfg: Config | None = None):
    """Collapse FL angles that are the same footage, keeping the FASTEST.

    The corpus stores some third-person captures twice -- "Demo (100FL).avi"
    and "Demo100FL-0000.avi" are exports of one recording. Playing both shows
    the viewer the same angle twice in a row, which reads as a mistake.

    Two clips are the same angle when they are byte-identical OR when they show
    the same thing (matching visual signature) at a comparable length. Within a
    group the SHORTEST clip wins -- user 2026-08-31: "the duplicate FL you can
    keep the fastest of the 2 same version only". The tighter export is the one
    without the dead air, and length is exactly what the viewer feels.
    """
    groups: dict = {}
    order: list = []
    for q in paths:
        try:
            h = hashlib.sha256()
            with q.open("rb") as fh:
                h.update(fh.read(1 << 20))
            key = ("exact", q.stat().st_size, h.hexdigest()[:16])
        except OSError:
            key = ("name", q.name.lower(), 0)
        if cfg is not None:
            sig = _angle_signature(q, cfg)
            if sig:
                key = ("visual", sig, 0)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(q)

    out = []
    for key in order:
        members = groups[key]
        if len(members) == 1 or cfg is None:
            out.append(members[0])
            continue
        # fastest == shortest playing time
        best, best_d = members[0], None
        for q in members:
            try:
                d = probe_duration(q, cfg)
            except Exception:                          # noqa: BLE001
                continue
            if best_d is None or d < best_d:
                best, best_d = q, d
        if len(members) > 1:
            print("  [angle] {} duplicate(s) of {} -- keeping the fastest"
                  .format(len(members) - 1, best.name))
        out.append(best)
    return out


def frags_from_queue(rows, cfg: Config) -> list[Frag]:
    """Build Frags from an explicit, already-ordered clip list.

    The continuous PartNN series packs its own clips: the orchestrator walks one
    master queue across historical Part boundaries, so the renderer must play
    exactly what it is handed, in that order, and select nothing itself.

    A row carries the POV path plus the other angles from the same folder, so a
    multi-angle frag keeps its angles without re-walking the directory tree --
    and an angle can still never be attached to a different kill.
    """
    out: list[Frag] = []
    for r in rows:
        fp = Path(r["canonical_avi_path"])
        if not fp.exists():
            print(f"  [queue] MISSING {fp.name} -- skipped")
            continue
        angles = _dedupe_angles(
            [Path(a) for a in (r.get("angles") or []) if Path(a).exists()], cfg)
        out.append(Frag(fp=fp, tier=r.get("tier", "T1"), fls=angles,
                        is_intro=is_intro(fp)))
    return out


def collect_frags(part: int, cfg: Config) -> list[Frag]:
    """Discover frags from the folder layout. Nothing clever.

    User 2026-08-29: "the clips are not in folder, the one in folders are all
    the clips for the same frag."

        Part4/Demo (22)  -  195.avi          loose file  = one frag, one clip
        Part4/Demo (152)  - 84/              folder      = ONE frag
            Demo (152)  - 84.avi                 the POV
            Demo (152FL1).avi                    another view of the SAME kill
        Part4/Demo (490)  - 596 intro/       folder tagged "intro" -> opens the video

    Everything inside a folder belongs to that one frag, so an angle can never
    be attached to a different kill. The POV is the file whose name matches the
    folder; failing that, the one without "FL" in it.
    """
    frags: list[Frag] = []
    for tier, tdir in _tier_dirs(part, cfg).items():
        if not tdir.is_dir():
            continue

        for f in sorted(tdir.glob("*.avi")):          # loose = single-clip frag
            frags.append(Frag(fp=f, tier=tier, is_intro=is_intro(f)))

        for sub in sorted(x for x in tdir.iterdir() if x.is_dir()):
            avis = sorted(sub.glob("*.avi"))
            if not avis:
                continue
            named = [a for a in avis if a.stem.strip() == sub.name.strip()]
            non_fl = [a for a in avis if not is_angle(a)]
            pov = (named or non_fl or avis)[0]
            others = [a for a in avis if a != pov]
            frags.append(Frag(fp=pov, tier=tier, fls=others,
                              is_intro=is_intro(sub)))
    return frags


def select_frags(frags: list[Frag], target_s: float,
                 cfg: Config) -> list[Frag]:
    """All T1 first, alternated with T2, until `target_s` of output.

    Duration is estimated from the speed plan, not the raw clip, because the
    ramp changes how long a frag actually occupies.
    """
    def _spread(pool: list[Frag]) -> list[Frag]:
        """Distribute multi-angle frags evenly through a tier.

        collect_frags() lists loose single-angle clips before folder frags, so a
        straight pass selects ~30 single-angle T1s and never reaches the
        multi-angle ones -- the whole third-person treatment silently vanished
        from the cut. Angle-bearing frags are also the showcase kills (they were
        the ones recaptured from a second angle in the first place), so they are
        spread through the tier rather than clustered at either end. Research
        2026-08-28: third-person is "selective seasoning", used sparingly.
        """
        withfl = [f for f in pool if f.fls]
        plain = [f for f in pool if not f.fls]
        if not withfl or not plain:
            return withfl + plain
        step = max(1, len(plain) // len(withfl))
        out: list[Frag] = []
        wi = 0
        for i, f in enumerate(plain):
            if i % step == 0 and wi < len(withfl):
                out.append(withfl[wi]); wi += 1
            out.append(f)
        out.extend(withfl[wi:])
        return out

    t1 = _spread([f for f in frags if f.tier == "T1"])
    t2 = _spread([f for f in frags if f.tier == "T2"])
    t3 = _spread([f for f in frags if f.tier == "T3"])

    ordered: list[Frag] = []
    i = j = 0
    while i < len(t1) or j < len(t2):
        if i < len(t1):
            ordered.append(t1[i]); i += 1
        if j < len(t2):
            ordered.append(t2[j]); j += 1
    ordered.extend(t3)

    # A frag whose folder is tagged "intro" is the designated opener
    # (user 2026-08-29: "the one labelled intro is the one to use for the
    # intro"). It is NOT excluded -- it goes first.
    intro = [f for f in ordered if f.is_intro]
    ordered = intro + [f for f in ordered if not f.is_intro]

    # Over-select: per-frag duration is only an estimate (beat snapping and
    # ramps move it), so give the build loop surplus to reach target_s.
    budget = target_s * 1.45
    # Reserve the tail of the reel for T3 (atmospheric / cinematic, Rule P1-B).
    # Without this the budget runs out before selection reaches T3 and the video
    # simply stops on a frag instead of closing.
    outro_pool = [f for f in ordered if f.tier == "T3"][:OUTRO_FRAGS]
    ordered = [f for f in ordered if f not in outro_pool]

    chosen: list[Frag] = []
    total = 0.0
    for f in ordered:
        if total >= budget:
            break
        f.duration = probe_duration(f.fp, cfg)
        if f.duration < 1.5:
            continue
        f.peak = peak_guard.find_peak_guarded(f.fp, f.duration)
        w0, w1 = source_window(f.peak, f.duration, f.fp)
        # Estimate STRAIGHT playback, which is what most frags get. Sizing every
        # frag as if it were slow-mo ramped inflated the estimate ~60% and the
        # reel landed at 3.2 min against a 5 min target (Parts 5/6, v4). Only
        # ~1 in 4 T1 frags is actually accented, and the build loop stops on the
        # real running timeline anyway.
        f.out_duration = min(w1 - w0, MAX_FRAG_OUT_S)
        if f.out_duration < MIN_FRAG_OUT_S:
            continue
        chosen.append(f)
        total += f.out_duration
    for f in outro_pool:                       # always closes on T3
        f.duration = probe_duration(f.fp, cfg)
        if f.duration < 1.5:
            continue
        f.peak = peak_guard.find_peak_guarded(f.fp, f.duration)
        w0, w1 = source_window(f.peak, f.duration, f.fp)
        f.out_duration = w1 - w0
        chosen.append(f)
    return chosen


# ── beat grid ────────────────────────────────────────────────────────────────

def load_beats(part: int, cfg: Config) -> tuple[list[float], list[float]]:
    """(beat_times, downbeats) for the Part's music, or ([], [])."""
    for name in (f"part{part:02d}_music.mp3.beats.json",
                 f"part{part:02d}_music.ogg.beats.json"):
        p = Path(cfg.music_dir) / name if hasattr(cfg, "music_dir") else None
        p = p or (REPO_ROOT / "creative_suite" / "engine" / "music" / name)
        if not p.exists():
            p = REPO_ROOT / "creative_suite" / "engine" / "music" / name
        if p.exists():
            d = json.loads(p.read_text(encoding="utf-8"))
            return (list(d.get("beat_times", [])),
                    list(d.get("downbeats", [])))
    return ([], [])


# ── rendering ────────────────────────────────────────────────────────────────

def _valid_segment(path: Path, cfg: Config) -> bool:
    """True if a rendered segment is actually decodable.

    ffmpeg can exit 0 and still leave an unreadable file: seg018 came back with
    returncode 0, a 68 MB size and a duration of 0.00 s, which then blew up the
    whole concat with "Invalid data found when processing input". Same failure
    family as the render_part_v6 chunk cache -- never trust an output you have
    not probed.
    """
    try:
        if not (path.exists() and path.stat().st_size > 1024):
            return False
        if probe_duration(path, cfg) <= 0.05:
            return False
        # Must carry BOTH streams. A video-only segment makes every downstream
        # filtergraph referencing [N:a] fail with "matches no streams", which
        # took down all nine Parts at once.
        r = subprocess.run(
            [str(cfg.ffprobe_bin), "-v", "error", "-show_entries",
             "stream=codec_type", "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=30)
        kinds = {x.strip() for x in r.stdout.splitlines() if x.strip()}
        if not {"video", "audio"} <= kinds:
            print(f"  [drop] {path.name}: missing stream(s), has {sorted(kinds)}")
            return False
        return True
    except Exception:
        return False


def music_grid(tracks: list[Path], cfg: Config):
    """Beats, downbeats and drops for the whole video, in VIDEO time.

    Two corrections over reading one track's grid directly, both found by
    watching the feature do nothing in a real render rather than in a test:

      * a video is scored by one or two songs, and the second one's beats sit
        after the first has played out. Reading only the first track leaves the
        back half of the video with no grid at all -- which is most of it, since
        the first song here ran 145 s against a 280 s body.
      * the songs are joined with a crossfade, so song two starts one crossfade
        BEFORE song one ends, not after it.

    Times are returned on the finished video's clock, which is where the music
    actually sits: the mix starts at video t=0, under the opener.
    """
    from creative_suite.engine import music_beatmatch as _mb
    beats, downs, drops = [], [], []
    at = 0.0
    for q in tracks:
        try:
            b, d = _mb.full_grid(q)
            k = _mb.detect_drops(q)
        except Exception as exc:                       # noqa: BLE001
            print(f"[hl] track grid unavailable for {q.name} ({exc})")
            continue
        beats += [at + x for x in b]
        downs += [at + x for x in d]
        drops += [at + x for x in k]
        at += max(0.0, probe_duration(q, cfg) - MUSIC_XFADE_S)
    return sorted(beats), sorted(downs), sorted(drops)


def video_time(timeline: float, seg_index: int) -> float:
    """Where a body segment starts on the FINISHED video's clock.

    `timeline` accumulates body segment durations, but the finished video also
    carries the opener, and every seam crossfade overlaps two segments and so
    removes its own length from the running total. Without this the accent
    solver compares body time against music time and lands nothing.
    """
    return INTRO_S + timeline - (seg_index + 1) * XFADE_S


_FRAME_ASSETS: dict = {}


def inset_frame_asset(w: int, h: int) -> Optional[Path]:
    """The branded bezel for the inset, rendered once and cached on disk.

    The window used to be a bare white rectangle, which read as a debug
    overlay. Drawing it in the mark's own language -- brushed silver, one gold
    hairline, the temple emblem in the corner -- makes the second camera look
    like part of the film. Falls back to no frame rather than failing a render.
    """
    key = (w, h)
    if key in _FRAME_ASSETS:
        return _FRAME_ASSETS[key]
    out = None
    try:
        from creative_suite.engine import pantheon_brand as _pb
        d = REPO_ROOT / "creative_suite" / "generated" / "brand"
        d.mkdir(parents=True, exist_ok=True)
        q = d / f"inset_frame_{w}x{h}.png"
        if not q.exists():
            _pb.inset_frame(w, h).save(q)
        out = q
    except Exception as exc:                           # noqa: BLE001
        print(f"  [inset] branded frame unavailable ({exc})")
    _FRAME_ASSETS[key] = out
    return out


def cfg_ffmpeg() -> Path:
    """ffmpeg path without threading a Config through the audio helpers."""
    return Config().ffmpeg_bin


_GRENADE_CACHE: dict = {}

# Correlation a grenade-launcher shot has to reach to count. Tuned by
# measurement, not taste: the full family (fire plus both bounce samples) at
# the library's default 0.32 fired on 50% of angled clips, which is not a
# grenade rate -- the bounces were matching every other impact in the game.
# Requiring the LAUNCHER FIRING at 0.65 gives 5%, which is what a grenade play
# actually is in Clan Arena.
GRENADE_MIN_CORR = 0.65


def has_grenade(clip: Path) -> bool:
    """Was a grenade launcher fired in this clip?

    The blast itself is no help -- Quake reuses the rocket explosion for it.
    The launcher's own firing sound is the identifying event, and it is matched
    against the sample shipped in pak00 rather than inferred from anything.
    """
    key = str(clip.resolve()).lower()
    if key in _GRENADE_CACHE:
        return _GRENADE_CACHE[key]
    hit = False
    tmp = None
    try:
        import os
        import subprocess as _sp
        import librosa
        from creative_suite.engine import game_beat as _gb

        tmp = Path(os.environ.get("TEMP", ".")) / f"_gren_{os.getpid()}.wav"
        r = _sp.run([str(cfg_ffmpeg()), "-y", "-v", "error", "-i", str(clip),
                     "-vn", "-ac", "1", "-ar", str(_gb.SR), "-f", "wav",
                     str(tmp)], capture_output=True)
        if r.returncode == 0 and tmp.exists():
            y, _ = librosa.load(str(tmp), sr=_gb.SR, mono=True)
            fire, _ = librosa.load(
                str(_gb.TROOT / "weapons/grenade/grenlf1a.wav"),
                sr=_gb.SR, mono=True)
            hit = bool(_gb._match(y, fire, GRENADE_MIN_CORR))
    except Exception:                                  # noqa: BLE001
        hit = False
    finally:
        try:
            if tmp:
                tmp.unlink()
        except OSError:
            pass
    _GRENADE_CACHE[key] = hit
    return hit


def accent_window(w0: float, w1: float, peak: float) -> tuple[float, float]:
    """Where the slow-mo accent starts and ends inside a clip's play window.

    The loop that solves the accent's STRENGTH has to model the exact segment
    the renderer will build; if the two drift apart the solved rate predicts a
    length the render never produces and the cut lands off the beat it was
    solved for. So both call this.
    """
    pk = min(max(peak, w0 + 0.4), w1 - 0.4)
    return max(w0, pk - SLOW_PRE_S), min(w1, pk + SLOW_POST_S)


def render_frag(frag: Frag, dst: Path, cfg: Config,
                slowmo: bool = False,
                slow_rate: Optional[float] = None,
                scratch: bool = False,
                pip: Optional[Path] = None) -> float:
    """Render one frag -- the WHOLE clip, at natural speed.

    The clip is already exactly one frag, so nothing is selected out of it.
    Speed rules (user 2026-08-29):
      - the action is NEVER sped up
      - slow-mo is an accent applied around the action peak
      - speed-up is allowed only on the quiet lead-in of a genuinely long clip
    """
    w0, w1 = source_window(frag.peak, frag.duration, frag.fp)
    span = w1 - w0

    if slowmo:
        # Accent: hold the clip at natural speed, slow the money shot, resume.
        a, b = accent_window(w0, w1, frag.peak)
        rate = slow_rate if slow_rate else speed_ramp.SLOW_RATE
        parts_, vl, al, i = [], [], [], 0

        def add(t0: float, t1: float, rate: float, interp: bool,
                reverse: bool = False) -> None:
            nonlocal i
            if t1 - t0 <= 0.02:
                return
            vf = f"[0:v]trim={t0:.4f}:{t1:.4f},setpts=PTS-STARTPTS"
            af = f"[0:a]atrim={t0:.4f}:{t1:.4f},asetpts=PTS-STARTPTS"
            if reverse:
                # the rollback: picture and sound both run backwards, which is
                # what makes it read as a record being pulled back rather than
                # as a glitch
                vf += ",reverse"
                af += ",areverse"
            vf += f",setpts=(PTS-STARTPTS)/{rate:.6f}"
            if interp:
                vf += f",{speed_ramp.MINTERP.format(fps=cfg.target_fps)}"
            af += f",{speed_ramp._atempo_chain(rate)}"
            parts_.append(vf + f"[v{i}]")
            parts_.append(af + f"[a{i}]")
            vl.append(f"[v{i}]"); al.append(f"[a{i}]"); i += 1

        add(w0, a, 1.0, False)
        add(a, b, rate, speed_ramp.SMOOTH_SLOWMO)
        if scratch:
            # pull it back, then play it straight
            add(a, b, SCRATCH_REWIND_RATE, False, reverse=True)
            add(a, b, 1.0, False)
        add(b, w1, 1.0, False)
        filt = ";".join(parts_)
        filt += (f";{''.join(vl)}concat=n={len(vl)}:v=1:a=0[vc]"
                 f";{''.join(al)}concat=n={len(al)}:v=0:a=1[aout]")
    # NOTE: there is deliberately no speed-up branch. An earlier version
    # compressed the "quiet lead-in" of long clips, but the action often starts
    # early and it sped through real frags (user 2026-08-29: "you also sped up a
    # whole clip including frags"). Clips are already cut to their frag, so the
    # only speed change permitted anywhere is slow-mo.
    elif pip is not None:
        # Both cameras at once. The inset runs from the same moment as the POV
        # so the two clocks agree; it is not re-windowed independently, which
        # is what previously made two angles read as two different frags.
        pip_dur = probe_duration(pip, cfg)
        p1 = min(w1 - w0, max(0.5, pip_dur))
        iw = int(cfg.target_width * PIP_WIDTH_FRAC) // 2 * 2
        ih = int(iw * cfg.target_height / cfg.target_width) // 2 * 2
        frame_png = inset_frame_asset(iw, ih)
        filt = (f"[0:v]trim={w0:.4f}:{w1:.4f},setpts=PTS-STARTPTS[base];"
                f"[1:v]trim=0:{p1:.4f},setpts=PTS-STARTPTS,"
                f"scale={iw}:{ih},setsar=1[ins];")
        if frame_png:
            filt += (f"[2:v]format=rgba[frm];"
                     f"[ins][frm]overlay=0:0:format=auto[insf];")
        else:
            filt += "[ins]null[insf];"
        filt += (f"[base][insf]overlay="
                 f"W-w-{PIP_MARGIN_PX}:H-h-{PIP_MARGIN_PX}"
                 f":enable='lte(t,{p1:.4f})'[vc];"
                 f"[0:a]atrim={w0:.4f}:{w1:.4f},asetpts=PTS-STARTPTS[aout]")
    else:
        filt = (f"[0:v]trim={w0:.4f}:{w1:.4f},setpts=PTS-STARTPTS[vc];"
                f"[0:a]atrim={w0:.4f}:{w1:.4f},asetpts=PTS-STARTPTS[aout]")

    filt += (f";[vc]scale={cfg.target_width}:{cfg.target_height}"
             f":force_original_aspect_ratio=increase,"
             f"crop={cfg.target_width}:{cfg.target_height},setsar=1,"
             f"fps={cfg.target_fps},format=yuv420p[vfin]")

    cmd = [str(cfg.ffmpeg_bin), "-y", "-v", "error", "-i", str(frag.fp)]
    if pip is not None and not slowmo:
        cmd += ["-i", str(pip)]
        _fr = inset_frame_asset(
            int(cfg.target_width * PIP_WIDTH_FRAC) // 2 * 2,
            int(int(cfg.target_width * PIP_WIDTH_FRAC) // 2 * 2
                * cfg.target_height / cfg.target_width) // 2 * 2)
        if _fr:
            cmd += ["-i", str(_fr)]
    cmd += ["-filter_complex", filt, "-map", "[vfin]", "-map", "[aout]",
           "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
           "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "-ar", "48000",
           "-f", "mov", str(dst)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(
            "frag render failed " + frag.fp.name + ":\n" + r.stderr[-800:])
    return probe_duration(dst, cfg)


def render_fl_angle(frag: Frag, dst: Path, cfg: Config, which: int = 0,
                    slow: float = 0.5) -> Optional[float]:
    """Another camera on the SAME frag, played in full.

    The angle clips are cut by hand alongside their POV -- they are already
    exactly this frag from another camera (user 2026-08-29: "pov view need to
    match the frag from the clip too"). So this plays the whole clip, same as
    the POV, minus the console head and the cut-out tail. Windowing it
    independently is what put the two angles on different moments and made them
    read as different frags.
    """
    if which >= len(frag.fls):
        return None
    fl = frag.fls[which]
    fl_dur = probe_duration(fl, cfg)
    if fl_dur < 1.0:
        return None
    a, b = source_window(0.0, fl_dur, fl)
    # Angle captures show the console at the END as the camera falls off.
    b = max(a + 0.5, b - min(FL_TAIL_TRIM_S, fl_dur * 0.20))
    if b - a < 0.5:
        return None

    rate = max(0.35, min(1.0, slow))
    filt = (
        f"[0:v]trim={a:.3f}:{b:.3f},setpts=(PTS-STARTPTS)/{rate:.4f},"
        f"scale={cfg.target_width}:{cfg.target_height}"
        f":force_original_aspect_ratio=increase,"
        f"crop={cfg.target_width}:{cfg.target_height},setsar=1,"
        f"fps={cfg.target_fps},format=yuv420p[vfin];"
        f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,"
        f"{speed_ramp._atempo_chain(rate)}[aout]"
    )
    cmd = [str(cfg.ffmpeg_bin), "-y", "-v", "error", "-i", str(fl),
           "-filter_complex", filt, "-map", "[vfin]", "-map", "[aout]",
           "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
           "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "-ar", "48000",
           "-f", "mov", str(dst)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return probe_duration(dst, cfg)


XFADE_GROUP = 6


def build_titled_intro(part: int, episode: int, dst: Path, cfg: Config,
                      backdrop: list[Path]) -> Optional[Path]:
    """Produced opener: PANTHEON mark + title text over T2/T3 footage.

    User 2026-08-29: "use t2 or t3 to do intro outro with effect / text /
    watermarks / wow factor." The frag clips are the BODY; the opener is a
    made thing -- animated brand mark, title, grade, aberration -- built on
    atmospheric lower-tier footage (Rule P1-B: T3/T2 are the intro/outro pool).

    Reuses the PANTHEON generator so the branding matches the series.
    """
    try:
        from creative_suite.engine import pantheon_intro as pi
    except Exception as exc:
        print(f"  [intro] generator unavailable ({exc}) -- skipping")
        return None
    try:
        # No own music: the reel's continuous bed plays across it.
        out = pi.render_intro(part, dst, cfg, duration=INTRO_S,
                              with_music=False)
        return out if out and out.exists() else None
    except Exception as exc:
        print(f"  [intro] render failed ({exc}) -- skipping")
        return None


def build_titled_outro(part: int, dst: Path, cfg: Config,
                       label: str | None = None,
                       facts: list | None = None) -> Optional[Path]:
    """Produced closer: mark held high, credits stacked, slow graded footage."""
    try:
        from creative_suite.engine import pantheon_intro as pi
    except Exception as exc:
        print(f"  [outro] generator unavailable ({exc}) -- skipping")
        return None
    try:
        out = pi.render_outro(part, dst, cfg, duration=OUTRO_S,
                              label=label, facts=facts,
                              with_music=False)
        return out if out and out.exists() else None
    except Exception as exc:
        print(f"  [outro] render failed ({exc}) -- skipping")
        return None


def concat_hard(segments: list[Path], dst: Path, cfg: Config) -> Path:
    """Butt segments together with HARD CUTS via the concat demuxer.

    Rule (learned, pre-existing): "xfade between fragmovie clips = terrible.
    Always use concat (hard cuts)." A dissolve smears two different rooms over
    each other and reads as a mistake, not a transition -- confirmed on the
    0.75 s build. Hard cuts are also what lets a cut land exactly on a beat.

    The demuxer needs no re-encode of the whole graph, so this is fast and
    cannot melt down the way a 71-input xfade chain did.
    """
    lst = dst.parent / "_concat.txt"
    # The concat DEMUXER is wrong for this job: it stitches bitstreams without
    # re-encoding, and our segments carry different SPS/PPS, so the result was a
    # corrupt stream ("Invalid NAL unit size", "Error splitting the input into
    # NAL units") and silently lost 78 s of a 290 s reel. The concat FILTER
    # decodes every input and re-encodes once, which cannot desync.
    lines = [f"file '{s.as_posix()}'" for s in segments]
    lst.write_text("\n".join(lines) + "\n", encoding="utf-8")

    inputs: list[str] = []
    for seg in segments:
        inputs += ["-i", str(seg)]
    pre = "".join(
        f"[{i}:v]setpts=PTS-STARTPTS,fps={cfg.target_fps},"
        f"scale={cfg.target_width}:{cfg.target_height},setsar=1,"
        f"format=yuv420p[v{i}];"
        f"[{i}:a]asetpts=PTS-STARTPTS,aresample=async=1:first_pts=0,"
        f"aformat=sample_rates=48000:channel_layouts=stereo[a{i}];"
        for i in range(len(segments))
    )
    pairs = "".join(f"[v{i}][a{i}]" for i in range(len(segments)))
    filt = f"{pre}{pairs}concat=n={len(segments)}:v=1:a=1[vout][aout]"

    cmd = ([str(cfg.ffmpeg_bin), "-y", "-v", "error"] + inputs
           + ["-filter_complex", filt, "-map", "[vout]", "-map", "[aout]",
              "-c:v", "libx264", "-crf", "18", "-preset", "medium",
              "-pix_fmt", "yuv420p", "-r", str(cfg.target_fps),
              "-c:a", "pcm_s16le", "-ar", "48000", "-f", "mov", str(dst)])
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("concat failed:\n" + r.stderr[-1500:])
    return dst


def concat_with_xfade(segments: list[Path], dst: Path, cfg: Config) -> Path:
    """Cross-dissolve every seam, assembled as a two-level tree.

    A single linear xfade chain over N inputs is serial -- each xfade consumes
    the previous one's output -- and ffmpeg crawls on it. At 71 segments it
    burned 600+ CPU-seconds without emitting a frame. Grouping into small
    chains and then joining the groups keeps every seam dissolved while each
    individual graph stays shallow.
    """
    if len(segments) == 1:
        subprocess.run([str(cfg.ffmpeg_bin), "-y", "-v", "error",
                        "-i", str(segments[0]), "-c", "copy", str(dst)],
                       check=True)
        return dst

    if len(segments) > XFADE_GROUP:
        groups = [segments[i:i + XFADE_GROUP]
                  for i in range(0, len(segments), XFADE_GROUP)]
        parts: list[Path] = []
        for gi, grp in enumerate(groups):
            gp = dst.parent / f"_grp{gi:03d}.mov"
            if not gp.exists():
                _xfade_chain(grp, gp, cfg)
            parts.append(gp)
            print(f"  [xfade] group {gi + 1}/{len(groups)} ({len(grp)} segs)")
        return _xfade_chain(parts, dst, cfg)

    return _xfade_chain(segments, dst, cfg)


def _xfade_chain(segments: list[Path], dst: Path, cfg: Config) -> Path:
    """Linear xfade over a short list of uniform segments."""
    if len(segments) == 1:
        subprocess.run([str(cfg.ffmpeg_bin), "-y", "-v", "error",
                        "-i", str(segments[0]), "-c", "copy", str(dst)],
                       check=True)
        return dst

    durs = [probe_duration(s, cfg) for s in segments]
    inputs: list[str] = []
    for s in segments:
        inputs += ["-i", str(s)]

    vchain, achain = [], []
    for i in range(len(segments)):
        vchain.append(f"[{i}:v]setpts=PTS-STARTPTS,fps={cfg.target_fps},"
                      f"format=yuv420p[v{i}]")
        achain.append(f"[{i}:a]asetpts=PTS-STARTPTS,aresample=async=1[a{i}]")

    cur_v, cur_a = "[v0]", "[a0]"
    offset = durs[0]
    steps = []
    for i in range(1, len(segments)):
        off = max(0.0, offset - XFADE_S)
        steps.append(f"{cur_v}[v{i}]xfade=transition=fade:duration={XFADE_S}"
                     f":offset={off:.4f}[vx{i}]")
        steps.append(f"{cur_a}[a{i}]acrossfade=d={XFADE_S}:c1=tri:c2=tri[ax{i}]")
        cur_v, cur_a = f"[vx{i}]", f"[ax{i}]"
        offset = off + durs[i]

    filt = ";".join(vchain + achain + steps)
    cmd = ([str(cfg.ffmpeg_bin), "-y", "-v", "error"] + inputs
           + ["-filter_complex", filt,
              "-map", cur_v, "-map", cur_a,
              # CRF 17, not 18: these group files are joined by STREAM COPY
              # now, so they are the final picture rather than an
              # intermediate re-encoded to 17 later. One generation at
              # the ceiling beats two generations ending at it (P1-J).
              "-c:v", "libx264", "-crf", "17", "-preset", "medium",
              "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", "-ar", "48000",
              "-f", "mov", str(dst)])
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"xfade concat failed:\n{r.stderr[-1500:]}")
    return dst


def _stream_sig(path: Path, cfg: Config) -> str | None:
    """Codec/geometry signature, for deciding whether copy-concat is safe."""
    r = subprocess.run(
        [str(cfg.ffprobe_bin), "-v", "error", "-select_streams", "v:0",
         "-show_entries",
         "stream=codec_name,profile,level,width,height,pix_fmt,r_frame_rate",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True)
    return r.stdout.strip() or None


def _atomic_json(path: Path, obj) -> None:
    """Write JSON atomically -- a torn file must never parse as valid state."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def concat_copy(segments: list[Path], dst: Path, cfg: Config) -> Path:
    """Join ALREADY-UNIFORM segments with no re-encode.

    Safe here and nowhere else. The corruption that made the concat demuxer
    untouchable ("Invalid NAL unit size", 78 s silently lost) came from feeding
    it the RAW clip segments, which carry different SPS/PPS. The group files are
    all produced by _xfade_chain under one fixed encoder setting, so their
    bitstreams already agree.

    Verified on Part 4: 1.2 s instead of 2.5 min, duration within 6 ms, clean
    full decode under -xerror. It also drops a whole generation of loss, since
    body.mov is stream-copied into the final mp4.

    Uniformity is CHECKED, not assumed -- mismatched inputs fall back to the
    re-encoding path rather than risk a corrupt reel.
    """
    sigs = {_stream_sig(x, cfg) for x in segments}
    if len(sigs) != 1 or None in sigs:
        print(f"  [concat] {len(sigs)} differing stream formats -- re-encoding")
        return concat_hard(segments, dst, cfg)

    lst = dst.parent / "_concat_copy.txt"
    lines = [f"file '{x.as_posix()}'" for x in segments]
    lst.write_text("\n".join(lines) + "\n", encoding="utf-8")
    r = subprocess.run(
        [str(cfg.ffmpeg_bin), "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", str(lst), "-c", "copy", str(dst)],
        capture_output=True, text=True)
    if r.returncode != 0 or not dst.exists():
        print("  [concat] copy failed -- re-encoding")
        return concat_hard(segments, dst, cfg)
    return dst


def mux_music(body: Path, music: list[Path], dst: Path, cfg: Config) -> Path:
    """Game audio + music at ONE CONSTANT level.

    Two songs per video (user 2026-08-29), joined end to end and trimmed to the
    body. No sidechain duck, no loudness gate, and the music is never resampled
    or time-stretched, so its pitch is untouched (Rule P1-G v6).
    """
    body_dur = probe_duration(body, cfg)
    inputs: list[str] = ["-i", str(body)]
    for m in music:
        inputs += ["-i", str(m)]

    n = len(music)
    if n == 1:
        pre = "[1:a]anull[mraw];"
    else:
        # Crossfade, never a hard concat. A straight join made song 2 snap in
        # with no beat relationship to song 1 (user: "swap to another music with
        # no beatmatch"). acrossfade overlaps them so the change is a blend.
        pre = "".join(f"[{i + 1}:a]aresample=48000[m{i}];" for i in range(n))
        cur = "[m0]"
        for i in range(1, n):
            pre += f"{cur}[m{i}]acrossfade=d={MUSIC_XFADE_S}:c1=tri:c2=tri[mx{i}];"
            cur = f"[mx{i}]"
        pre += f"{cur}anull[mraw];"

    filt = (
        f"[0:a]volume={GAME_VOLUME}[g];"
        + pre
        + f"[mraw]volume={MUSIC_VOLUME},afade=t=in:st=0:d=1.0,"
          f"afade=t=out:st={max(0.0, body_dur - 4.0):.3f}:d=4.0[m];"
          f"[g][m]amix=inputs=2:duration=first:dropout_transition=0:"
          f"normalize=0[mixed];"
        # SAFETY GATE. amix with normalize=0 SUMS its inputs, so music 1.24 +
        # game 1.45 can reach 2.69x and hard-clip. Measured on the rejected
        # Part12_highlight.mp4: +1.94 dBFS.
        #
        # alimiter is a SAMPLE limiter -- keeping samples under 0 dBFS does not
        # bound the reconstructed TRUE peak. loudnorm targets true peak directly
        # and, in dynamic (single-pass) mode, upsamples internally for true-peak
        # detection. TP is set below the -1.0 dBTP requirement for margin, since
        # AAC encoding can nudge peaks upward after the filter graph.
        # HARD CEILING. loudnorm is a NORMALISER, not a limiter: when the mix
        # sits below target it applies gain to reach I=-14 and its internal
        # true-peak control overshoots badly. Measured on real episodes with
        # TP asked at -2.0, output still landed at +0.2 and -0.1 dBTP -- both
        # over the -1.0 dBTP acceptance ceiling, and a retry reproduces them
        # because the input is identical.
        #
        # alimiter is a SAMPLE limiter, so on its own it cannot bound the
        # reconstructed inter-sample peak. Running it at 4x the sample rate
        # makes it a true-peak limiter in practice: the resampler exposes the
        # inter-sample overshoots as real samples, the limiter catches them,
        # and the result is downsampled back. Verified on the rejected
        # Part3_highlight_ep2.mp4: +0.2 dBTP in, -1.9 dBTP out.
        #
        # This is a peak ceiling only. It does not follow the action and does
        # not modulate music level, so P1-G still holds -- the music stays at
        # one fixed level.
          f"[mixed]loudnorm=I={TARGET_LUFS}:TP={TARGET_TP}:LRA=11,"
          f"aresample=192000,alimiter=limit={TP_LIMIT_LINEAR}:level=false,"
          f"aresample=48000[aout]"
    )

    # Video is mapped through UNTOUCHED -- no video filter runs here, this step
    # only attaches the audio. body.mov is already H.264 High 1920x1080p60 at
    # CRF 17, which IS the quality ceiling (P1-J), so re-encoding it a second
    # time bought nothing and cost everything: ~20 min per episode of wall clock
    # plus a generation loss on top of an already-final picture. Stream-copy is
    # both faster and strictly higher quality. Only the audio is encoded.
    cmd = ([str(cfg.ffmpeg_bin), "-y", "-v", "error"] + inputs
           + ["-filter_complex", filt, "-map", "0:v", "-map", "[aout]",
              "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
              "-t", f"{body_dur:.3f}", "-movflags", "+faststart", str(dst)])
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("music mux failed:\n" + r.stderr[-1500:])
    return dst


def _pick_music(part: int, cfg: Config, episode: int = 1,
                count: int = 2, mean_clip_s: float = 0.0,
                body_s: float = 300.0) -> list[Path]:
    """A song no other video has used.

    Every Part gets a different track (user 2026-08-29: "never 2 of the same"),
    and uniqueness is by CONTENT hash, not filename -- four pairs of slot files
    in this library hold the identical song under different names.

    Prefers this Part's own slots, then falls back to any unused slot in the
    library so extra episodes still get fresh music.
    """
    mdir = REPO_ROOT / "creative_suite" / "engine" / "music"
    mine = sorted(mdir.glob(f"part{part:02d}_music_*.mp3"))
    mine += sorted(mdir.glob(f"part{part:02d}_music.mp3"))

    # The per-Part slots hold only ~42 distinct songs, but exhausting T1+T2
    # across 12 Parts needs ~71 episodes x 2 songs = ~142 unique tracks. The
    # full libraries carry 1400+, so draw from those once the slots run out --
    # otherwise "never 2 of the same" silently breaks after 21 videos.
    others: list[Path] = sorted(
        q for q in mdir.glob("part*_music_*.mp3") if q not in mine)
    for lib in (REPO_ROOT / "engine" / "music" / "library",
                mdir / "library"):
        if lib.is_dir():
            others += sorted(q for q in lib.rglob("*")
                             if q.suffix.lower() in (".mp3", ".ogg")
                             and q.is_file())

    picked: list[Path] = []

    # BEATMATCH. When the analysis cache is populated, choose by how well the
    # track's BAR grid fits this episode's actual clip pacing -- a cut reads as
    # deliberate when it lands on a downbeat, so we want the tempo where the
    # mean clip length is close to a whole number of bars. Falls back to the
    # plain unused-song picker when a song is not analysed yet, so a cold cache
    # never blocks a render.
    if mean_clip_s and mean_clip_s > 0:
        try:
            used = set(highlight_ledger.used_songs().keys())
            cands = music_beatmatch.pick_for_episode(
                mean_clip_s=mean_clip_s,
                min_duration_s=max(120.0, body_s / max(1, count) * 0.9),
                used_ids=used, count=max(1, count))
            for c in cands:
                q = Path(c["path"])
                if not q.exists():
                    continue
                highlight_ledger.claim_song(q, f"part{part:02d}ep{episode}")
                picked.append(q)
                print(f"  [beatmatch] {q.name[:46]}  {c['bpm']:.1f} bpm  "
                      f"bar-fit {c['bar_fit']:.3f}  score {c['match_score']:.3f}")
        except Exception as exc:                    # noqa: BLE001
            print(f"  [beatmatch] unavailable ({exc}); using plain picker")

    for _ in range(max(1, count) - len(picked)):
        pick = highlight_ledger.pick_unused_song(mine + others)
        if pick is None:
            break
        highlight_ledger.claim_song(pick, f"part{part:02d}ep{episode}")
        picked.append(pick)
    if not picked and mine:
        print(f"  [music] WARNING: library exhausted, reusing {mine[0].name}")
        picked = [mine[0]]
    return picked


def build(part: int, minutes: float, out: Path, cfg: Config,
          work: Optional[Path] = None, episode: int = 1,
          manifest: Optional[Path] = None,
          preset_music: Optional[list[Path]] = None,
          exclude: Optional[Path] = None,
          queue_rows: Optional[list] = None) -> Path:
    target_s = minutes * 60.0
    # The work dir MUST be episode-scoped. Segments are cached by index
    # ("seg000.mov", reused when it already exists), so a Part-scoped dir made
    # episode 2 reuse episode 1's rendered segments: the reel would show
    # episode 1's clips while the ledger recorded episode 2's SELECTED clips as
    # shipped. Clips marked consumed that never appeared on screen.
    work = work or (REPO_ROOT / "output" / f"_hl_part{part:02d}_ep{episode:02d}")
    work.mkdir(parents=True, exist_ok=True)

    if queue_rows is not None:
        # Explicit list from the master queue: play these, in this order.
        frags = frags_from_queue(queue_rows, cfg)
        print(f"[hl] {len(frags)} frag(s) handed in from the master queue")
    else:
        print(f"[hl] collecting frags for Part {part}")
        frags = collect_frags(part, cfg)

    # EXCLUSION. Selection previously ran over EVERY frag in the Part, so a
    # second episode re-picked the same top clips while the ledger recorded
    # them as newly shipped -- coverage counted up while the same footage kept
    # being rendered. The caller passes the canonical paths already consumed by
    # committed episodes and they are removed here, before selection.
    if exclude:
        spent = set()
        try:
            for line in Path(exclude).read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    spent.add(line.lower())
        except OSError as exc:
            raise RuntimeError(f"exclude list unreadable: {exc}") from exc
        before = len(frags)
        frags = [f for f in frags
                 if str(f.fp.resolve()).lower() not in spent]
        print(f"[hl] excluded {before - len(frags)} already-shipped clip(s); "
              f"{len(frags)} remain selectable")

    t1 = sum(1 for f in frags if f.tier == "T1")
    print(f"[hl] {len(frags)} frags parsed (T1={t1}, "
          f"with-FL={sum(1 for f in frags if f.fls)})")

    if queue_rows is not None:
        # Packing already happened in the orchestrator against MEASURED
        # durations. Re-running selection here would drop or reorder clips and
        # break the "every clip exactly once" chain.
        chosen = []
        for f in frags:
            f.duration = probe_duration(f.fp, cfg)
            if f.duration <= 0:
                print(f"  [skip] {f.fp.name}: unreadable")
                continue
            f.peak = peak_guard.find_peak_guarded(f.fp, f.duration)
            w0, w1 = source_window(f.peak, f.duration, f.fp)
            f.out_duration = w1 - w0
            chosen.append(f)
    else:
        chosen = select_frags(frags, target_s, cfg)
    print(f"[hl] selected {len(chosen)} frags "
          f"(T1={sum(1 for f in chosen if f.tier=='T1')}, "
          f"T2={sum(1 for f in chosen if f.tier=='T2')}) "
          f"~{sum(f.out_duration for f in chosen)/60:.2f} min")

    # The grid comes from the track this video will actually carry, not from a
    # per-Part beats file written for some earlier run. Drops are the strongest
    # landing points a listener hears, so they are loaded too.
    beats, downbeats, drops = [], [], []
    if preset_music:
        beats, downbeats, drops = music_grid(
            [q for q in preset_music if q.exists()], cfg)
    if not beats:
        beats, downbeats = load_beats(part, cfg)
    print(f"[hl] beat grid: {len(beats)} beats, {len(downbeats)} downbeats, "
          f"{len(drops)} drops, spans {beats[-1] if beats else 0:.0f}s")

    segments: list[Path] = []
    used_frags: list[Frag] = []
    timeline = 0.0
    n_accent = 0               # accented shots so far
    last_scratch = -99         # keeps rollbacks from bunching up
    last_pip = -99             # ...and insets
    for n, f in enumerate(chosen):
        seg = work / f"seg{n:03d}.mov"
        # There is deliberately no "target duration" here. An earlier version
        # snapped a target length to the next beat and handed it to the
        # renderer, which ignored it -- so the whole thing was decoration. It
        # could not have worked anyway: reaching a beat by shortening a clip is
        # banned (P1-S -- beat-sync moves seams, never clip durations), and the
        # user's own rule is that clips play their full length. Landing on the
        # grid is done below instead, by solving the slow-mo STRENGTH, which
        # changes when the cut arrives without cutting anything out.
        # Accent only every Nth frag, and only a T1 one. Everything else plays
        # straight -- per-frag slow-mo is the scene's most-mocked mistake.
        # Accent every Nth T1, PLUS any short clip: a short capture is almost
        # all money-shot, so it earns the accent regardless of cadence.
        slowmo = (((n % SLOWMO_EVERY_N == 0) and f.tier == "T1")
                  or f.duration <= SHORT_CLIP_SLOWMO_S)

        # Variable slow-mo STRENGTH, on the clips that already get an accent.
        # User 2026-08-31: "we are allowed here to change the strength of the
        # slowmo to match ... 30% / 60%", and "use existing slowmo dont make the
        # video a yoyo" -- so this never adds an accent, it only tunes the ones
        # already chosen, and only on SHORT single-frag clips so the treatment
        # stays consistent across the video. A long multi-kill keeps the
        # standard rate; stretching those to chase a beat would be obvious.
        # The scratch replay is a VARIATION on the long accented T1 shots --
        # the ones with enough runway for a rollback to read. It is deliberately
        # disjoint from the short-clip beat lock below, so a shot gets one
        # treatment or the other, never both.
        rate, scratch = None, False
        if slowmo:
            n_accent += 1
            w0, w1 = source_window(f.peak, f.duration, f.fp)
            aw, bw = accent_window(w0, w1, f.peak)
            vt = video_time(timeline, n)

            # The rollback has to be MUSICALLY motivated -- user 2026-08-31:
            # "it need to happen when the music fit or do something similar
            # (like downbeat tempo)". So the scratch is not a cadence: the
            # moment the picture is pulled back must land on a drop or a
            # downbeat, and the slow rate is solved to put it there. Modelling
            # the segment as ending at `bw` makes the solved landing the START
            # of the rewind, which is the beat the viewer actually feels. A
            # plain beat is not reason enough for an effect this strong.
            if (beats and f.tier == "T1"
                    and f.duration >= SCRATCH_MIN_SRC_S
                    and f.duration > SHORT_CLIP_SLOWMO_S
                    and n_accent - last_scratch >= SCRATCH_MIN_GAP):
                hit = speed_ramp.accent_rate_for_landing(
                    w0, aw, bw, bw, vt, beats, downbeats, drops,
                    allowed_kinds=("drop", "downbeat"))
                if hit:
                    rate, land, kind = hit
                    scratch = True
                    last_scratch = n_accent
                    print(f"  [scratch] {f.fp.name[:30]:30} slow {rate:.2f}x, "
                          f"rollback on {kind} at {land:.2f}s")

            # Short single-frag shots instead get their accent STRENGTH solved
            # so the cut lands on the music. Disjoint from the scratch above --
            # one treatment per shot, never both.
            if not scratch and beats and f.duration <= SHORT_CLIP_SLOWMO_S:
                lock = speed_ramp.accent_rate_for_landing(
                    w0, aw, bw, w1, vt, beats, downbeats, drops)
                if lock:
                    rate, land, kind = lock
                    print(f"  [lock] {f.fp.name[:34]:34} slow {rate:.2f}x -> "
                          f"lands on {kind} at {land:.2f}s")

        # A grenade play with a second camera gets the follow angle inset, so
        # the shell's flight and its landing are both visible. Only on shots
        # playing straight -- a speed ramp would put the two cameras on
        # different clocks.
        pip = None
        if (not slowmo and f.fls and n - last_pip >= PIP_MIN_GAP
                and has_grenade(f.fp)):
            pip = f.fls[0]
            last_pip = n
            print(f"  [inset] {f.fp.name[:34]:34} grenade -- follow camera inset")

        if not seg.exists():
            try:
                render_frag(f, seg, cfg, slowmo=slowmo, slow_rate=rate,
                            scratch=scratch, pip=pip)
            except RuntimeError as exc:
                print(f"  [skip] {f.fp.name}: {exc}")
                continue

        # MULTIPLE angles on the same frag (user 2026-08-29: "multiple pov for
        # same frag"). Angle 1 leads IN to the POV so the viewer reads the
        # geometry first; any further angle plays after as a second look. Every
        # angle comes from this frag's own folder, so they cannot cross frags.
        lead = work / f"seg{n:03d}_fl.mov"
        has_lead = False
        if f.fls and FL_LEADS_IN:
            if not lead.exists():
                render_fl_angle(f, lead, cfg, which=0, slow=0.55)
            if _valid_segment(lead, cfg):
                segments.append(lead)
                timeline += probe_duration(lead, cfg)
                has_lead = True

        if not _valid_segment(seg, cfg):
            print(f"  [drop] {f.fp.name}: segment unreadable, skipping frag")
            try:
                seg.unlink()
            except OSError:
                pass
            if has_lead and segments and segments[-1] == lead:
                # Its lead-in would otherwise dangle with no POV to lead into.
                segments.pop()
                timeline -= probe_duration(lead, cfg)
            continue

        d = probe_duration(seg, cfg)
        f.slowmo_applied = slowmo
        segments.append(seg)
        used_frags.append(f)
        timeline += d

        n_angles = 1 + int(has_lead)
        if len(f.fls) > 1:
            second = work / f"seg{n:03d}_fl2.mov"
            if not second.exists():
                render_fl_angle(f, second, cfg, which=1, slow=0.5)
            if _valid_segment(second, cfg):
                segments.append(second)
                timeline += probe_duration(second, cfg)
                n_angles += 1

        print(f"  [{n+1}/{len(chosen)}] {f.tier} {f.fp.name} "
              f"-> {d:.2f}s{f' [{n_angles} angles]' if n_angles > 1 else ''}"
              f"{' [SLOWMO]' if slowmo else ''} "
              f"(timeline {timeline/60:.2f} min)")
        # PACKING (user 2026-08-29): "keep adding complete clips while the
        # episode remains around the target; if the next COMPLETE clip makes
        # the episode unreasonably long, carry that clip to the next episode."
        # Never split a frag for packaging. The decision uses the FINAL
        # RENDERED duration, so a slow-mo expansion cannot silently blow the
        # episode out to seven minutes.
        if queue_rows is not None:
            continue            # explicit list: every handed-in clip must ship
        if timeline >= target_s:
            break
        if timeline >= target_s * BODY_SOFT_FLOOR:
            nxt = chosen[n + 1] if n + 1 < len(chosen) else None
            if nxt is not None and timeline + nxt.out_duration > target_s * BODY_HARD_CEIL:
                print(f"  [pack] carrying {nxt.fp.name} "
                      f"(~{nxt.out_duration:.1f}s) to the next episode -- "
                      f"would take this one to "
                      f"{(timeline + nxt.out_duration)/60:.2f} min")
                break

    # Produced opener and closer bracket the frag body.
    opener = build_titled_intro(part, 1, work / "_intro.mp4", cfg, [])
    # The outro credits the OUTPUT part, and carries a couple of facts about
    # what is actually in this video -- clip count, tiers, the frag types.
    _label = "Part {:02d}".format(episode)
    _t1 = sum(1 for f in used_frags if f.tier == "T1")
    _t2 = sum(1 for f in used_frags if f.tier == "T2")
    _facts = ["{} frags  ·  {} T1  ·  {} T2".format(len(used_frags), _t1, _t2)]
    _sm = sum(1 for f in used_frags if getattr(f, "slowmo_applied", False))
    if _sm:
        _facts.append("{} slow-motion accents".format(_sm))
    closer = build_titled_outro(part, work / "_outro.mp4", cfg,
                                label=_label, facts=_facts)
    if opener and not _valid_segment(opener, cfg):
        print("  [intro] produced opener invalid -- omitting")
        opener = None
    if closer and not _valid_segment(closer, cfg):
        print("  [outro] produced closer invalid -- omitting")
        closer = None
    if opener:
        segments.insert(0, opener)
        print(f"  [intro] produced opener {probe_duration(opener, cfg):.1f}s")
    if closer:
        segments.append(closer)
        print(f"  [outro] produced closer {probe_duration(closer, cfg):.1f}s")

    print(f"[hl] {len(segments)} segments, {XFADE_S}s crossfades")
    body = work / "body.mov"
    # Crossfade every seam (0.20 s, below the visibility ceiling), assembled as
    # groups so no single graph gets deep enough to stall, then joined with the
    # concat FILTER -- the demuxer corrupts these streams.
    if len(segments) > XFADE_GROUP:
        groups = [segments[i:i + XFADE_GROUP]
                  for i in range(0, len(segments), XFADE_GROUP)]
        parts_: list[Path] = []
        for gi, grp in enumerate(groups):
            gp = work / f"_grp{gi:03d}.mov"
            if not gp.exists():
                _xfade_chain(grp, gp, cfg) if len(grp) > 1 else concat_hard(grp, gp, cfg)
            if _valid_segment(gp, cfg):
                parts_.append(gp)
            print(f"  [xfade] group {gi + 1}/{len(groups)} ({len(grp)} segs)")
        concat_copy(parts_, body, cfg)
    else:
        _xfade_chain(segments, body, cfg)

    # Pacing drives the music choice, so it is measured from the segments we
    # actually rendered -- not from raw clip lengths, which slow-mo invalidates.
    _seg_durs = [f.out_duration for f in used_frags if f.out_duration]
    _mean_clip = (sum(_seg_durs) / len(_seg_durs)) if _seg_durs else 0.0
    if preset_music:
        music = [q for q in preset_music if q.exists()]
        print("  [music] using {} caller-selected track(s)".format(len(music)))
    else:
        music = _pick_music(part, cfg, episode=episode,
                            mean_clip_s=_mean_clip,
                            body_s=probe_duration(body, cfg))
    if music:
        print(f"[hl] music (constant {MUSIC_VOLUME}, no duck): "
              + ", ".join(m.name for m in music))
        mux_music(body, music, out, cfg)
    else:
        subprocess.run([str(cfg.ffmpeg_bin), "-y", "-v", "error", "-i",
                        str(body), "-c:v", "libx264", "-crf", "17",
                        "-c:a", "aac", str(out)], check=True)

    print(f"[hl] DONE {out}  {probe_duration(out, cfg)/60:.2f} min  "
          f"{out.stat().st_size/1048576:.1f} MB")

    used_clips = [f.fp for f in used_frags]

    if manifest is not None:
        # ORCHESTRATED MODE. Report what was used and burn NOTHING. The caller
        # runs audio and decode QA first, and only commits coverage once the
        # episode passes -- a failed render must never consume its clips.
        rec = {
            "part": part,
            "episode": episode,
            "output_path": str(out),
            "clips": [
                {"path": str(f.fp.resolve()), "tier": f.tier,
                 "rendered_duration_s": round(float(f.out_duration or 0.0), 3)}
                for f in used_frags
            ],
            "clip_count": len(used_clips),
            "t1_clips": sum(1 for f in used_frags if f.tier == "T1"),
            "t2_clips": sum(1 for f in used_frags if f.tier == "T2"),
            "t3_clips": sum(1 for f in used_frags if f.tier == "T3"),
        }
        seg_map = []
        for i, f in enumerate(used_frags):
            try:
                st = f.fp.stat()
                size, mtime = st.st_size, int(st.st_mtime)
            except OSError:
                size, mtime = None, None
            seg_map.append({
                "segment_index": i,
                "canonical_source_path": str(f.fp.resolve()),
                "tier": f.tier,
                "source_duration_s": round(float(f.duration or 0.0), 3),
                "rendered_segment_duration_s": round(float(f.out_duration or 0.0), 3),
                "slowmo": bool(getattr(f, "slowmo_applied", False)),
                "source_filesize": size,
                "source_mtime": mtime,
                "angles": len(f.fls),
                "generated_segment": "seg{:03d}.mov".format(i),
            })
        rec["segment_map"] = seg_map

        manifest.parent.mkdir(parents=True, exist_ok=True)
        _atomic_json(manifest, rec)
        smp = manifest.with_name(manifest.stem + "_segment_map.json")
        _atomic_json(smp, {"part": part, "episode": episode,
                           "output_path": str(out), "segments": seg_map})
        print(f"[hl] manifest -> {manifest}  ({len(used_clips)} clips, "
              f"NOT yet committed)")
        return out

    # Standalone mode keeps the old self-committing behaviour.
    ep = highlight_ledger.mark_used(part, used_clips, output=out.name)
    n_left, folder = highlight_ledger.stage_unused(part, frags, used_clips)
    cov = highlight_ledger.coverage(part, frags)
    print(f"[hl] episode {ep}: {len(used_clips)} clips used, "
          f"{cov.left}/{cov.total} left ({cov.pct:.0f}% of Part {part} shipped)")
    print(f"[hl] unused staged -> {folder}  ({n_left} file(s), hard-linked)")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", type=int, required=True)
    ap.add_argument("--minutes", type=float, default=5.0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--episode", type=int, default=1)
    ap.add_argument("--work", default=None,
                    help="work directory for this render; MUST be unique per "
                         "output or cached segments leak between them")
    ap.add_argument("--queue", default=None,
                    help="JSON file with an ordered list of queue rows to "
                         "render; disables internal selection entirely")
    ap.add_argument("--exclude", default=None,
                    help="file of canonical clip paths already shipped; they "
                         "are removed before selection")
    ap.add_argument("--music", default=None,
                    help="pipe-separated track paths chosen by the caller; "
                         "skips selection entirely so parallel episodes cannot "
                         "race on the song registry")
    ap.add_argument("--manifest", default=None,
                    help="write the used-clip manifest here and DO NOT commit "
                         "coverage; the caller commits after QA passes")
    a = ap.parse_args()
    cfg = Config()
    out = Path(a.out) if a.out else (
        REPO_ROOT / "output" / f"Part{a.part}_highlight_5min.mp4")
    preset = [Path(x) for x in a.music.split("|") if x.strip()] if a.music else None
    build(a.part, a.minutes, out, cfg,
          work=Path(a.work) if a.work else None,
          episode=a.episode,
          manifest=Path(a.manifest) if a.manifest else None,
          preset_music=preset,
          exclude=Path(a.exclude) if a.exclude else None,
          queue_rows=(json.loads(Path(a.queue).read_text(encoding="utf-8"))
                      if a.queue else None))
    return 0


if __name__ == "__main__":
    sys.exit(main())
