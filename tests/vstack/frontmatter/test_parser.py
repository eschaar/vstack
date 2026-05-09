"""Tests for frontmatter parser behavior."""

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

    def test_parse_yaml_empty_input_returns_empty_dict(self) -> None:
        """Empty input and non-mapping YAML values return an empty dict."""
        assert FrontmatterParser.parse_yaml("") == {}
        assert FrontmatterParser.parse_yaml("just a scalar") == {}
        assert FrontmatterParser.parse_yaml("- a\n- b\n") == {}

    def test_parse_yaml_raw_block(self) -> None:
        """Raw block value is parsed as a nested dict by PyYAML."""
        meta = FrontmatterParser.parse_yaml("mcp-servers:\n  srv:\n    command: cmd\n")
        assert isinstance(meta["mcp-servers"], dict)
        assert meta["mcp-servers"]["srv"]["command"] == "cmd"

    def test_parse_yaml_ignores_comments_and_handles_object_list_continuation(self) -> None:
        """Test that parse yaml ignores comments and handles object list continuation."""
        raw = "# comment\nhandoffs:\n  - label: A\n    prompt: hi\n"
        meta = FrontmatterParser.parse_yaml(raw)
        assert isinstance(meta["handoffs"], list)
        assert meta["handoffs"][0]["prompt"] == "hi"

    def test_parse_yaml_raw_block_closed_by_next_key(self) -> None:
        """Nested mapping value and subsequent sibling key are both parsed correctly."""
        raw = "mcp-servers:\n  srv:\n    type: local\nname: x\n"
        meta = FrontmatterParser.parse_yaml(raw)
        assert meta["mcp-servers"]["srv"]["type"] == "local"
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
        assert meta["handoffs"][0]["send"] is False

    def test_parse_yaml_wildcard_list_item(self) -> None:
        """Bare ``*`` list items (VS Code wildcard) are pre-processed so PyYAML parses them as strings."""
        raw = "agents:\n  - '*'\n  - architect\n"
        meta = FrontmatterParser.parse_yaml(raw)
        assert meta["agents"] == ["*", "architect"]

    def test_parse_yaml_unquoted_wildcard_list_item(self) -> None:
        """Unquoted ``- *`` in existing generated files is pre-processed before PyYAML."""
        raw = "agents:\n  - *\n  - architect\n"
        meta = FrontmatterParser.parse_yaml(raw)
        assert meta["agents"] == ["*", "architect"]

    def test_parse_yaml_object_list_nested_block_dict(self) -> None:
        """Nested dict block inside an object-list item is parsed as a dict by PyYAML."""
        raw = (
            "stages:\n"
            "  - role: architect\n"
            "    gate: required\n"
            "    handoffs:\n"
            "      prompt: Architecture done.\n"
            "      agent: designer\n"
        )
        meta = FrontmatterParser.parse_yaml(raw)
        assert isinstance(meta["stages"], list)
        stage = meta["stages"][0]
        assert stage["role"] == "architect"
        assert stage["gate"] == "required"
        # PyYAML parses the nested mapping directly as a dict
        assert isinstance(stage["handoffs"], dict)
        assert stage["handoffs"]["prompt"] == "Architecture done."
        assert stage["handoffs"]["agent"] == "designer"

    def test_parse_yaml_object_list_nested_block_with_block_scalar(self) -> None:
        """Nested block inside an object-list item: folded scalar prompt is parsed directly."""
        raw = (
            "stages:\n"
            "  - role: architect\n"
            "    gate: required\n"
            "    handoffs:\n"
            "      prompt: >\n"
            "        Line one\n"
            "        Line two\n"
            "    other: value\n"
        )
        meta = FrontmatterParser.parse_yaml(raw)
        stage = meta["stages"][0]
        # PyYAML parses the nested mapping directly as a dict with the folded scalar resolved
        assert isinstance(stage["handoffs"], dict)
        assert "Line one" in stage["handoffs"]["prompt"]
        assert "Line two" in stage["handoffs"]["prompt"]
        # The sibling key is parsed correctly
        assert stage["other"] == "value"

    def test_parse_yaml_object_list_empty_nested_block_is_none(self) -> None:
        """An empty-value nested key in an object-list item is None (PyYAML null)."""
        raw = "stages:\n  - role: release\n    gate: required\n    handoffs:\n"
        meta = FrontmatterParser.parse_yaml(raw)
        stage = meta["stages"][0]
        assert stage["handoffs"] is None
