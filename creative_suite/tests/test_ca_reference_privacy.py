"""The CA reference extractor must not emit player names.

WHY THIS TEST EXISTS. The first run of the extractor wrote round traces
containing `server_text`, and CA server text is chat -- opponent nicknames
verbatim, colour codes and all, plus vote lines naming the caller. Those JSON
files were committed to a public repository before anyone looked at them.

CLAUDE.md's rule is absolute: no player name, nickname or personal identifier
is ever committed. A rule that depends on remembering to check is not a rule,
so redaction is the default and this asserts it.
"""
from __future__ import annotations

from pathlib import Path

from engine.parser import ca_reference as R

REPO = Path(__file__).resolve().parents[2]


def test_server_text_is_redacted_by_default():
    rows = [{"server_time_ms": 10, "kind": "chat", "round": 1,
             "text": "^1SomeNick^7: hello there"}]
    out = R._redact(rows, keep=False)
    assert "SomeNick" not in str(out)
    assert out[0]["kind"] == "chat"          # shape survives
    assert out[0]["chars"] == len(rows[0]["text"])


def test_identifying_mode_is_opt_in_and_explicit():
    rows = [{"server_time_ms": 10, "kind": "chat", "round": 1, "text": "X"}]
    assert R._redact(rows, keep=True) == rows


def test_demo_id_is_not_the_filename():
    """A QL demo filename embeds the recorder's handle:
    `CA-<name>-<map>-<date>.dm_73`."""
    p = Path("CA-SomeHandle-campgrounds-2011_06_29-23_49_45.dm_73")
    ident = R._demo_id(p, keep=False)
    assert "SomeHandle" not in ident
    assert ident.startswith("demo-")
    assert R._demo_id(p, keep=False) == R._demo_id(p, keep=False)   # stable
    assert R._demo_id(p, keep=True) == p.name


def test_no_committed_trace_carries_chat():
    """Whatever is in the repo now must be clean, regardless of how it got
    there."""
    traces = REPO / "docs/reference/ca_rounds"
    if not traces.exists():
        return
    for f in traces.glob("*.json"):
        body = f.read_text(encoding="utf-8", errors="replace")
        assert '"kind": "chat"' not in body or "redacted" in body, f
        assert '"kind": "tchat"' not in body or "redacted" in body, f


def test_redacted_rows_have_no_text_channel_at_all():
    """Not even a placeholder. A `text` key invites someone to repopulate it
    'just for debugging'; a schema without one does not."""
    rows = [{"server_time_ms": 1, "kind": "chat", "round": 1, "text": "^1Nick: x"}]
    out = R._redact(rows, keep=False)
    assert "text" not in out[0]
    assert set(out[0]) == {"server_time_ms", "kind", "chars", "round"}


def test_no_server_text_kind_is_considered_safe():
    """chat, tchat, print and cp all carry nicknames in QL."""
    assert R.SAFE_TEXT_KINDS == frozenset()
