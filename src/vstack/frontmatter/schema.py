"""Frontmatter schema types — FieldSpec, FrontmatterSchema, FieldType.

These are the building blocks used to declare which fields are valid in a
frontmatter block, how to serialise them, and how to validate them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

FieldType = Literal["str", "bool", "list", "object-list", "raw"]


@dataclass
class FieldSpec:
    """Describes a single frontmatter field and how to serialise it.

    Attributes:
        name:                Field key as it appears in the frontmatter block.
        type:                Serialisation type: ``"str"``, ``"bool"``, ``"list"``,
                             ``"object-list"``, or ``"raw"`` (verbatim indented YAML block).
        required:            When ``True``, :meth:`FrontmatterSchema.validate_meta` will
                             flag its absence as an error.
        max_length:          Truncate string values to this many characters before quoting.
        quoted:              Wrap string values in single quotes (``'…'``).
        normalize_whitespace: Collapse runs of whitespace before serialising.
        pattern:             Optional regular expression that string values must match.
        item_schema:         For ``"object-list"`` fields: an optional
                             :class:`FrontmatterSchema` that describes the keys of each
                             list item.  When set, serialisation output is ordered and
                             filtered by this schema, and :meth:`FrontmatterSchema.validate_meta`
                             recurses into each item.
    """

    name: str
    type: FieldType = "str"
    required: bool = False
    max_length: int | None = None
    quoted: bool = True
    normalize_whitespace: bool = False
    pattern: str | None = None
    item_schema: FrontmatterSchema | None = None


@dataclass
class FrontmatterSchema:
    """Ordered list of fields recognised in a frontmatter block.

    Fields present in *meta* but absent from the schema are silently dropped
    when building output.  The declaration order determines the output order.
    """

    fields: list[FieldSpec] = field(default_factory=list)

    def get(self, name: str) -> FieldSpec | None:
        """Return the :class:`FieldSpec` for *name*, or ``None`` if not declared."""
        return next((f for f in self.fields if f.name == name), None)

    def validate_meta(self, meta: dict) -> list[str]:
        """Validate *meta* against declared schema fields.

        Checks performed:

        * Required fields are present and non-empty.
        * ``"bool"`` fields contain ``"true"`` or ``"false"`` (case-insensitive).
        * ``"list"`` fields contain a Python list.
        * ``"object-list"`` fields contain a list of dicts; when
          :attr:`FieldSpec.item_schema` is set each item is validated recursively.
        * ``"str"`` fields do not exceed :attr:`FieldSpec.max_length`.

        Unknown fields in *meta* (not declared in the schema) are silently ignored.

        Returns:
            A list of human-readable error strings.  An empty list means valid.
        """
        errors: list[str] = []
        for spec in self.fields:
            value = meta.get(spec.name)
            if spec.required and not value:
                errors.append(f"required field '{spec.name}' is missing or empty")
                continue
            if value is None:
                continue
            if spec.type == "bool":
                if str(value).lower() not in ("true", "false"):
                    errors.append(f"field '{spec.name}' must be 'true' or 'false', got: {value!r}")
            elif spec.type == "list":
                if not isinstance(value, list):
                    errors.append(f"field '{spec.name}' must be a list, got: {value!r}")
            elif spec.type == "object-list":
                if not isinstance(value, list):
                    errors.append(f"field '{spec.name}' must be a list, got: {value!r}")
                else:
                    for i, item in enumerate(value):
                        if not isinstance(item, dict):
                            errors.append(
                                f"field '{spec.name}[{i}]' must be a mapping, got: {item!r}"
                            )
                        elif spec.item_schema is not None:
                            for err in spec.item_schema.validate_meta(item):
                                errors.append(f"{spec.name}[{i}].{err}")
            elif spec.type == "raw":
                pass  # raw blocks are carried through verbatim; no structural validation
            else:  # "str"
                if spec.max_length and isinstance(value, str) and len(value) > spec.max_length:
                    errors.append(
                        f"field '{spec.name}' exceeds max length {spec.max_length} ({len(value)} chars)"
                    )
                if (
                    spec.pattern
                    and isinstance(value, str)
                    and not re.fullmatch(spec.pattern, value)
                ):
                    errors.append(
                        f"field '{spec.name}' does not match required pattern {spec.pattern!r}: {value!r}"
                    )
        return errors
