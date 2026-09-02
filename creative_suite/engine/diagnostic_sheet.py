"""The editorial diagnostic sheet: one timeline that explains an edit.

WHAT IT IS FOR. Looking at a rendered scene tells you it feels wrong. This
tells you why, before the full movie is built: the kill is here but the beat
is there, the effect starts after the event it reacts to, the camera outlives
its subject, the counter decrements before the frag. Every claim about
timing in this project that turned out to be false would have been visible on
a sheet like this in one glance.

It is a DIAGNOSTIC INSTRUMENT, not a dashboard. Nothing is drawn to look
impressive. Lanes share one x axis, the hero event gets one unmissable line,
and anything that can be off by milliseconds is drawn where the milliseconds
are readable.

LANES ARE GENERIC ON PURPOSE. There are only four primitives -- instants,
intervals, waveforms and curves -- and every present and future lane is one
of them. Music is a waveform plus instants. A camera segment is an interval
with a subject. A texture swap, a ghost trail, a projectile bridge, an enemy
counter: all intervals with a semantic purpose. Adding the effects lanes
later means constructing intervals, not extending this module.

EVERY EFFECT LANE CARRIES A PURPOSE. An interval may say why it exists
(REVEAL_TRAJECTORY, REINFORCE_MUSIC_DROP, SHOW_1VX_THREATS...). A future
review tool can then ask the question that matters about any effect: why is
this here?
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Sequence

import numpy as np

SHEET_VERSION = "diagnostic-sheet-v1.0.0"

# Lane categories, in the order they are drawn. Gameplay at the top because
# it is the truth everything else is measured against.
CAT_GAMEPLAY = "GAMEPLAY"
CAT_TIME = "TIME"
CAT_CAMERA = "CAMERA"
CAT_GAME_AUDIO = "GAME_AUDIO"
CAT_SELECTIVE = "SELECTIVE_REFERENCE"
CAT_MUSIC = "MUSIC"
CAT_MUSIC_COMPONENTS = "MUSIC_COMPONENTS"
CAT_FX = "FX"
CAT_TRANSITION = "TRANSITION"
CAT_MATERIAL = "MATERIAL"
CAT_MODEL = "MODEL"
CAT_SEMANTIC = "SEMANTIC_STATE"
CAT_SYNC = "SYNC"

CATEGORY_ORDER = (CAT_GAMEPLAY, CAT_SEMANTIC, CAT_TIME, CAT_CAMERA,
                  CAT_FX, CAT_TRANSITION, CAT_MATERIAL, CAT_MODEL,
                  CAT_GAME_AUDIO, CAT_SELECTIVE, CAT_MUSIC,
                  CAT_MUSIC_COMPONENTS, CAT_SYNC)

# Semantic purposes an effect may declare.
PURPOSES = ("REVEAL_TRAJECTORY", "SHOW_1VX_THREATS", "EMPHASIZE_LOW_HP",
            "TRANSITION_TO_NEXT_SCENE", "REINFORCE_MUSIC_DROP",
            "EXPOSE_DODGE_CLEARANCE", "ESTABLISH_SUBJECT", "NONE")

PALETTE = {
    "bg": "#0f1115", "panel": "#171a20", "grid": "#2b313b",
    "text": "#e9eef7", "muted": "#aab3c0",
    "game": "#4fd1ff", "music": "#c9a227", "perc": "#ff8c42",
    "harm": "#7ee787", "hero": "#ff4d4d", "target": "#ffd166",
    "fx": "#b78cff", "camera": "#5ad1b0", "warn": "#ff6b6b",
}


# ── lane primitives ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Instant:
    """A moment. The thing whose milliseconds matter."""
    us: int
    label: str = ""
    color: str = PALETTE["game"]
    weight: float = 1.0


@dataclass(frozen=True)
class Interval:
    """A span with a beginning, an end and, ideally, a reason."""
    start_us: int
    end_us: int
    label: str = ""
    purpose: str = "NONE"
    state: str = ""
    color: str = PALETTE["fx"]
    trigger_us: int | None = None       # the event this span answers to
    delivered_start_us: int | None = None   # where it actually began

    @property
    def duration_us(self) -> int:
        return self.end_us - self.start_us

    @property
    def latency_ms(self) -> float | None:
        """How late the span began relative to the event that triggered it."""
        if self.trigger_us is None:
            return None
        start = (self.delivered_start_us if self.delivered_start_us is not None
                 else self.start_us)
        return round((start - self.trigger_us) / 1000.0, 2)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["latency_ms"] = self.latency_ms
        return d


@dataclass
class Lane:
    """One row. Exactly one of the four primitives is populated."""
    name: str
    category: str
    instants: tuple[Instant, ...] = ()
    intervals: tuple[Interval, ...] = ()
    waveform: np.ndarray | None = None
    waveform_sr: int | None = None
    waveform_offset_us: int = 0
    curve: tuple[tuple[int, float], ...] = ()
    color: str = PALETTE["game"]
    height: float = 1.0
    note: str = ""
    # A lane may zoom to a window around the hero event. Layer offsets of a
    # few milliseconds are invisible on a ten-second axis, so the lane whose
    # whole job is those milliseconds gets its own scale.
    zoom_us: int | None = None

    @property
    def kind(self) -> str:
        if self.waveform is not None:
            return "waveform"
        if self.intervals:
            return "interval"
        if self.curve:
            return "curve"
        return "instant"


@dataclass(frozen=True)
class SyncMarker:
    """One side-by-side timing relationship, drawn where it can be read."""
    label: str
    game_us: int
    music_us: int
    target_delta_ms: float | None = None
    color: str = PALETTE["target"]

    @property
    def delta_ms(self) -> float:
        return round((self.music_us - self.game_us) / 1000.0, 2)

    @property
    def error_ms(self) -> float | None:
        if self.target_delta_ms is None:
            return None
        return round(self.delta_ms - self.target_delta_ms, 2)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["delta_ms"] = self.delta_ms
        d["error_ms"] = self.error_ms
        return d


# ── the sheet ───────────────────────────────────────────────────────────────

@dataclass
class DiagnosticSheet:
    title: str
    scene_start_us: int
    scene_end_us: int
    lanes: list[Lane] = field(default_factory=list)
    hero_us: int | None = None
    hero_label: str = "HERO"
    sync_markers: tuple[SyncMarker, ...] = ()
    subtitle: str = ""

    def add(self, lane: Lane) -> "DiagnosticSheet":
        self.lanes.append(lane)
        return self

    def ordered(self) -> list[Lane]:
        rank = {c: i for i, c in enumerate(CATEGORY_ORDER)}
        return sorted(self.lanes, key=lambda l: rank.get(l.category, 99))

    # ── the readable summary, independent of any drawing ────────────────────

    def findings(self) -> list[str]:
        """What the sheet would tell a reader, in words.

        Kept separate from rendering so the same conclusions can be asserted
        in a test without parsing an image.
        """
        out: list[str] = []
        for m in self.sync_markers:
            line = f"{m.label}: music {m.delta_ms:+.1f} ms from the game event"
            if m.error_ms is not None:
                line += f" ({m.error_ms:+.1f} ms from the target)"
            out.append(line)
        for lane in self.ordered():
            for iv in lane.intervals:
                if iv.latency_ms is not None and abs(iv.latency_ms) > 0:
                    out.append(f"{lane.name}/{iv.label}: begins "
                               f"{iv.latency_ms:+.1f} ms from its trigger")
        return out

    def to_dict(self) -> dict[str, Any]:
        return {"title": self.title, "sheet_version": SHEET_VERSION,
                "scene_start_us": self.scene_start_us,
                "scene_end_us": self.scene_end_us,
                "hero_us": self.hero_us,
                "lanes": [{"name": l.name, "category": l.category,
                           "kind": l.kind,
                           "instants": len(l.instants),
                           "intervals": [i.to_dict() for i in l.intervals]}
                          for l in self.ordered()],
                "sync": [m.to_dict() for m in self.sync_markers],
                "findings": self.findings()}

    # ── drawing ─────────────────────────────────────────────────────────────

    def render(self, dst: Path | str, *, dpi: int = 125,
               width: float = 15.0) -> Path:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        lanes = self.ordered()
        if not lanes:
            raise ValueError("a sheet needs at least one lane")
        heights = [l.height for l in lanes]
        fig, axes = plt.subplots(len(lanes), 1, figsize=(
            width, max(3.0, 0.9 * sum(heights) + 1.2)),
            gridspec_kw={"height_ratios": heights})
        if len(lanes) == 1:
            axes = [axes]
        fig.patch.set_facecolor(PALETTE["bg"])
        x0, x1 = self.scene_start_us / 1e6, self.scene_end_us / 1e6
        full = [l for l in lanes if not l.zoom_us]
        last_full = full[-1] if full else None

        for ax, lane in zip(axes, lanes):
            ax.set_facecolor(PALETTE["panel"])
            ax.tick_params(colors=PALETTE["muted"], labelsize=8)
            for s in ax.spines.values():
                s.set_color(PALETTE["grid"])
            if lane.zoom_us and self.hero_us is not None:
                z = lane.zoom_us / 1e6
                ax.set_xlim(self.hero_us / 1e6 - z, self.hero_us / 1e6 + z)
            else:
                ax.set_xlim(x0, x1)
            ax.set_ylabel(lane.name, color=PALETTE["text"], fontsize=8.5,
                          rotation=0, ha="right", va="center")
            if self.hero_us is not None:
                ax.axvline(self.hero_us / 1e6, color=PALETTE["hero"], lw=1.7,
                           zorder=8)
            self._draw_lane(ax, lane)
            # A zoomed lane carries its OWN scale. Without labelling the
            # last full-scale lane too, the zoomed numbers at the bottom read
            # as if they applied to every lane above them.
            if not lane.zoom_us and lane is not last_full:
                ax.set_xticklabels([])

        axes[0].set_title(
            self.title + (f"\n{self.subtitle}" if self.subtitle else ""),
            color=PALETTE["text"], fontsize=11.5, loc="left", pad=10)
        for ax, lane in zip(axes, lanes):
            if lane is last_full or (lane is lanes[-1] and not lane.zoom_us):
                ax.set_xlabel("edit time (s)", color=PALETTE["muted"], fontsize=9)
            elif lane.zoom_us:
                ax.set_xlabel(f"edit time (s) — ZOOMED to "
                              f"±{lane.zoom_us / 1000:.0f} ms around the hero",
                              color=PALETTE["target"], fontsize=9)
        if self.hero_us is not None:
            axes[0].text(self.hero_us / 1e6 + (x1 - x0) * 0.004, 0.5,
                         self.hero_label, color=PALETTE["hero"], fontsize=9,
                         va="center", clip_on=True)
        fig.tight_layout()
        dst = Path(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(dst, dpi=dpi, facecolor=fig.get_facecolor())
        plt.close(fig)
        return dst

    def _draw_lane(self, ax, lane: Lane) -> None:
        kind = lane.kind
        if kind == "waveform" and lane.waveform is not None:
            sr = lane.waveform_sr or 22050
            y = lane.waveform
            n = max(1, int(sr * 0.015))
            k = y.size // n
            if k:
                t = (lane.waveform_offset_us / 1e6 +
                     np.arange(k) * n / sr)
                e = np.array([np.sqrt(np.mean(y[i * n:(i + 1) * n] ** 2))
                              for i in range(k)])
                ax.fill_between(t, e, color=lane.color, alpha=.85, lw=0)
            ax.set_yticks([])
        elif kind == "interval":
            ax.set_ylim(0, 1)
            ax.set_yticks([])
            for i, iv in enumerate(lane.intervals):
                y = 0.55 if len(lane.intervals) < 4 else 0.2 + 0.6 * (i % 3) / 3
                ax.barh(y, (iv.end_us - iv.start_us) / 1e6,
                        left=iv.start_us / 1e6, height=0.3,
                        color=iv.color, alpha=.75)
                if iv.label:
                    ax.text(iv.start_us / 1e6, y, " " + iv.label,
                            color=PALETTE["text"], fontsize=7.5,
                            va="center", clip_on=True)
                if iv.trigger_us is not None:
                    ax.plot([iv.trigger_us / 1e6], [y], marker="|", ms=12,
                            color=PALETTE["warn"], clip_on=True)
        elif kind == "curve":
            t = [p[0] / 1e6 for p in lane.curve]
            v = [p[1] for p in lane.curve]
            ax.plot(t, v, color=lane.color, lw=1.6, drawstyle="steps-post")
            ax.set_ylim(min(v) - 0.05 * (max(v) - min(v) or 1),
                        max(v) + 0.05 * (max(v) - min(v) or 1))
        else:
            ax.set_ylim(0, 1)
            ax.set_yticks([])
            if lane.instants:
                by_color: dict[str, list[float]] = {}
                for ins in lane.instants:
                    by_color.setdefault(ins.color, []).append(ins.us / 1e6)
                for color, xs in by_color.items():
                    ax.eventplot(xs, colors=color, lineoffsets=.5,
                                 linelengths=.85, linewidths=1.8)
                # Stagger the labels. Timing lanes exist to show events that
                # are milliseconds apart, so their labels land on top of each
                # other at exactly the moment the lane matters most.
                labelled = [i for i in lane.instants if i.label]
                for n, ins in enumerate(labelled):
                    ax.text(ins.us / 1e6, 0.95 - 0.24 * (n % 4),
                            " " + ins.label, color=ins.color, fontsize=7.5,
                            va="top", clip_on=True)
        if lane.note:
            ax.text(0.995, 0.05, lane.note, transform=ax.transAxes,
                    color=PALETTE["muted"], fontsize=7.5, ha="right",
                    clip_on=True)


# ── builders: turning project evidence into lanes ───────────────────────────

def gameplay_lane(events: Sequence[Any], *, name: str = "GAMEPLAY",
                  kinds: Sequence[str] | None = None) -> Lane:
    """Authoritative events as instants. Never derived from audio."""
    want = set(kinds) if kinds else None
    picked = [e for e in events
              if (want is None or e.kind in want)]
    return Lane(name=name, category=CAT_GAMEPLAY, height=0.5,
                instants=tuple(Instant(e.edit_us, "", PALETTE["game"])
                               for e in picked),
                note=f"{len(picked)} events from demo evidence")


def waveform_lane(name: str, samples: np.ndarray, sr: int, *,
                  category: str = CAT_GAME_AUDIO, offset_us: int = 0,
                  color: str | None = None, note: str = "") -> Lane:
    return Lane(name=name, category=category, waveform=samples,
                waveform_sr=sr, waveform_offset_us=offset_us,
                color=color or PALETTE["game"], note=note)


def anchor_lane(anchors: Sequence[Any], *, name: str = "MUSIC ANCHORS"
                ) -> Lane:
    """Music Intelligence V3 anchors: perceptual time, coloured by component."""
    return Lane(name=name, category=CAT_MUSIC, height=0.4,
                instants=tuple(Instant(
                    a.perceptual_anchor_us, "",
                    PALETTE["perc"] if a.component == "PERCUSSIVE"
                    else PALETTE["harm"]) for a in anchors),
                note="perceptual anchor, not raw onset")


def effect_lane(name: str, intervals: Sequence[Interval], *,
                category: str = CAT_FX) -> Lane:
    """Generic span lane: FX, transitions, materials, models, scene state.

    This is the extension point. A ghost trail, a texture countdown, a
    projectile bridge and an enemy counter are all intervals with a trigger
    and a purpose, so none of them needs new drawing code.
    """
    return Lane(name=name, category=category, intervals=tuple(intervals),
                height=max(0.5, 0.3 * min(len(intervals), 4)))


def rate_lane(timemap: Sequence[dict], *, name: str = "RATE") -> Lane:
    """Requested rate over edit time, as a step curve."""
    pts: list[tuple[int, float]] = []
    for piece in timemap:
        pts.append((int(piece["edit_in_us"]), float(piece["rate"])))
        pts.append((int(piece["edit_out_us"]), float(piece["rate"])))
    return Lane(name=name, category=CAT_TIME, curve=tuple(pts),
                color=PALETTE["camera"], height=0.6,
                note="requested rate; measured rate is a separate lane")


def camera_lane(segments: Sequence[Interval], *, name: str = "CAMERA") -> Lane:
    return Lane(name=name, category=CAT_CAMERA, intervals=tuple(segments),
                height=0.6)


# ── keyframe strip ──────────────────────────────────────────────────────────

def keyframe_strip(video: Path | str, times_us: Sequence[int], dst: Path | str,
                   *, labels: Sequence[str] = (), height: int = 220,
                   redact_hud: bool = True) -> Path:
    """Frames at chosen moments, tiled, so visual defects are obvious.

    HUD leaking into a cinematic segment, a camera pointed at nothing, an
    effect that has not started yet: all of these are one glance on a strip
    and invisible in a timeline.

    REDACTION IS ON BY DEFAULT. Quake Live burns opponent names into the
    frag message and the scoreboard, so a raw strip carries real players'
    nicknames into a committed image. The top band is blurred unless a
    caller explicitly asks otherwise, which keeps the camera, the subject
    and the effects readable while the names are not.
    """
    import subprocess
    import tempfile
    from creative_suite.engine import director_preview as dp

    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        frames: list[Path] = []
        for i, us in enumerate(times_us):
            f = Path(tmp) / f"f{i:02d}.png"
            # Blur the top band in place: the frag message and scoreboard
            # live there and carry real nicknames.
            vf = (f"scale=-1:{height},split[a][b];"
                  f"[b]crop=iw:ih*0.36:0:0,boxblur=lr=10:lp=3:cr=5:cp=3[t];"
                  f"[a][t]overlay=0:0" if redact_hud
                  else f"scale=-1:{height}")
            subprocess.run(
                [str(dp.FFMPEG), "-y", "-v", "error", "-ss",
                 f"{us / 1e6:.3f}", "-i", str(video), "-frames:v", "1",
                 "-filter_complex", vf, str(f)], check=True)
            if f.exists():
                frames.append(f)
        if not frames:
            raise ValueError("no frames could be extracted")
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.image as mpimg
        fig, axes = plt.subplots(1, len(frames),
                                 figsize=(3.2 * len(frames), 2.6))
        if len(frames) == 1:
            axes = [axes]
        fig.patch.set_facecolor(PALETTE["bg"])
        for ax, f, i in zip(axes, frames, range(len(frames))):
            ax.imshow(mpimg.imread(f))
            ax.set_xticks([])
            ax.set_yticks([])
            for s in ax.spines.values():
                s.set_color(PALETTE["grid"])
            label = labels[i] if i < len(labels) else ""
            ax.set_title(f"{label}  {times_us[i] / 1e6:.3f}s".strip(),
                         color=PALETTE["text"], fontsize=9)
        fig.tight_layout()
        fig.savefig(dst, dpi=110, facecolor=fig.get_facecolor())
        plt.close(fig)
    return dst
