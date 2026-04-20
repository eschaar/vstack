"""Tests for frontmatter schema validation."""

from __future__ import annotations

from vstack.frontmatter import FieldSpec, FrontmatterSchema


class TestFieldSpec:
    """Test cases for FieldSpec."""

    def test_fields_default_values(self) -> None:
        """Test that fields default values."""
        spec = FieldSpec("name")
        assert spec.type == "str"
        assert spec.required is False


class TestFrontmatterSchema:
    """Test cases for FrontmatterSchema."""

    def _schema(self) -> FrontmatterSchema:
        """Internal helper to schema."""
        return FrontmatterSchema(
            [
                FieldSpec("name", required=True, quoted=False),
                FieldSpec("description", required=True, max_length=50),
                FieldSpec("active", type="bool"),
                FieldSpec("tags", type="list"),
            ]
        )

    def test_get_returns_field(self) -> None:
        """Test that get returns field."""
        assert self._schema().get("name") is not None

    def test_get_returns_none_for_unknown(self) -> None:
        """Test that get returns none for unknown."""
        assert self._schema().get("missing") is None

    def test_validate_meta_valid(self) -> None:
        """Test that validate meta valid."""
        errors = self._schema().validate_meta(
            {
                "name": "foo",
                "description": "short",
                "active": "true",
                "tags": ["a", "b"],
            }
        )
        assert errors == []

    def test_validate_meta_required_missing(self) -> None:
        """Test that validate meta required missing."""
        errors = self._schema().validate_meta({"name": "foo"})
        assert any("description" in e for e in errors)

    def test_validate_meta_invalid_bool(self) -> None:
        """Test that validate meta invalid bool."""
        errors = self._schema().validate_meta({"name": "foo", "description": "d", "active": "yes"})
        assert any("active" in e for e in errors)

    def test_validate_meta_invalid_list(self) -> None:
        """Test that validate meta invalid list."""
        errors = self._schema().validate_meta({"name": "foo", "description": "d", "tags": "oops"})
        assert any("tags" in e for e in errors)

    def test_validate_meta_max_length_exceeded(self) -> None:
        """Test that validate meta max length exceeded."""
        errors = self._schema().validate_meta({"name": "foo", "description": "x" * 60})
        assert any("max length" in e for e in errors)

    def test_validate_meta_object_list_not_list(self) -> None:
        """Test that validate meta object list not list."""
        schema = FrontmatterSchema([FieldSpec("items", type="object-list")])
        errors = schema.validate_meta({"items": "bad"})
        assert any("must be a list" in e for e in errors)

    def test_validate_meta_object_list_item_not_mapping(self) -> None:
        """Test that validate meta object list item not mapping."""
        schema = FrontmatterSchema([FieldSpec("items", type="object-list")])
        errors = schema.validate_meta({"items": ["x"]})
        assert any("must be a mapping" in e for e in errors)

    def test_validate_meta_object_list_nested_schema_error(self) -> None:
        """Test that validate meta object list nested schema error."""
        item_schema = FrontmatterSchema([FieldSpec("enabled", type="bool")])
        schema = FrontmatterSchema(
            [FieldSpec("items", type="object-list", item_schema=item_schema)]
        )
        errors = schema.validate_meta({"items": [{"enabled": "maybe"}]})
        assert any("items[0].field 'enabled'" in e for e in errors)

    def test_validate_meta_object_list_mapping_without_item_schema(self) -> None:
        """Test that mapping items are accepted when object-list has no item schema."""
        schema = FrontmatterSchema([FieldSpec("items", type="object-list")])
        assert schema.validate_meta({"items": [{"k": "v"}]}) == []

    def test_validate_meta_raw_field_has_no_structural_validation(self) -> None:
        """Test that validate meta raw field has no structural validation."""
        schema = FrontmatterSchema([FieldSpec("meta", type="raw")])
        assert schema.validate_meta({"meta": {"any": "shape"}}) == []
