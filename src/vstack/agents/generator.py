"""AgentGenerator — generator for agent artifacts with artifacts-section support.

Import :class:`AgentGenerator` to get a generator pre-configured for the
``agents`` artifact type.  The generator extends
:class:`~vstack.artifacts.generator.GenericArtifactGenerator` with
per-template placeholder injection that builds the ``## artifacts you use``
subsections from each agent's ``config.yaml`` ``artifacts:`` block.

Placeholder tokens injected per template:

``{{AGENT_ARTIFACTS_INPUT}}``
    Markdown ``### input`` block (header + table) built from ``artifacts.input``,
    or an empty string when no input entries are configured.

``{{AGENT_ARTIFACTS_OUTPUT}}``
    Markdown ``### output`` block (header + table) built from ``artifacts.output``,
    or an empty string when no output entries are configured.

``{{AGENT_ARTIFACTS_INPUT_COMMENTS}}``
    Verbatim text from ``artifacts.input_comments``, or an empty string.

``{{AGENT_ARTIFACTS_OUTPUT_COMMENTS}}``
    Verbatim text from ``artifacts.output_comments``, or an empty string.

Path construction rules
-----------------------
Input items in ``artifacts.input`` are relative to :data:`~vstack.constants.ARTIFACTS_DOCS_ROOT`
(default ``"docs"``), so ``product/**/*.md`` renders as ``docs/product/**/*.md``.

Output items in ``artifacts.output`` are interpreted as follows:

- When ``artifacts.dir`` is set: items are relative to ``{root}/{dir}/``, e.g.
  ``overview.md`` → ``docs/architecture/overview.md``.
- When an item (string or ``path`` key) starts with ``./``, the ``./`` prefix is
  stripped and the remainder is used verbatim — allowing paths outside the docs
  root (e.g. ``./src/**/*``, ``./tests/**/*``).
- When ``artifacts.dir`` is absent: all output items are used verbatim.
"""

from __future__ import annotations

from pathlib import Path

from vstack.agents.config import AGENT_TYPE
from vstack.artifacts.generator import GenericArtifactGenerator
from vstack.constants import ARTIFACTS_DOCS_ROOT, TEMPLATES_ROOT


class AgentGenerator(GenericArtifactGenerator):
    """Generate agent artifacts using the built-in agent type configuration."""

    def __init__(self, templates_root: Path | None = None) -> None:
        """Create an agent generator bound to *templates_root*.

        Args:
            templates_root: Root directory containing the source templates.
                When ``None``, the built-in package template root is used.
        """
        super().__init__(
            AGENT_TYPE, templates_root if templates_root is not None else TEMPLATES_ROOT
        )

    def template_partials(self, tmpl_dir: Path) -> dict[str, str]:
        """Inject per-template artifact placeholder tokens.

        Returns a dict with four keys:
        ``AGENT_ARTIFACTS_INPUT``, ``AGENT_ARTIFACTS_OUTPUT``,
        ``AGENT_ARTIFACTS_INPUT_COMMENTS``, ``AGENT_ARTIFACTS_OUTPUT_COMMENTS``.
        """
        from vstack.frontmatter import FrontmatterParser

        artifact_config = self.load_artifact_config(tmpl_dir)
        artifacts = artifact_config.get("artifacts") or {}

        # The minimal YAML parser stores nested dicts as raw indented strings.
        # Re-parse by stripping the 2-space indent that the raw-block mode preserves.
        if isinstance(artifacts, str):
            dedented = "\n".join(
                line[2:] if line.startswith("  ") else line for line in artifacts.split("\n")
            )
            artifacts = FrontmatterParser.parse_yaml(dedented) or {}

        if not isinstance(artifacts, dict):
            artifacts = {}

        doc_root = ARTIFACTS_DOCS_ROOT
        agent_dir: str = str(artifacts.get("dir", "")).strip()

        raw_inputs: list = artifacts.get("input", [])
        if not isinstance(raw_inputs, list):
            raw_inputs = []
        raw_outputs: list = artifacts.get("output", [])
        if not isinstance(raw_outputs, list):
            raw_outputs = []

        input_entries = [
            {"path": f"{doc_root}/{item}", "notes": ""}
            for item in raw_inputs
            if isinstance(item, str)
        ]
        output_entries = self._resolve_output_entries(raw_outputs, doc_root, agent_dir)

        return {
            "AGENT_ARTIFACTS_INPUT": self._build_section("input", input_entries),
            "AGENT_ARTIFACTS_OUTPUT": self._build_section("output", output_entries),
            "AGENT_ARTIFACTS_INPUT_COMMENTS": str(artifacts.get("input_comments", "") or ""),
            "AGENT_ARTIFACTS_OUTPUT_COMMENTS": str(artifacts.get("output_comments", "") or ""),
        }

    @staticmethod
    def _resolve_output_entries(
        raw_outputs: list, doc_root: str, agent_dir: str
    ) -> list[dict[str, str]]:
        """Resolve raw output config items to display-path dicts.

        :param raw_outputs: List of strings or dicts from ``artifacts.output``.
        :param doc_root: Global artifacts root directory (e.g. ``"docs"``).
        :param agent_dir: Subdirectory for this agent (e.g. ``"architecture"``).
            When empty, output paths are used verbatim.
        :returns: List of ``{"path": ..., "notes": ...}`` dicts.
        """
        result: list[dict[str, str]] = []
        for item in raw_outputs:
            if isinstance(item, str):
                path, notes = item, ""
            elif isinstance(item, dict):
                path, notes = str(item.get("path", "")), str(item.get("notes", ""))
            else:
                continue

            if path.startswith("./"):
                # Explicit project-root path; strip marker and use verbatim.
                display = path[2:]
            elif agent_dir:
                display = f"{doc_root}/{agent_dir}/{path}"
            else:
                display = path

            result.append({"path": display, "notes": notes})
        return result

    @staticmethod
    def _build_table(entries: list[dict[str, str]]) -> str:
        """Build a Markdown table from normalised artifact entry dicts.

        Produces a single-column ``Artifact`` table when no entry has notes,
        or a two-column ``Artifact | Notes`` table when any entry does.
        All rows are padded to equal column widths.
        """
        cells = [f"`{e['path']}`" for e in entries]
        notes_cells = [e.get("notes", "") for e in entries]
        has_notes = any(notes_cells)

        if has_notes:
            art_w = max(len("Artifact"), *(len(c) for c in cells))
            notes_w = max(len("Notes"), *(len(n) for n in notes_cells))
            lines = [
                f"| {'Artifact':<{art_w}} | {'Notes':<{notes_w}} |",
                f"| {'-' * art_w} | {'-' * notes_w} |",
                *(
                    f"| {cell:<{art_w}} | {note:<{notes_w}} |"
                    for cell, note in zip(cells, notes_cells)
                ),
            ]
        else:
            col_w = max(len("Artifact"), *(len(c) for c in cells))
            lines = [
                f"| {'Artifact':<{col_w}} |",
                f"| {'-' * col_w} |",
                *(f"| {cell:<{col_w}} |" for cell in cells),
            ]

        return "\n".join(lines)

    @staticmethod
    def _build_section(heading: str, entries: list[dict[str, str]]) -> str:
        """Build a ``### {heading}`` Markdown subsection with a table.

        Returns an empty string when *entries* is empty.
        """
        if not entries:
            return ""
        return f"### {heading}\n\n{AgentGenerator._build_table(entries)}"
