"""Frontmatter serializer — schema-filtered YAML output.

:class:`FrontmatterSerializer` converts a metadata dict to a ``---`` / ``---`` YAML
frontmatter block, filtered and ordered by a :class:`~vstack.frontmatter.FrontmatterSchema`.
Fields absent from the schema are silently dropped so generator-internal
metadata (``version``, etc.) never leaks into output files.

:func:`build_output` is a backward-compatible wrapper for :meth:`FrontmatterSerializer.serialize`.
"""

from __future__ import annotations

import re
import textwrap

from vstack.frontmatter.schema import FieldSpec, FrontmatterSchema


class FrontmatterSerializer:
    """Stateless frontmatter serializer — converts metadata dict to YAML.

    No mutable instance state; class/static methods mirror the parser style
    while preserving simple call sites.
    """

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def _should_emit_multiline(value: object, preserve_multiline: bool) -> bool:
        """Return True when scalar should be emitted as a folded block string."""
        if not preserve_multiline:
            return False
        text = str(value)
        return "\n" in text or len(text) > 90

    @staticmethod
    def _serialize_bool(value: object) -> str:
        """Return ``"true"`` or ``"false"`` regardless of input representation."""
        if isinstance(value, bool):
            return str(value).lower()
        return "true" if str(value).strip().lower() == "true" else "false"

    @staticmethod
    def _serialize_object_unschematized(item: dict, preserve_multiline: bool = False) -> list[str]:
        """Serialize object without schema — accepts any keys/values."""
        lines: list[str] = []
        for k, v in item.items():
            v_str = str(v).strip()
            if isinstance(v, bool) or v_str.lower() in ("true", "false"):
                lines.append(f"{k}: {FrontmatterSerializer._serialize_bool(v)}")
            elif FrontmatterSerializer._should_emit_multiline(v, preserve_multiline):
                lines.extend(FrontmatterSerializer._serialize_multiline_scalar(k, v))
            else:
                safe = v_str.replace("'", "''")
                lines.append(f"{k}: '{safe}'")
        return lines

    @staticmethod
    def _serialize_object_field_pair(
        spec: FieldSpec,
        value: object,
        preserve_multiline: bool = False,
    ) -> list[str]:
        """Render one field from a schematized object."""
        if spec.type == "bool":
            return [f"{spec.name}: {FrontmatterSerializer._serialize_bool(value)}"]
        if spec.type == "list":
            if isinstance(value, list) and value:
                lines = [f"{spec.name}:"]
                lines.extend(f"  - {item_v}" for item_v in value)
                return lines
            return []
        if FrontmatterSerializer._should_emit_multiline(value, preserve_multiline):
            return FrontmatterSerializer._serialize_multiline_scalar(spec.name, value)
        return [f"{spec.name}: {FrontmatterSerializer._serialize_scalar(spec, value)}"]

    @classmethod
    def _serialize_object(
        cls,
        item: dict,
        item_schema: FrontmatterSchema | None,
        preserve_multiline: bool = False,
    ) -> list[str]:
        """Serialize one object-list item to YAML lines (without leading ``  - ``)."""
        if item_schema is None:
            return cls._serialize_object_unschematized(item, preserve_multiline)

        pairs = [
            (spec, item.get(spec.name))
            for spec in item_schema.fields
            if item.get(spec.name) is not None
        ]
        ordered_lines: list[str] = []
        for spec, value in pairs:
            ordered_lines.extend(cls._serialize_object_field_pair(spec, value, preserve_multiline))
        return ordered_lines

    @staticmethod
    def _append_object_list_items(
        lines: list[str],
        value: list,
        item_schema: FrontmatterSchema | None,
        preserve_multiline: bool = False,
    ) -> None:
        """Append object-list items to lines with proper YAML indentation."""
        for item in value:
            if not isinstance(item, dict):
                continue
            obj_lines = FrontmatterSerializer._serialize_object(
                item,
                item_schema,
                preserve_multiline=preserve_multiline,
            )
            for i, obj_line in enumerate(obj_lines):
                prefix = "  - " if i == 0 else "    "
                lines.append(f"{prefix}{obj_line}")

    @staticmethod
    def _append_raw_field(lines: list[str], name: str, value: object) -> None:
        """Append raw field value (unserialized) to lines."""
        raw_str = str(value).strip() if value is not None else ""
        if raw_str:
            lines.append(f"{name}:")
            for raw_line in str(value).split("\n"):
                lines.append(raw_line)

    @staticmethod
    def _append_field_by_type(
        lines: list[str],
        spec: FieldSpec,
        value: object,
        preserve_multiline: bool = False,
    ) -> None:
        """Dispatch field rendering by type."""
        if spec.type == "bool":
            lines.append(f"{spec.name}: {FrontmatterSerializer._serialize_bool(value)}")
            return
        if spec.type == "list":
            if isinstance(value, list) and value:
                lines.append(f"{spec.name}:")
                for item in value:
                    lines.append(f"  - {item}")
            return
        if spec.type == "object-list":
            if isinstance(value, list) and value:
                lines.append(f"{spec.name}:")
                FrontmatterSerializer._append_object_list_items(
                    lines,
                    value,
                    spec.item_schema,
                    preserve_multiline=preserve_multiline,
                )
            return
        if spec.type == "raw":
            FrontmatterSerializer._append_raw_field(lines, spec.name, value)
            return
        if FrontmatterSerializer._should_emit_multiline(value, preserve_multiline):
            lines.extend(FrontmatterSerializer._serialize_multiline_scalar(spec.name, value))
        else:
            lines.append(f"{spec.name}: {FrontmatterSerializer._serialize_scalar(spec, value)}")

    @classmethod
    def serialize(
        cls,
        meta: dict,
        schema: FrontmatterSchema,
        preserve_multiline: bool = False,
    ) -> str:
        """Serialize metadata dict to VS Code frontmatter block (YAML --- / ---)."""
        lines = ["---"]
        for spec in schema.fields:
            value = meta.get(spec.name)
            if value is None:
                continue
            cls._append_field_by_type(lines, spec, value, preserve_multiline)
        lines.append("---")
        lines.append("")
        return "\n".join(lines)


def build_output(meta: dict, schema: FrontmatterSchema, preserve_multiline: bool = False) -> str:
    """Backward-compatible wrapper; use :meth:`FrontmatterSerializer.serialize` instead."""
    return FrontmatterSerializer.serialize(
        meta,
        schema,
        preserve_multiline=preserve_multiline,
    )
