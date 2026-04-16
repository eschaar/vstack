"""Utilities and tests for models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CheckMessage:
    """Represents CheckMessage."""

    level: str  # "pass" | "fail"
    message: str


@dataclass
class ValidationResult:
    """Represents ValidationResult."""

    messages: list[CheckMessage] = field(default_factory=list)

    @property
    def passes(self) -> int:
        """Passes."""
        return sum(1 for m in self.messages if m.level == "pass")

    @property
    def failures(self) -> int:
        """Failures."""
        return sum(1 for m in self.messages if m.level == "fail")

    @property
    def ok(self) -> bool:
        """Ok."""
        return self.failures == 0
