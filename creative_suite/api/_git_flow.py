# creative_suite/api/_git_flow.py
"""Private git sub-repo wrapper for flow_plan.json version history.

Every successful rebuild creates a git tag `part{NN}/{tag}` on a commit that
contains `part{NN}_flow_plan.json`. The repo lives at `output/.git` and is
never pushed — it is a local-only history for the cinema suite.
"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# Git refname constraints we can enforce cheaply: word chars + dot/hyphen,
# non-empty, no leading dot or hyphen (git rejects those), no double dots.
_TAG_RE = re.compile(r"^(?![.\-])[\w.\-]+$")


def _validate_tag(tag: str) -> None:
    if not tag or ".." in tag or not _TAG_RE.match(tag):
        raise ValueError(
            f"invalid tag {tag!r}: must match [A-Za-z0-9_.-]+, no leading "
            f"dot/hyphen, no '..'"
        )


@dataclass(frozen=True)
class GitTag:
    name: str        # "part04/v10.5-opener"
    sha: str         # commit SHA


class GitFlow:
    def __init__(self, repo_root: Path) -> None:
        self.root = repo_root

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(self.root), *args],
            check=True, capture_output=True, text=True,
        )

    def _tag_exists(self, tag: str) -> bool:
        r = subprocess.run(
            ["git", "-C", str(self.root), "tag", "--list", tag],
            check=True, capture_output=True, text=True,
        )
        return bool(r.stdout.strip())

    def save_and_tag(
        self, *, part: int, flow_plan: dict[str, Any], tag: str, notes: str
    ) -> str:
        """Write JSON, commit, tag. Returns commit SHA.

        Raises ValueError if ``tag`` isn't a safe refname component
        (prevents DB row / missing-git-tag divergence if git rejects the
        tag AFTER the render_versions INSERT has already been written).
        """
        _validate_tag(tag)
        full_tag = f"part{part:02d}/{tag}"
        if self._tag_exists(full_tag):
            raise ValueError(f"Tag {full_tag} already exists")
        jpath = self.root / f"part{part:02d}_flow_plan.json"
        jpath.write_text(json.dumps(flow_plan, indent=2), encoding="utf-8")
        self._run("add", jpath.name)
        msg = f"cinema: part{part:02d} {tag}\n\n{notes}".rstrip()
        self._run("commit", "-m", msg)
        sha = self._run("rev-parse", "HEAD").stdout.strip()
        self._run("tag", full_tag, sha)
        return sha

    def list_tags(self, part: int) -> list[GitTag]:
        prefix = f"part{part:02d}/"
        r = self._run("tag", "--list", f"{prefix}*")
        names = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
        out: list[GitTag] = []
        for n in names:
            sha = self._run("rev-parse", n).stdout.strip()
            out.append(GitTag(name=n, sha=sha))
        return out

    def diff(self, tag_a: str, tag_b: str, file_path: str) -> str:
        r = subprocess.run(
            ["git", "-C", str(self.root), "diff", tag_a, tag_b, "--", file_path],
            check=True, capture_output=True, text=True,
        )
        return r.stdout
