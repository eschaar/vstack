"""Tests for generic artifact generation."""

from __future__ import annotations

import difflib
import re
import textwrap
from collections.abc import Callable
from pathlib import Path

import pytest

import vstack.artifacts.generator as generator_module
from vstack.agents.config import AGENT_TYPE
from vstack.agents.generator import AgentGenerator
from vstack.artifacts.generator import GenericArtifactGenerator
from vstack.instructions.config import INSTRUCTION_TYPE
from vstack.models import ValidationResult
from vstack.prompts.config import PROMPT_TYPE
from vstack.skills.config import SKILL_TYPE


class TestGenericArtifactGenerator:
    """Test cases for GenericArtifactGenerator."""

    _VSTACK_META_COMMENT_RE = re.compile(
        r"(?P<prefix><!--\s*VSTACK-META:\s*)(?P<payload>\{.*?\})(?P<suffix>\s*-->)"
    )
    _VSTACK_VERSION_FIELD_RE = re.compile(r'("vstack_version"\s*:\s*")[^"]*(")')
    _NORMALIZED_VSTACK_VERSION = "<vstack-version>"

    @classmethod
    def _normalize_vstack_version_in_meta_comment(cls, content: str) -> str:
        """Normalize VSTACK-META vstack_version values for deterministic fixture checks."""

        def _normalize_match(match: re.Match[str]) -> str:
            payload = match.group("payload")
            normalized_payload = cls._VSTACK_VERSION_FIELD_RE.sub(
                rf"\g<1>{cls._NORMALIZED_VSTACK_VERSION}\g<2>",
                payload,
                count=1,
            )
            return f"{match.group('prefix')}{normalized_payload}{match.group('suffix')}"

        return cls._VSTACK_META_COMMENT_RE.sub(_normalize_match, content)

    def _assert_matches_golden_fixture(
        self,
        *,
        artifact_content: str,
        expected_fixture: Path,
        artifact_label: str,
    ) -> None:
        """Assert rendered output matches fixture bytes except VSTACK-META version variability."""
        normalized_actual = self._normalize_vstack_version_in_meta_comment(artifact_content)
        normalized_expected = self._normalize_vstack_version_in_meta_comment(
            expected_fixture.read_text(encoding="utf-8")
        )

        actual_bytes = normalized_actual.encode("utf-8")
        expected_bytes = normalized_expected.encode("utf-8")

        if actual_bytes != expected_bytes:
            diff = "\n".join(
                difflib.unified_diff(
                    normalized_expected.splitlines(),
                    normalized_actual.splitlines(),
                    fromfile="expected fixture",
                    tofile="rendered output",
                    lineterm="",
                )
            )
            pytest.fail(
                f"Golden fixture drift detected for {artifact_label}.\n"
                f"If intentional, update {expected_fixture.as_posix()}.\n"
                f"{diff}"
            )

    def test_normalize_vstack_version_in_meta_comment_only_changes_version_value(self) -> None:
        """Normalization should only rewrite vstack_version inside VSTACK-META payload."""
        content = (
            "line-before\n"
            '<!-- VSTACK-META: {"artifact_name":"x","vstack_version":"0.0.0","artifact_version":"1"} -->\n'
            "line-after\n"
        )

        normalized = self._normalize_vstack_version_in_meta_comment(content)

        assert '"artifact_name":"x"' in normalized
        assert '"artifact_version":"1"' in normalized
        assert f'"vstack_version":"{self._NORMALIZED_VSTACK_VERSION}"' in normalized
        assert '"vstack_version":"0.0.0"' not in normalized
        assert normalized.startswith("line-before\n")
        assert normalized.endswith("line-after\n")

    def test_normalize_vstack_version_in_meta_comment_ignores_non_meta_occurrences(self) -> None:
        """Normalization should not touch vstack_version outside VSTACK-META comments."""
        content = '{"vstack_version":"outside"}\n<!-- unrelated: {"vstack_version":"other"} -->\n'

        normalized = self._normalize_vstack_version_in_meta_comment(content)

        assert normalized == content

    def _make_skill_gen(self, tmp_path: Path) -> GenericArtifactGenerator:
        """Internal helper to make skill gen."""
        return GenericArtifactGenerator(SKILL_TYPE, tmp_path / "templates")

    def _assert_verify_failures(
        self,
        *,
        result: ValidationResult,
        expected_substrings: list[str],
    ) -> None:
        """Assert deterministic verification failures with specific message fragments."""
        fail_messages = [m.message for m in result.messages if m.level == "fail"]
        assert not result.ok
        assert fail_messages
        for expected in expected_substrings:
            assert any(expected in message for message in fail_messages), (
                f"Expected failure containing: {expected}\n"
                f"Observed failures:\n" + "\n".join(fail_messages)
            )

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
        assert "VSTACK-META" in artifact.content
        assert artifact.unresolved == []

    def test_render_emits_parseable_vstack_metadata_footer(self, tmp_path: Path) -> None:
        """Test that render emits machine-readable footer metadata."""
        (tmp_path / "templates" / "skills" / "_partials").mkdir(parents=True)
        (tmp_path / "templates" / "skills" / "_partials" / "skill-context.md").write_text(
            "context", encoding="utf-8"
        )
        tmpl_dir = tmp_path / "templates" / "skills" / "verify"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "template.md").write_text(
            "---\nname: verify\nversion: 2.3.4\ndescription: d\n---\n{{SKILL_CONTEXT}}\n",
            encoding="utf-8",
        )

        artifact = self._make_skill_gen(tmp_path).render(tmpl_dir)
        metadata = GenericArtifactGenerator.parse_generation_metadata(artifact.content)

        assert metadata is not None
        assert metadata["generator"] == "vstack"
        assert metadata["artifact_type"] == "skill"
        assert metadata["artifact_name"] == "verify"
        assert metadata["artifact_version"] == "2.3.4"

    def test_parse_generation_metadata_returns_none_without_footer(self) -> None:
        """Test that metadata parser returns none when footer is missing."""
        assert GenericArtifactGenerator.parse_generation_metadata("plain content") is None

    def test_parse_generation_metadata_returns_none_on_invalid_json(self) -> None:
        """Test that metadata parser returns none when footer JSON is invalid."""
        text = "<!-- VSTACK-META: {not-json} -->"
        assert GenericArtifactGenerator.parse_generation_metadata(text) is None

    def test_parse_generation_metadata_returns_none_on_non_object(self) -> None:
        """Test that metadata parser returns none when footer JSON is not an object."""
        text = '<!-- VSTACK-META: ["a", "b"] -->'
        assert GenericArtifactGenerator.parse_generation_metadata(text) is None

    def test_render_instruction_security_matches_golden_fixture(
        self,
        templates_root: Path,
        instruction_fixture_path: Callable[[str], Path],
    ) -> None:
        """Security instruction rendering must remain byte-for-byte stable."""
        templates = templates_root
        template_dir = templates / "instructions" / "security"
        expected_fixture = instruction_fixture_path("security")

        artifact = GenericArtifactGenerator(INSTRUCTION_TYPE, templates).render(template_dir)
        self._assert_matches_golden_fixture(
            artifact_content=artifact.content,
            expected_fixture=expected_fixture,
            artifact_label="instruction/security",
        )

    def test_render_instruction_testing_matches_golden_fixture(
        self,
        templates_root: Path,
        instruction_fixture_path: Callable[[str], Path],
    ) -> None:
        """Testing instruction rendering must remain byte-for-byte stable."""
        templates = templates_root
        template_dir = templates / "instructions" / "testing"
        expected_fixture = instruction_fixture_path("testing")

        artifact = GenericArtifactGenerator(INSTRUCTION_TYPE, templates).render(template_dir)
        self._assert_matches_golden_fixture(
            artifact_content=artifact.content,
            expected_fixture=expected_fixture,
            artifact_label="instruction/testing",
        )

    def test_render_skill_concise_matches_golden_fixture(
        self,
        templates_root: Path,
        skill_fixture_path: Callable[[str], Path],
    ) -> None:
        """Concise skill rendering must remain byte-for-byte stable."""
        templates = templates_root
        template_dir = templates / "skills" / "concise"
        expected_fixture = skill_fixture_path("concise")

        artifact = GenericArtifactGenerator(SKILL_TYPE, templates).render(template_dir)
        self._assert_matches_golden_fixture(
            artifact_content=artifact.content,
            expected_fixture=expected_fixture,
            artifact_label="skill/concise",
        )

    def test_render_agent_planner_matches_golden_fixture(
        self,
        templates_root: Path,
        agent_fixture_path: Callable[[str], Path],
    ) -> None:
        """Planner agent rendering must remain byte-for-byte stable."""
        templates = templates_root
        template_dir = templates / "agents" / "planner"
        expected_fixture = agent_fixture_path("planner")

        artifact = AgentGenerator(templates_root=templates).render(template_dir)
        self._assert_matches_golden_fixture(
            artifact_content=artifact.content,
            expected_fixture=expected_fixture,
            artifact_label="agent/planner",
        )

    def test_render_agent_product_matches_golden_fixture(
        self,
        templates_root: Path,
        agent_fixture_path: Callable[[str], Path],
    ) -> None:
        """Product agent rendering must remain byte-for-byte stable."""
        templates = templates_root
        template_dir = templates / "agents" / "product"
        expected_fixture = agent_fixture_path("product")

        artifact = AgentGenerator(templates_root=templates).render(template_dir)
        self._assert_matches_golden_fixture(
            artifact_content=artifact.content,
            expected_fixture=expected_fixture,
            artifact_label="agent/product",
        )

    def test_render_prompt_quick_review_matches_golden_fixture(
        self,
        templates_root: Path,
        prompt_fixture_path: Callable[[str], Path],
    ) -> None:
        """Quick-review prompt rendering must remain byte-for-byte stable."""
        templates = templates_root
        template_dir = templates / "prompts" / "quick-review"
        expected_fixture = prompt_fixture_path("quick-review")

        artifact = GenericArtifactGenerator(PROMPT_TYPE, templates).render(template_dir)
        self._assert_matches_golden_fixture(
            artifact_content=artifact.content,
            expected_fixture=expected_fixture,
            artifact_label="prompt/quick-review",
        )

    def test_render_prompt_api_design_review_matches_golden_fixture(
        self,
        templates_root: Path,
        prompt_fixture_path: Callable[[str], Path],
    ) -> None:
        """API-design-review prompt rendering must remain byte-for-byte stable."""
        templates = templates_root
        template_dir = templates / "prompts" / "api-design-review"
        expected_fixture = prompt_fixture_path("api-design-review")

        artifact = GenericArtifactGenerator(PROMPT_TYPE, templates).render(template_dir)
        self._assert_matches_golden_fixture(
            artifact_content=artifact.content,
            expected_fixture=expected_fixture,
            artifact_label="prompt/api-design-review",
        )

    def test_render_skill_verify_matches_golden_fixture(
        self,
        templates_root: Path,
        skill_fixture_path: Callable[[str], Path],
    ) -> None:
        """Verify skill rendering must remain byte-for-byte stable."""
        templates = templates_root
        template_dir = templates / "skills" / "verify"
        expected_fixture = skill_fixture_path("verify")

        artifact = GenericArtifactGenerator(SKILL_TYPE, templates).render(template_dir)
        self._assert_matches_golden_fixture(
            artifact_content=artifact.content,
            expected_fixture=expected_fixture,
            artifact_label="skill/verify",
        )

    def test_parse_generation_metadata_returns_none_when_loader_returns_non_dict(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that metadata parser rejects non-dict payloads from JSON loader."""
        monkeypatch.setattr(generator_module.json, "loads", lambda _text: ["not", "dict"])
        text = "<!-- VSTACK-META: {} -->"
        assert GenericArtifactGenerator.parse_generation_metadata(text) is None

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

    def test_defect_fixture_unknown_placeholder_reports_registered_failure(
        self, tmp_path: Path
    ) -> None:
        """Defect fixture: unknown placeholder should fail with explicit registry message."""
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

        self._assert_verify_failures(
            result=result,
            expected_substrings=[
                "unknown placeholder '{{UNKNOWN_TOKEN}}'",
            ],
        )

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
            "name: writer\ndescription: A writer agent\nuser-invocable: maybe\n",
            encoding="utf-8",
        )
        gen = GenericArtifactGenerator(AGENT_TYPE, tmp_path / "templates")
        result = gen.verify_input(expected_names=["writer"])
        assert not result.ok
        assert any("user-invocable" in m.message for m in result.messages if m.level == "fail")

    def test_defect_fixture_schema_violation_reports_field_name(self, tmp_path: Path) -> None:
        """Defect fixture: schema violations should fail with field-specific feedback."""
        tmpl_dir = tmp_path / "templates" / "agents" / "writer"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "template.md").write_text("# writer\nbody\n", encoding="utf-8")
        (tmpl_dir / "config.yaml").write_text(
            "name: writer\ndescription: A writer agent\nuser-invocable: maybe\n",
            encoding="utf-8",
        )
        gen = GenericArtifactGenerator(AGENT_TYPE, tmp_path / "templates")
        result = gen.verify_input(expected_names=["writer"])

        self._assert_verify_failures(
            result=result,
            expected_substrings=[
                "user-invocable",
            ],
        )

    def test_defect_fixture_missing_expected_template_reports_missing(self, tmp_path: Path) -> None:
        """Defect fixture: missing expected template should report a MISSING failure."""
        result = self._make_skill_gen(tmp_path).verify_input(expected_names=["vision"])

        self._assert_verify_failures(
            result=result,
            expected_substrings=[
                "MISSING",
            ],
        )

    def test_defect_fixture_name_mismatch_in_metadata_reports_mismatch(
        self, tmp_path: Path
    ) -> None:
        """Defect fixture: name mismatch should report a mismatch failure."""
        tmpl_dir = tmp_path / "templates" / "skills" / "vision"
        tmpl_dir.mkdir(parents=True)
        (tmp_path / "templates" / "skills" / "_partials").mkdir(parents=True)
        (tmpl_dir / "template.md").write_text(
            "---\nname: not-vision\nversion: 1.0.0\ndescription: d\n---\n{{SKILL_CONTEXT}}\n",
            encoding="utf-8",
        )
        result = self._make_skill_gen(tmp_path).verify_input(expected_names=["vision"])

        self._assert_verify_failures(
            result=result,
            expected_substrings=[
                "name mismatch",
            ],
        )

    def test_defect_fixture_required_field_missing_reports_required_field_message(
        self, tmp_path: Path
    ) -> None:
        """Defect fixture: missing required metadata should report required fields."""
        cfg = type(SKILL_TYPE)(**{**SKILL_TYPE.__dict__, "frontmatter_schema": None})
        gen = GenericArtifactGenerator(cfg, tmp_path / "templates")
        tmpl_dir = tmp_path / "templates" / "skills" / "vision"
        tmpl_dir.mkdir(parents=True)
        (tmp_path / "templates" / "skills" / "_partials").mkdir(parents=True, exist_ok=True)
        (tmpl_dir / "template.md").write_text(
            "---\nname: vision\n---\n{{SKILL_CONTEXT}}\n", encoding="utf-8"
        )
        result = gen.verify_input(expected_names=["vision"])

        self._assert_verify_failures(
            result=result,
            expected_substrings=[
                "MISSING required fields",
            ],
        )

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

    def test_template_partials_returns_empty_dict_by_default(self, tmp_path: Path) -> None:
        """Test that template_partials returns an empty dict in the base class."""
        gen = self._make_skill_gen(tmp_path)
        assert gen.template_partials(tmp_path / "any" / "dir") == {}

    def test_render_merges_template_partials_into_resolution(self, tmp_path: Path) -> None:
        """Test that render uses template_partials to resolve per-template tokens."""

        class _CustomGen(GenericArtifactGenerator):
            def template_partials(self, tmpl_dir: Path) -> dict[str, str]:
                return {"CUSTOM_TOKEN": "injected-value"}

        (tmp_path / "templates" / "skills" / "_partials").mkdir(parents=True)
        tmpl_dir = tmp_path / "templates" / "skills" / "custom"
        tmpl_dir.mkdir(parents=True)
        (tmpl_dir / "template.md").write_text(
            "---\nname: custom\nversion: 1.0.0\ndescription: x\n---\n{{CUSTOM_TOKEN}}\n",
            encoding="utf-8",
        )

        gen = _CustomGen(SKILL_TYPE, tmp_path / "templates")
        artifact = gen.render(tmpl_dir)
        assert "injected-value" in artifact.content
        assert artifact.unresolved == []
