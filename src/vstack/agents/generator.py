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

    def __init__(
        self,
        templates_root: Path | None = None,
        *,
        artifacts_root: str = ARTIFACTS_DOCS_ROOT,
        workflow_stages: list[dict] | None = None,
    ) -> None:
        """Create an agent generator bound to *templates_root*.

        Args:
            templates_root: Root directory containing the source templates.
                When ``None``, the built-in package template root is used.
            artifacts_root: Root directory for all agent artifacts.  Defaults
                to :data:`~vstack.constants.ARTIFACTS_DOCS_ROOT`.  Override
                via ``artifacts.root`` in ``.vstack/config.yaml`` to relocate
                generated artifact paths (e.g. ``"documentation"`` instead of
                ``"docs"``).
            workflow_stages: Ordered list of pipeline stage dicts read from
                ``workflow.stages`` in ``.vstack/config.yaml``.  Each dict has
                ``role`` and ``gate`` string keys, a ``handoffs`` key containing
                a list of dicts with ``prompt``, ``agent``, and ``label`` string
                keys, and an optional ``hitl`` string key.  When ``None`` or
                empty the generator falls back to v3 behaviour: a generic
                handoff label without an explicit ``agent:`` target.
        """
        super().__init__(
            AGENT_TYPE, templates_root if templates_root is not None else TEMPLATES_ROOT
        )
        self.artifacts_root = artifacts_root
        self.workflow_stages: list[dict] = workflow_stages or []

    def template_partials(self, tmpl_dir: Path) -> dict[str, str]:
        """Inject per-template artifact placeholder tokens.

        Returns a dict with five keys:
        ``AGENT_ARTIFACTS_INPUT``, ``AGENT_ARTIFACTS_OUTPUT``,
        ``AGENT_ARTIFACTS_INPUT_COMMENTS``, ``AGENT_ARTIFACTS_OUTPUT_COMMENTS``,
        and ``AGENT_ARTIFACTS_BASELINE``.
        """

        artifact_config = self.load_artifact_config(tmpl_dir)
        artifacts = artifact_config.get("artifacts") or {}

        if not isinstance(artifacts, dict):
            artifacts = {}

        doc_root = self.artifacts_root
        agent_dir: str = str(artifacts.get("dir", "")).strip()

        raw_inputs: list = artifacts.get("input", [])
        if not isinstance(raw_inputs, list):
            raw_inputs = []
        raw_outputs: list = artifacts.get("output", [])
        if not isinstance(raw_outputs, list):
            raw_outputs = []

        input_entries: list[dict[str, str | bool]] = [
            {"path": f"{doc_root}/{item}", "notes": "", "baseline": False}
            for item in raw_inputs
            if isinstance(item, str)
        ]
        output_entries = self._resolve_output_entries(raw_outputs, agent_dir)
        baseline_entries = [e for e in output_entries if e.get("baseline")]

        return {
            "AGENT_ARTIFACTS_INPUT": self._build_section("input", input_entries),
            "AGENT_ARTIFACTS_OUTPUT": self._build_section("output", output_entries),
            "AGENT_ARTIFACTS_INPUT_COMMENTS": str(artifacts.get("input_comments", "") or ""),
            "AGENT_ARTIFACTS_OUTPUT_COMMENTS": str(artifacts.get("output_comments", "") or ""),
            "AGENT_ARTIFACTS_BASELINE": self._build_baseline_section(baseline_entries),
        }

    def _extract_defaults(self, config: dict) -> dict:
        """Return the ``defaults:`` block from *config*, or an empty dict.

        PyYAML always returns ``defaults:`` as a dict when the block is
        present in ``config.yaml``.  Non-dict values (e.g. ``None`` when the
        key is absent) are normalised to ``{}``.

        :param config: Raw config dict as returned by ``load_artifact_config``.
        :returns: Parsed ``defaults`` dict, or ``{}`` when absent or not a mapping.
        """
        defaults = config.get("defaults") or {}
        return defaults if isinstance(defaults, dict) else {}

    def load_artifact_config(self, tmpl_dir: Path) -> dict:
        """Load agent config and inject workflow-derived ``handoffs`` into the result.

        Extends :meth:`~vstack.artifacts.generator.GenericArtifactGenerator.load_artifact_config`
        by extracting the ``defaults:`` block from the agent's ``config.yaml``,
        resolving the handoff prompt from ``defaults.handoffs.prompt``, and
        injecting a fully resolved ``handoffs`` list that the frontmatter
        serializer can emit directly.  The ``defaults:`` key is removed from the
        config so it never appears in the generated ``agent.md`` frontmatter.

        When no workflow stages are configured the fallback ``handoffs`` list
        uses the agent's own prompt without an explicit ``agent:`` target,
        preserving v3 behaviour.
        """
        config = super().load_artifact_config(tmpl_dir)
        agent_role = tmpl_dir.name
        defaults = self._extract_defaults(config)
        config.pop("defaults", None)
        # Re-expose artifacts at top level so template_partials can read them
        # via the standard artifact_config.get("artifacts") path.
        if "artifacts" not in config:
            artifacts_from_defaults = defaults.get("artifacts")
            if artifacts_from_defaults:
                config["artifacts"] = artifacts_from_defaults
        handoffs_block = defaults.get("handoffs") or {}
        if isinstance(handoffs_block, dict):
            handoff_prompt: str = str(handoffs_block.get("prompt", "") or "")
        else:
            handoff_prompt = ""
        handoffs = self._resolve_handoffs(agent_role, handoff_prompt)
        if handoffs:
            config["handoffs"] = handoffs
        return config

    def _resolve_handoffs(self, agent_role: str, handoff_prompt: str) -> list[dict[str, str]]:
        """Resolve the handoffs list for *agent_role* from workflow stages.

        Each workflow stage may define one or more handoffs under
        ``workflow.stages[].handoffs``.  Each handoff dict has ``prompt``
        (required), and optional ``agent`` and ``label`` overrides.

        When no explicit ``agent`` is set on a handoff, it defaults to the
        next stage in the workflow sequence.  When no explicit ``label`` is
        set, it defaults to ``"Go to next stage: {Agent}"``.

        The *handoff_prompt* argument (from the agent template's own
        ``defaults.handoffs.prompt``) overrides the ``prompt`` of the first
        handoff that targets the natural next stage (no ``agent`` override),
        allowing per-template prompt customisation without editing the central
        config.

        :param agent_role: Role name (template directory name).
        :param handoff_prompt: Raw prompt text from the agent's ``config.yaml``.
        :returns: List of handoff dicts suitable for frontmatter serialization,
            or an empty list when this is the last stage or no prompts exist.
        """
        if not self.workflow_stages:
            # No workflow configured — emit a generic handoff without an
            # explicit ``agent:`` target when a prompt is available, so that
            # projects without a workflow: block still get a usable handoff
            # entry rather than silently dropping the configured prompt.
            if not handoff_prompt.strip():
                return []
            return [
                {
                    "label": "Continue to next stage",
                    "prompt": handoff_prompt.strip(),
                }
            ]

        roles = [s["role"] for s in self.workflow_stages]
        try:
            idx = roles.index(agent_role)
        except ValueError:
            return []
        if idx >= len(roles) - 1:
            return []
        next_role = roles[idx + 1]

        stage_handoffs: list[dict[str, str]] = self.workflow_stages[idx].get("handoffs", [])
        if not isinstance(stage_handoffs, list):
            stage_handoffs = []

        result: list[dict[str, str]] = []
        agent_override_applied = False

        for h in stage_handoffs:
            if not isinstance(h, dict):
                continue
            h_agent = str(h.get("agent", "") or "").strip()
            target_agent = h_agent or next_role

            # Apply per-agent handoff_prompt override to the first handoff that
            # targets the natural next stage (no explicit agent override).
            if handoff_prompt.strip() and not h_agent and not agent_override_applied:
                prompt = handoff_prompt.strip()
                agent_override_applied = True
            else:
                prompt = str(h.get("prompt", "") or "").strip()

            if not prompt:
                continue

            label = str(h.get("label", "") or "").strip() or (
                f"Go to next stage: {target_agent.capitalize()}"
            )
            result.append({"label": label, "agent": target_agent, "prompt": prompt})

        return result

    def _resolve_output_entries(
        self, raw_outputs: list, agent_dir: str
    ) -> list[dict[str, str | bool]]:
        """Resolve raw output config items to display-path dicts.

        :param raw_outputs: List of strings or dicts from ``artifacts.output``.
        :param agent_dir: Subdirectory for this agent (e.g. ``"architecture"``).
            When empty, output paths are used verbatim.
        :returns: List of ``{"path": ..., "notes": ..., "baseline": ...}`` dicts.
        """
        doc_root = self.artifacts_root
        result: list[dict[str, str | bool]] = []
        for item in raw_outputs:
            if isinstance(item, str):
                path, notes, baseline = item, "", False
            elif isinstance(item, dict):
                path = str(item.get("path", ""))
                notes = str(item.get("notes", ""))
                baseline = bool(item.get("baseline", False))
            else:
                continue

            if path.startswith("./"):
                # Explicit project-root path; strip marker and use verbatim.
                display = path[2:]
            elif agent_dir:
                display = f"{doc_root}/{agent_dir}/{path}"
            else:
                display = path

            result.append({"path": display, "notes": notes, "baseline": baseline})
        return result

    def _build_table(self, entries: list[dict[str, str | bool]]) -> str:
        """Build a Markdown table from normalised artifact entry dicts.

        Produces a single-column ``Artifact`` table when no entry has notes,
        or a two-column ``Artifact | Notes`` table when any entry does.
        All rows are padded to equal column widths.
        """
        cells = [f"`{e['path']}`" for e in entries]
        notes_cells = [str(e.get("notes", "")) for e in entries]
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

    def _build_section(self, heading: str, entries: list[dict[str, str | bool]]) -> str:
        """Build a ``### {heading}`` Markdown subsection with a table.

        Returns an empty string when *entries* is empty.
        """
        if not entries:
            return ""
        return f"### {heading}\n\n{self._build_table(entries)}"

    def _build_baseline_section(self, entries: list[dict[str, str | bool]]) -> str:
        """Build the ``### baseline docs you maintain`` subsection.

        Renders a table of output artifacts flagged with ``baseline: true``.
        Returns an empty string when no baseline entries are present.

        :param entries: Resolved output entries where ``baseline`` is ``True``.
        :returns: Markdown subsection string, or empty string.
        """
        if not entries:
            return ""
        return (
            "### baseline docs you maintain\n\n"
            "Keep these files current. Update them whenever the relevant scope, "
            "design, or implementation changes — do not let them go stale.\n\n"
            f"{self._build_table(entries)}"
        )

    def _build_handoffs(self, agent_role: str, handoff_prompt: str) -> str:
        """Build the ``handoffs:`` frontmatter block for this agent.

        .. deprecated::
            Use :meth:`_resolve_handoffs` instead.  This method is retained
            only for backward compatibility with any direct call sites in tests.
        """
        entries = self._resolve_handoffs(agent_role, handoff_prompt)
        if not entries:
            return ""
        entry = entries[0]
        lines = [f'handoffs:\n  - label: "{entry["label"]}"']
        if "agent" in entry:
            lines.append(f"    agent: {entry['agent']}")
        lines.append("    prompt: >")
        lines.extend(f"      {line}" for line in entry["prompt"].splitlines())
        return "\n".join(lines)
