"""Base command contract for CLI command handlers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CommandContext:
    """Runtime context passed to every CLI command handler."""

    args: Namespace
    install_dir: Path | None
    only: list[str] | None

    def require_install_dir(self, command_name: str) -> Path:
        """Return install_dir or raise when the command requires one."""
        if self.install_dir is None:
            raise ValueError(f"{command_name} requires install_dir")
        return self.install_dir


class BaseCommand(ABC):
    """Abstract base class for top-level CLI command handlers."""

    @abstractmethod
    def run(
        self,
        *,
        context: CommandContext,
    ) -> int:
        """Execute the command and return a process-style status code."""
