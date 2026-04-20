"""
Engine knowledge graph builder.

Generates an interactive HTML file showing the relationships between all
PANTHEON system components: demos -> parser -> frags -> scoring -> render -> studio.

Run:  python -m creative_suite.engine.graph_builder
      python -m creative_suite.engine.graph_builder --json

Output: graphify-out/engine_knowledge_graph.html
        graphify-out/engine_knowledge_graph.json  (with --json)
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import TypedDict


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

class Node(TypedDict):
    id: str
    label: str
    category: str


class Edge(TypedDict):
    source: str
    target: str
    label: str


class Graph(TypedDict):
    nodes: list[Node]
    edges: list[Edge]


# ---------------------------------------------------------------------------
# Graph data
# ---------------------------------------------------------------------------

CATEGORY_COLORS: dict[str, str] = {
    "DEMOS":    "#2a4a2a",
    "ANALYSIS": "#2a2a4a",
    "RENDER":   "#4a2a2a",
    "ENGINE":   "#4a3a1a",
    "STUDIO":   "#1a3a4a",
}

CATEGORY_TEXT_COLORS: dict[str, str] = {
    "DEMOS":    "#88dd88",
    "ANALYSIS": "#8888dd",
    "RENDER":   "#dd8888",
    "ENGINE":   "#ddbb66",
    "STUDIO":   "#66bbdd",
}


def build_graph() -> Graph:
    """Return the canonical PANTHEON engine knowledge graph."""
    nodes: list[Node] = [
        # DEMOS
        {"id": "demo_corpus",        "label": "Demo Corpus\n(6,465 .dm_73 files)",  "category": "DEMOS"},
        {"id": "dm73_parser",        "label": "dm73 C++17\nParser (FT-1)",           "category": "DEMOS"},
        {"id": "frag_events",        "label": "Frag Events\n(JSON Lines)",           "category": "DEMOS"},
        # ANALYSIS
        {"id": "highlight_criteria", "label": "Highlight\nCriteria v2",              "category": "ANALYSIS"},
        {"id": "frag_scoring",       "label": "Frag Scoring\nEngine",                "category": "ANALYSIS"},
        {"id": "music_matcher",      "label": "Music Match\nEngine",                 "category": "ANALYSIS"},
        # RENDER
        {"id": "clip_lists",         "label": "Clip Lists\n(part04-12.txt)",          "category": "RENDER"},
        {"id": "phase1_pipeline",    "label": "Phase 1\nFFmpeg Pipeline",            "category": "RENDER"},
        {"id": "otio_bridge",        "label": "OTIO Bridge\n(.otio output)",          "category": "RENDER"},
        {"id": "music_contract",     "label": "Music Full-Length\nContract",          "category": "RENDER"},
        # ENGINE
        {"id": "wolfcamql",          "label": "WolfcamQL\n(demo playback)",           "category": "ENGINE"},
        {"id": "q3mme",              "label": "q3mme\n(4K capture)",                 "category": "ENGINE"},
        {"id": "forge",              "label": "FORGE Engine\n(stub)",                "category": "ENGINE"},
        # STUDIO
        {"id": "studio_ui",          "label": "PANTHEON\nStudio UI",                 "category": "STUDIO"},
        {"id": "preview_panel",      "label": "Preview Panel\n(WebCodecs)",           "category": "STUDIO"},
        {"id": "timeline_panel",     "label": "Clip Timeline",                       "category": "STUDIO"},
        {"id": "audio_panel",        "label": "Audio Timeline\n(wavesurfer)",         "category": "STUDIO"},
        {"id": "effects_panel",      "label": "Effect Graph\n(LiteGraph)",            "category": "STUDIO"},
        {"id": "inspector_panel",    "label": "Inspector\n(Tweakpane)",               "category": "STUDIO"},
        {"id": "music_panel",        "label": "Music Library",                       "category": "STUDIO"},
        {"id": "beatmarkers",        "label": "Beat Markers\nOverlay",               "category": "STUDIO"},
    ]

    edges: list[Edge] = [
        {"source": "demo_corpus",        "target": "dm73_parser",      "label": "parses"},
        {"source": "dm73_parser",        "target": "frag_events",      "label": "emits"},
        {"source": "frag_events",        "target": "frag_scoring",     "label": "scored by"},
        {"source": "highlight_criteria", "target": "frag_scoring",     "label": "defines rules for"},
        {"source": "frag_scoring",       "target": "clip_lists",       "label": "populates"},
        {"source": "clip_lists",         "target": "phase1_pipeline",  "label": "assembles"},
        {"source": "phase1_pipeline",    "target": "otio_bridge",      "label": "emits artifact"},
        {"source": "music_matcher",      "target": "music_contract",   "label": "validates"},
        {"source": "music_contract",     "target": "phase1_pipeline",  "label": "gates"},
        {"source": "wolfcamql",          "target": "demo_corpus",      "label": "records from"},
        {"source": "q3mme",              "target": "wolfcamql",        "label": "will replace"},
        {"source": "forge",              "target": "wolfcamql",        "label": "controls"},
        {"source": "forge",              "target": "dm73_parser",      "label": "uses"},
        {"source": "studio_ui",          "target": "phase1_pipeline",  "label": "triggers rebuild"},
        {"source": "studio_ui",          "target": "preview_panel",    "label": "mounts"},
        {"source": "studio_ui",          "target": "timeline_panel",   "label": "mounts"},
        {"source": "studio_ui",          "target": "audio_panel",      "label": "mounts"},
        {"source": "studio_ui",          "target": "effects_panel",    "label": "mounts"},
        {"source": "studio_ui",          "target": "inspector_panel",  "label": "mounts"},
        {"source": "studio_ui",          "target": "music_panel",      "label": "mounts"},
        {"source": "studio_ui",          "target": "beatmarkers",      "label": "mounts"},
        {"source": "timeline_panel",     "target": "inspector_panel",  "label": "drives"},
        {"source": "music_panel",        "target": "music_contract",   "label": "displays"},
        {"source": "phase1_pipeline",    "target": "studio_ui",        "label": "streams SSE to"},
        {"source": "beatmarkers",        "target": "phase1_pipeline",  "label": "reads beats from"},
    ]

    return {"nodes": nodes, "edges": edges}


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

def _layout_nodes(nodes: list[Node]) -> dict[str, tuple[float, float]]:
    """
    Place nodes in category clusters arranged around an ellipse.
    Returns {node_id: (x, y)} in a 1200x800 canvas coordinate space.
    """
    cx, cy = 600.0, 400.0
    groups: dict[str, list[Node]] = {}
    for n in nodes:
        groups.setdefault(n["category"], []).append(n)

    categories = list(groups.keys())
    n_cats = len(categories)
    cluster_rx, cluster_ry = 380.0, 270.0

    cluster_centers: dict[str, tuple[float, float]] = {}
    for i, cat in enumerate(categories):
        angle = -math.pi / 2 + (2 * math.pi * i / n_cats)
        cluster_centers[cat] = (
            cx + cluster_rx * math.cos(angle),
            cy + cluster_ry * math.sin(angle),
        )

    positions: dict[str, tuple[float, float]] = {}
    for cat, cat_nodes in groups.items():
        bx, by = cluster_centers[cat]
        n = len(cat_nodes)
        if n == 1:
            positions[cat_nodes[0]["id"]] = (bx, by)
            continue
        r = min(93.6 * n / (2 * math.pi), 160)
        for j, node in enumerate(cat_nodes):
            a = -math.pi / 2 + (2 * math.pi * j / n)
            positions[node["id"]] = (bx + r * math.cos(a), by + r * math.sin(a))

    return positions


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

_JS_GRAPH_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PANTHEON Engine Knowledge Graph</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0e0e12; color: #ccc;
         font-family: 'Courier New', monospace; overflow: hidden; }
  #header { position: fixed; top: 0; left: 0; right: 0;
            padding: 8px 16px; background: rgba(10,10,16,0.92);
            border-bottom: 1px solid #2a2a3a;
            display: flex; align-items: center; gap: 20px; z-index: 10; }
  #header h1 { font-size: 14px; color: #ddbb66;
               letter-spacing: 2px; text-transform: uppercase; }
  .stats { font-size: 11px; color: #666; }
  #legend { display: flex; gap: 12px; margin-left: auto; }
  .legend-item { display: flex; align-items: center; gap: 5px;
                 font-size: 10px; letter-spacing: 1px; }
  .legend-dot { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }
  #canvas-wrap { position: fixed; top: 38px; left: 0; right: 0; bottom: 0; }
  canvas { display: block; width: 100%; height: 100%; cursor: grab; }
  canvas:active { cursor: grabbing; }
  #tooltip { position: fixed; background: rgba(20,20,30,0.95);
             border: 1px solid #444; padding: 6px 10px; font-size: 11px;
             color: #ccc; pointer-events: none; display: none;
             border-radius: 3px; max-width: 200px; z-index: 20; }
  #instructions { position: fixed; bottom: 10px; right: 14px;
                  font-size: 10px; color: #444; z-index: 10; }
</style>
</head>
<body>
<div id="header">
  <h1>PANTHEON &#8212; Engine Knowledge Graph</h1>
  <span class="stats">__NODE_COUNT__ nodes &#183; __EDGE_COUNT__ edges</span>
  <div id="legend">
__LEGEND__
  </div>
</div>
<div id="canvas-wrap">
  <canvas id="graph-canvas"></canvas>
</div>
<div id="tooltip"></div>
<div id="instructions">scroll to zoom &#8226; drag to pan &#8226; hover nodes</div>

<script>
"use strict";

const NODES = __NODES_JS__;
const EDGES = __EDGES_JS__;
const POSITIONS = __POSITIONS_JS__;
const CAT_COLORS = __COLORS_JS__;
const CAT_TEXT = __TEXT_JS__;

const NODE_W = 140, NODE_H = 50, ARROW_SIZE = 8;
const GRAPH_W = 1200;

const canvas = document.getElementById('graph-canvas');
const ctx = canvas.getContext('2d');
const tooltip = document.getElementById('tooltip');

let transform = { x: 0, y: 0, scale: 1.0 };
let dragging = false, dragStart = { x: 0, y: 0 }, transformStart = { x: 0, y: 0 };
let hoveredNode = null;

function resize() {
  const wrap = document.getElementById('canvas-wrap');
  canvas.width = wrap.clientWidth;
  canvas.height = wrap.clientHeight;
  if (transform.x === 0 && transform.y === 0) {
    transform.x = (canvas.width - GRAPH_W) / 2;
    transform.y = (canvas.height - 800) / 2;
  }
  draw();
}
window.addEventListener('resize', resize);

function nodePos(id) { return POSITIONS[id]; }

function screenToGraph(sx, sy) {
  return [(sx - transform.x) / transform.scale,
          (sy - transform.y) / transform.scale];
}

function hitTest(gx, gy, id) {
  const [x, y] = nodePos(id);
  return gx >= x - NODE_W/2 - 4 && gx <= x + NODE_W/2 + 4 &&
         gy >= y - NODE_H/2 - 4 && gy <= y + NODE_H/2 + 4;
}

function drawArrow(x1, y1, x2, y2, label, highlight) {
  const dx = x2 - x1, dy = y2 - y1;
  const len = Math.sqrt(dx*dx + dy*dy);
  if (len < 1) return;
  const ux = dx/len, uy = dy/len;
  const clip = Math.sqrt((NODE_W/2)**2 + (NODE_H/2)**2) * 0.72;
  const sx = x1 + ux*clip, sy = y1 + uy*clip;
  const ex = x2 - ux*(clip + ARROW_SIZE + 2), ey = y2 - uy*(clip + ARROW_SIZE + 2);

  ctx.beginPath();
  ctx.moveTo(sx, sy);
  ctx.lineTo(ex, ey);
  ctx.strokeStyle = highlight ? '#ddbb66' : 'rgba(120,120,140,0.55)';
  ctx.lineWidth = highlight ? 2 : 1;
  ctx.stroke();

  const angle = Math.atan2(ey - sy, ex - sx);
  ctx.beginPath();
  ctx.moveTo(ex, ey);
  ctx.lineTo(ex - ARROW_SIZE*Math.cos(angle - 0.4), ey - ARROW_SIZE*Math.sin(angle - 0.4));
  ctx.lineTo(ex - ARROW_SIZE*Math.cos(angle + 0.4), ey - ARROW_SIZE*Math.sin(angle + 0.4));
  ctx.closePath();
  ctx.fillStyle = highlight ? '#ddbb66' : 'rgba(120,120,140,0.55)';
  ctx.fill();

  if (label) {
    const mx = (sx + ex) / 2, my = (sy + ey) / 2;
    ctx.save();
    ctx.font = "9px 'Courier New', monospace";
    const tw = ctx.measureText(label).width + 6;
    ctx.fillStyle = highlight ? 'rgba(40,32,0,0.9)' : 'rgba(14,14,18,0.8)';
    ctx.fillRect(mx - tw/2, my - 7, tw, 14);
    ctx.fillStyle = highlight ? '#ddbb66' : 'rgba(160,160,180,0.6)';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(label, mx, my);
    ctx.restore();
  }
}

function drawNode(node, highlight) {
  const [x, y] = nodePos(node.id);
  const bg = CAT_COLORS[node.category] || '#2a2a2a';
  const fg = CAT_TEXT[node.category] || '#aaa';
  const hw = NODE_W/2, hh = NODE_H/2;

  if (highlight) { ctx.shadowColor = fg; ctx.shadowBlur = 14; }
  ctx.beginPath();
  ctx.roundRect(x - hw, y - hh, NODE_W, NODE_H, 5);
  ctx.fillStyle = bg;
  ctx.fill();
  ctx.strokeStyle = highlight ? fg : 'rgba(120,120,140,0.4)';
  ctx.lineWidth = highlight ? 2 : 1;
  ctx.stroke();
  ctx.shadowBlur = 0;

  ctx.beginPath();
  ctx.roundRect(x - hw, y - hh, NODE_W, 12, [5, 5, 0, 0]);
  ctx.fillStyle = 'rgba(255,255,255,0.05)';
  ctx.fill();

  ctx.font = "7px 'Courier New', monospace";
  ctx.fillStyle = 'rgba(180,180,200,0.5)';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(node.category, x, y - hh + 6);

  const lines = node.label.split('\\n');
  const lineH = 14;
  const startY = y - (lines.length * lineH)/2 + lineH/2 + 4;
  ctx.font = "bold 11px 'Courier New', monospace";
  ctx.fillStyle = highlight ? '#ffffff' : fg;
  ctx.textAlign = 'center';
  lines.forEach((line, i) => {
    ctx.textBaseline = 'middle';
    ctx.fillText(line, x, startY + i * lineH);
  });
}

// Tooltip built with DOM API only — no untrusted data via dynamic markup insertion.
function buildTooltip(node) {
  while (tooltip.firstChild) { tooltip.removeChild(tooltip.firstChild); }
  const outgoing = EDGES.filter(e => e.source === node.id);
  const incoming = EDGES.filter(e => e.target === node.id);

  const title = document.createElement('div');
  title.textContent = node.label.replace('\\n', ' ');
  title.style.cssText = 'color:#ddbb66;font-weight:bold;margin-bottom:2px';
  tooltip.appendChild(title);

  const cat = document.createElement('div');
  cat.textContent = node.category;
  cat.style.cssText = 'color:#888;margin-bottom:2px';
  tooltip.appendChild(cat);

  const conns = document.createElement('div');
  conns.textContent = 'out: ' + outgoing.length + '  in: ' + incoming.length;
  conns.style.color = '#aaa';
  tooltip.appendChild(conns);
}

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.save();
  ctx.translate(transform.x, transform.y);
  ctx.scale(transform.scale, transform.scale);

  const hlEdges = new Set(), hlNodes = new Set();
  if (hoveredNode) {
    hlNodes.add(hoveredNode);
    EDGES.forEach(e => {
      if (e.source === hoveredNode || e.target === hoveredNode) {
        hlEdges.add(e.source + '|' + e.target);
        hlNodes.add(e.source);
        hlNodes.add(e.target);
      }
    });
  }

  EDGES.forEach(e => {
    const [x1, y1] = nodePos(e.source);
    const [x2, y2] = nodePos(e.target);
    const key = e.source + '|' + e.target;
    const hl = hlEdges.size === 0 ? false : hlEdges.has(key);
    drawArrow(x1, y1, x2, y2, hl || !hoveredNode ? e.label : null, hl);
  });

  NODES.forEach(n => {
    const hl = hlNodes.size === 0 ? false : hlNodes.has(n.id);
    if (!hoveredNode || hl) {
      drawNode(n, hl);
    } else {
      ctx.globalAlpha = 0.3;
      drawNode(n, false);
      ctx.globalAlpha = 1.0;
    }
  });

  ctx.restore();
}

canvas.addEventListener('mousemove', e => {
  if (dragging) {
    transform.x = transformStart.x + (e.clientX - dragStart.x);
    transform.y = transformStart.y + (e.clientY - dragStart.y);
    draw(); return;
  }
  const rect = canvas.getBoundingClientRect();
  const [gx, gy] = screenToGraph(e.clientX - rect.left, e.clientY - rect.top);
  const node = NODES.find(n => hitTest(gx, gy, n.id)) || null;
  hoveredNode = node ? node.id : null;
  if (node) {
    tooltip.style.display = 'block';
    tooltip.style.left = (e.clientX + 14) + 'px';
    tooltip.style.top = (e.clientY - 10) + 'px';
    buildTooltip(node);
  } else {
    tooltip.style.display = 'none';
  }
  draw();
});

canvas.addEventListener('mouseleave', () => {
  hoveredNode = null; tooltip.style.display = 'none'; draw();
});
canvas.addEventListener('mousedown', e => {
  dragging = true;
  dragStart = { x: e.clientX, y: e.clientY };
  transformStart = { x: transform.x, y: transform.y };
});
window.addEventListener('mouseup', () => { dragging = false; });
canvas.addEventListener('wheel', e => {
  e.preventDefault();
  const factor = e.deltaY < 0 ? 1.12 : 0.89;
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left, my = e.clientY - rect.top;
  transform.x = mx - (mx - transform.x) * factor;
  transform.y = my - (my - transform.y) * factor;
  transform.scale = Math.min(4, Math.max(0.15, transform.scale * factor));
  draw();
}, { passive: false });

resize();
</script>
</body>
</html>
"""


def generate_html(graph: Graph) -> str:
    """Generate a standalone HTML string for the knowledge graph."""
    nodes = graph["nodes"]
    edges = graph["edges"]
    positions = _layout_nodes(nodes)

    legend_parts = []
    for cat, color in CATEGORY_COLORS.items():
        tc = CATEGORY_TEXT_COLORS[cat]
        legend_parts.append(
            f'    <div class="legend-item">'
            f'<span class="legend-dot" style="background:{color};border:1px solid {tc}"></span>'
            f'<span style="color:{tc}">{cat}</span>'
            f'</div>'
        )

    html = _JS_GRAPH_TEMPLATE
    html = html.replace("__NODE_COUNT__", str(len(nodes)))
    html = html.replace("__EDGE_COUNT__", str(len(edges)))
    html = html.replace("__LEGEND__", "\n".join(legend_parts))
    html = html.replace("__NODES_JS__", json.dumps(nodes, indent=2))
    html = html.replace("__EDGES_JS__", json.dumps(edges, indent=2))
    html = html.replace(
        "__POSITIONS_JS__",
        json.dumps({k: list(v) for k, v in positions.items()}, indent=2),
    )
    html = html.replace("__COLORS_JS__", json.dumps(CATEGORY_COLORS, indent=2))
    html = html.replace("__TEXT_JS__", json.dumps(CATEGORY_TEXT_COLORS, indent=2))
    return html


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate PANTHEON engine knowledge graph as HTML."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Also write graphify-out/engine_knowledge_graph.json",
    )
    args = parser.parse_args()

    here = Path(__file__).resolve()
    repo_root = here.parent.parent.parent  # creative_suite/engine/ -> repo root
    out_dir = repo_root / "graphify-out"
    out_dir.mkdir(parents=True, exist_ok=True)

    graph = build_graph()
    html = generate_html(graph)

    html_path = out_dir / "engine_knowledge_graph.html"
    html_path.write_text(html, encoding="utf-8")
    print(f"Graph written to {html_path}")

    if args.json:
        json_path = out_dir / "engine_knowledge_graph.json"
        json_path.write_text(json.dumps(graph, indent=2), encoding="utf-8")
        print(f"JSON written to {json_path}")


if __name__ == "__main__":
    main()
