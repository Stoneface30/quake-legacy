"""SCENE-PER-COMMAND: one FrameTruth, N configurations, nothing else moving.

THE DOCUMENTARY CLAIM THIS MAKES POSSIBLE. "This command changes what you can
see" is only evidence if the two shots differ in that command and in nothing
else. So a ConfigScene films the SAME demo, from the SAME serverTime window,
with the SAME camera, once per variant. The players, routes, projectiles,
animation timing and lighting are identical because they are literally the
same file replayed, not a re-performance.

WHY ONE CAPTURE PER VARIANT RATHER THAN TOGGLING MID-SHOT. Because the engine
will not have it. r_picmip, r_vertexLight, r_mapOverBrightBits,
r_overBrightBits, r_intensity and r_subdivisions are all CVAR_LATCH in the
11.3 binary (measured -- docs/reference/engine_cvarlist_11_3.json): setting
one mid-capture stores the value and changes nothing until a vid_restart. An
"at 5000 set r_picmip 8" would have produced a film where the command visibly
fires and the picture never changes, and the honest reading of that film would
have been "picmip does nothing".

THREE GUARDS, ALL OF WHICH HAVE ALREADY CAUGHT SOMETHING:
  * a cvar the documentary names must EXIST in the runtime inventory --
    cg_useCustomRedBlueModels is accepted by the console and registered by
    nothing;
  * a cvar the documentary names must not be USER_CREATED, for the same
    reason;
  * a LATCH cvar may vary BETWEEN variants and never WITHIN one.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from engine.pantheon.shot import (PassKind, ShotSpec, SourceKind, VisualProfile,
                                  render)

INVENTORY = Path("docs/reference/engine_cvarlist_11_3.json")


class CvarInventory:
    """What the FILMED BINARY registers. Not what the source tree declares.

    The canonical source is 12.7test49 and the capture binary is 11.3; the two
    disagree, and the disagreement is not cosmetic. cg_useCustomRedBlueRail,
    with its absolute red/blue rail colours, is fully implemented in that
    source and does not exist here -- which removes an entire scene design.
    """

    def __init__(self, rows: dict) -> None:
        self.by_name: dict[str, dict] = {}
        for entries in rows.values():
            for c in entries:
                self.by_name.setdefault(c["name"].lower(), c)

    @classmethod
    def load(cls, path: Path = INVENTORY) -> "CvarInventory":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def get(self, name: str) -> dict | None:
        return self.by_name.get(name.lower())

    def check(self, name: str) -> dict:
        c = self.get(name)
        if c is None:
            raise KeyError(
                f"{name!r} is not registered by the capture binary. It may "
                f"exist in the 12.7test49 source; that is not the same thing. "
                f"Re-run engine.pantheon.cvar_probe if the inventory is stale.")
        if c["user_created"]:
            raise ValueError(
                f"{name!r} is USER_CREATED: the engine took the name and "
                f"registered nothing behind it. Setting it is a silent no-op, "
                f"and naming it on screen would be a false claim.")
        return c

    def is_latched(self, name: str) -> bool:
        return bool(self.check(name)["latched"])


@dataclass
class Variant:
    """One configuration state of a scene, and the command that names it."""
    label: str                       # e.g. "r_picmip 8"
    cvars: dict[str, object] = field(default_factory=dict)
    on_screen: str = ""              # exactly what typography shows, if any
    note: str = ""

    def key(self) -> frozenset:
        return frozenset(str(k) for k in self.cvars)


@dataclass
class ConfigScene:
    """A command's scene: one source window, several configurations of it."""
    scene_id: str
    source: Path
    start_s: float
    end_s: float
    variants: Sequence[Variant]
    base: VisualProfile = field(default_factory=VisualProfile)
    truth_reference: Path | None = None
    source_kind: SourceKind = SourceKind.SYNTHETIC

    # -- the contract -----------------------------------------------------
    def validate(self, inv: CvarInventory | None = None) -> dict:
        """Refuse to film anything that cannot prove what it claims."""
        inv = inv or CvarInventory.load()
        if len(self.variants) < 2:
            raise ValueError(f"{self.scene_id}: a comparison needs 2+ variants")

        report: dict = {"scene_id": self.scene_id, "variants": [],
                        "latched": [], "varying": []}
        keys = [v.key() for v in self.variants]
        if len(set(keys)) != 1:
            union = set().union(*keys)
            common = set.intersection(*[set(k) for k in keys])
            raise ValueError(
                f"{self.scene_id}: every variant must set the SAME cvar names "
                f"and differ only in their VALUES, or the comparison has more "
                f"than one moving part. Uneven: {sorted(union - common)}")

        for name in sorted(keys[0]):
            c = inv.check(name)
            values = {str(v.cvars[name]) for v in self.variants}
            if len(values) > 1:
                report["varying"].append(name)
                if c["latched"]:
                    report["latched"].append(name)
        if not report["varying"]:
            raise ValueError(f"{self.scene_id}: no cvar actually differs "
                             f"between variants -- nothing is demonstrated")

        # The base profile must not also move: it is the CONSTANT.
        collide = set(keys[0]) & {str(k) for k in self.base.cvars()}
        if collide:
            raise ValueError(
                f"{self.scene_id}: {sorted(collide)} is set by BOTH the base "
                f"profile and the variants. The base profile is the constant; "
                f"a cvar cannot be constant and variable in the same scene.")

        report["variants"] = [
            {"label": v.label, "on_screen": v.on_screen,
             "cvars": {str(k): str(x) for k, x in v.cvars.items()}}
            for v in self.variants]
        report["requires_separate_capture"] = bool(report["latched"])
        return report

    # -- filming ----------------------------------------------------------
    def specs(self) -> list[ShotSpec]:
        out = []
        for v in self.variants:
            prof = VisualProfile(
                name=f"{self.base.name}__{v.label}",
                xray=self.base.xray,
                xray_enemy_color=self.base.xray_enemy_color,
                xray_enemy_alpha=self.base.xray_enemy_alpha,
                extra={**self.base.extra, **v.cvars})
            out.append(ShotSpec(
                shot_id=f"{self.scene_id}__{_slug(v.label)}",
                source=self.source, source_kind=self.source_kind,
                start_s=self.start_s, end_s=self.end_s, visual=prof,
                passes=(PassKind.BEAUTY,),
                truth_reference=self.truth_reference,
                provenance=f"CONFIG_SCENE:{self.scene_id}"))
        return out

    def film(self, out_dir: Path, *, inv: CvarInventory | None = None
             ) -> list[Path]:
        """Validate, then film one capture per variant."""
        self.validate(inv)
        return [render(s, out_dir) for s in self.specs()]


def _slug(s: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in s).strip("_")
