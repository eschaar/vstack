"""Tests for agent generator behavior."""

from __future__ import annotations

from pathlib import Path

from vstack.agents.generator import AgentGenerator
from vstack.constants import ARTIFACTS_DOCS_ROOT


class TestAgentGenerator:
    """Test cases for AgentGenerator."""

    def test_generator_uses_agent_type(self) -> None:
        """Test that generator uses agent type."""
        gen = AgentGenerator()
        assert gen.config.type_name == "agent"

    def test_template_partials_returns_four_keys(self, tmp_path: Path) -> None:
        """Test that template_partials always returns all four placeholder keys."""
        tmpl_dir = tmp_path / "architect"
        tmpl_dir.mkdir()
        (tmpl_dir / "config.yaml").write_text("name: architect\n", encoding="utf-8")

        result = AgentGenerator().template_partials(tmpl_dir)

        assert set(result) == {
            "AGENT_ARTIFACTS_INPUT",
            "AGENT_ARTIFACTS_OUTPUT",
            "AGENT_ARTIFACTS_INPUT_COMMENTS",
            "AGENT_ARTIFACTS_OUTPUT_COMMENTS",
        }

    def test_template_partials_empty_when_no_artifacts_block(self, tmp_path: Path) -> None:
        """Test that all artifact placeholders are empty strings when config has no artifacts."""
        tmpl_dir = tmp_path / "plain"
        tmpl_dir.mkdir()
        (tmpl_dir / "config.yaml").write_text("name: plain\n", encoding="utf-8")

        result = AgentGenerator().template_partials(tmpl_dir)

        assert result["AGENT_ARTIFACTS_INPUT"] == ""
        assert result["AGENT_ARTIFACTS_OUTPUT"] == ""
        assert result["AGENT_ARTIFACTS_INPUT_COMMENTS"] == ""
        assert result["AGENT_ARTIFACTS_OUTPUT_COMMENTS"] == ""

    def test_template_partials_input_prefixed_with_docs_root(self, tmp_path: Path) -> None:
        """Test that input paths are prefixed with ARTIFACTS_DOCS_ROOT."""
        tmpl_dir = tmp_path / "architect"
        tmpl_dir.mkdir()
        (tmpl_dir / "config.yaml").write_text(
            "name: architect\nartifacts:\n  dir: architecture\n  input:\n    - product/**/*.md\n",
            encoding="utf-8",
        )

        result = AgentGenerator().template_partials(tmpl_dir)

        assert f"`{ARTIFACTS_DOCS_ROOT}/product/**/*.md`" in result["AGENT_ARTIFACTS_INPUT"]

    def test_template_partials_output_prefixed_with_root_and_dir(self, tmp_path: Path) -> None:
        """Test that output paths are prefixed with root/dir when dir is set."""
        tmpl_dir = tmp_path / "architect"
        tmpl_dir.mkdir()
        (tmpl_dir / "config.yaml").write_text(
            "name: architect\nartifacts:\n  dir: architecture\n  output:\n    - overview.md\n",
            encoding="utf-8",
        )

        result = AgentGenerator().template_partials(tmpl_dir)

        assert (
            f"`{ARTIFACTS_DOCS_ROOT}/architecture/overview.md`" in result["AGENT_ARTIFACTS_OUTPUT"]
        )

    def test_template_partials_output_verbatim_when_no_dir(self, tmp_path: Path) -> None:
        """Test that output paths are used verbatim when no dir is set."""
        tmpl_dir = tmp_path / "engineer"
        tmpl_dir.mkdir()
        (tmpl_dir / "config.yaml").write_text(
            "name: engineer\nartifacts:\n  output:\n    - path: ./src/**/*\n",
            encoding="utf-8",
        )

        result = AgentGenerator().template_partials(tmpl_dir)

        assert "`src/**/*`" in result["AGENT_ARTIFACTS_OUTPUT"]
        assert "docs/" not in result["AGENT_ARTIFACTS_OUTPUT"]

    def test_template_partials_dotslash_strips_prefix_with_dir(self, tmp_path: Path) -> None:
        """Test that ./path output items bypass dir prefix even when dir is set."""
        tmpl_dir = tmp_path / "tester"
        tmpl_dir.mkdir()
        (tmpl_dir / "config.yaml").write_text(
            "name: tester\nartifacts:\n  dir: reports\n  output:\n    - ./tests/**/*\n",
            encoding="utf-8",
        )

        result = AgentGenerator().template_partials(tmpl_dir)

        assert "`tests/**/*`" in result["AGENT_ARTIFACTS_OUTPUT"]
        assert "docs/reports/" not in result["AGENT_ARTIFACTS_OUTPUT"]

    def test_template_partials_input_comments_from_config(self, tmp_path: Path) -> None:
        """Test that input_comments config field populates AGENT_ARTIFACTS_INPUT_COMMENTS."""
        tmpl_dir = tmp_path / "custom"
        tmpl_dir.mkdir()
        (tmpl_dir / "config.yaml").write_text(
            "name: custom\nartifacts:\n  input_comments: 'Read in order.'\n",
            encoding="utf-8",
        )

        result = AgentGenerator().template_partials(tmpl_dir)

        assert result["AGENT_ARTIFACTS_INPUT_COMMENTS"] == "Read in order."

    def test_template_partials_output_comments_from_config(self, tmp_path: Path) -> None:
        """Test that output_comments config field populates AGENT_ARTIFACTS_OUTPUT_COMMENTS."""
        tmpl_dir = tmp_path / "custom"
        tmpl_dir.mkdir()
        (tmpl_dir / "config.yaml").write_text(
            "name: custom\nartifacts:\n  output_comments: 'See ADR-001.'\n",
            encoding="utf-8",
        )

        result = AgentGenerator().template_partials(tmpl_dir)

        assert result["AGENT_ARTIFACTS_OUTPUT_COMMENTS"] == "See ADR-001."

    def test_template_partials_handles_non_dict_artifacts_gracefully(self, tmp_path: Path) -> None:
        """Test that template_partials handles malformed (non-dict) artifacts gracefully."""
        tmpl_dir = tmp_path / "broken"
        tmpl_dir.mkdir()
        # When artifacts is a list rather than a dict mapping, the generator must not crash.
        (tmpl_dir / "config.yaml").write_text(
            "name: broken\nartifacts:\n  - foo\n  - bar\n", encoding="utf-8"
        )

        result = AgentGenerator().template_partials(tmpl_dir)

        assert result["AGENT_ARTIFACTS_INPUT"] == ""
        assert result["AGENT_ARTIFACTS_OUTPUT"] == ""

    def test_template_partials_handles_non_list_input_output_gracefully(
        self, tmp_path: Path
    ) -> None:
        """Test that scalar input/output values are treated as empty lists."""
        tmpl_dir = tmp_path / "scalar"
        tmpl_dir.mkdir()
        # After re-parsing a nested raw block, input or output may be scalar strings
        # if the indented content is malformed. Verify defensive guards hold.
        (tmpl_dir / "config.yaml").write_text(
            "name: scalar\nartifacts:\n  dir: architecture\n  input: not-a-list\n  output: not-a-list\n",
            encoding="utf-8",
        )

        result = AgentGenerator().template_partials(tmpl_dir)

        assert result["AGENT_ARTIFACTS_INPUT"] == ""
        assert result["AGENT_ARTIFACTS_OUTPUT"] == ""

    def test_product_has_no_input_section(self, tmp_path: Path) -> None:
        """Test that AGENT_ARTIFACTS_INPUT is empty for product (no input in config)."""
        tmpl_dir = tmp_path / "product"
        tmpl_dir.mkdir()
        (tmpl_dir / "config.yaml").write_text(
            "name: product\nartifacts:\n  dir: product\n  output:\n    - vision.md\n",
            encoding="utf-8",
        )

        result = AgentGenerator().template_partials(tmpl_dir)

        assert result["AGENT_ARTIFACTS_INPUT"] == ""
        assert "### output" in result["AGENT_ARTIFACTS_OUTPUT"]

    def test_template_partials_uses_custom_artifacts_root(self, tmp_path: Path) -> None:
        """Test that a custom artifacts_root replaces the default 'docs' prefix."""
        tmpl_dir = tmp_path / "architect"
        tmpl_dir.mkdir()
        (tmpl_dir / "config.yaml").write_text(
            "name: architect\nartifacts:\n  dir: architecture\n  input:\n    - product/**/*.md\n"
            "  output:\n    - overview.md\n",
            encoding="utf-8",
        )

        result = AgentGenerator(artifacts_root="documentation").template_partials(tmpl_dir)

        assert "`documentation/product/**/*.md`" in result["AGENT_ARTIFACTS_INPUT"]
        assert "`documentation/architecture/overview.md`" in result["AGENT_ARTIFACTS_OUTPUT"]
        assert "docs/" not in result["AGENT_ARTIFACTS_INPUT"]
        assert "docs/" not in result["AGENT_ARTIFACTS_OUTPUT"]


class TestResolveOutputEntries:
    """Unit tests for AgentGenerator._resolve_output_entries."""

    def test_plain_string_with_dir_gets_root_and_dir_prefix(self) -> None:
        """Test that plain string items are prefixed with root/dir when dir is set."""
        result = AgentGenerator._resolve_output_entries(["overview.md"], "docs", "architecture")
        assert result == [{"path": "docs/architecture/overview.md", "notes": ""}]

    def test_plain_string_without_dir_is_verbatim(self) -> None:
        """Test that plain string items are used verbatim when no dir is set."""
        result = AgentGenerator._resolve_output_entries(["src/**/*"], "docs", "")
        assert result == [{"path": "src/**/*", "notes": ""}]

    def test_non_string_non_dict_item_is_skipped(self) -> None:
        """Test that non-string, non-dict output items are silently skipped."""
        result = AgentGenerator._resolve_output_entries([42, None], "docs", "architecture")
        assert result == []

    def test_dotslash_prefix_strips_and_uses_verbatim(self) -> None:
        """Test that ./path items strip the ./ and bypass dir prefix."""
        result = AgentGenerator._resolve_output_entries(["./tests/**/*"], "docs", "reports")
        assert result == [{"path": "tests/**/*", "notes": ""}]

    def test_dict_item_with_notes_and_dir(self) -> None:
        """Test that dict items with notes are resolved with dir prefix."""
        result = AgentGenerator._resolve_output_entries(
            [{"path": "ux.md", "notes": "frontend only"}], "docs", "design"
        )
        assert result == [{"path": "docs/design/ux.md", "notes": "frontend only"}]

    def test_dict_item_with_dotslash_path(self) -> None:
        """Test that dict items with ./path bypass the dir prefix."""
        result = AgentGenerator._resolve_output_entries(
            [{"path": "./issues/rca.md", "notes": "on issue"}], "docs", "reports"
        )
        assert result == [{"path": "issues/rca.md", "notes": "on issue"}]

    def test_glob_with_slash_is_relative_to_dir(self) -> None:
        """Test that glob paths like adr/*.md are prefixed with root/dir."""
        result = AgentGenerator._resolve_output_entries(["adr/*.md"], "docs", "architecture")
        assert result == [{"path": "docs/architecture/adr/*.md", "notes": ""}]

    def test_double_glob_relative_to_dir(self) -> None:
        """Test that **/*.md is prefixed with root/dir when dir is set."""
        result = AgentGenerator._resolve_output_entries(["**/*.md"], "docs", "reports")
        assert result == [{"path": "docs/reports/**/*.md", "notes": ""}]


class TestBuildTable:
    """Unit tests for AgentGenerator._build_table."""

    def test_single_column_when_no_notes(self) -> None:
        """Test that a single-column table is produced when no entry has notes."""
        table = AgentGenerator._build_table([{"path": "docs/foo.md", "notes": ""}])
        lines = table.splitlines()
        assert lines[0].startswith("| Artifact")
        assert lines[0].count("|") == 2
        assert "`docs/foo.md`" in lines[2]

    def test_two_column_when_any_entry_has_notes(self) -> None:
        """Test that a two-column table is produced when at least one entry has notes."""
        entries = [
            {"path": "docs/foo.md", "notes": ""},
            {"path": "docs/bar.md", "notes": "important"},
        ]
        table = AgentGenerator._build_table(entries)
        assert "Notes" in table.splitlines()[0]

    def test_rows_have_equal_length(self) -> None:
        """Test that all rows in the table have equal string length."""
        entries = [
            {"path": "docs/a.md", "notes": ""},
            {"path": "docs/b.md", "notes": "a very long note here"},
        ]
        table = AgentGenerator._build_table(entries)
        row_lengths = {len(line) for line in table.splitlines()}
        assert len(row_lengths) == 1


class TestBuildSection:
    """Unit tests for AgentGenerator._build_section."""

    def test_returns_empty_string_when_no_entries(self) -> None:
        """Test that an empty string is returned when entries list is empty."""
        assert AgentGenerator._build_section("input", []) == ""

    def test_includes_heading_and_table(self) -> None:
        """Test that the section includes the heading and table."""
        section = AgentGenerator._build_section("input", [{"path": "docs/a.md", "notes": ""}])
        assert section.startswith("### input")
        assert "`docs/a.md`" in section

    def test_heading_matches_argument(self) -> None:
        """Test that the section heading matches the heading argument."""
        section = AgentGenerator._build_section("output", [{"path": "docs/b.md", "notes": ""}])
        assert "### output" in section
