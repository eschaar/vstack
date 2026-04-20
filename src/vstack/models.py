"""Shared validation result models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CheckMessage:
    """Represent a single validation message with a pass/fail level."""

    level: str  # "pass" | "fail"
    message: str


@dataclass
class ValidationResult:
    """Store validation messages and expose aggregate result helpers."""

    messages: list[CheckMessage] = field(default_factory=list)

    @property
    def passes(self) -> int:
        """Return the number of passing validation messages."""
        return sum(1 for m in self.messages if m.level == "pass")

    @property
    def failures(self) -> int:
        """Return the number of failing validation messages."""
        return sum(1 for m in self.messages if m.level == "fail")

    @property
    def ok(self) -> bool:
        """Return ``True`` when the validation result contains no failures."""
        return self.failures == 0
