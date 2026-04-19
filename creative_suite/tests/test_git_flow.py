# creative_suite/tests/test_git_flow.py
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from creative_suite.api._git_flow import GitFlow


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "t"], check=True)
    return tmp_path


def test_save_and_tag_writes_json_commits_and_tags(repo: Path) -> None:
    gf = GitFlow(repo)
    plan = {"clips": [{"chunk": "chunk_0001.mp4", "duration": 3.2}]}
    sha = gf.save_and_tag(part=4, flow_plan=plan, tag="v10.5-test", notes="test note")
    assert len(sha) == 40
    jpath = repo / "part04_flow_plan.json"
    assert json.loads(jpath.read_text()) == plan
    tags = subprocess.run(
        ["git", "-C", str(repo), "tag", "--list", "part04/*"],
        check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    assert "part04/v10.5-test" in tags


def test_list_tags_returns_part_tags_only(repo: Path) -> None:
    gf = GitFlow(repo)
    gf.save_and_tag(part=4, flow_plan={"a": 1}, tag="v1", notes="")
    gf.save_and_tag(part=5, flow_plan={"a": 2}, tag="v1", notes="")
    tags = gf.list_tags(part=4)
    assert [t.name for t in tags] == ["part04/v1"]


def test_save_and_tag_rejects_duplicate_tag(repo: Path) -> None:
    gf = GitFlow(repo)
    gf.save_and_tag(part=4, flow_plan={"a": 1}, tag="v1", notes="")
    with pytest.raises(ValueError, match="already exists"):
        gf.save_and_tag(part=4, flow_plan={"a": 2}, tag="v1", notes="")
