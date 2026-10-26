"""Tests for skill template source files."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

import pytest

from tests.conftest import ROOT, SKILLS_TEMPLATES_DIR
from vstack.cli.constants import EXPECTED_CANONICAL_NAMES
from vstack.frontmatter import FrontmatterParser


@pytest.mark.parametrize(
    "candidate_kind", ["none", "other-fork", "other-repo", "other-branch", "matching"]
)
@pytest.mark.parametrize("push_status", [0, 7])
def test_pr_recipe_pushes_before_reusing_existing_pr(
    tmp_path: Path, generated_dir: Path, candidate_kind: str, push_status: int
) -> None:
    """Existing and new PR paths push first and never hide push failures."""
    text = (generated_dir / "pr" / "SKILL.md").read_text(encoding="utf-8")
    blocks = []
    for heading in ("## Step 1:", "## Step 3:", "## Step 4:"):
        match = re.search(r"```bash\n(.*?)```", text.split(heading, 1)[1], re.DOTALL)
        assert match is not None
        blocks.append(
            match.group(1)
            .replace("<push-owner>/<push-repo>", "contributor/fork")
            .replace("<base-owner>/<base-repo>", "upstream/project")
        )
    stubs = """
git() {
  case "$1" in
    branch) echo feature/example ;;
    push)
      test "$*" = "push --set-upstream origin feature/example" || return 99
      echo push >> "$CALL_LOG"; return "$PUSH_STATUS" ;;
  esac
}
gh() {
  if [ "$1 $2" = "pr list" ]; then
    test "$3 $4" = "--repo upstream/project" || return 99
    printf '%s' "$PR_CANDIDATES_JSON"
  fi
}
"""
    candidate = {
        "url": "https://example.invalid/pull/1",
        "headRepositoryOwner": {"login": "contributor"},
        "headRepository": {"name": "fork"},
        "headRefName": "feature/example",
    }
    if candidate_kind == "other-fork":
        candidate["headRepositoryOwner"] = {"login": "unrelated"}
    elif candidate_kind == "other-repo":
        candidate["headRepository"] = {"name": "another"}
    elif candidate_kind == "other-branch":
        candidate["headRefName"] = "feature/different"
    candidates = [] if candidate_kind == "none" else [candidate]
    if candidate_kind == "matching":
        candidates.insert(
            0,
            {
                **candidate,
                "url": "https://example.invalid/pull/unrelated",
                "headRepositoryOwner": {"login": "unrelated"},
            },
        )
    log = tmp_path / "calls.txt"
    result = subprocess.run(
        ["bash", "-c", stubs + "\n".join(blocks) + '\necho create >> "$CALL_LOG"'],
        cwd=tmp_path,
        env={
            **os.environ,
            "CALL_LOG": str(log),
            "PUSH_STATUS": str(push_status),
            "PR_CANDIDATES_JSON": json.dumps(candidates),
        },
        capture_output=True,
        text=True,
    )
    assert result.returncode == push_status, result.stdout + result.stderr
    assert log.read_text(encoding="utf-8").splitlines() == (
        ["push", "create"] if candidate_kind != "matching" and push_status == 0 else ["push"]
    )
    if candidate_kind == "matching" and push_status == 0:
        assert "PR updated: https://example.invalid/pull/1" in result.stdout
        assert "PR updated: https://example.invalid/pull/unrelated" not in result.stdout
    assert "git add -A\n" not in text
    assert 'git commit -m "chore: pre-release cleanup"' not in text


@pytest.mark.parametrize("failed_command", ["auth status", "pr list"])
def test_pr_preflight_stops_on_github_errors(
    tmp_path: Path, generated_dir: Path, failed_command: str
) -> None:
    """Authentication and PR lookup failures do not become successful PR updates."""
    text = (generated_dir / "pr" / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r"```bash\n(.*?)```", text.split("## Step 1:", 1)[1], re.DOTALL)
    assert match is not None
    stubs = """
git() { echo feature/example; }
gh() {
  if [ "$1 $2" = "$FAILED_COMMAND" ]; then return 8; fi
}
"""
    result = subprocess.run(
        ["bash", "-c", stubs + match.group(1) + "\necho unexpected-continuation"],
        cwd=tmp_path,
        env={**os.environ, "FAILED_COMMAND": failed_command},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 8
    assert "unexpected-continuation" not in result.stdout


def _skill_templates() -> list[Path]:
    """Internal helper to skill templates."""
    if not SKILLS_TEMPLATES_DIR.exists():
        return []
    return sorted(SKILLS_TEMPLATES_DIR.glob("*/template.md"))


def _skill_name(path: Path) -> str:
    """Internal helper to skill name."""
    return path.parent.name


def _skill_config(path: Path) -> Path:
    """Internal helper to skill config."""
    return path.parent / "config.yaml"


class TestSkillTemplates:
    """Test cases for SkillTemplates."""

    def test_all_expected_canonical_skills_have_template(self) -> None:
        """Test that all expected canonical skills have template."""
        templates = {_skill_name(t) for t in _skill_templates()}
        for name in EXPECTED_CANONICAL_NAMES:
            assert name in templates

    def test_every_template_has_valid_config_yaml(self) -> None:
        """Test that every template has valid config yaml."""
        for tmpl in _skill_templates():
            name = _skill_name(tmpl)
            cfg = _skill_config(tmpl)
            assert cfg.exists(), f"{name}: missing config.yaml"
            meta = FrontmatterParser.parse_yaml(cfg.read_text(encoding="utf-8"))
            assert meta.get("name"), f"{name}: missing name"
            assert meta.get("version"), f"{name}: missing version"
            assert meta.get("description"), f"{name}: missing description"

    def test_config_name_matches_directory(self) -> None:
        """Test that config name matches directory."""
        for tmpl in _skill_templates():
            name = _skill_name(tmpl)
            meta = FrontmatterParser.parse_yaml(_skill_config(tmpl).read_text(encoding="utf-8"))
            assert str(meta.get("name")) == name


class TestGeneratedSkillFiles:
    """Test cases for GeneratedSkillFiles."""

    def test_every_expected_skill_generates_md_file(self, generated_dir: Path) -> None:
        """Test that every expected skill generates md file."""
        for name in EXPECTED_CANONICAL_NAMES:
            assert (generated_dir / name / "SKILL.md").exists()

    def test_generated_files_have_auto_gen_footer(self, generated_dir: Path) -> None:
        """Test that generated files have auto gen footer."""
        for md in generated_dir.glob("*/SKILL.md"):
            content = md.read_text(encoding="utf-8")
            lines = content.rstrip().splitlines()
            assert len(lines) >= 2
            assert (
                lines[-2] == "<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->"
            )
            assert re.fullmatch(r"<!-- VSTACK-META: \{.*\} -->", lines[-1])

    def test_generated_count_matches_expected(self, generated_dir: Path) -> None:
        """Test that generated count matches expected."""
        md_files = list(generated_dir.glob("*/SKILL.md"))
        assert len(md_files) == len(EXPECTED_CANONICAL_NAMES)


@pytest.mark.parametrize(
    ("name", "obligations"),
    [
        (
            "changedoc",
            (
                "Small, clear, low-risk work",
                "Older customized templates remain valid",
                "real prerequisites",
                "preserve established references",
                "Required failed/unrun checks",
                "`ARCHIVED`: closed history; never authorizes",
            ),
        ),
        (
            "requirements",
            (
                "existing issue or conversation",
                "one focused question",
                "existing intent source",
                "wording review is not proof",
                "independently verifiable delivery slices",
            ),
        ),
        (
            "analyse",
            (
                "before implementation",
                "contradictions",
                "uncovered obligations",
                "no requirement or engineering rationale",
                "Do not silently change intent",
                "no mandatory standalone report",
            ),
        ),
        (
            "inspect",
            (
                "required behavior absent from the diff",
                "unexplained additions",
                "evidence gaps",
                "only when authorized",
                "policy-approved exception",
            ),
        ),
        (
            "verify",
            (
                "required behavior absent from the diff",
                "Commit only when authorized",
                "Stop and report blockers",
                "attempts repeat without new evidence",
                "do not loop indefinitely or weaken criteria",
                "no duplicate reports",
            ),
        ),
    ],
)
def test_rendered_sdd_skills_preserve_key_obligations(
    generated_dir: Path, name: str, obligations: tuple[str, ...]
) -> None:
    """Rendered procedures retain routing, ownership, and completion safeguards."""
    text = " ".join((generated_dir / name / "SKILL.md").read_text(encoding="utf-8").split())
    for obligation in obligations:
        assert obligation in text
    assert "{{" not in text


@pytest.mark.parametrize("name", ["changedoc", "inspect", "verify"])
def test_rendered_evidence_states_do_not_hide_missing_checks(
    generated_dir: Path, name: str
) -> None:
    """Each evidence procedure distinguishes freshness and failed/unrun checks."""
    text = (generated_dir / name / "SKILL.md").read_text(encoding="utf-8")
    for state in ("passed", "failed", "not run", "no longer current"):
        assert state in text
    assert "Required failed/unrun checks" in text
    assert "reviewed" in text.lower()
    procedure = text.split(f"# {name} ", 1)[1]
    assert "2>/dev/null" not in procedure
    assert "|| true" not in procedure


def test_sdd_guidance_stays_below_prechange_source_and_rendered_size(
    installed_target: Path,
) -> None:
    """Compact guidance retains contracts without aggregate word or byte growth."""
    source_root = ROOT / "src" / "vstack" / "_templates"
    paths = (
        [("skills", name) for name in ("changedoc", "requirements", "analyse", "inspect", "verify")]
        + [
            ("agents", name)
            for name in (
                "product",
                "planner",
                "architect",
                "designer",
                "engineer",
                "tester",
                "release",
            )
        ]
        + [("instructions", "testing")]
    )
    source_text = "".join(
        (source_root / family / name / filename).read_text(encoding="utf-8")
        for family, name in paths
        for filename in ("template.md", "config.yaml")
    ) + (source_root / "agents/product/artifacts/changes/changedoc.md").read_text(encoding="utf-8")
    output_paths = [
        Path("skills") / name / "SKILL.md"
        if family == "skills"
        else Path("agents") / f"{name}.agent.md"
        if family == "agents"
        else Path("instructions") / f"{name}.instructions.md"
        for family, name in paths
    ]
    rendered_text = "".join(
        (installed_target / ".github" / path).read_text(encoding="utf-8") for path in output_paths
    )
    assert len(source_text.split()) <= 11483
    assert len(source_text.encode("utf-8")) <= 81847
    assert len(rendered_text.split()) <= 14763
    assert len(rendered_text.encode("utf-8")) <= 105562
