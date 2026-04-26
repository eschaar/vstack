"""Tests for CLI shared internal helpers."""

from __future__ import annotations

from vstack.cli.helpers import normalize_targeted_names


class TestNormalizeTargetedNames:
    """Test cases for normalize_targeted_names."""

    def test_returns_empty_set_for_none(self) -> None:
        """None input produces an empty set."""
        assert normalize_targeted_names(None) == set()

    def test_returns_empty_set_for_empty_list(self) -> None:
        """Empty list produces an empty set."""
        assert normalize_targeted_names([]) == set()

    def test_strips_whitespace(self) -> None:
        """Names with surrounding whitespace are stripped."""
        assert normalize_targeted_names(["  vision  ", " debug "]) == {"vision", "debug"}

    def test_deduplicates_names(self) -> None:
        """Duplicate names collapse into a single entry."""
        assert normalize_targeted_names(["vision", "vision", "debug"]) == {"vision", "debug"}

    def test_filters_blank_strings(self) -> None:
        """Blank strings (empty or whitespace-only) are excluded."""
        assert normalize_targeted_names(["  ", "", "debug"]) == {"debug"}

    def test_returns_set_of_names(self) -> None:
        """Result is always a set."""
        result = normalize_targeted_names(["a", "b"])
        assert isinstance(result, set)
        assert result == {"a", "b"}
