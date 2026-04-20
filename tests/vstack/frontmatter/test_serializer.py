"""Tests for FrontmatterSerializer behavior."""

from __future__ import annotations

from vstack.frontmatter import FieldSpec, FrontmatterSchema, FrontmatterSerializer
from vstack.skills.config import SKILL_SCHEMA


class TestFrontmatterSerializer:
    """Test cases for FrontmatterSerializer."""

    def test_serialize_raw_field(self) -> None:
        """Test that serialize renders raw field."""
        schema = FrontmatterSchema(
            [FieldSpec("name", quoted=False), FieldSpec("mcp-servers", type="raw")]
        )
        output = FrontmatterSerializer.serialize(
            {"name": "agent", "mcp-servers": "  srv:\n    command: cmd"},
            schema,
        )
        assert "mcp-servers:\n  srv:" in output

    def test_serialize_raw_field_empty_skipped(self) -> None:
        """Test that serialize skips empty raw field."""
        schema = FrontmatterSchema(
            [FieldSpec("name", quoted=False), FieldSpec("mcp-servers", type="raw")]
        )
        output = FrontmatterSerializer.serialize({"name": "agent", "mcp-servers": ""}, schema)
        assert "mcp-servers" not in output

    def test_serialize_frontmatter_required_fields(self) -> None:
        """Test that serialize includes required frontmatter fields."""
        output = FrontmatterSerializer.serialize(
            {"name": "vision", "description": "A test skill"}, SKILL_SCHEMA
        )
        assert output.startswith("---\n")
        assert "name: vision" in output

    def test_serialize_frontmatter_optional_fields(self) -> None:
        """Test that serialize includes optional frontmatter fields."""
        output = FrontmatterSerializer.serialize(
            {
                "name": "x",
                "description": "d",
                "argument-hint": "some hint",
                "user-invocable": True,
            },
            SKILL_SCHEMA,
        )
        assert "argument-hint: 'some hint'" in output
        assert "user-invocable: true" in output

    def test_serialize_strips_extra_fields(self) -> None:
        """Test that serialize strips fields not in schema."""
        output = FrontmatterSerializer.serialize(
            {"name": "x", "description": "d", "version": "1.0.0", "extra": "value"},
            SKILL_SCHEMA,
        )
        assert "version: 1.0.0" not in output
        assert "extra" not in output

    def test_serialize_object_list_without_item_schema(self) -> None:
        """Test that serialize renders object-list without item schema."""
        schema = FrontmatterSchema([FieldSpec("handoffs", type="object-list")])
        output = FrontmatterSerializer.serialize(
            {
                "handoffs": [
                    {"label": "A", "send": True, "prompt": "go"},
                ]
            },
            schema,
        )
        assert "handoffs:" in output
        assert "- label: 'A'" in output
        assert "send: true" in output

    def test_serialize_object_list_with_item_schema_and_list_field(self) -> None:
        """Test that serialize renders object-list with schematized fields and nested lists."""
        item_schema = FrontmatterSchema(
            [
                FieldSpec("label"),
                FieldSpec("send", type="bool"),
                FieldSpec("roles", type="list"),
            ]
        )
        schema = FrontmatterSchema(
            [FieldSpec("handoffs", type="object-list", item_schema=item_schema)]
        )
        output = FrontmatterSerializer.serialize(
            {
                "handoffs": [
                    {"label": "handoff", "send": "false", "roles": ["reader", "writer"]},
                ]
            },
            schema,
        )
        assert "- label: 'handoff'" in output
        assert "send: false" in output
        assert "roles:" in output
        assert "- reader" in output

    def test_serialize_object_list_skips_non_dict_items(self) -> None:
        """Test that serialize skips non-dict items in object-list."""
        schema = FrontmatterSchema([FieldSpec("handoffs", type="object-list")])
        output = FrontmatterSerializer.serialize({"handoffs": ["bad", {"label": "ok"}]}, schema)
        assert "- label: 'ok'" in output
        assert "bad" not in output

    def test_serialize_multiline_scalar_when_enabled(self) -> None:
        """Test that serialize uses folded blocks when preserve_multiline=True."""
        output = FrontmatterSerializer.serialize(
            {
                "name": "x",
                "description": "This is a very long description that should be emitted as a folded block scalar when multiline output is enabled for readability in generated frontmatter.",
            },
            SKILL_SCHEMA,
            preserve_multiline=True,
        )
        assert "description: >-" in output

    def test_serialize_multiline_object_list_scalar_when_enabled(self) -> None:
        """Test that serialize uses folded blocks in object-list scalars."""
        schema = FrontmatterSchema([FieldSpec("handoffs", type="object-list")])
        output = FrontmatterSerializer.serialize(
            {
                "handoffs": [
                    {
                        "label": "Continue",
                        "prompt": "Translate architecture into concrete design contracts and include edge cases and failure behavior details.",
                    }
                ]
            },
            schema,
            preserve_multiline=True,
        )
        assert "    prompt: >-" in output

    def test_serialize_multiline_scalar_preserves_content_around_blank_lines(self) -> None:
        """Test that serialize preserves blank lines in folded block scalars."""
        output = FrontmatterSerializer.serialize(
            {
                "name": "x",
                "description": "First paragraph.\n\nSecond paragraph.",
            },
            SKILL_SCHEMA,
            preserve_multiline=True,
        )
        assert "description: >-" in output
        assert "  First paragraph." in output
        assert "  Second paragraph." in output
