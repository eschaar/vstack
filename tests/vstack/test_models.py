"""Tests for shared validation models."""

from __future__ import annotations

from vstack.models import CheckMessage, ValidationResult


class TestCheckMessage:
    """Test cases for CheckMessage."""

    def test_check_message_fields(self) -> None:
        """Test that check message fields."""
        msg = CheckMessage(level="pass", message="ok")
        assert msg.level == "pass"
        assert msg.message == "ok"


class TestValidationResult:
    """Test cases for ValidationResult."""

    def test_passes_counts_only_pass(self) -> None:
        """Test that passes counts only pass."""
        result = ValidationResult(messages=[CheckMessage("pass", "a"), CheckMessage("fail", "b")])
        assert result.passes == 1

    def test_failures_counts_only_fail(self) -> None:
        """Test that failures counts only fail."""
        result = ValidationResult(messages=[CheckMessage("pass", "a"), CheckMessage("fail", "b")])
        assert result.failures == 1

    def test_ok_true_when_no_failures(self) -> None:
        """Test that ok true when no failures."""
        result = ValidationResult(messages=[CheckMessage("pass", "a")])
        assert result.ok

    def test_ok_false_when_failures(self) -> None:
        """Test that ok false when failures."""
        result = ValidationResult(messages=[CheckMessage("fail", "a")])
        assert not result.ok
