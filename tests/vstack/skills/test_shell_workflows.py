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
@pytest.mark.parametrize("component_path", ["", "services/go service"])
def test_performance_baseline_preserves_user_git_state(
    tmp_path: Path,
    generated_dir: Path,
    state: str,
    benchmark_status: int,
    component_path: str,
) -> None:
    """Baseline success and failure leave branches, index, files and stashes intact."""
    repo = tmp_path / "user project"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "fixture@example.invalid")
    _git(repo, "config", "user.name", "Fixture")
    component = repo / component_path
    component.mkdir(parents=True, exist_ok=True)
    (repo / "package.json").write_text("{}", encoding="utf-8")
    if component_path:
        (component / "go.mod").write_text("module fixture\n", encoding="utf-8")
    tracked = component / "tracked.txt"
    tracked.write_text("base\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "base")
    tracked.write_text("older unrelated work\n", encoding="utf-8")
    _git(repo, "stash", "push", "-m", "unrelated stash")
    _git(repo, "switch", "-c", "feature/benchmark")
    tracked.write_text("feature\n", encoding="utf-8")
    _git(repo, "commit", "-am", "feature")
    if state in {"unstaged", "staged"}:
        tracked.write_text("user changes\n", encoding="utf-8")
    if state == "staged":
        _git(repo, "add", str(tracked.relative_to(repo)))
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
        cwd=component,
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


def test_performance_missing_base_component_does_not_benchmark_root(
    tmp_path: Path, generated_dir: Path
) -> None:
    """A newly added component cannot produce a false root-level comparison."""
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.email", "fixture@example.invalid")
    _git(tmp_path, "config", "user.name", "Fixture")
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "base")
    _git(tmp_path, "switch", "-c", "feature/new-component")
    component = tmp_path / "services" / "new"
    component.mkdir(parents=True)
    (component / "go.mod").write_text("module fixture\n", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "add component")
    text = (generated_dir / "performance" / "SKILL.md").read_text(encoding="utf-8")
    script = _bash_block(text, "## Phase 2:").replace('BASE_REF="<base>"', 'BASE_REF="main"')
    result = subprocess.run(
        ["bash", "-c", "run_benchmark() { echo WRONG_COMPONENT; }\n" + script],
        cwd=component,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "baseline benchmark failed" in result.stdout
    assert "WRONG_COMPONENT" not in result.stdout
    assert _git(tmp_path, "status", "--porcelain") == ""
    assert _git(tmp_path, "worktree", "list", "--porcelain").count("worktree ") == 1


@pytest.mark.parametrize(
    ("marker", "runner"),
    [
        ("package.json", "npm"),
        ("pyproject.toml", "python"),
        ("go.mod", "go"),
        ("Cargo.toml", "cargo"),
    ],
)
@pytest.mark.parametrize("runner_status", [0, 6])
def test_performance_runs_only_component_native_benchmarks(
    tmp_path: Path, generated_dir: Path, marker: str, runner: str, runner_status: int
) -> None:
    """A failed native benchmark remains a failure without invoking fallback tools."""
    (tmp_path / marker).touch()
    log = tmp_path / "runners.txt"
    text = (generated_dir / "performance" / "SKILL.md").read_text(encoding="utf-8")
    script = _bash_block(text, "## Phase 1:")
    stubs = """
npm() { echo npm >> "$CALL_LOG"; return "$RUNNER_STATUS"; }
python() { echo python >> "$CALL_LOG"; return "$RUNNER_STATUS"; }
go() { echo go >> "$CALL_LOG"; return "$RUNNER_STATUS"; }
cargo() { echo cargo >> "$CALL_LOG"; return "$RUNNER_STATUS"; }
npx() { echo unexpected-npx >> "$CALL_LOG"; return 99; }
"""
    result = subprocess.run(
        ["bash", "-c", stubs + script],
        cwd=tmp_path,
        env={**os.environ, "CALL_LOG": str(log), "RUNNER_STATUS": str(runner_status)},
        capture_output=True,
        text=True,
    )
    assert result.returncode == runner_status, result.stdout + result.stderr
    assert log.read_text(encoding="utf-8").splitlines() == [runner]
    procedure = text.split("# performance ", 1)[1]
    assert "|| true" not in procedure
    assert "2>/dev/null" not in procedure


def test_performance_reports_unconfigured_benchmarks(tmp_path: Path, generated_dir: Path) -> None:
    """Unknown projects fail explicitly instead of reporting successful measurement."""
    text = (generated_dir / "performance" / "SKILL.md").read_text(encoding="utf-8")
    result = subprocess.run(
        ["bash", "-c", _bash_block(text, "## Phase 1:")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "no benchmark runner configured" in result.stdout
