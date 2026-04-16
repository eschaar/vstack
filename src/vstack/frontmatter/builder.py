"""Frontmatter output builder — schema-filtered YAML serialisation.

:func:`build_output` converts a metadata dict to a ``---`` / ``---`` YAML
frontmatter block, filtered and ordered by a :class:`~vstack.frontmatter.FrontmatterSchema`.
Fields absent from the schema are silently dropped so generator-internal
metadata (``version``, etc.) never leaks into output files.
"""

from __future__ import annotations

import re
import textwrap

from vstack.frontmatter.schema import FieldSpec, FrontmatterSchema


def _serialize_scalar(spec: FieldSpec, value: object) -> str:
    """Serialize a single ``"str"`` value according to *spec* options."""
    text = str(value)
    if spec.normalize_whitespace:
        text = re.sub(r"\s+", " ", text).strip()
    if spec.max_length:
        text = text[: spec.max_length]
    if spec.quoted:
        return f"'{text.replace(chr(39), chr(39) * 2)}'"
    return text


def _serialize_multiline_scalar(name: str, value: object, base_indent: str = "") -> list[str]:
    """Serialize a string scalar as YAML folded block (``>-``) lines."""
    text = str(value).strip()
    wrapped_lines: list[str] = []
    for paragraph in text.splitlines() or [text]:
        if not paragraph.strip():
            wrapped_lines.append("")
            continue
        wrapped_lines.extend(textwrap.wrap(paragraph.strip(), width=100))
    out = [f"{base_indent}{name}: >-"]
    out.extend(f"{base_indent}  {line}" for line in wrapped_lines if line != "")
    return out


def _should_emit_multiline(value: object, preserve_multiline: bool) -> bool:
    """Return True when scalar should be emitted as a folded block string."""
    if not preserve_multiline:
        return False
    text = str(value)
    return "\n" in text or len(text) > 90


def _serialize_bool(value: object) -> str:
    """Return ``"true"`` or ``"false"`` regardless of input representation."""
    if isinstance(value, bool):
        return str(value).lower()
    return "true" if str(value).strip().lower() == "true" else "false"


def _serialize_object(
    item: dict,
    item_schema: FrontmatterSchema | None,
    preserve_multiline: bool = False,
) -> list[str]:
    """Serialize one object-list item to a list of YAML lines (without leading ``  - ``).

    When *item_schema* is provided the item is ordered and filtered by the
    schema.  Without a schema the item keys are emitted in their natural order.
    """
    if item_schema is None:
        lines: list[str] = []
        for k, v in item.items():
            v_str = str(v).strip()
            if isinstance(v, bool) or v_str.lower() in ("true", "false"):
                lines.append(f"{k}: {_serialize_bool(v)}")
            elif _should_emit_multiline(v, preserve_multiline):
                lines.extend(_serialize_multiline_scalar(k, v))
            else:
                safe = v_str.replace("'", "''")
                lines.append(f"{k}: '{safe}'")
        return lines

    pairs = [
        (spec, item.get(spec.name))
        for spec in item_schema.fields
        if item.get(spec.name) is not None
    ]
    lines = []
    for spec, value in pairs:
        if spec.type == "bool":
            lines.append(f"{spec.name}: {_serialize_bool(value)}")
        elif spec.type == "list":
            if isinstance(value, list) and value:
                lines.append(f"{spec.name}:")
                for item_v in value:
                    lines.append(f"  - {item_v}")
        else:  # "str" (object items don't recurse into object-list)
            if _should_emit_multiline(value, preserve_multiline):
                lines.extend(_serialize_multiline_scalar(spec.name, value))
            else:
                lines.append(f"{spec.name}: {_serialize_scalar(spec, value)}")
    return lines


def build_output(meta: dict, schema: FrontmatterSchema, preserve_multiline: bool = False) -> str:
    """Build a VS Code frontmatter block from *meta* filtered by *schema*.

    Iterates *schema* fields in declaration order.  Fields present in *meta*
    but absent from *schema* are silently dropped.

    Serialisation rules:

    * ``"str"``         — optionally single-quoted, whitespace-normalised, truncated.
    * ``"bool"``        — ``true`` / ``false`` (VS Code requires lowercase).
    * ``"list"``        — YAML block sequence (``  - item`` per element).
    * ``"object-list"`` — YAML block sequence of mappings.  When the field's
                          :attr:`~vstack.frontmatter.FieldSpec.item_schema`
                          is set, each item is ordered and filtered by that
                          schema; otherwise item keys are written in natural order.
    """
    lines = ["---"]
    for spec in schema.fields:
        value = meta.get(spec.name)
        if value is None:
            continue

        if spec.type == "bool":
            lines.append(f"{spec.name}: {_serialize_bool(value)}")

        elif spec.type == "list":
            if isinstance(value, list) and value:
                lines.append(f"{spec.name}:")
                for item in value:
                    lines.append(f"  - {item}")

        elif spec.type == "object-list":
            if isinstance(value, list) and value:
                lines.append(f"{spec.name}:")
                for item in value:
                    if not isinstance(item, dict):
                        continue
                    obj_lines = _serialize_object(
                        item,
                        spec.item_schema,
                        preserve_multiline=preserve_multiline,
                    )
                    for i, obj_line in enumerate(obj_lines):
                        prefix = "  - " if i == 0 else "    "
                        lines.append(f"{prefix}{obj_line}")

        elif spec.type == "raw":
            raw_str = str(value).strip() if value is not None else ""
            if raw_str:
                lines.append(f"{spec.name}:")
                for raw_line in str(value).split("\n"):
                    lines.append(raw_line)

        else:  # "str"
            if _should_emit_multiline(value, preserve_multiline):
                lines.extend(_serialize_multiline_scalar(spec.name, value))
            else:
                lines.append(f"{spec.name}: {_serialize_scalar(spec, value)}")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)
