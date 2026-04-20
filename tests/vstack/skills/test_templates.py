"""Tests for skill template source files."""

from __future__ import annotations

from pathlib import Path

from tests.conftest import SKILLS_TEMPLATES_DIR
from vstack.cli.constants import EXPECTED_CANONICAL_NAMES
from vstack.frontmatter import FrontmatterParser


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
            assert "AUTO-GENERATED" in content
            assert "<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->" in content
            assert "<!-- VSTACK-META:" in content

    def test_generated_count_matches_expected(self, generated_dir: Path) -> None:
        """Test that generated count matches expected."""
        md_files = list(generated_dir.glob("*/SKILL.md"))
        assert len(md_files) == len(EXPECTED_CANONICAL_NAMES)
