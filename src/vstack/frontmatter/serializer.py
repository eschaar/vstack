"""Frontmatter serializer — schema-filtered YAML output.

:class:`FrontmatterSerializer` converts a metadata dict to a ``---`` / ``---`` YAML
frontmatter block, filtered and ordered by a :class:`~vstack.frontmatter.FrontmatterSchema`.
Fields absent from the schema are silently dropped so generator-internal
metadata (``version``, etc.) never leaks into output files.

Main entry point: :meth:`FrontmatterSerializer.serialize`.
"""

from __future__ import annotations

import re
import textwrap

from vstack.frontmatter.schema import FieldSpec, FrontmatterSchema


class FrontmatterSerializer:
    """Frontmatter serializer — converts metadata dict to YAML.

    Instantiate once, then call :meth:`serialize` to render frontmatter.
    No mutable instance state; state exists only for the duration of a single call.
    """

    def _serialize_scalar(self, spec: FieldSpec, value: object) -> str:
        """Serialize a single ``"str"`` value according to *spec* options."""
        text = str(value)
        if spec.normalize_whitespace:
            text = re.sub(r"\s+", " ", text).strip()
        if spec.max_length:
            text = text[: spec.max_length]
        if spec.quoted:
            return f"'{text.replace(chr(39), chr(39) * 2)}'"
        return text

    def _serialize_multiline_scalar(
        self, name: str, value: object, base_indent: str = ""
    ) -> list[str]:
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

    def _should_emit_multiline(self, value: object, preserve_multiline: bool) -> bool:
        """Return True when scalar should be emitted as a folded block string."""
        if not preserve_multiline:
            return False
        text = str(value)
        return "\n" in text or len(text) > 90

    def _serialize_bool(self, value: object) -> str:
        """Return ``"true"`` or ``"false"`` regardless of input representation."""
        if isinstance(value, bool):
            return str(value).lower()
        return "true" if str(value).strip().lower() == "true" else "false"

    def _serialize_object_unschematized(
        self, item: dict, preserve_multiline: bool = False
    ) -> list[str]:
        """Serialize object without schema — accepts any keys/values."""
        lines: list[str] = []
        for k, v in item.items():
            v_str = str(v).strip()
            if isinstance(v, bool) or v_str.lower() in ("true", "false"):
                lines.append(f"{k}: {self._serialize_bool(v)}")
            elif self._should_emit_multiline(v, preserve_multiline):
                lines.extend(self._serialize_multiline_scalar(k, v))
            else:
                safe = v_str.replace("'", "''")
                lines.append(f"{k}: '{safe}'")
        return lines

    def _serialize_object_field_pair(
        self,
        spec: FieldSpec,
        value: object,
        preserve_multiline: bool = False,
    ) -> list[str]:
        """Render one field from a schematized object."""
        if spec.type == "bool":
            return [f"{spec.name}: {self._serialize_bool(value)}"]
        if spec.type == "list":
            if isinstance(value, list) and value:
                lines = [f"{spec.name}:"]
                lines.extend(f"  - {item_v}" for item_v in value)
                return lines
            return []
        if self._should_emit_multiline(value, preserve_multiline):
            return self._serialize_multiline_scalar(spec.name, value)
        return [f"{spec.name}: {self._serialize_scalar(spec, value)}"]

    def _serialize_object(
        self,
        item: dict,
        item_schema: FrontmatterSchema | None,
        preserve_multiline: bool = False,
    ) -> list[str]:
        """Serialize one object-list item to YAML lines (without leading ``  - ``)."""
        if item_schema is None:
            return self._serialize_object_unschematized(item, preserve_multiline)

        pairs = [
            (spec, item.get(spec.name))
            for spec in item_schema.fields
            if item.get(spec.name) is not None
        ]
        ordered_lines: list[str] = []
        for spec, value in pairs:
            ordered_lines.extend(self._serialize_object_field_pair(spec, value, preserve_multiline))
        return ordered_lines

    def _append_object_list_items(
        self,
        lines: list[str],
        value: list,
        item_schema: FrontmatterSchema | None,
        preserve_multiline: bool = False,
    ) -> None:
        """Append object-list items to lines with proper YAML indentation."""
        for item in value:
            if not isinstance(item, dict):
                continue
            obj_lines = self._serialize_object(
                item,
                item_schema,
                preserve_multiline=preserve_multiline,
            )
            for i, obj_line in enumerate(obj_lines):
                prefix = "  - " if i == 0 else "    "
                lines.append(f"{prefix}{obj_line}")

    def _append_raw_field(self, lines: list[str], name: str, value: object) -> None:
        """Append raw field value (unserialized) to lines."""
        raw_str = str(value).strip() if value is not None else ""
        if raw_str:
            lines.append(f"{name}:")
            for raw_line in str(value).split("\n"):
                lines.append(raw_line)

    def _append_field_by_type(
        self,
        lines: list[str],
        spec: FieldSpec,
        value: object,
        preserve_multiline: bool = False,
    ) -> None:
        """Dispatch field rendering by type."""
        if spec.type == "bool":
            lines.append(f"{spec.name}: {self._serialize_bool(value)}")
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
                self._append_object_list_items(
                    lines,
                    value,
                    spec.item_schema,
                    preserve_multiline=preserve_multiline,
                )
            return
        if spec.type == "raw":
            self._append_raw_field(lines, spec.name, value)
            return
        if self._should_emit_multiline(value, preserve_multiline):
            lines.extend(self._serialize_multiline_scalar(spec.name, value))
        else:
            lines.append(f"{spec.name}: {self._serialize_scalar(spec, value)}")

    def serialize(
        self,
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
            self._append_field_by_type(lines, spec, value, preserve_multiline)
        lines.append("---")
        lines.append("")
        return "\n".join(lines)
