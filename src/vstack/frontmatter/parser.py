"""YAML frontmatter parser — no external dependencies.

Supports:
- String scalars (quoted and unquoted)
- Inline lists  ``[a, b, c]``
- Block lists   ``\n  - item``
- Block sequences of mappings (object-lists)  ``\n  - key: val\n    key2: val2``
- Block scalars ``|``
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

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
    """Parse the repository's supported subset of YAML frontmatter."""

    @staticmethod
    def _is_current_object_list_item(meta: dict, current_key: str) -> bool:
        """Return ``True`` when ``current_key`` points to the active object-list item."""
        return (
            bool(current_key)
            and isinstance(meta.get(current_key), list)
            and bool(meta[current_key])
            and isinstance(meta[current_key][-1], dict)
        )

    @staticmethod
    def _flush_object_block_scalar(
        *,
        meta: dict,
        current_key: str,
        object_scalar_field: str,
        object_block_lines: list[str],
    ) -> None:
        """Flush buffered block-scalar content into the active object-list item."""
        text = " ".join(b for b in object_block_lines if b).strip()
        if FrontmatterParser._is_current_object_list_item(meta, current_key):
            meta[current_key][-1][object_scalar_field] = text

    @staticmethod
    def _flush_raw_block(*, meta: dict, current_key: str, raw_lines: list[str]) -> None:
        """Flush buffered raw block content into the current top-level key."""
        meta[current_key] = "\n".join(raw_lines).rstrip()

    @staticmethod
    def _flush_block_scalar(*, meta: dict, current_key: str, block_lines: list[str]) -> None:
        """Flush a buffered top-level block scalar into the current key."""
        meta[current_key] = " ".join(b for b in block_lines if b).strip()

    @staticmethod
    def parse(content: str) -> FrontmatterContent:
        """Split YAML frontmatter from body content.

        Returns a :class:`FrontmatterContent` instance.  When no frontmatter
        block is present, ``metadata`` is empty and ``content`` equals the
        original input.
        """
        match = _FRONTMATTER_RE.match(content)
        if not match:
            return FrontmatterContent(metadata={}, content=content)
        meta = FrontmatterParser._parse_yaml_block(match.group(1))
        return FrontmatterContent(metadata=meta, content=match.group(2))

    @staticmethod
    def parse_yaml(raw: str) -> dict:
        """Parse a raw YAML string without frontmatter delimiters.

        Args:
            raw: YAML content without surrounding ``---`` delimiters.

        Returns:
            A parsed metadata dictionary.
        """
        return FrontmatterParser._parse_yaml_block(raw)

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_scalar(val: str) -> str:
        """Strip surrounding quotes from a YAML scalar string."""
        return val.strip().strip("\"'")

    @staticmethod
    def _parse_yaml_block(raw: str) -> dict:
        """Parse a minimal YAML subset (no external dependencies).

        Supports: string values, inline lists ``[a, b]``,
        block lists ``\n  - item``, block scalars ``|``,
        block sequences of mappings (object-lists):
        ``\n  - key: val\n    key2: val2``, and
        raw mapping blocks where the value is indented non-list YAML content:
        ``\n  server:\n    type: local`` (used for ``mcp-servers``, ``hooks``, etc.).
        """
        meta: dict = {}
        current_key = ""
        in_block_scalar = False
        block_lines: list[str] = []
        in_raw_block = False
        raw_lines: list[str] = []
        in_object_block_scalar = False
        object_scalar_field = ""
        object_block_lines: list[str] = []

        for line in raw.split("\n"):
            if line.strip().startswith("#"):
                continue

            if in_object_block_scalar:
                if line.startswith("      ") or line == "":
                    object_block_lines.append(line.strip())
                    continue
                else:
                    FrontmatterParser._flush_object_block_scalar(
                        meta=meta,
                        current_key=current_key,
                        object_scalar_field=object_scalar_field,
                        object_block_lines=object_block_lines,
                    )
                    in_object_block_scalar = False
                    object_scalar_field = ""
                    object_block_lines = []

            # ── Raw block accumulation ────────────────────────────────────────
            if in_raw_block:
                if line == "" or line.startswith(" "):
                    raw_lines.append(line)
                    continue
                else:
                    # Non-indented line closes the raw block; fall through to process it
                    FrontmatterParser._flush_raw_block(
                        meta=meta,
                        current_key=current_key,
                        raw_lines=raw_lines,
                    )
                    in_raw_block = False
                    raw_lines = []

            if in_block_scalar:
                if line.startswith("  ") or line == "":
                    block_lines.append(line.strip())
                    continue
                else:
                    FrontmatterParser._flush_block_scalar(
                        meta=meta,
                        current_key=current_key,
                        block_lines=block_lines,
                    )
                    in_block_scalar = False
                    block_lines = []

            # 4-space key: continuation of an object-list item
            obj_kv = re.match(r"^    ([a-zA-Z_-]+):\s*(.*)$", line)
            if obj_kv and FrontmatterParser._is_current_object_list_item(meta, current_key):
                obj_key = obj_kv.group(1)
                obj_val = obj_kv.group(2).strip()
                if obj_val in ("|", "|-", "|+", ">", ">-", ">+"):
                    in_object_block_scalar = True
                    object_scalar_field = obj_key
                    object_block_lines = []
                    meta[current_key][-1][obj_key] = ""
                else:
                    meta[current_key][-1][obj_key] = FrontmatterParser._parse_scalar(obj_val)
                continue

            # Raw block trigger: 2-space non-list indented line when the current key
            # has an empty provisional value (set by a bare ``key:`` with no value).
            if (
                line.startswith("  ")
                and not line.startswith("  - ")
                and current_key
                and meta.get(current_key) == []
            ):
                in_raw_block = True
                raw_lines = [line]
                meta[current_key] = ""  # clear empty-list placeholder
                continue

            # 2-space list item
            list_match = re.match(r"^  - (.+)$", line)
            if list_match and current_key:
                item_str = list_match.group(1).strip()
                item_kv = re.match(r"^([a-zA-Z_-]+):\s*(.*)$", item_str)
                if item_kv:
                    # Object-list item — first key bootstraps the dict
                    if not isinstance(meta.get(current_key), list):
                        meta[current_key] = []
                    meta[current_key].append(
                        {item_kv.group(1): FrontmatterParser._parse_scalar(item_kv.group(2))}
                    )
                else:
                    if not isinstance(meta.get(current_key), list):
                        meta[current_key] = []
                    meta[current_key].append(item_str.strip("\"'"))
                continue

            kv = re.match(r"^([a-zA-Z_-]+):\s*(.*)$", line)
            if kv:
                current_key = kv.group(1)
                val = kv.group(2).strip()
                if val.startswith("[") and val.endswith("]"):
                    meta[current_key] = [
                        v.strip().strip("\"'") for v in val[1:-1].split(",") if v.strip()
                    ]
                elif val in ("|", "|-", "|+", ">", ">-", ">+"):
                    in_block_scalar = True
                    block_lines = []
                    meta[current_key] = ""
                elif val == "":
                    meta[current_key] = []  # provisional: may become a raw block
                else:
                    meta[current_key] = val.strip("\"'")

        if in_object_block_scalar:
            if object_scalar_field:
                FrontmatterParser._flush_object_block_scalar(
                    meta=meta,
                    current_key=current_key,
                    object_scalar_field=object_scalar_field,
                    object_block_lines=object_block_lines,
                )
        if in_raw_block and raw_lines:
            FrontmatterParser._flush_raw_block(
                meta=meta,
                current_key=current_key,
                raw_lines=raw_lines,
            )
        if in_block_scalar and block_lines:
            FrontmatterParser._flush_block_scalar(
                meta=meta,
                current_key=current_key,
                block_lines=block_lines,
            )

        return meta
