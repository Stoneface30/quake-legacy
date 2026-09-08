"""Forensic replay: a NetcodeAnomaly turned into a video that explains it.

DOMAIN. FORENSIC_REFERENCE -- diagnostic media, reproducible from a
manifest, factual. It is not the movie, it never consumes the canonical
frag (no VALIDATED / ASSIGNED / USED transition happens here, and nothing in
this module writes to the recognition database), and the artistic version
that may one day be made from the same evidence (CINEMATIC_INTERPRETATION)
lives elsewhere and never overwrites it.

TIME. The replay has its own edit clock built from scene_recipe.TimeSegment
pieces at exact rational rates: normal context before, a freeze where the
client's observation ends, slow motion through the reconstructed stretch,
normal context after. Every anchor is a demo_us; the TimeMap is the only
bridge, and it is written into the manifest.

PRESENTATION. Recorded samples and reconstructed samples never look alike:
recorded points are solid discs, the reconstructed path is a dashed line
of a different colour, the boundary is drawn and labelled OBSERVATION ENDS.
Non-FPV forensic cameras are CINEMATIC_CLEAN (no gameplay HUD); the
diagnostic overlay is its own layer. Numbers are shown compactly and only
the ones that explain the event.

RENDERING. Schematic frames (matplotlib) encoded with the project ffmpeg.
Detection and recipes are cheap; rendering is on demand, one case at a time.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any, Sequence

from creative_suite.engine import demo_truth as dt
from creative_suite.engine import netcode_anomaly as na
from creative_suite.engine import projectile_reconstruction as pr
from creative_suite.engine.scene_recipe import TimeMap, TimeSegment

FORENSIC_VERSION = "forensic-replay-v1.0.0"
DOMAIN_FORENSIC = "FORENSIC_REFERENCE"
DOMAIN_CINEMATIC = "CINEMATIC_INTERPRETATION"

# Visual layers a replay may draw, each only when its evidence exists.
LAYER_RECORDED_PLAYER = "RECORDED_PLAYER_POSITION"
LAYER_RECORDED_PROJECTILE = "RECORDED_PROJECTILE_POINTS"
LAYER_RECONSTRUCTED_PATH = "RECONSTRUCTED_PROJECTILE_PATH"
LAYER_BSP_CONTACT = "STATIC_BSP_COLLISION"
LAYER_EXPECTED_TERMINAL = "EXPECTED_TERMINAL_POINT"
LAYER_RECORDED_IMPACT = "RECORDED_IMPACT_EXPLOSION"
LAYER_VICTIM = "VICTIM_POSITION_BOUNDS"
LAYER_SPLASH = "SPLASH_RADIUS"
LAYER_HIT_TRACE = "HIT_TRACE"
LAYER_DAMAGE = "DAMAGE_LEDGER"
LAYER_SNAPSHOT_GAP = "SNAPSHOT_GAP"
LAYER_PROVENANCE_BOUNDARY = "PROVENANCE_BOUNDARY"
LAYERS = (LAYER_RECORDED_PLAYER, LAYER_RECORDED_PROJECTILE, LAYER_RECONSTRUCTED_PATH,
          LAYER_BSP_CONTACT, LAYER_EXPECTED_TERMINAL, LAYER_RECORDED_IMPACT,
          LAYER_VICTIM, LAYER_SPLASH, LAYER_HIT_TRACE, LAYER_DAMAGE,
          LAYER_SNAPSHOT_GAP, LAYER_PROVENANCE_BOUNDARY)

CAMERA_SIDE = "SIDE"                 # orthographic side view of the flight plane
CAMERA_TOP = "TOP"
CAMERA_PROJECTILE = "PROJECTILE"     # follows the projectile
CAMERAS = (CAMERA_SIDE, CAMERA_TOP, CAMERA_PROJECTILE)
HUD_MODE = "CINEMATIC_CLEAN"

AUDIO_GAME = "GAME_AUDIO"            # default reference: relevant game audio, no music
AUDIO_NONE = "NONE"

PHYSICS_CONSTANTS = {
    "GRAVITY": pr.GRAVITY, "ROCKET_SPEED_QL": pr.ROCKET_SPEED_QL,
    "ROCKET_LIFE_MS": pr.ROCKET_LIFE_MS, "ROCKET_SPLASH": pr.ROCKET_SPLASH,
    "GRENADE_SPEED": pr.GRENADE_SPEED, "GRENADE_FUSE_MS": pr.GRENADE_FUSE_MS,
    "GRENADE_SPLASH": pr.GRENADE_SPLASH, "BOUNCE_DAMPING": pr.BOUNCE_DAMPING,
    "REST_NORMAL_Z": pr.REST_NORMAL_Z, "REST_SPEED": pr.REST_SPEED,
    "STEP_MS": pr.STEP_MS}

# Presentation conventions: recorded and reconstructed must differ on sight.
STYLE = {"recorded": dict(color="#ffd24d", marker="o", ls="-", lw=2.2),
         "reconstructed": dict(color="#7fb3ff", marker="", ls="--", lw=1.6),
         "event_constrained": dict(color="#c792ea", marker="", ls=":", lw=1.6),
         "bounce": dict(color="#ff8c42", marker="v"),
         "impact": dict(color="#ff4d4d", marker="x"),
         "expected": dict(color="#7fb3ff", marker="+"),
         "boundary": dict(color="#ffffff"),
         "bg": "#101010", "fg": "#e6e6e6"}


# ── recipe ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ForensicReplayRecipe:
    """Everything needed to rebuild one replay, with exact anchors."""
    anomaly_id: str
    content_hash: str
    anomaly_type: str
    assessment: str
    # demo_us anchors
    context_before_us: int
    observation_end_us: int
    anomaly_end_us: int
    context_after_us: int
    slow_rate: Fraction = Fraction(1, 4)
    freeze_us: int = 1_500_000            # edit time spent on OBSERVATION ENDS
    layers: tuple[str, ...] = ()
    camera: str = CAMERA_SIDE
    hud_mode: str = HUD_MODE
    audio: str = AUDIO_GAME
    fps: int = 60
    domain: str = DOMAIN_FORENSIC
    version: str = FORENSIC_VERSION

    def __post_init__(self) -> None:
        if self.domain != DOMAIN_FORENSIC:
            raise ValueError("a forensic recipe lives in FORENSIC_REFERENCE only")
        if not (self.context_before_us <= self.observation_end_us
                <= self.anomaly_end_us <= self.context_after_us):
            raise ValueError("anchors must be ordered: before <= observation end "
                             "<= anomaly end <= after")
        if self.slow_rate <= 0 or self.slow_rate > 1:
            raise ValueError("slow rate must be in (0, 1]")
        for l in self.layers:
            if l not in LAYERS:
                raise ValueError(f"unknown layer {l!r}")
        if self.camera not in CAMERAS:
            raise ValueError(f"unknown camera {self.camera!r}")
        if self.hud_mode != HUD_MODE:
            raise ValueError("forensic cameras are CINEMATIC_CLEAN")

    def time_segments(self) -> tuple[TimeSegment, ...]:
        """Normal context, freeze at the observation boundary, slow motion
        through the anomaly, normal context after. Exact rates, contiguous
        edit clock, no temporal debt: every segment's edit span is exactly
        demo span / rate."""
        segs: list[TimeSegment] = []
        edit = 0
        num, den = self.slow_rate.numerator, self.slow_rate.denominator

        def add(kind: str, d0: int, d1: int, rn: int, rd: int) -> None:
            nonlocal edit
            if kind == "freeze":
                span = self.freeze_us
            else:
                span = (d1 - d0) * rd // rn
                d1 = d0 + span * rn // rd          # keep the rational identity exact
            if span <= 0:
                return
            segs.append(TimeSegment(kind, d0, d1, edit, edit + span, rn, rd))
            edit += span

        add("normal", self.context_before_us, self.observation_end_us, 1, 1)
        if self.freeze_us > 0:
            segs.append(TimeSegment("freeze", self.observation_end_us,
                                    self.observation_end_us, edit,
                                    edit + self.freeze_us, 0, 1))
            edit += self.freeze_us
        add("slow" if self.slow_rate < 1 else "normal", self.observation_end_us,
            self.anomaly_end_us, num, den)
        add("normal", self.anomaly_end_us, self.context_after_us, 1, 1)
        return tuple(segs)

    def time_map(self) -> TimeMap:
        return TimeMap(self.time_segments())

    @property
    def edit_duration_us(self) -> int:
        segs = self.time_segments()
        return segs[-1].edit_end_us if segs else 0

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["slow_rate"] = str(self.slow_rate)
        d["time_segments"] = [asdict(s) for s in self.time_segments()]
        d["edit_duration_us"] = self.edit_duration_us
        return d

    @property
    def recipe_hash(self) -> str:
        return hashlib.sha256(json.dumps(self.to_dict(), sort_keys=True)
                              .encode()).hexdigest()[:24]


def recipe_for_projectile(anomaly: na.NetcodeAnomaly, cont: pr.Continuation, *,
                          before_us: int = 1_500_000, after_us: int = 1_500_000,
                          camera: str = CAMERA_SIDE) -> ForensicReplayRecipe:
    """Default window for a projectile anomaly: context before launch, the
    recorded prefix at normal speed, a freeze where observation ends, the
    reconstructed stretch slowed, context after the terminal event."""
    segs = pr.provenance_segments(cont)
    recorded_end = max((s.end_us for s in segs if dt.is_recorded(s.evidence)),
                       default=cont.points[0].t_us)
    layers = [LAYER_RECORDED_PROJECTILE, LAYER_PROVENANCE_BOUNDARY, LAYER_SNAPSHOT_GAP]
    if any(not dt.is_recorded(s.evidence) for s in segs):
        layers += [LAYER_RECONSTRUCTED_PATH, LAYER_EXPECTED_TERMINAL]
    if cont.bounces:
        layers.append(LAYER_BSP_CONTACT)
    if anomaly.recorded_after.get("event_pos"):
        layers += [LAYER_RECORDED_IMPACT, LAYER_SPLASH]
    if anomaly.damage_evidence:
        layers.append(LAYER_DAMAGE)
    return ForensicReplayRecipe(
        anomaly_id=anomaly.anomaly_id, content_hash=anomaly.content_hash,
        anomaly_type=anomaly.anomaly_type, assessment=anomaly.assessment,
        context_before_us=max(0, cont.points[0].t_us - before_us),
        observation_end_us=recorded_end, anomaly_end_us=cont.end_t_us,
        context_after_us=cont.end_t_us + after_us, layers=tuple(layers),
        camera=camera)


# ── manifest ────────────────────────────────────────────────────────────────

MANIFEST_VERSION = "forensic-manifest-v1.0.0"


@dataclass(frozen=True)
class ForensicManifest:
    anomaly_id: str
    anomaly_hash: str                  # sha256 of the anomaly evidence dict
    content_hash: str
    source_event: dict[str, Any]       # identity of the recorded event
    reconstruction_version: str
    bsp_hash: str
    physics_constants: dict[str, float]
    provenance_segments: list[dict[str, Any]]
    camera: str
    hud_mode: str
    audio: str
    time_map: list[dict[str, Any]]
    layers: tuple[str, ...]
    recipe_hash: str
    output_sha256: str = ""
    output_path: str = ""
    domain: str = DOMAIN_FORENSIC
    manifest_version: str = MANIFEST_VERSION

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write(self, path: Path | str) -> Path:
        p = Path(path)
        p.write_text(json.dumps(self.to_dict(), indent=1, sort_keys=True),
                     encoding="utf-8")
        return p

    @classmethod
    def load(cls, path: Path | str) -> "ForensicManifest":
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        d["layers"] = tuple(d["layers"])
        return cls(**d)


def anomaly_hash(anomaly: na.NetcodeAnomaly) -> str:
    return hashlib.sha256(json.dumps(anomaly.evidence_dict(), sort_keys=True,
                                     default=str).encode()).hexdigest()


def bsp_entry_hash(map_name: str, pk3_path: Path | str | None = None) -> str:
    """sha256 of the exact BSP bytes the trace used (read-only pak)."""
    import zipfile
    from engine.parser import bsp_geometry as bg
    pk3 = Path(pk3_path) if pk3_path else bg.DEFAULT_PK3
    with zipfile.ZipFile(pk3, "r") as z:
        return hashlib.sha256(z.read(f"maps/{map_name.lower()}.bsp")).hexdigest()


def build_manifest(anomaly: na.NetcodeAnomaly, recipe: ForensicReplayRecipe,
                   cont: pr.Continuation, *, bsp_hash: str,
                   output_path: Path | str = "") -> ForensicManifest:
    out = Path(output_path) if output_path else None
    return ForensicManifest(
        anomaly_id=anomaly.anomaly_id, anomaly_hash=anomaly_hash(anomaly),
        content_hash=anomaly.content_hash,
        source_event={"server_time_ms": anomaly.server_time_ms,
                      "entity_num": anomaly.entity_num, "event_type": anomaly.event_type,
                      "weapon_wp": anomaly.weapon_wp, "weapon_mod": anomaly.weapon_mod},
        reconstruction_version=pr.RECON_VERSION, bsp_hash=bsp_hash,
        physics_constants=dict(PHYSICS_CONSTANTS),
        provenance_segments=[s.to_dict() for s in pr.provenance_segments(cont)],
        camera=recipe.camera, hud_mode=recipe.hud_mode, audio=recipe.audio,
        time_map=[asdict(s) for s in recipe.time_segments()],
        layers=recipe.layers, recipe_hash=recipe.recipe_hash,
        output_sha256=(hashlib.sha256(out.read_bytes()).hexdigest()
                       if out and out.exists() else ""),
        output_path=str(out) if out else "")


# ── numeric overlay ─────────────────────────────────────────────────────────

def overlay_lines(anomaly: na.NetcodeAnomaly, cont: pr.Continuation,
                  demo_us: int) -> list[str]:
    """The compact numbers for one frame. Readable, not telemetry soup."""
    t_rel = (demo_us - cont.points[0].t_us) / 1000.0
    segs = pr.provenance_segments(cont)
    recorded_end = max((s.end_us for s in segs if dt.is_recorded(s.evidence)),
                       default=cont.points[0].t_us)
    phase = "RECORDED" if demo_us < recorded_end else (
        "RECONSTRUCTED" if demo_us <= cont.end_t_us else "AFTER")
    lines = [f"t = {t_rel:+.0f} ms   {phase}",
             f"speed {anomaly.recorded_before.get('launch_speed_u_s', 0):.0f} u/s"]
    if demo_us >= recorded_end:
        lines.append(f"observation gap {anomaly.snapshot_gap_us / 1000:.0f} ms")
    bounces = sum(1 for b in cont.bounces if b.t_us <= demo_us)
    if cont.bounces:
        lines.append(f"bounces {bounces}/{len(cont.bounces)}")
    if demo_us >= cont.end_t_us:
        lines.append(f"{cont.end_reason} at {cont.flight_us / 1000:.0f} ms")
        if anomaly.spatial_residual_u is not None:
            lines.append(f"residual {anomaly.spatial_residual_u:.1f} u")
        lines.append(cont.confidence.replace("_UNTIL_", "_UNTIL_" + chr(10) + "  "))
        lines.append(anomaly.anomaly_type)
        lines.append(anomaly.assessment)
    return lines


# ── rendering ───────────────────────────────────────────────────────────────

def _plane_axes(camera: str) -> tuple[int, int, tuple[str, str]]:
    return (0, 2, ("x", "z")) if camera in (CAMERA_SIDE, CAMERA_PROJECTILE) else (0, 1, ("x", "y"))


def render_forensic_replay(anomaly: na.NetcodeAnomaly, recipe: ForensicReplayRecipe,
                           cont: pr.Continuation, dst: Path | str, *,
                           ffmpeg: Path | str | None = None,
                           title: str = "", width_px: int = 1280,
                           height_px: int = 720, bsp_hash: str = "") -> ForensicManifest:
    """Schematic replay of the flight on the recipe's edit clock. Writes the
    MP4 and its manifest sidecar; touches nothing else."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    tm = recipe.time_map()
    n_frames = max(1, int(round(recipe.edit_duration_us * recipe.fps / 1_000_000)))
    i, j, (lx, ly) = _plane_axes(recipe.camera)
    pts = sorted(cont.points, key=lambda p: p.t_us)
    segs = pr.provenance_segments(cont)
    recorded_end = max((s.end_us for s in segs if dt.is_recorded(s.evidence)),
                       default=pts[0].t_us)
    ev_pos = anomaly.recorded_after.get("event_pos")
    xs = [p.pos[i] for p in pts] + ([ev_pos[i]] if ev_pos else [])
    ys = [p.pos[j] for p in pts] + ([ev_pos[j]] if ev_pos else [])
    pad = max(60.0, 0.12 * max(max(xs) - min(xs), max(ys) - min(ys), 1.0))
    lim = ((min(xs) - pad, max(xs) + pad), (min(ys) - pad, max(ys) + pad))
    splash = pr.GRENADE_SPLASH if cont.kind == pr.KIND_GRENADE else pr.ROCKET_SPLASH

    dpi = 100
    fig = plt.figure(figsize=(width_px / dpi, height_px / dpi), dpi=dpi,
                     facecolor=STYLE["bg"])
    ax = fig.add_axes([0.06, 0.08, 0.66, 0.84])
    frames_dir = dst.with_suffix("")
    frames_dir.mkdir(exist_ok=True)
    for f in frames_dir.glob("f_*.png"):
        f.unlink()
    for n in range(n_frames):
        edit_us = int(n * 1_000_000 / recipe.fps)
        demo_us = tm.edit_to_demo(min(edit_us, recipe.edit_duration_us - 1))
        ax.clear()
        ax.set_facecolor(STYLE["bg"])
        ax.set_xlim(*lim[0]); ax.set_ylim(*lim[1]); ax.set_aspect("equal")
        ax.tick_params(colors="#777", labelsize=8)
        for s in ax.spines.values():
            s.set_color("#333")
        ax.set_xlabel(lx, color="#777"); ax.set_ylabel(ly, color="#777")
        shown = [p for p in pts if p.t_us <= demo_us]
        rec = [p for p in shown if dt.is_recorded(p.evidence)]
        der = [p for p in shown if not dt.is_recorded(p.evidence)]
        if rec and LAYER_RECORDED_PROJECTILE in recipe.layers:
            st = STYLE["recorded"]
            ax.plot([p.pos[i] for p in rec], [p.pos[j] for p in rec], color=st["color"],
                    lw=st["lw"], ls=st["ls"], marker=st["marker"], ms=7, zorder=5,
                    label="recorded samples")
        if der and LAYER_RECONSTRUCTED_PATH in recipe.layers:
            st = STYLE["reconstructed"]
            head = rec[-1:] + der
            ax.plot([p.pos[i] for p in head], [p.pos[j] for p in head], color=st["color"],
                    lw=st["lw"], ls=st["ls"], zorder=4, label="reconstructed (physics)")
        if LAYER_PROVENANCE_BOUNDARY in recipe.layers and rec and demo_us >= recorded_end:
            b = rec[-1]
            ax.scatter([b.pos[i]], [b.pos[j]], s=160, facecolors="none",
                       edgecolors=STYLE["boundary"]["color"], lw=1.5, zorder=6)
            ax.annotate("OBSERVATION ENDS", (b.pos[i], b.pos[j]), xytext=(8, 10),
                        textcoords="offset points", color=STYLE["fg"], fontsize=9)
        if LAYER_BSP_CONTACT in recipe.layers:
            bs = [b for b in cont.bounces if b.t_us <= demo_us]
            if bs:
                st = STYLE["bounce"]
                ax.scatter([b.point[i] for b in bs], [b.point[j] for b in bs], s=50,
                           marker=st["marker"], color=st["color"], zorder=6,
                           label=f"BSP bounce ({len(bs)})")
        if demo_us >= cont.end_t_us:
            if LAYER_EXPECTED_TERMINAL in recipe.layers:
                st = STYLE["expected"]
                ax.scatter([cont.end_pos[i]], [cont.end_pos[j]], s=140, marker=st["marker"],
                           color=st["color"], lw=2, zorder=7, label=f"predicted {cont.end_reason}")
            if ev_pos and LAYER_RECORDED_IMPACT in recipe.layers:
                st = STYLE["impact"]
                ax.scatter([ev_pos[i]], [ev_pos[j]], s=160, marker=st["marker"],
                           color=st["color"], lw=2.5, zorder=8, label="recorded explosion")
                if LAYER_SPLASH in recipe.layers:
                    ax.add_patch(plt.Circle((ev_pos[i], ev_pos[j]), splash, fill=False,
                                            ec=st["color"], ls=":", lw=1, alpha=0.6))
        if shown:
            cur = shown[-1] if demo_us <= cont.end_t_us else None
            if cur is not None:
                ax.scatter([cur.pos[i]], [cur.pos[j]], s=36, color="#ffffff", zorder=9)
        ax.legend(loc="lower left", facecolor="#1a1a1a", edgecolor="#333",
                  labelcolor="#ddd", fontsize=8)
        fig.texts.clear()
        fig.text(0.74, 0.90, title or f"anomaly {anomaly.anomaly_id}", color=STYLE["fg"],
                 fontsize=11, weight="bold")
        for k, line in enumerate(overlay_lines(anomaly, cont, demo_us)):
            fig.text(0.74, 0.84 - 0.05 * k, line, color=STYLE["fg"], fontsize=9,
                     family="monospace")
        fig.text(0.74, 0.10, f"{DOMAIN_FORENSIC} · {HUD_MODE}\n{recipe.version}",
                 color="#777", fontsize=8)
        fig.savefig(frames_dir / f"f_{n:05d}.png", dpi=dpi, facecolor=STYLE["bg"])
    plt.close(fig)

    ff = Path(ffmpeg) if ffmpeg else _default_ffmpeg()
    cmd = [str(ff), "-y", "-loglevel", "error", "-framerate", str(recipe.fps),
           "-i", str(frames_dir / "f_%05d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p",
           "-crf", "18", "-preset", "medium", "-movflags", "+faststart", str(dst)]
    subprocess.run(cmd, check=True, timeout=900)
    for f in frames_dir.glob("f_*.png"):
        f.unlink()
    frames_dir.rmdir()
    manifest = build_manifest(anomaly, recipe, cont, bsp_hash=bsp_hash, output_path=dst)
    manifest.write(dst.with_suffix(".forensic.json"))
    return manifest


def _default_ffmpeg() -> Path:
    """The project ffmpeg (creative_suite/tools/ffmpeg), else the PATH one."""
    local = Path(__file__).resolve().parents[1] / "tools" / "ffmpeg" / "ffmpeg.exe"
    return local if local.exists() else Path("ffmpeg")


# ── diagnostic sheet lanes ──────────────────────────────────────────────────

def forensic_sheet(anomaly: na.NetcodeAnomaly, cont: pr.Continuation, *,
                   events: Sequence[Any] = (), snapshot_times_us: Sequence[int] = (),
                   audio_lane: Any = None, camera_intervals: Sequence[Any] = (),
                   title: str = ""):
    """The existing diagnostic sheet with forensic lanes: DEMO EVENTS,
    SNAPSHOT OBSERVATION, RECORDED TRAJECTORY, RECONSTRUCTION, IMPACT/FRAG,
    DAMAGE, AUDIO, CAMERA, PROVENANCE. Numbers stay the truth; the sheet is
    a drawing of them."""
    from creative_suite.engine import diagnostic_sheet as ds
    segs = pr.provenance_segments(cont)
    start = cont.points[0].t_us - 1_000_000
    end = cont.end_t_us + 1_000_000
    sheet = ds.DiagnosticSheet(title or f"forensic {anomaly.anomaly_id}", start, end,
                               hero_us=cont.end_t_us, hero_label=cont.end_reason,
                               subtitle=f"{anomaly.anomaly_type} · {anomaly.assessment}")
    if events:
        sheet.add(ds.gameplay_lane(events, name="DEMO EVENTS"))
    if snapshot_times_us:
        sheet.add(ds.Lane("SNAPSHOT OBSERVATION", ds.CAT_GAMEPLAY,
                          instants=tuple(ds.Instant(t, "", ds.PALETTE["game"], 0.4)
                                         for t in snapshot_times_us)))
    rec = tuple(ds.Instant(p.t_us, "", STYLE["recorded"]["color"])
                for p in cont.points if dt.is_recorded(p.evidence))
    sheet.add(ds.Lane("RECORDED TRAJECTORY", ds.CAT_SEMANTIC, instants=rec,
                      color=STYLE["recorded"]["color"]))
    der = tuple(ds.Interval(s.start_us, s.end_us, s.evidence, "RECONSTRUCTION",
                            color=STYLE["reconstructed"]["color"])
                for s in segs if not dt.is_recorded(s.evidence))
    if der:
        sheet.add(ds.Lane("RECONSTRUCTION", ds.CAT_SEMANTIC, intervals=der,
                          color=STYLE["reconstructed"]["color"]))
    bounce = tuple(ds.Instant(b.t_us, "bounce", STYLE["bounce"]["color"], 0.8)
                   for b in cont.bounces)
    impact = (ds.Instant(anomaly.recorded_after["event_t_us"], anomaly.event_type,
                         STYLE["impact"]["color"], 1.2),)
    sheet.add(ds.Lane("IMPACT/FRAG", ds.CAT_GAMEPLAY, instants=bounce + impact))
    if anomaly.damage_evidence:
        sheet.add(ds.Lane("DAMAGE", ds.CAT_SEMANTIC, note=json.dumps(anomaly.damage_evidence),
                          instants=(ds.Instant(anomaly.recorded_after["event_t_us"], "damage"),)))
    if audio_lane is not None:
        sheet.add(audio_lane)
    if camera_intervals:
        sheet.add(ds.camera_lane(tuple(camera_intervals)))
    span = max(1, end - start)
    sheet.add(ds.Lane("PROVENANCE", ds.CAT_SEMANTIC,
                      intervals=tuple(ds.Interval(s.start_us, s.end_us,
                                                  s.evidence if s.duration_us >= span // 40 else "",
                                                  "PROVENANCE", s.evidence,
                                                  color=(STYLE["recorded"]["color"]
                                                         if dt.is_recorded(s.evidence)
                                                         else STYLE["reconstructed"]["color"]))
                                      for s in segs)))
    return sheet
