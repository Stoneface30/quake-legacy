"""
test_dm73_scaffold.py — FT-1 scaffold verification tests

Verifies that all required files exist and contain the expected symbols/stubs.
Does NOT attempt to compile or run the C++ code — that requires CMake + a
compiler.  These tests are the CI gate that confirms the scaffold is complete.

Run:
    cd G:/QUAKE_LEGACY
    python -m pytest creative_suite/tests/test_dm73_scaffold.py -v
"""

import os
import pytest

# ---------------------------------------------------------------------------
# Root path helpers
# ---------------------------------------------------------------------------

REPO_ROOT   = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
PARSER_ROOT = os.path.join(REPO_ROOT, "creative_suite", "engine", "parser")


def parser_path(*parts: str) -> str:
    return os.path.join(PARSER_ROOT, *parts)


def read_file(rel: str) -> str:
    path = parser_path(*rel.split("/"))
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# Test: directory structure
# ---------------------------------------------------------------------------

def test_parser_directory_exists():
    assert os.path.isdir(PARSER_ROOT), \
        f"Parser directory missing: {PARSER_ROOT}"


def test_include_dm73_directory_exists():
    assert os.path.isdir(parser_path("include", "dm73")), \
        "include/dm73/ directory missing"


def test_src_directory_exists():
    assert os.path.isdir(parser_path("src")), \
        "src/ directory missing"


def test_vendor_directory_exists():
    assert os.path.isdir(parser_path("vendor")), \
        "vendor/ directory missing"


# ---------------------------------------------------------------------------
# Test: CMakeLists.txt
# ---------------------------------------------------------------------------

def test_cmakelists_exists():
    assert os.path.isfile(parser_path("CMakeLists.txt")), \
        "CMakeLists.txt missing"


def test_cmakelists_project_name():
    content = read_file("CMakeLists.txt")
    assert "dm73parser" in content, \
        "CMakeLists.txt does not declare project(dm73parser)"


def test_cmakelists_static_library():
    content = read_file("CMakeLists.txt")
    assert "add_library(dm73 STATIC" in content, \
        "CMakeLists.txt does not declare add_library(dm73 STATIC)"


def test_cmakelists_cli_target():
    content = read_file("CMakeLists.txt")
    assert "add_executable(dm73dump" in content, \
        "CMakeLists.txt does not declare add_executable(dm73dump)"


def test_cmakelists_vendor_sources():
    content = read_file("CMakeLists.txt")
    for src in ("vendor/msg.c", "vendor/huffman.c", "vendor/common.c"):
        assert src in content, f"CMakeLists.txt missing vendor source: {src}"


def test_cmakelists_cpp17():
    content = read_file("CMakeLists.txt")
    assert "CMAKE_CXX_STANDARD 17" in content, \
        "CMakeLists.txt does not set CMAKE_CXX_STANDARD 17"


# ---------------------------------------------------------------------------
# Test: include/dm73/reader.h
# ---------------------------------------------------------------------------

def test_reader_header_exists():
    assert os.path.isfile(parser_path("include", "dm73", "reader.h")), \
        "include/dm73/reader.h missing"


def test_mod_rocket_defined():
    content = read_file("include/dm73/reader.h")
    assert "MOD_ROCKET" in content, "reader.h missing MOD_ROCKET"


def test_mod_railgun_defined():
    content = read_file("include/dm73/reader.h")
    assert "MOD_RAILGUN" in content, "reader.h missing MOD_RAILGUN"


def test_mod_hmg_defined():
    content = read_file("include/dm73/reader.h")
    assert "MOD_HMG" in content, \
        "reader.h missing MOD_HMG (wolfcam-specific, confirms protocol 73)"


def test_mod_lightning_defined():
    content = read_file("include/dm73/reader.h")
    assert "MOD_LIGHTNING" in content, "reader.h missing MOD_LIGHTNING"


def test_mod_constants_defined():
    """Composite: all four required MOD_* constants present."""
    content = read_file("include/dm73/reader.h")
    for mod in ("MOD_ROCKET", "MOD_RAILGUN", "MOD_HMG", "MOD_LIGHTNING"):
        assert mod in content, f"reader.h missing {mod}"


def test_frag_event_struct():
    content = read_file("include/dm73/reader.h")
    assert "struct FragEvent" in content, \
        "reader.h missing FragEvent struct"


def test_frag_event_fields():
    content = read_file("include/dm73/reader.h")
    for field in ("server_time_ms", "killer_client", "victim_client", "weapon"):
        assert field in content, f"FragEvent missing field: {field}"


def test_demo_header_struct():
    content = read_file("include/dm73/reader.h")
    assert "struct DemoHeader" in content, \
        "reader.h missing DemoHeader struct"


def test_dm73_reader_class():
    content = read_file("include/dm73/reader.h")
    assert "class Dm73Reader" in content, \
        "reader.h missing Dm73Reader class"


def test_protocol_constant():
    content = read_file("include/dm73/reader.h")
    assert "PROTOCOL" in content and "73" in content, \
        "reader.h missing PROTOCOL = 73"


def test_namespace_dm73():
    content = read_file("include/dm73/reader.h")
    assert "namespace dm73" in content, \
        "reader.h missing namespace dm73"


# ---------------------------------------------------------------------------
# Test: src/dm73_reader.cpp
# ---------------------------------------------------------------------------

def test_stub_implementations():
    content = read_file("src/dm73_reader.cpp")
    assert "not yet implemented" in content, \
        "dm73_reader.cpp missing 'not yet implemented' stub markers"


def test_reader_cpp_exists():
    assert os.path.isfile(parser_path("src", "dm73_reader.cpp")), \
        "src/dm73_reader.cpp missing"


def test_reader_cpp_scaffold_markers():
    content = read_file("src/dm73_reader.cpp")
    assert "SCAFFOLD" in content, \
        "dm73_reader.cpp missing SCAFFOLD markers"


def test_reader_cpp_read_frags():
    content = read_file("src/dm73_reader.cpp")
    assert "read_frags" in content, \
        "dm73_reader.cpp missing read_frags implementation stub"


def test_reader_cpp_read_header():
    content = read_file("src/dm73_reader.cpp")
    assert "read_header" in content, \
        "dm73_reader.cpp missing read_header implementation stub"


# ---------------------------------------------------------------------------
# Test: src/main.cpp
# ---------------------------------------------------------------------------

def test_main_cli_exists():
    assert os.path.isfile(parser_path("src", "main.cpp")), \
        "src/main.cpp missing"


def test_main_cpp_dm73dump_usage():
    content = read_file("src/main.cpp")
    assert "dm73dump" in content, \
        "main.cpp missing dm73dump usage string"


def test_main_cpp_header_mode():
    content = read_file("src/main.cpp")
    assert "--header" in content, \
        "main.cpp missing --header flag support"


# ---------------------------------------------------------------------------
# Test: src/frag_extractor.cpp
# ---------------------------------------------------------------------------

def test_frag_extractor_exists():
    assert os.path.isfile(parser_path("src", "frag_extractor.cpp")), \
        "src/frag_extractor.cpp missing"


def test_frag_extractor_jsonl_function():
    content = read_file("src/frag_extractor.cpp")
    assert "extract_frags_jsonl" in content, \
        "frag_extractor.cpp missing extract_frags_jsonl function"


# ---------------------------------------------------------------------------
# Test: vendor stub files
# ---------------------------------------------------------------------------

def test_vendor_msg_c_exists():
    assert os.path.isfile(parser_path("vendor", "msg.c")), \
        "vendor/msg.c missing"


def test_vendor_huffman_c_exists():
    assert os.path.isfile(parser_path("vendor", "huffman.c")), \
        "vendor/huffman.c missing"


def test_vendor_common_c_exists():
    assert os.path.isfile(parser_path("vendor", "common.c")), \
        "vendor/common.c missing"


def test_vendor_stubs_exist():
    """Composite: all three vendor .c stubs present."""
    for name in ("msg.c", "huffman.c", "common.c"):
        assert os.path.isfile(parser_path("vendor", name)), \
            f"vendor/{name} missing"


def test_vendor_q_shared_h_exists():
    assert os.path.isfile(parser_path("vendor", "q_shared.h")), \
        "vendor/q_shared.h missing"


def test_vendor_bg_public_h_exists():
    assert os.path.isfile(parser_path("vendor", "bg_public.h")), \
        "vendor/bg_public.h missing"


def test_vendor_stubs_preserve_gpl_header():
    """All vendor .c stubs must carry the GPL-2.0 copyright header."""
    for name in ("msg.c", "huffman.c", "common.c"):
        content = read_file(f"vendor/{name}")
        assert "Copyright (C) 1999-2005 Id Software" in content, \
            f"vendor/{name} missing GPL-2.0 copyright header"
        assert "GNU General Public License" in content, \
            f"vendor/{name} missing GPL license text"


def test_vendor_stubs_reference_canonical_source():
    """Vendor stubs must document where to copy the real source from."""
    for name in ("msg.c", "huffman.c", "common.c"):
        content = read_file(f"vendor/{name}")
        assert "_canonical" in content, \
            f"vendor/{name} missing reference to _canonical source path"


# ---------------------------------------------------------------------------
# Test: documentation
# ---------------------------------------------------------------------------

def test_readme_exists():
    assert os.path.isfile(parser_path("README.md")), \
        "parser/README.md missing"


def test_dm73_format_deep_dive_exists():
    """The authoritative format reference must already exist."""
    ref_path = os.path.join(
        REPO_ROOT, "docs", "reference", "dm73-format-deep-dive.md"
    )
    assert os.path.isfile(ref_path), \
        f"docs/reference/dm73-format-deep-dive.md missing (needed by FT-1 alpha)"
