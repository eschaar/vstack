"""YAML frontmatter parser.

Delegates YAML parsing to :func:`yaml.safe_load` (PyYAML).  Supports the full
YAML 1.1 feature set used by vstack config files, including nested mappings,
block sequences, block scalars, and inline lists.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import yaml

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)", re.DOTALL)


@dataclass
class FrontmatterContent:
    """Result of parsing a document that may contain YAML frontmatter.

    Attributes:
        metadata: Parsed key/value pairs from the ``---`` block.
                  Empty dict when no frontmatter was found.
        content:  The body text after the closing ``---``.
                  Equals the original input when no frontmatter was found.
    """

    metadata: dict = field(default_factory=dict)
    content: str = ""

    # ── Convenience accessors ─────────────────────────────────────────────────

    def get(self, key: str, default: object = None) -> object:
        """Return *key* from metadata, falling back to *default*."""
        return self.metadata.get(key, default)

    def __contains__(self, key: object) -> bool:
        """Return ``True`` when *key* exists in parsed metadata."""
        return key in self.metadata

    def __getitem__(self, key: str) -> object:
        """Provide dict-style indexing for metadata lookups."""
        return self.metadata[key]

    def __bool__(self) -> bool:
        """Return ``True`` when parsed metadata is non-empty."""
        return bool(self.metadata)


class FrontmatterParser:
    """Parse YAML frontmatter using :func:`yaml.safe_load`."""

    def parse(self, content: str) -> FrontmatterContent:
        """Split YAML frontmatter from body content.

        Returns a :class:`FrontmatterContent` instance.  When no frontmatter
        block is present, ``metadata`` is empty and ``content`` equals the
        original input.
        """
        match = _FRONTMATTER_RE.match(content)
        if not match:
            return FrontmatterContent(metadata={}, content=content)
        meta = self._parse_yaml_block(match.group(1))
        return FrontmatterContent(metadata=meta, content=match.group(2))

    def parse_yaml(self, raw: str) -> dict:
        """Parse a raw YAML string without frontmatter delimiters.

        Args:
            raw: YAML content without surrounding ``---`` delimiters.

        Returns:
            A parsed metadata dictionary.
        """
        return self._parse_yaml_block(raw)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _parse_yaml_block(self, raw: str) -> dict:
        """Delegate YAML parsing to :func:`yaml.safe_load`.

        Pre-processes ``- *`` (VS Code wildcard list items) into quoted form
        so that PyYAML does not interpret the bare ``*`` as a YAML alias.

        Returns an empty dict when *raw* is empty or parses to a non-mapping
        value.
        """
        # Replace bare wildcard items (``  - *``) with single-quoted form so that
        # PyYAML does not treat the leading ``*`` as a YAML alias marker.
        preprocessed = re.sub(r"^(\s*-\s)\*(\s*)$", r"\1'*'\2", raw, flags=re.MULTILINE)
        result = yaml.safe_load(preprocessed)
        if not isinstance(result, dict):
            return {}
        return result
