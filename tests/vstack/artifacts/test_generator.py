"""Tests for generic artifact generation."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from vstack.agents.config import AGENT_TYPE
from vstack.artifacts.generator import GenericArtifactGenerator
from vstack.skills.config import SKILL_TYPE


class TestGenericArtifactGenerator:
    """Test cases for GenericArtifactGenerator."""

    def _make_skill_gen(self, tmp_path: Path) -> GenericArtifactGenerator:
        """Internal helper to make skill gen."""
        return GenericArtifactGenerator(SKILL_TYPE, tmp_path / "templates")

    def test_resolve_placeholders_replaces_known_token(self) -> None:
        """Test that resolve placeholders replaces known token."""
        assert (
            GenericArtifactGenerator.resolve_placeholders("hi {{NAME}}", {"NAME": "vstack"})
            == "hi vstack"
        )

    def test_find_unresolved_detects_tokens(self) -> None:
        """Test that find unresolved detects tokens."""
        assert GenericArtifactGenerator.find_unresolved("{{FOO}} {{BAR}}") == ["FOO", "BAR"]

    def test_load_partials_reads_files(self, tmp_path: Path) -> None:
        """Test that load partials reads files."""
        partials = tmp_path / "templates" / "skills" / "_partials"
        partials.mkdir(parents=True)
        (partials / "skill-context.md").write_text("ctx", encoding="utf-8")
        gen = self._make_skill_gen(tmp_path)
        loaded = gen.load_partials()
        assert loaded["SKILL_CONTEXT"] == "ctx"

    def test_find_templates_ignores_underscored_dirs(self, tmp_path: Path) -> None:
        """Test that find templates ignores underscored dirs."""
        a = tmp_path / "templates" / "skills" / "vision"
        a.mkdir(parents=True)
        (a / "template.md").write_text("x", encoding="utf-8")
        b = tmp_path / "templates" / "skills" / "_partials"
        b.mkdir(parents=True)
        gen = self._make_skill_gen(tmp_path)
        names = [p.name for p in gen.find_templates()]
        assert names == ["vision"]

    def test_render_produces_rendered_artifact(self, tmp_path: Path) -> None:
        """Test that render produces rendered artifact."""
        (tmp_path / "templates" / "skills" / "_partials").mkdir(parents=True)
        (tmp_path / "templates" / "skills" / "_partials" / "skill-context.md").write_text(
            "context", encoding="utf-8"
        )
        tmpl_dir = tmp_path / "templates" / "skills" / "vision"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "template.md").write_text(
            textwrap.dedent(
                """\
                ---
                name: vision
                version: 1.0.0
                description: Test vision skill
                ---

                {{SKILL_CONTEXT}}
                """
            ),
            encoding="utf-8",
        )

        artifact = self._make_skill_gen(tmp_path).render(tmpl_dir)
        assert artifact.name == "vision"
        assert "AUTO-GENERATED" in artifact.content
        assert artifact.unresolved == []

    def test_generate_writes_files(self, tmp_path: Path) -> None:
        """Test that generate writes files."""
        tmpl_dir = tmp_path / "templates" / "skills" / "alpha"
        tmpl_dir.mkdir(parents=True)
        (tmp_path / "templates" / "skills" / "_partials").mkdir(parents=True)
        (tmpl_dir / "template.md").write_text(
            "---\nname: alpha\nversion: 1.0.0\ndescription: d\n---\n{{SKILL_CONTEXT}}\n",
            encoding="utf-8",
        )
        (tmp_path / "templates" / "skills" / "_partials" / "skill-context.md").write_text(
            "context", encoding="utf-8"
        )
        out = tmp_path / "output"
        result = self._make_skill_gen(tmp_path).generate(out)
        assert (out / "alpha" / "SKILL.md").exists()
        assert len(result.artifacts) == 1

    def test_verify_input_rejects_unknown_placeholder_when_registry_enabled(
        self, tmp_path: Path
    ) -> None:
        """Test that verify input rejects unknown placeholder when registry enabled."""
        tmpl_dir = tmp_path / "templates" / "skills" / "vision"
        tmpl_dir.mkdir(parents=True)
        (tmp_path / "templates" / "skills" / "_partials").mkdir(parents=True)
        (tmpl_dir / "template.md").write_text(
            "---\nname: vision\nversion: 1.0.0\ndescription: d\n---\n{{UNKNOWN_TOKEN}}\n",
            encoding="utf-8",
        )
        cfg = type(SKILL_TYPE)(
            **{**SKILL_TYPE.__dict__, "placeholders": {"SKILL_CONTEXT": "skill-context.md"}}
        )
        gen = GenericArtifactGenerator(cfg, tmp_path / "templates")
        result = gen.verify_input(expected_names=["vision"])
        assert not result.ok
        assert any("unknown placeholder" in m.message for m in result.messages if m.level == "fail")

    def test_verify_input_accepts_registered_placeholder_with_template_reference(
        self, tmp_path: Path
    ) -> None:
        """Test that verify input accepts registered placeholder with template reference."""
        tmpl_dir = tmp_path / "templates" / "skills" / "vision"
        tmpl_dir.mkdir(parents=True)
        (tmp_path / "templates" / "skills" / "_partials").mkdir(parents=True)
        (tmpl_dir / "template.md").write_text(
            "---\nname: vision\nversion: 1.0.0\ndescription: d\n---\n{{SKILL_CONTEXT}}\n",
            encoding="utf-8",
        )
        cfg = type(SKILL_TYPE)(
            **{**SKILL_TYPE.__dict__, "placeholders": {"SKILL_CONTEXT": "skill-context.md"}}
        )
        gen = GenericArtifactGenerator(cfg, tmp_path / "templates")
        result = gen.verify_input(expected_names=["vision"])
        assert result.ok
        assert any(
            "placeholder SKILL_CONTEXT mapped to skill-context.md" in m.message
            for m in result.messages
            if m.level == "pass"
        )

    def test_verify_output_detects_missing_file(self, tmp_path: Path) -> None:
        """Test that verify output detects missing file."""
        out = tmp_path / "out"
        out.mkdir()
        result = self._make_skill_gen(tmp_path).verify_output(out, expected_names=["vision"])
        assert not result.ok

    def test_agent_verify_input_uses_schema_for_bool_field(self, tmp_path: Path) -> None:
        """Test that agent verify input uses schema for bool field."""
        tmpl_dir = tmp_path / "templates" / "agents" / "writer"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "template.md").write_text("# writer\nbody\n", encoding="utf-8")
        (tmpl_dir / "config.yaml").write_text(
            "name: writer\ndescription: A writer agent\nuser-invocable: yes\n",
            encoding="utf-8",
        )
        gen = GenericArtifactGenerator(AGENT_TYPE, tmp_path / "templates")
        result = gen.verify_input(expected_names=["writer"])
        assert not result.ok
        assert any("user-invocable" in m.message for m in result.messages if m.level == "fail")

    def test_render_raises_when_add_frontmatter_but_schema_missing(self, tmp_path: Path) -> None:
        """Test that render raises when add frontmatter but schema missing."""
        cfg = AGENT_TYPE
        monkey_cfg = type(cfg)(**{**cfg.__dict__, "frontmatter_schema": None})
        gen = GenericArtifactGenerator(monkey_cfg, tmp_path / "templates")
        tmpl_dir = tmp_path / "templates" / "agents" / "x"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "template.md").write_text("---\nname: x\n---\nbody\n", encoding="utf-8")
        with pytest.raises(ValueError):
            gen.render(tmpl_dir)

    def test_render_adds_frontmatter_from_config_when_template_has_none(
        self, tmp_path: Path
    ) -> None:
        """Test that render adds frontmatter from config when template has none."""
        tmpl_dir = tmp_path / "templates" / "agents" / "writer"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "template.md").write_text("# writer\n", encoding="utf-8")
        (tmpl_dir / "config.yaml").write_text("name: writer\ndescription: d\n", encoding="utf-8")
        gen = GenericArtifactGenerator(AGENT_TYPE, tmp_path / "templates")
        artifact = gen.render(tmpl_dir)
        assert artifact.content.startswith("---\n")
        assert "name: writer" in artifact.content

    def test_render_reads_multiline_handoff_prompt_from_config(self, tmp_path: Path) -> None:
        """Test that render reads multiline handoff prompt from config."""
        tmpl_dir = tmp_path / "templates" / "agents" / "architect"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "template.md").write_text("# architect\n", encoding="utf-8")
        (tmpl_dir / "config.yaml").write_text(
            textwrap.dedent(
                """\
                name: architect
                description: >
                                    Senior architect profile focused on reliability, decomposition,
                                    bounded context design, operability, and migration-safe change planning.
                handoffs:
                  - label: Continue to design
                    agent: designer
                    prompt: |
                                            Translate architecture into concrete contracts including
                                            failures, retries, timeouts, validation constraints,
                                            and explicit edge-case behavior.
                    send: false
                """
            ),
            encoding="utf-8",
        )
        gen = GenericArtifactGenerator(AGENT_TYPE, tmp_path / "templates")
        artifact = gen.render(tmpl_dir)

        assert "description: >-" in artifact.content
        assert "handoffs:" in artifact.content
        assert "prompt: >-" in artifact.content

    def test_render_multiline_frontmatter_disabled_when_type_config_off(
        self, tmp_path: Path
    ) -> None:
        """Test that render multiline frontmatter disabled when type config off."""
        cfg = type(AGENT_TYPE)(**{**AGENT_TYPE.__dict__, "preserve_multiline_frontmatter": False})
        tmpl_dir = tmp_path / "templates" / "agents" / "architect"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "template.md").write_text("# architect\n", encoding="utf-8")
        (tmpl_dir / "config.yaml").write_text(
            textwrap.dedent(
                """\
                name: architect
                description: >
                  First line
                  second line
                handoffs:
                  - label: Continue to design
                    agent: designer
                    prompt: >
                      Translate architecture into concrete interfaces and include
                      error and edge-case behavior in design contracts.
                """
            ),
            encoding="utf-8",
        )
        gen = GenericArtifactGenerator(cfg, tmp_path / "templates")
        artifact = gen.render(tmpl_dir)

        assert "description: >-" not in artifact.content
        assert "prompt: >-" not in artifact.content

    def test_render_no_frontmatter_when_config_empty_and_template_plain(
        self, tmp_path: Path
    ) -> None:
        """Test that render no frontmatter when config empty and template plain."""
        tmpl_dir = tmp_path / "templates" / "agents" / "plain"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "template.md").write_text("plain-body\n", encoding="utf-8")
        gen = GenericArtifactGenerator(AGENT_TYPE, tmp_path / "templates")
        artifact = gen.render(tmpl_dir)
        assert not artifact.content.startswith("---\n")
        assert "plain-body" in artifact.content

    def test_verify_input_without_schema_uses_fallback_required_fields(
        self, tmp_path: Path
    ) -> None:
        """Test that verify input without schema uses fallback required fields."""
        cfg = type(SKILL_TYPE)(**{**SKILL_TYPE.__dict__, "frontmatter_schema": None})
        gen = GenericArtifactGenerator(cfg, tmp_path / "templates")
        tmpl_dir = tmp_path / "templates" / "skills" / "vision"
        tmpl_dir.mkdir(parents=True)
        (tmp_path / "templates" / "skills" / "_partials").mkdir(parents=True, exist_ok=True)
        (tmpl_dir / "template.md").write_text(
            "---\nname: vision\n---\n{{SKILL_CONTEXT}}\n", encoding="utf-8"
        )
        result = gen.verify_input(expected_names=["vision"])
        assert not result.ok
        assert any(
            "MISSING required fields" in m.message for m in result.messages if m.level == "fail"
        )

    def test_verify_output_without_expected_names_and_flat_pattern(self, tmp_path: Path) -> None:
        """Test that verify output without expected names and flat pattern."""
        cfg = type(AGENT_TYPE)(**{**AGENT_TYPE.__dict__, "output_pattern": "{name}.agent.md"})
        gen = GenericArtifactGenerator(cfg, tmp_path / "templates")
        out = tmp_path / "out"
        out.mkdir(parents=True)
        (out / "engineer.agent.md").write_text("---\nname: engineer\n---\nbody\n", encoding="utf-8")
        result = gen.verify_output(out)
        assert not result.ok
        assert any("missing AUTO-GENERATED footer" in m.message for m in result.messages)

    def test_verify_output_frontmatter_and_footer_failures(self, tmp_path: Path) -> None:
        """Test that verify output frontmatter and footer failures."""
        out = tmp_path / "out"
        out.mkdir(parents=True)
        (out / "x.agent.md").write_text("no frontmatter\n", encoding="utf-8")
        gen = GenericArtifactGenerator(AGENT_TYPE, tmp_path / "templates")
        result = gen.verify_output(out, expected_names=["x"])
        assert not result.ok
        fail_messages = [m.message for m in result.messages if m.level == "fail"]
        assert any("missing frontmatter" in m for m in fail_messages)
        assert any("missing AUTO-GENERATED footer" in m for m in fail_messages)

    def test_output_path_helpers(self, tmp_path: Path) -> None:
        """Test that output path helpers."""
        gen = GenericArtifactGenerator(SKILL_TYPE, tmp_path / "templates")
        assert gen.output_path("vision") == "vision/SKILL.md"
        assert gen.install_relative_path("vision") == "skills/vision/SKILL.md"

    def test_render_adds_default_name_when_missing_in_config(self, tmp_path: Path) -> None:
        """Test that render adds default name when missing in config."""
        tmpl_dir = tmp_path / "templates" / "agents" / "writer"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "template.md").write_text("# writer\n", encoding="utf-8")
        (tmpl_dir / "config.yaml").write_text("description: d\n", encoding="utf-8")
        gen = GenericArtifactGenerator(AGENT_TYPE, tmp_path / "templates")
        artifact = gen.render(tmpl_dir)
        assert artifact.frontmatter is not None
        assert artifact.frontmatter["name"] == "writer"

    def test_render_raises_when_config_frontmatter_needs_schema(self, tmp_path: Path) -> None:
        """Test that render raises when config frontmatter needs schema."""
        cfg = AGENT_TYPE
        monkey_cfg = type(cfg)(**{**cfg.__dict__, "frontmatter_schema": None})
        gen = GenericArtifactGenerator(monkey_cfg, tmp_path / "templates")
        tmpl_dir = tmp_path / "templates" / "agents" / "writer"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "template.md").write_text("plain body\n", encoding="utf-8")
        (tmpl_dir / "config.yaml").write_text("name: writer\ndescription: d\n", encoding="utf-8")
        with pytest.raises(ValueError):
            gen.render(tmpl_dir)

    def test_generate_copies_extra_files(self, tmp_path: Path) -> None:
        """Test that generate copies extra files."""
        tmpl_dir = tmp_path / "templates" / "skills" / "alpha"
        tmpl_dir.mkdir(parents=True)
        (tmp_path / "templates" / "skills" / "_partials").mkdir(parents=True)
        (tmp_path / "templates" / "skills" / "_partials" / "skill-context.md").write_text(
            "context", encoding="utf-8"
        )
        (tmpl_dir / "template.md").write_text(
            "---\nname: alpha\nversion: 1.0.0\ndescription: d\n---\n{{SKILL_CONTEXT}}\n",
            encoding="utf-8",
        )
        (tmpl_dir / "example.sh").write_text("echo hi\n", encoding="utf-8")
        out = tmp_path / "output"
        self._make_skill_gen(tmp_path).generate(out)
        assert (out / "alpha" / "example.sh").exists()

    def test_verify_input_reports_missing_expected_template(self, tmp_path: Path) -> None:
        """Test that verify input reports missing expected template."""
        gen = self._make_skill_gen(tmp_path)
        result = gen.verify_input(expected_names=["vision"])
        assert not result.ok
        assert any("MISSING" in m.message for m in result.messages if m.level == "fail")

    def test_verify_input_without_schema_accepts_valid_name_description(
        self, tmp_path: Path
    ) -> None:
        """Test that verify input without schema accepts valid name description."""
        cfg = type(SKILL_TYPE)(**{**SKILL_TYPE.__dict__, "frontmatter_schema": None})
        gen = GenericArtifactGenerator(cfg, tmp_path / "templates")
        tmpl_dir = tmp_path / "templates" / "skills" / "vision"
        tmpl_dir.mkdir(parents=True)
        (tmp_path / "templates" / "skills" / "_partials").mkdir(parents=True, exist_ok=True)
        (tmpl_dir / "template.md").write_text(
            "---\nname: vision\ndescription: desc\n---\n{{SKILL_CONTEXT}}\n",
            encoding="utf-8",
        )
        result = gen.verify_input(expected_names=["vision"])
        assert result.ok

    def test_verify_input_reports_name_mismatch(self, tmp_path: Path) -> None:
        """Test that verify input reports name mismatch."""
        tmpl_dir = tmp_path / "templates" / "skills" / "vision"
        tmpl_dir.mkdir(parents=True)
        (tmp_path / "templates" / "skills" / "_partials").mkdir(parents=True)
        (tmpl_dir / "template.md").write_text(
            "---\nname: not-vision\nversion: 1.0.0\ndescription: d\n---\n{{SKILL_CONTEXT}}\n",
            encoding="utf-8",
        )
        result = self._make_skill_gen(tmp_path).verify_input(expected_names=["vision"])
        assert not result.ok
        assert any("name mismatch" in m.message for m in result.messages if m.level == "fail")

    def test_verify_output_without_expected_names_and_missing_output_dir(
        self, tmp_path: Path
    ) -> None:
        """Test that verify output without expected names and missing output dir."""
        gen = self._make_skill_gen(tmp_path)
        result = gen.verify_output(tmp_path / "does-not-exist")
        assert result.ok
        assert result.messages == []

    def test_verify_output_without_expected_names_and_subdir_pattern(self, tmp_path: Path) -> None:
        """Test that verify output without expected names and subdir pattern."""
        out = tmp_path / "out"
        (out / "vision").mkdir(parents=True)
        (out / "vision" / "SKILL.md").write_text(
            "---\nname: vision\ndescription: d\nversion: 1.0.0\n---\nbody\n"
            "<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->\n",
            encoding="utf-8",
        )
        result = self._make_skill_gen(tmp_path).verify_output(out)
        assert result.ok

    def test_verify_output_reports_unresolved_placeholders(self, tmp_path: Path) -> None:
        """Test that verify output reports unresolved placeholders."""
        out = tmp_path / "out"
        (out / "vision").mkdir(parents=True)
        (out / "vision" / "SKILL.md").write_text(
            "---\nname: vision\ndescription: d\nversion: 1.0.0\n---\n{{MISSING}}\n"
            "<!-- AUTO-GENERATED — maintained by vstack, do not edit directly -->\n",
            encoding="utf-8",
        )
        result = self._make_skill_gen(tmp_path).verify_output(out, expected_names=["vision"])
        assert not result.ok
        assert any(
            "unresolved placeholders" in m.message for m in result.messages if m.level == "fail"
        )
