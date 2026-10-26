"""Exercise executable skill recipes without touching the user's repository."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest


def _git(repo: Path, *args: str) -> str:
    """Run Git in an isolated fixture repository."""
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def _bash_block(text: str, heading: str) -> str:
    """Extract the first shell recipe following a known section heading."""
    section = text.split(heading, 1)[1]
    match = re.search(r"```bash\n(.*?)```", section, re.DOTALL)
    assert match is not None
    return match.group(1)


@pytest.mark.parametrize("state", ["clean", "unstaged", "staged", "untracked"])
@pytest.mark.parametrize("benchmark_status", [0, 9])
def test_performance_baseline_preserves_user_git_state(
    tmp_path: Path, generated_dir: Path, state: str, benchmark_status: int
) -> None:
    """Baseline success and failure leave branches, index, files and stashes intact."""
    repo = tmp_path / "user project"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "fixture@example.invalid")
    _git(repo, "config", "user.name", "Fixture")
    tracked = repo / "tracked.txt"
    tracked.write_text("base\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "base")
    tracked.write_text("older unrelated work\n", encoding="utf-8")
    _git(repo, "stash", "push", "-m", "unrelated stash")
    _git(repo, "switch", "-c", "feature/benchmark")
    tracked.write_text("feature\n", encoding="utf-8")
    _git(repo, "commit", "-am", "feature")
    if state in {"unstaged", "staged"}:
        tracked.write_text("user changes\n", encoding="utf-8")
    if state == "staged":
        _git(repo, "add", "tracked.txt")
    if state == "untracked":
        (repo / "user.txt").write_text("keep me\n", encoding="utf-8")
    before = (
        _git(repo, "status", "--porcelain"),
        _git(repo, "rev-parse", "HEAD"),
        _git(repo, "symbolic-ref", "HEAD"),
        _git(repo, "stash", "list", "--format=%H"),
        _git(repo, "diff", "--cached"),
        tracked.read_text(encoding="utf-8"),
    )
    text = (generated_dir / "performance" / "SKILL.md").read_text(encoding="utf-8")
    script = _bash_block(text, "## Phase 2:")
    script = script.replace('BASE_REF="<base>"', 'BASE_REF="main"').replace(
        "run_benchmark",
        f'test "$(cat tracked.txt)" = base || exit 99\n  exit {benchmark_status}',
    )
    result = subprocess.run(
        ["bash", "-c", script],
        cwd=repo,
        env={**os.environ, "TMPDIR": str(tmp_path)},
        capture_output=True,
        text=True,
    )
    assert result.returncode == benchmark_status, result.stdout + result.stderr
    after = (
        _git(repo, "status", "--porcelain"),
        _git(repo, "rev-parse", "HEAD"),
        _git(repo, "symbolic-ref", "HEAD"),
        _git(repo, "stash", "list", "--format=%H"),
        _git(repo, "diff", "--cached"),
        tracked.read_text(encoding="utf-8"),
    )
    assert after == before
    assert _git(repo, "worktree", "list", "--porcelain").count("worktree ") == 1
    if state == "untracked":
        assert (repo / "user.txt").read_text(encoding="utf-8") == "keep me\n"
