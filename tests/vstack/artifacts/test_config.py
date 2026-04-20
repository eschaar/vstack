"""Tests for artifact type configuration."""

from __future__ import annotations

from vstack.artifacts.config import INSTRUCTION_SCHEMA, PROMPT_SCHEMA, ArtifactTypeConfig


class TestArtifactTypeConfig:
    """Test cases for ArtifactTypeConfig."""

    def test_post_init_sets_manifest_key(self) -> None:
        """Test that post init sets manifest key."""
        cfg = ArtifactTypeConfig(
            type_name="x",
            templates_dir="x",
            output_subdir="xs",
            output_pattern="{name}.md",
            add_frontmatter=False,
        )
        assert cfg.manifest_key == "xs"


class TestSchemas:
    """Test cases for Schemas."""

    def test_prompt_schema_has_description(self) -> None:
        """Test that prompt schema has description."""
        assert PROMPT_SCHEMA.get("description") is not None

    def test_instruction_schema_has_apply_to(self) -> None:
        """Test that instruction schema has apply to."""
        assert INSTRUCTION_SCHEMA.get("applyTo") is not None
