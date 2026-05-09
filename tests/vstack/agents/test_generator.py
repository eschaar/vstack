"""Tests for agent generator behavior."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from vstack.agents.generator import AgentGenerator
from vstack.constants import ARTIFACTS_DOCS_ROOT


class TestAgentGenerator:
    """Tests for AgentGenerator and all its methods."""

    def test_generator_uses_agent_type(self) -> None:
        """Test that generator uses agent type."""
        gen = AgentGenerator()
        assert gen.config.type_name == "agent"

    class TestTemplatePartials:
        """Tests for AgentGenerator.template_partials."""

        def test_returns_five_keys(self, tmp_path: Path) -> None:
            """template_partials always returns all five placeholder keys."""
            tmpl_dir = tmp_path / "architect"
            tmpl_dir.mkdir()
            (tmpl_dir / "config.yaml").write_text("name: architect\n", encoding="utf-8")

            result = AgentGenerator().template_partials(tmpl_dir)

            assert set(result) == {
                "AGENT_ARTIFACTS_INPUT",
                "AGENT_ARTIFACTS_OUTPUT",
                "AGENT_ARTIFACTS_INPUT_COMMENTS",
                "AGENT_ARTIFACTS_OUTPUT_COMMENTS",
                "AGENT_ARTIFACTS_BASELINE",
            }

        def test_empty_when_no_artifacts_block(self, tmp_path: Path) -> None:
            """All artifact placeholders are empty strings when config has no artifacts."""
            tmpl_dir = tmp_path / "plain"
            tmpl_dir.mkdir()
            (tmpl_dir / "config.yaml").write_text("name: plain\n", encoding="utf-8")

            result = AgentGenerator().template_partials(tmpl_dir)

            assert result["AGENT_ARTIFACTS_INPUT"] == ""
            assert result["AGENT_ARTIFACTS_OUTPUT"] == ""
            assert result["AGENT_ARTIFACTS_INPUT_COMMENTS"] == ""
            assert result["AGENT_ARTIFACTS_OUTPUT_COMMENTS"] == ""

        def test_input_prefixed_with_docs_root(self, tmp_path: Path) -> None:
            """Input paths are prefixed with ARTIFACTS_DOCS_ROOT."""
            tmpl_dir = tmp_path / "architect"
            tmpl_dir.mkdir()
            (tmpl_dir / "config.yaml").write_text(
                "name: architect\ndefaults:\n  artifacts:\n    dir: architecture\n    input:\n      - product/**/*.md\n",
                encoding="utf-8",
            )

            result = AgentGenerator().template_partials(tmpl_dir)

            assert f"`{ARTIFACTS_DOCS_ROOT}/product/**/*.md`" in result["AGENT_ARTIFACTS_INPUT"]

        def test_output_prefixed_with_root_and_dir(self, tmp_path: Path) -> None:
            """Output paths are prefixed with root/dir when dir is set."""
            tmpl_dir = tmp_path / "architect"
            tmpl_dir.mkdir()
            (tmpl_dir / "config.yaml").write_text(
                "name: architect\ndefaults:\n  artifacts:\n    dir: architecture\n    output:\n      - overview.md\n",
                encoding="utf-8",
            )

            result = AgentGenerator().template_partials(tmpl_dir)

            assert (
                f"`{ARTIFACTS_DOCS_ROOT}/architecture/overview.md`"
                in result["AGENT_ARTIFACTS_OUTPUT"]
            )

        def test_output_verbatim_when_no_dir(self, tmp_path: Path) -> None:
            """Output paths are used verbatim when no dir is set."""
            tmpl_dir = tmp_path / "engineer"
            tmpl_dir.mkdir()
            (tmpl_dir / "config.yaml").write_text(
                "name: engineer\ndefaults:\n  artifacts:\n    output:\n      - path: ./src/**/*\n",
                encoding="utf-8",
            )

            result = AgentGenerator().template_partials(tmpl_dir)

            assert "`src/**/*`" in result["AGENT_ARTIFACTS_OUTPUT"]
            assert "docs/" not in result["AGENT_ARTIFACTS_OUTPUT"]

        def test_dotslash_strips_prefix_with_dir(self, tmp_path: Path) -> None:
            """./path output items bypass dir prefix even when dir is set."""
            tmpl_dir = tmp_path / "tester"
            tmpl_dir.mkdir()
            (tmpl_dir / "config.yaml").write_text(
                "name: tester\ndefaults:\n  artifacts:\n    dir: reports\n    output:\n      - ./tests/**/*\n",
                encoding="utf-8",
            )

            result = AgentGenerator().template_partials(tmpl_dir)

            assert "`tests/**/*`" in result["AGENT_ARTIFACTS_OUTPUT"]
            assert "docs/reports/" not in result["AGENT_ARTIFACTS_OUTPUT"]

        def test_input_comments_from_config(self, tmp_path: Path) -> None:
            """input_comments config field populates AGENT_ARTIFACTS_INPUT_COMMENTS."""
            tmpl_dir = tmp_path / "custom"
            tmpl_dir.mkdir()
            (tmpl_dir / "config.yaml").write_text(
                "name: custom\ndefaults:\n  artifacts:\n    input_comments: 'Read in order.'\n",
                encoding="utf-8",
            )

            result = AgentGenerator().template_partials(tmpl_dir)

            assert result["AGENT_ARTIFACTS_INPUT_COMMENTS"] == "Read in order."

        def test_output_comments_from_config(self, tmp_path: Path) -> None:
            """output_comments config field populates AGENT_ARTIFACTS_OUTPUT_COMMENTS."""
            tmpl_dir = tmp_path / "custom"
            tmpl_dir.mkdir()
            (tmpl_dir / "config.yaml").write_text(
                "name: custom\ndefaults:\n  artifacts:\n    output_comments: 'See ADR-001.'\n",
                encoding="utf-8",
            )

            result = AgentGenerator().template_partials(tmpl_dir)

            assert result["AGENT_ARTIFACTS_OUTPUT_COMMENTS"] == "See ADR-001."

        def test_handles_non_dict_artifacts_gracefully(self, tmp_path: Path) -> None:
            """template_partials handles malformed (non-dict) artifacts without crashing."""
            tmpl_dir = tmp_path / "broken"
            tmpl_dir.mkdir()
            (tmpl_dir / "config.yaml").write_text(
                "name: broken\ndefaults:\n  artifacts:\n    - foo\n    - bar\n", encoding="utf-8"
            )

            result = AgentGenerator().template_partials(tmpl_dir)

            assert result["AGENT_ARTIFACTS_INPUT"] == ""
            assert result["AGENT_ARTIFACTS_OUTPUT"] == ""

        def test_handles_non_list_input_output_gracefully(self, tmp_path: Path) -> None:
            """Scalar input/output values are treated as empty lists."""
            tmpl_dir = tmp_path / "scalar"
            tmpl_dir.mkdir()
            (tmpl_dir / "config.yaml").write_text(
                "name: scalar\ndefaults:\n  artifacts:\n    dir: architecture\n    input: not-a-list\n    output: not-a-list\n",
                encoding="utf-8",
            )

            result = AgentGenerator().template_partials(tmpl_dir)

            assert result["AGENT_ARTIFACTS_INPUT"] == ""
            assert result["AGENT_ARTIFACTS_OUTPUT"] == ""

        def test_product_has_no_input_section(self, tmp_path: Path) -> None:
            """AGENT_ARTIFACTS_INPUT is empty for product (no input in config)."""
            tmpl_dir = tmp_path / "product"
            tmpl_dir.mkdir()
            (tmpl_dir / "config.yaml").write_text(
                "name: product\ndefaults:\n  artifacts:\n    dir: product\n    output:\n      - vision.md\n",
                encoding="utf-8",
            )

            result = AgentGenerator().template_partials(tmpl_dir)

            assert result["AGENT_ARTIFACTS_INPUT"] == ""
            assert "### output" in result["AGENT_ARTIFACTS_OUTPUT"]

        def test_uses_custom_artifacts_root(self, tmp_path: Path) -> None:
            """A custom artifacts_root replaces the default 'docs' prefix."""
            tmpl_dir = tmp_path / "architect"
            tmpl_dir.mkdir()
            (tmpl_dir / "config.yaml").write_text(
                "name: architect\ndefaults:\n  artifacts:\n    dir: architecture\n    input:\n      - product/**/*.md\n"
                "    output:\n      - overview.md\n",
                encoding="utf-8",
            )

            result = AgentGenerator(artifacts_root="documentation").template_partials(tmpl_dir)

            assert "`documentation/product/**/*.md`" in result["AGENT_ARTIFACTS_INPUT"]
            assert "`documentation/architecture/overview.md`" in result["AGENT_ARTIFACTS_OUTPUT"]
            assert "docs/" not in result["AGENT_ARTIFACTS_INPUT"]
            assert "docs/" not in result["AGENT_ARTIFACTS_OUTPUT"]

    class TestExtractDefaults:
        """Tests for AgentGenerator._extract_defaults."""

        def test_returns_empty_dict_when_no_defaults_key(self) -> None:
            """Returns an empty dict when the config has no defaults key."""
            assert AgentGenerator()._extract_defaults({}) == {}

        def test_returns_empty_dict_when_defaults_is_none(self) -> None:
            """Returns an empty dict when defaults is None."""
            assert AgentGenerator()._extract_defaults({"defaults": None}) == {}

        def test_returns_dict_as_is(self) -> None:
            """Returns the dict unchanged when defaults is already a plain dict."""
            assert AgentGenerator()._extract_defaults({"defaults": {"artifacts": {}}}) == {
                "artifacts": {}
            }

        def test_returns_empty_dict_when_defaults_is_non_dict_non_string(self) -> None:
            """Returns empty dict when defaults is neither a string nor a dict."""
            assert AgentGenerator()._extract_defaults({"defaults": 42}) == {}

        def test_returns_empty_dict_for_non_dict_string(self) -> None:
            """Non-dict values (including strings) return an empty dict.

            PyYAML always produces a dict for a ``defaults:`` mapping block, so
            a string value is not produced in normal operation.  The method still
            handles it defensively and returns ``{}``.
            """
            assert (
                AgentGenerator()._extract_defaults({"defaults": "  artifacts:\n    dir: design\n"})
                == {}
            )

    class TestLoadArtifactConfig:
        """Tests for AgentGenerator.load_artifact_config."""

        def test_handoffs_block_as_list_yields_empty_prompt(self, tmp_path: Path) -> None:
            """When handoffs parses as a list (not a dict), handoff_prompt falls back to empty."""
            tmpl_dir = tmp_path / "product"
            tmpl_dir.mkdir()
            (tmpl_dir / "config.yaml").write_text(
                "defaults:\n  handoffs:\n    - prompt: foo\n",
                encoding="utf-8",
            )
            config = AgentGenerator().load_artifact_config(tmpl_dir)
            assert "handoffs" not in config

        def test_handoffs_block_not_a_dict_or_string_yields_empty_prompt(
            self, tmp_path: Path
        ) -> None:
            """When handoffs_block is neither a dict nor a str, handoff_prompt falls back to empty."""
            tmpl_dir = tmp_path / "product"
            tmpl_dir.mkdir()
            # Inject a stage that sets handoffs to a plain list value so the block-scalar
            # path is triggered but is not a dict — a bare list under defaults.handoffs.
            # Write config with an inline list under handoffs to hit the else branch.
            (tmpl_dir / "config.yaml").write_text(
                "name: product\ndefaults:\n  handoffs: []\n",
                encoding="utf-8",
            )
            config = AgentGenerator().load_artifact_config(tmpl_dir)
            assert "handoffs" not in config

        def test_handoffs_injected_when_workflow_resolves(self, tmp_path: Path) -> None:
            """Resolved handoffs are injected into config when workflow stages are present."""
            tmpl_dir = tmp_path / "architect"
            tmpl_dir.mkdir()
            (tmpl_dir / "config.yaml").write_text(
                "name: architect\n",
                encoding="utf-8",
            )
            stages: list[dict[str, Any]] = [
                {
                    "role": "architect",
                    "gate": "required",
                    "handoffs": [{"prompt": "Arch done.", "agent": "", "label": ""}],
                },
                {"role": "designer", "gate": "optional", "handoffs": []},
            ]
            gen = AgentGenerator(workflow_stages=stages)
            config = gen.load_artifact_config(tmpl_dir)
            assert "handoffs" in config
            assert config["handoffs"][0]["agent"] == "designer"

    class TestResolveOutputEntries:
        """Tests for AgentGenerator._resolve_output_entries."""

        def test_plain_string_with_dir_gets_root_and_dir_prefix(self) -> None:
            """Plain string items are prefixed with root/dir when dir is set."""
            result = AgentGenerator()._resolve_output_entries(["overview.md"], "architecture")
            assert result == [
                {"path": "docs/architecture/overview.md", "notes": "", "baseline": False}
            ]

        def test_plain_string_without_dir_is_verbatim(self) -> None:
            """Plain string items are used verbatim when no dir is set."""
            result = AgentGenerator()._resolve_output_entries(["src/**/*"], "")
            assert result == [{"path": "src/**/*", "notes": "", "baseline": False}]

        def test_non_string_non_dict_item_is_skipped(self) -> None:
            """Non-string, non-dict output items are silently skipped."""
            result = AgentGenerator()._resolve_output_entries([42, None], "architecture")
            assert result == []

        def test_dotslash_prefix_strips_and_uses_verbatim(self) -> None:
            """./path items strip the ./ and bypass dir prefix."""
            result = AgentGenerator()._resolve_output_entries(["./tests/**/*"], "reports")
            assert result == [{"path": "tests/**/*", "notes": "", "baseline": False}]

        def test_dict_item_with_notes_and_dir(self) -> None:
            """Dict items with notes are resolved with dir prefix."""
            result = AgentGenerator()._resolve_output_entries(
                [{"path": "ux.md", "notes": "frontend only"}], "design"
            )
            assert result == [
                {"path": "docs/design/ux.md", "notes": "frontend only", "baseline": False}
            ]

        def test_dict_item_with_dotslash_path(self) -> None:
            """Dict items with ./path bypass the dir prefix."""
            result = AgentGenerator()._resolve_output_entries(
                [{"path": "./issues/rca.md", "notes": "on issue"}], "reports"
            )
            assert result == [{"path": "issues/rca.md", "notes": "on issue", "baseline": False}]

        def test_glob_with_slash_is_relative_to_dir(self) -> None:
            """Glob paths like adr/*.md are prefixed with root/dir."""
            result = AgentGenerator()._resolve_output_entries(["adr/*.md"], "architecture")
            assert result == [
                {"path": "docs/architecture/adr/*.md", "notes": "", "baseline": False}
            ]

        def test_double_glob_relative_to_dir(self) -> None:
            """**/*.md is prefixed with root/dir when dir is set."""
            result = AgentGenerator()._resolve_output_entries(["**/*.md"], "reports")
            assert result == [{"path": "docs/reports/**/*.md", "notes": "", "baseline": False}]

    class TestResolveHandoffs:
        """Tests for AgentGenerator._resolve_handoffs."""

        def test_returns_empty_when_no_workflow_and_no_prompt(self) -> None:
            """Returns empty list when no workflow is configured and no prompt given."""
            assert AgentGenerator()._resolve_handoffs("architect", "") == []

        def test_no_handoff_without_workflow(self) -> None:
            """Returns empty list when no workflow is configured, even with a prompt.

            A handoff without an explicit ``agent:`` target is invalid per the
            VS Code agent schema, so none is emitted when no workflow is configured.
            """
            assert AgentGenerator()._resolve_handoffs("architect", "Do some work.") == []

        def test_with_workflow_finds_next_role(self) -> None:
            """Returns handoff with correct next agent when workflow is configured."""
            stages: list[dict[str, Any]] = [
                {
                    "role": "product",
                    "gate": "required",
                    "handoffs": [{"prompt": "Product done.", "agent": "", "label": ""}],
                },
                {
                    "role": "architect",
                    "gate": "required",
                    "handoffs": [{"prompt": "Arch done.", "agent": "", "label": ""}],
                },
                {
                    "role": "designer",
                    "gate": "optional",
                    "handoffs": [{"prompt": "Design done.", "agent": "", "label": ""}],
                },
            ]
            gen = AgentGenerator(workflow_stages=stages)
            result = gen._resolve_handoffs("architect", "Arch done.")
            assert len(result) == 1
            assert result[0]["agent"] == "designer"
            assert result[0]["label"] == "Go to next stage: Designer"

        def test_last_stage_returns_empty(self) -> None:
            """Returns empty list when the agent is the last stage in the workflow."""
            stages: list[dict[str, Any]] = [
                {
                    "role": "architect",
                    "gate": "required",
                    "handoffs": [{"prompt": "Arch done.", "agent": "", "label": ""}],
                },
                {"role": "release", "gate": "required", "handoffs": []},
            ]
            gen = AgentGenerator(workflow_stages=stages)
            assert gen._resolve_handoffs("release", "") == []

        def test_unknown_role_returns_empty(self) -> None:
            """Returns empty list when the agent role is not found in workflow stages."""
            stages: list[dict[str, Any]] = [
                {
                    "role": "product",
                    "gate": "required",
                    "handoffs": [{"prompt": "Done.", "agent": "", "label": ""}],
                }
            ]
            gen = AgentGenerator(workflow_stages=stages)
            assert gen._resolve_handoffs("unknown", "Some prompt.") == []

        def test_workflow_prompt_used_as_fallback(self) -> None:
            """Uses the workflow handoffs[0].prompt when the agent's own prompt is empty."""
            stages: list[dict[str, Any]] = [
                {
                    "role": "engineer",
                    "gate": "required",
                    "handoffs": [{"prompt": "From workflow.", "agent": "", "label": ""}],
                },
                {"role": "tester", "gate": "required", "handoffs": []},
            ]
            gen = AgentGenerator(workflow_stages=stages)
            result = gen._resolve_handoffs("engineer", "")
            assert len(result) == 1
            assert "From workflow." in result[0]["prompt"]

        def test_multiple_handoffs_per_stage(self) -> None:
            """All handoff entries are returned when a stage defines multiple."""
            stages: list[dict[str, Any]] = [
                {
                    "role": "architect",
                    "gate": "required",
                    "handoffs": [
                        {"prompt": "Go to designer.", "agent": "", "label": ""},
                        {
                            "prompt": "Skip to engineer.",
                            "agent": "engineer",
                            "label": "Skip design",
                        },
                    ],
                },
                {"role": "designer", "gate": "optional", "handoffs": []},
                {"role": "engineer", "gate": "required", "handoffs": []},
            ]
            gen = AgentGenerator(workflow_stages=stages)
            result = gen._resolve_handoffs("architect", "")
            assert len(result) == 2
            assert result[0]["agent"] == "designer"
            assert result[1]["agent"] == "engineer"
            assert result[1]["label"] == "Skip design"

        def test_empty_workflow_prompt_returns_empty(self) -> None:
            """Returns empty when both agent prompt and workflow handoffs prompts are empty."""
            stages: list[dict[str, Any]] = [
                {
                    "role": "engineer",
                    "gate": "required",
                    "handoffs": [{"prompt": "", "agent": "", "label": ""}],
                },
                {"role": "tester", "gate": "required", "handoffs": []},
            ]
            gen = AgentGenerator(workflow_stages=stages)
            assert gen._resolve_handoffs("engineer", "") == []

        def test_non_list_stage_handoffs_returns_empty(self) -> None:
            """Returns empty list when stage handoffs value is not a list."""
            stages: list[dict[str, Any]] = [
                {"role": "engineer", "gate": "required", "handoffs": "bad-value"},
                {"role": "tester", "gate": "required", "handoffs": []},
            ]
            gen = AgentGenerator(workflow_stages=stages)
            assert gen._resolve_handoffs("engineer", "") == []

        def test_non_dict_handoff_entry_is_skipped(self) -> None:
            """Non-dict handoff entries are skipped."""
            stages: list[dict[str, Any]] = [
                {
                    "role": "engineer",
                    "gate": "required",
                    "handoffs": ["not-a-dict", {"prompt": "Go.", "agent": "", "label": ""}],
                },
                {"role": "tester", "gate": "required", "handoffs": []},
            ]
            gen = AgentGenerator(workflow_stages=stages)
            result = gen._resolve_handoffs("engineer", "")
            assert len(result) == 1
            assert result[0]["agent"] == "tester"

    class TestBuildHandoffs:
        """Tests for AgentGenerator._build_handoffs (compatibility shim)."""

        def test_returns_empty_string_when_no_prompt(self) -> None:
            """Returns empty string when no workflow and no prompt."""
            assert AgentGenerator()._build_handoffs("architect", "") == ""

        def test_returns_empty_string_without_workflow(self) -> None:
            """Returns empty string when no workflow is configured, even with a prompt."""
            assert AgentGenerator()._build_handoffs("architect", "Work done.") == ""

        def test_returns_handoff_string_with_agent(self) -> None:
            """Returns handoffs block with agent key when workflow is configured."""
            stages: list[dict[str, Any]] = [
                {
                    "role": "architect",
                    "gate": "required",
                    "handoffs": [{"prompt": "", "agent": "", "label": ""}],
                },
                {"role": "designer", "gate": "optional", "handoffs": []},
            ]
            gen = AgentGenerator(workflow_stages=stages)
            result = gen._build_handoffs("architect", "Work done.")
            assert "handoffs:" in result
            assert "agent: designer" in result

    class TestBuildTable:
        """Tests for AgentGenerator._build_table."""

        def test_single_column_when_no_notes(self) -> None:
            """A single-column Artifact table is produced when no entry has notes."""
            table = AgentGenerator()._build_table(
                [{"path": "docs/foo.md", "notes": "", "baseline": False}]
            )
            lines = table.splitlines()
            assert lines[0].startswith("| Artifact")
            assert lines[0].count("|") == 2
            assert "`docs/foo.md`" in lines[2]

        def test_two_column_when_any_entry_has_notes(self) -> None:
            """A two-column Artifact | Notes table is produced when any entry has notes."""
            entries: list[dict[str, str | bool]] = [
                {"path": "docs/foo.md", "notes": "", "baseline": False},
                {"path": "docs/bar.md", "notes": "important", "baseline": False},
            ]
            table = AgentGenerator()._build_table(entries)
            assert "Notes" in table.splitlines()[0]

        def test_rows_have_equal_length(self) -> None:
            """All rows in the table have equal string length."""
            entries: list[dict[str, str | bool]] = [
                {"path": "docs/a.md", "notes": "", "baseline": False},
                {"path": "docs/b.md", "notes": "a very long note here", "baseline": False},
            ]
            table = AgentGenerator()._build_table(entries)
            row_lengths = {len(line) for line in table.splitlines()}
            assert len(row_lengths) == 1

    class TestBuildSection:
        """Tests for AgentGenerator._build_section and _build_baseline_section."""

        def test_returns_empty_string_when_no_entries(self) -> None:
            """An empty string is returned when entries list is empty."""
            assert AgentGenerator()._build_section("input", []) == ""

        def test_includes_heading_and_table(self) -> None:
            """The section includes the heading and table."""
            section = AgentGenerator()._build_section(
                "input", [{"path": "docs/a.md", "notes": "", "baseline": False}]
            )
            assert section.startswith("### input")
            assert "`docs/a.md`" in section

        def test_heading_matches_argument(self) -> None:
            """The section heading matches the heading argument."""
            section = AgentGenerator()._build_section(
                "output", [{"path": "docs/b.md", "notes": ""}]
            )
            assert "### output" in section

        def test_baseline_section_with_entries_contains_heading(self) -> None:
            """_build_baseline_section returns a section with the fixed heading when entries given."""
            entries: list[dict[str, str | bool]] = [
                {"path": "docs/architecture/overview.md", "notes": "", "baseline": True}
            ]
            section = AgentGenerator()._build_baseline_section(entries)
            assert "### baseline docs you maintain" in section
            assert "`docs/architecture/overview.md`" in section

        def test_baseline_section_empty_when_no_entries(self) -> None:
            """_build_baseline_section returns an empty string when entries list is empty."""
            assert AgentGenerator()._build_baseline_section([]) == ""
