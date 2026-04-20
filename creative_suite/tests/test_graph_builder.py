"""creative_suite/tests/test_graph_builder.py

Unit tests for the engine knowledge graph builder (P3-T2).
Tests graph data integrity and HTML generation in isolation.
No file I/O required — generate_html() and build_graph() are pure.
"""
from __future__ import annotations

import pytest

from creative_suite.engine.graph_builder import build_graph, generate_html, Graph


# ---------------------------------------------------------------------------
# build_graph()
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def graph() -> Graph:
    return build_graph()


def test_build_graph_returns_nodes_and_edges(graph: Graph) -> None:
    assert "nodes" in graph
    assert "edges" in graph
    assert isinstance(graph["nodes"], list)
    assert isinstance(graph["edges"], list)


def test_node_count_at_least_20(graph: Graph) -> None:
    assert len(graph["nodes"]) >= 20, (
        f"Expected >= 20 nodes, got {len(graph['nodes'])}"
    )


def test_edge_count_at_least_20(graph: Graph) -> None:
    assert len(graph["edges"]) >= 20, (
        f"Expected >= 20 edges, got {len(graph['edges'])}"
    )


def test_each_node_has_required_fields(graph: Graph) -> None:
    required = {"id", "label", "category"}
    for node in graph["nodes"]:
        missing = required - set(node.keys())
        assert not missing, f"Node {node!r} missing fields: {missing}"


def test_each_edge_has_required_fields(graph: Graph) -> None:
    required = {"source", "target", "label"}
    for edge in graph["edges"]:
        missing = required - set(edge.keys())
        assert not missing, f"Edge {edge!r} missing fields: {missing}"


def test_node_ids_are_unique(graph: Graph) -> None:
    ids = [n["id"] for n in graph["nodes"]]
    assert len(ids) == len(set(ids)), "Duplicate node IDs found"


def test_edge_source_and_target_reference_known_nodes(graph: Graph) -> None:
    node_ids = {n["id"] for n in graph["nodes"]}
    for edge in graph["edges"]:
        assert edge["source"] in node_ids, (
            f"Edge source '{edge['source']}' not in node set"
        )
        assert edge["target"] in node_ids, (
            f"Edge target '{edge['target']}' not in node set"
        )


def test_demo_corpus_node_exists(graph: Graph) -> None:
    ids = {n["id"] for n in graph["nodes"]}
    assert "demo_corpus" in ids


def test_studio_ui_node_exists(graph: Graph) -> None:
    ids = {n["id"] for n in graph["nodes"]}
    assert "studio_ui" in ids


def test_forge_node_exists(graph: Graph) -> None:
    ids = {n["id"] for n in graph["nodes"]}
    assert "forge" in ids


def test_all_five_categories_present(graph: Graph) -> None:
    cats = {n["category"] for n in graph["nodes"]}
    expected = {"DEMOS", "ANALYSIS", "RENDER", "ENGINE", "STUDIO"}
    assert expected == cats, f"Categories mismatch: {cats}"


# ---------------------------------------------------------------------------
# generate_html()
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def html(graph: Graph) -> str:
    return generate_html(graph)


def test_generate_html_returns_string(html: str) -> None:
    assert isinstance(html, str)


def test_html_starts_with_doctype(html: str) -> None:
    assert html.strip().startswith("<!DOCTYPE html")


def test_html_contains_html_tag(html: str) -> None:
    assert "<html" in html


def test_html_contains_canvas_element(html: str) -> None:
    assert "graph-canvas" in html


def test_html_contains_node_data(html: str) -> None:
    assert "demo_corpus" in html
    assert "studio_ui" in html
    assert "forge" in html


def test_html_is_self_contained_no_external_urls(html: str) -> None:
    """No CDN or external script/style URLs — truly standalone."""
    forbidden = ["https://", "http://", "cdn.jsdelivr", "unpkg.com", "cdnjs"]
    for token in forbidden:
        assert token not in html, f"External URL found: {token}"


def test_html_size_reasonable(html: str) -> None:
    # Should be between 8 KB and 200 KB
    size = len(html.encode("utf-8"))
    assert 8_000 < size < 200_000, f"HTML size {size} bytes outside expected range"
