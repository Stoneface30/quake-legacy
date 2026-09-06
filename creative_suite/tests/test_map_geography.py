"""A map learned from play, and the promises that make it usable.

The user's idea, in their words: "we should also review how to map the map
localisation and everything else while we datamine we can know everything as
we have thosnad of records on only 10 maps."

These tests pin the four things that have to be true for a region id to be
worth printing next to a frag: it means the same thing tomorrow, it does not
merge two floors that happen to share a footprint, it is connected to its
neighbours by moves people actually made, and learning any of it never opens
a renderer.
"""
from __future__ import annotations

import ast
import sqlite3
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from engine.pantheon import map_geography as mg

GEO_DB = REPO_ROOT / "creative_suite" / "database" / "map_geography.db"
RECOG_DB = REPO_ROOT / "creative_suite" / "database" / "frag_recognition.db"


def _built() -> bool:
    try:
        with sqlite3.connect(f"file:{GEO_DB.as_posix()}?mode=ro",
                             uri=True) as c:
            return bool(c.execute(
                "SELECT 1 FROM map_regions_v1 LIMIT 1").fetchone())
    except sqlite3.Error:
        return False


live = pytest.mark.skipif(not _built(), reason="needs the built geography")


# ── a synthetic map, so the shape rules are testable without the corpus ─────

def _two_storey_map() -> tuple[list[tuple[float, float, float]], list[bool]]:
    """Two rooms joined by a thin corridor, and the whole thing again 400
    units higher. Flattened to XY it is one blob; it is not one place."""
    pts: list[tuple[float, float, float]] = []
    for z in (32.0, 432.0):
        for room_x in (0, 1600):
            for i in range(14):
                for j in range(14):
                    x = room_x + i * 64
                    y = j * 64
                    pts.extend([(x, y, z)] * 6)
        # the corridor: same length, far fewer people in it
        for k in range(10):
            pts.extend([(900.0 + k * 60, 400.0, z)] * 2)
    return pts, [False] * len(pts)


def test_two_heights_never_merge_into_one_region():
    """THE REASON Z COMES FIRST. The upper and lower storeys share every
    XY cell; clustering in XY alone would call them one place and every
    statement about either would be a lie about both."""
    pts, combat = _two_storey_map()
    layers, regions, lookup = mg.build_regions(pts, "synthetic", combat)
    assert len(layers) >= 2, "the two storeys were not separated"
    by_xy: dict[tuple[int, int], set[str]] = {}
    for (_lay, cx, cy), rid in lookup.items():
        by_xy.setdefault((cx, cy), set()).add(rid)
    stacked = [k for k, v in by_xy.items() if len(v) > 1]
    assert stacked, "no XY column carries two regions"
    lay_of = {r.region_id: r.layer for r in regions}
    for cell in stacked:
        assert len({lay_of[r] for r in by_xy[cell]}) > 1, \
            "two regions in one column on the same layer"


def test_a_thin_corridor_separates_two_rooms():
    """Connected components was tried first and returned one region per
    floor -- a Quake map is walkable end to end. Places are separated by
    THIN places, not by empty ones."""
    pts, combat = _two_storey_map()
    _layers, regions, _lookup = mg.build_regions(pts, "synthetic", combat)
    per_layer: dict[int, int] = {}
    for r in regions:
        per_layer[r.layer] = per_layer.get(r.layer, 0) + 1
    assert max(per_layer.values()) >= 2, \
        f"each storey came back as one blob: {per_layer}"


def test_region_ids_do_not_depend_on_input_order():
    """Ids go into the dossier and will go into human notes. If a rebuild
    renumbered them, every note written before it would silently start
    describing somewhere else."""
    pts, combat = _two_storey_map()
    a = mg.build_regions(pts, "synthetic", combat)
    shuffled = list(reversed(pts))
    b = mg.build_regions(shuffled, "synthetic", list(reversed(combat)))
    assert [r.region_id for r in a[1]] == [r.region_id for r in b[1]]
    assert a[2] == b[2]


def test_a_position_nobody_occupied_is_nowhere():
    """None is an honest answer. Snapping a stray point to the nearest
    region would put a confident wrong location on a clip."""
    pts, combat = _two_storey_map()
    layers, regions, lookup = mg.build_regions(pts, "synthetic", combat)
    idx = mg.MapIndex("synthetic", layers, regions, lookup)
    assert idx.region_at(0.0, 0.0, 32.0) is not None
    assert idx.region_at(90_000.0, 90_000.0, 32.0) is None


def test_a_layer_is_never_unknown():
    """A rocket-jump apex above the top walkway belongs to the top layer;
    there is no fifth answer."""
    layers = [mg.Layer("m", 0, 0, 200, 10), mg.Layer("m", 1, 200, 400, 10)]
    assert mg.layer_of(layers, -500) == 0
    assert mg.layer_of(layers, 99_999) == 1


# ── the boundary that matters most ──────────────────────────────────────────

RENDER_WORDS = ("wolfcam", "subprocess", "Popen", "capture_demo",
                "shot", "cvar_probe")


@pytest.mark.parametrize("module", ["map_geography", "map_context"])
def test_map_intelligence_never_reaches_a_renderer(module):
    """MAP INTELLIGENCE IS HEADLESS -- enforced on the import graph, not on
    a promise. Everything here is arithmetic over recorded positions."""
    src = (REPO_ROOT / "engine" / "pantheon" / f"{module}.py").read_text(
        encoding="utf-8")
    tree = ast.parse(src)
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    joined = " ".join(imported).lower()
    for bad in RENDER_WORDS:
        assert bad.lower() not in joined, f"{module} imports {bad}"


# ── against the real corpus ─────────────────────────────────────────────────

@live
def test_the_dominant_maps_were_learned():
    with sqlite3.connect(f"file:{GEO_DB.as_posix()}?mode=ro", uri=True) as c:
        c.row_factory = sqlite3.Row
        maps = {r["map"]: r["n"] for r in c.execute(
            "SELECT map, COUNT(*) n FROM map_regions_v1 GROUP BY 1")}
    for m in ("campgrounds", "asylum", "overkill"):
        assert maps.get(m, 0) >= 8, f"{m} has too few regions: {maps.get(m)}"


@live
def test_real_maps_stack_vertically():
    """Not a synthetic claim: on the real archive, the same footprint is
    occupied at more than one height."""
    with sqlite3.connect(f"file:{GEO_DB.as_posix()}?mode=ro", uri=True) as c:
        c.row_factory = sqlite3.Row
        rows = c.execute(
            "SELECT cx, cy, COUNT(DISTINCT layer) n FROM map_region_cells_v1 "
            "WHERE map='campgrounds' GROUP BY cx, cy HAVING n > 1").fetchall()
    assert len(rows) > 10, "campgrounds came back flat"


@live
def test_jump_pads_link_two_different_regions():
    """A pad that lands you where you left is not a link."""
    with sqlite3.connect(f"file:{GEO_DB.as_posix()}?mode=ro", uri=True) as c:
        c.row_factory = sqlite3.Row
        rows = c.execute(
            "SELECT map, launch_region, land_region, n FROM map_jump_pads_v1 "
            "WHERE n >= 20").fetchall()
    assert rows, "no jump pad arc was observed often enough to trust"
    for r in rows:
        assert r["launch_region"] != r["land_region"]


@live
def test_teleports_come_only_from_validated_pairs():
    """The backfill is NOT rerun and AMBIGUOUS transits are not geography."""
    src = (REPO_ROOT / "engine" / "pantheon"
           / "map_geography.py").read_text(encoding="utf-8")
    assert "TELEPORT_PLAYER_CONFIRMED" in src
    with sqlite3.connect(f"file:{GEO_DB.as_posix()}?mode=ro", uri=True) as c:
        c.row_factory = sqlite3.Row
        links = c.execute(
            "SELECT map, entry_region, exit_region, n "
            "FROM map_teleports_v1 WHERE n >= 50").fetchall()
        routes = c.execute(
            "SELECT COUNT(*) n FROM map_routes_v1 WHERE kind='TELEPORT'"
        ).fetchone()["n"]
    assert links, "no teleport link survived"
    # And no teleport edge was invented from position tracks, which carry no
    # client number for a transit and therefore cannot attribute one.
    assert routes == 0


@live
def test_routes_are_moves_people_made():
    with sqlite3.connect(f"file:{GEO_DB.as_posix()}?mode=ro", uri=True) as c:
        c.row_factory = sqlite3.Row
        rows = c.execute(
            "SELECT from_region, to_region, kind, n, median_ms "
            "FROM map_routes_v1 WHERE n >= 50").fetchall()
    assert len(rows) > 50
    for r in rows:
        assert r["from_region"] != r["to_region"]
        assert r["kind"] in (mg.WALK, mg.JUMP_PAD)
        assert mg.MIN_MOVE_MS <= r["median_ms"] <= mg.MAX_MOVE_MS


@live
def test_a_rebuild_of_one_map_reproduces_its_regions():
    """The stability claim, on real data rather than a fixture."""
    demo_map = mg.map_of_demos()
    hashes = sorted(h for h, m in demo_map.items() if m == "thunderstruck")
    if len(hashes) < 20:
        pytest.skip("thunderstruck not present")
    pts, combat = mg.discovery_points(hashes[:40])
    a = mg.build_regions(pts, "thunderstruck", combat)
    b = mg.build_regions(pts, "thunderstruck", combat)
    assert [r.to_dict() for r in a[1]] == [r.to_dict() for r in b[1]]


@live
def test_the_reviewed_frags_get_a_place_or_an_honest_silence():
    from engine.pantheon import map_context as mc
    mc.clear_cache()
    seen = 0
    for occ in (495, 1080, 18858):
        ctx = mc.context_for_kill(occ)
        if ctx is None:
            continue
        seen += 1
        assert ctx["location"] is None or \
            ctx["location"]["region_id"].startswith("REGION_")
        if ctx["location"]:
            assert ctx["location"]["layer_word"] in (
                "GROUND", "LOWER", "MID", "UPPER")
    assert seen, "no reviewed frag resolved to a map at all"


# ── the review site consumes truth; it does not fork it ─────────────────────

def test_the_review_api_knows_no_clustering_mathematics():
    """The UI asks the authority for a region. It must not import the
    watershed, the grid, or the layering -- when the shared engine takes
    over, `map_authority` is the only file outside it that changes."""
    src = (REPO_ROOT / "creative_suite" / "api"
           / "review.py").read_text(encoding="utf-8")
    assert "map_authority" in src
    for forked in ("map_geography", "map_context", "_watershed", "CELL_XY",
                   "build_regions"):
        assert forked not in src, f"review.py reaches past the authority: {forked}"


def test_the_frontend_knows_no_clustering_mathematics():
    html = (REPO_ROOT / "creative_suite" / "frontend"
            / "review.html").read_text(encoding="utf-8")
    for forked in ("watershed", "CELL_XY", "z_histogram", "cluster"):
        assert forked not in html, f"the UI knows about {forked}"


def test_the_authority_reports_which_backend_is_answering():
    """STILL RECONCILING is a legitimate state, and an operator should be
    able to see it rather than guess."""
    from engine.pantheon import map_authority as ma
    assert ma.backend() in (ma.BACKEND_REGIONS, ma.BACKEND_SHARED)


# ── aliases are a name, never an identity ───────────────────────────────────

def test_an_alias_never_renames_the_stable_key(tmp_path, monkeypatch):
    """"this is the RA room" is something the user tells us. REGION_04 is
    what every route edge, derived table and human note refers to, and it
    does not move because somebody gave it a nickname."""
    from engine.pantheon import map_authority as ma
    monkeypatch.setattr(ma, "ALIAS_DB", tmp_path / "alias.db")
    a = ma.set_alias("campgrounds", "REGION_04", "RA room")
    assert a.region_id == "REGION_04"
    assert ma.aliases("campgrounds") == {"REGION_04": "RA room"}
    # Removing every alias changes nothing about the geography itself.
    assert ma.aliases("asylum") == {}


def test_an_alias_must_attach_to_a_machine_id(tmp_path, monkeypatch):
    from engine.pantheon import map_authority as ma
    monkeypatch.setattr(ma, "ALIAS_DB", tmp_path / "alias.db")
    with pytest.raises(ValueError):
        ma.set_alias("campgrounds", "the RA room", "RA room")
    with pytest.raises(ValueError):
        ma.set_alias("campgrounds", "REGION_04", "   ")


def test_nothing_invents_an_alias_by_itself():
    """Community callouts are not inferred. A guess printed on every clip is
    worse than a machine label."""
    import inspect
    from engine.pantheon import map_authority as ma
    src = inspect.getsource(ma)
    i = src.index("def set_alias")
    callers = [ln for ln in src.split("\n") if "set_alias(" in ln]
    assert len(callers) == 1, f"set_alias is called from inside: {callers}"
    assert 'provenance: str = "HUMAN_USER"' in src[i:i + 400]
