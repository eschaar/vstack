"""Utilities and tests for test parser."""

from __future__ import annotations

from vstack.frontmatter import FrontmatterContent, FrontmatterParser


class TestFrontmatterContent:
    """Test cases for FrontmatterContent."""

    def test_get(self) -> None:
        """Test that get."""
        content = FrontmatterContent(metadata={"name": "x"}, content="b")
        assert content.get("name") == "x"

    def test_contains(self) -> None:
        """Test that contains."""
        content = FrontmatterContent(metadata={"name": "x"}, content="b")
        assert "name" in content

    def test_getitem(self) -> None:
        """Test that getitem."""
        content = FrontmatterContent(metadata={"name": "x"}, content="b")
        assert content["name"] == "x"

    def test_bool(self) -> None:
        """Test that bool."""
        assert bool(FrontmatterContent(metadata={"name": "x"}, content="b"))
        assert not bool(FrontmatterContent(metadata={}, content="b"))


class TestFrontmatterParser:
    """Test cases for FrontmatterParser."""

    def test_parse_frontmatter_string_value(self) -> None:
        """Test that parse frontmatter string value."""
        result = FrontmatterParser.parse("---\nname: vision\nversion: 1.0.0\n---\nbody")
        assert result.metadata["name"] == "vision"
        assert result.content == "body"

    def test_parse_frontmatter_inline_list(self) -> None:
        """Test that parse frontmatter inline list."""
        meta = FrontmatterParser.parse("---\naliases: [foo, bar]\n---\n").metadata
        assert meta["aliases"] == ["foo", "bar"]

    def test_parse_frontmatter_block_list(self) -> None:
        """Test that parse frontmatter block list."""
        meta = FrontmatterParser.parse("---\ntools:\n  - read\n  - edit\n---\n").metadata
        assert meta["tools"] == ["read", "edit"]

    def test_parse_frontmatter_block_scalar(self) -> None:
        """Test that parse frontmatter block scalar."""
        meta = FrontmatterParser.parse(
            "---\ndescription: |\n  line one\n  line two\n---\n"
        ).metadata
        assert "line one" in meta["description"]

    def test_parse_no_frontmatter(self) -> None:
        """Test that parse no frontmatter."""
        result = FrontmatterParser.parse("body-only")
        assert result.metadata == {}
        assert result.content == "body-only"

    def test_parse_yaml_raw_block(self) -> None:
        """Test that parse yaml raw block."""
        meta = FrontmatterParser.parse_yaml("mcp-servers:\n  srv:\n    command: cmd\n")
        assert isinstance(meta["mcp-servers"], str)
        assert "srv:" in meta["mcp-servers"]

    def test_parse_yaml_ignores_comments_and_handles_object_list_continuation(self) -> None:
        """Test that parse yaml ignores comments and handles object list continuation."""
        raw = "# comment\nhandoffs:\n  - label: A\n    prompt: hi\n"
        meta = FrontmatterParser.parse_yaml(raw)
        assert isinstance(meta["handoffs"], list)
        assert meta["handoffs"][0]["prompt"] == "hi"

    def test_parse_yaml_raw_block_closed_by_next_key(self) -> None:
        """Test that parse yaml raw block closed by next key."""
        raw = "mcp-servers:\n  srv:\n    type: local\nname: x\n"
        meta = FrontmatterParser.parse_yaml(raw)
        assert "type: local" in meta["mcp-servers"]
        assert meta["name"] == "x"

    def test_parse_yaml_block_scalar_closed_by_next_key(self) -> None:
        """Test that parse yaml block scalar closed by next key."""
        raw = "description: |\n  line one\nname: tool\n"
        meta = FrontmatterParser.parse_yaml(raw)
        assert "line one" in meta["description"]
        assert meta["name"] == "tool"

    def test_parse_yaml_folded_scalar_closed_by_next_key(self) -> None:
        """Test that parse yaml folded scalar closed by next key."""
        raw = "description: >\n  line one\n  line two\nname: tool\n"
        meta = FrontmatterParser.parse_yaml(raw)
        assert "line one" in meta["description"]
        assert "line two" in meta["description"]
        assert meta["name"] == "tool"

    def test_parse_yaml_object_list_block_scalar_value(self) -> None:
        """Test that parse yaml object list block scalar value."""
        raw = (
            "handoffs:\n"
            "  - label: Start implementation\n"
            "    prompt: |\n"
            "      Line one\n"
            "      Line two\n"
            "    send: false\n"
        )
        meta = FrontmatterParser.parse_yaml(raw)
        assert isinstance(meta["handoffs"], list)
        assert "Line one" in meta["handoffs"][0]["prompt"]
        assert "Line two" in meta["handoffs"][0]["prompt"]
        assert meta["handoffs"][0]["send"] == "false"

    def test_parse_yaml_object_list_coerces_from_scalar(self) -> None:
        """Test that parse yaml object list coerces from scalar."""
        raw = "handoffs: value\n  - label: A\n"
        meta = FrontmatterParser.parse_yaml(raw)
        assert isinstance(meta["handoffs"], list)
        assert meta["handoffs"][0]["label"] == "A"

    def test_parse_yaml_string_list_coerces_from_scalar(self) -> None:
        """Test that parse yaml string list coerces from scalar."""
        raw = "tools: value\n  - read\n"
        meta = FrontmatterParser.parse_yaml(raw)
        assert isinstance(meta["tools"], list)
        assert meta["tools"] == ["read"]
