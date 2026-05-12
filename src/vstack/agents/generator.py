"""AgentGenerator — generator for agent artifacts with work-items support.

Import :class:`AgentGenerator` to get a generator pre-configured for the
``agents`` artifact type.  The generator extends
:class:`~vstack.artifacts.generator.GenericArtifactGenerator` with
per-template placeholder injection that builds the ``## work items``
subsections from each agent's ``config.yaml`` ``items:`` block.

Placeholder tokens injected per template:

``{{AGENT_ARTIFACTS_INPUT}}``
    Markdown ``### input`` block (header + table) built from ``items.input``,
    or an empty string when no input entries are configured.

``{{AGENT_ARTIFACTS_OUTPUT}}``
    Markdown ``### output`` block (header + table) built from ``items.output``,
    or an empty string when no output entries are configured.

``{{AGENT_ARTIFACTS_INPUT_COMMENTS}}``
    Verbatim text from ``items.input_comments``, or an empty string.

``{{AGENT_ARTIFACTS_OUTPUT_COMMENTS}}``
    Verbatim text from ``items.output_comments``, or an empty string.

Path construction rules
-----------------------
Input items in ``items.input`` are relative to :data:`~vstack.constants.ARTIFACTS_DOCS_ROOT`
(default ``"docs"``), so ``product/**/*.md`` renders as ``docs/product/**/*.md``.

Output items in ``items.output`` are interpreted as follows:

- When ``items.dir`` is set: items are relative to ``{root}/{dir}/``, e.g.
  ``overview.md`` → ``docs/architecture/overview.md``.
- When an item (string or ``path`` key) starts with ``./``, the ``./`` prefix is
  stripped and the remainder is used verbatim — allowing paths outside the docs
  root (e.g. ``./src/**/*``, ``./tests/**/*``).
- When ``items.dir`` is absent: all output items are used verbatim.

Backward compatibility
----------------------
Legacy ``artifacts:`` blocks in agent template ``config.yaml`` files are still
accepted. When both ``items:`` and ``artifacts:`` are present, ``items:`` takes
precedence.
"""

from __future__ import annotations

import warnings
from pathlib import Path

from vstack.agents.config import AGENT_TYPE
from vstack.artifacts.generator import GenericArtifactGenerator
from vstack.constants import ARTIFACTS_DOCS_ROOT, TEMPLATES_ROOT


class AgentGenerator(GenericArtifactGenerator):
    """Generate agent artifacts using the built-in agent type configuration."""

    _legacy_items_block_warned = False

    def __init__(
        self,
        templates_root: Path | None = None,
        *,
        items_root: str = ARTIFACTS_DOCS_ROOT,
        artifacts_root: str | None = None,
        workflow_stages: list[dict] | None = None,
        workflow_mode: str = "agentic",
    ) -> None:
        """Create an agent generator bound to *templates_root*.

        Args:
            templates_root: Root directory containing the source templates.
                When ``None``, the built-in package template root is used.
            items_root: Root directory for all agent work-item paths.  Defaults
                to :data:`~vstack.constants.ARTIFACTS_DOCS_ROOT`.  Override
                via ``items.root`` in ``.vstack/config.yaml`` to relocate
                generated item paths (e.g. ``"documentation"`` instead of
                ``"docs"``).
            artifacts_root: Deprecated alias for ``items_root``. Retained for
                backward compatibility.
            workflow_stages: Ordered list of pipeline stage dicts read from
                ``workflow.stages`` in ``.vstack/config.yaml``.  Each dict has
                ``role`` and ``gate`` string keys, a ``handoffs`` key containing
                a list of dicts with ``prompt``, ``agent``, and ``label`` string
                keys, and an optional ``hitl`` string key.  When ``None`` or
                empty the generator falls back to v3 behaviour: a generic
                handoff label without an explicit ``agent:`` target.
            workflow_mode: Workflow execution mode read from
                ``workflow.mode`` in ``.vstack/config.yaml``. Supported values
                are ``manual``, ``agentic``, and ``hybrid``. In ``agentic``
                mode, worker-agent handoff buttons are omitted.
        """
        super().__init__(
            AGENT_TYPE, templates_root if templates_root is not None else TEMPLATES_ROOT
        )
        if artifacts_root is not None:
            self.items_root = artifacts_root
        else:
            self.items_root = items_root
        # Backward-compatible attribute used by older tests/callers.
        self.artifacts_root = self.items_root
        self.workflow_stages: list[dict] = workflow_stages or []
        self.workflow_mode = workflow_mode.strip().lower()

    def find_templates(self) -> list[Path]:
        """Return agent template dirs filtered by workflow mode.

        In ``manual`` mode, the planner coordinator agent is not generated.
        In ``agentic`` and ``hybrid`` modes, planner is generated alongside
        worker agents.
        """
        templates = super().find_templates()
        if self.workflow_mode != "manual":
            return templates
        return [p for p in templates if p.name != "planner"]

    def template_partials(self, tmpl_dir: Path) -> dict[str, str]:
        """Inject per-template work-item placeholder tokens.

        Returns a dict with five keys:
        ``AGENT_ARTIFACTS_INPUT``, ``AGENT_ARTIFACTS_OUTPUT``,
        ``AGENT_ARTIFACTS_INPUT_COMMENTS``, ``AGENT_ARTIFACTS_OUTPUT_COMMENTS``,
        and ``AGENT_ARTIFACTS_BASELINE``.
        """

        artifact_config = self.load_artifact_config(tmpl_dir)
        items = artifact_config.get("items") or {}

        # Backward compatibility: legacy ``artifacts`` block.
        if not items:
            items = artifact_config.get("artifacts") or {}
            if items and not AgentGenerator._legacy_items_block_warned:
                warnings.warn(
                    "Legacy defaults.artifacts is deprecated for agent work items; "
                    "use defaults.items instead.",
                    FutureWarning,
                    stacklevel=2,
                )
                AgentGenerator._legacy_items_block_warned = True

        if not isinstance(items, dict):
            items = {}

        doc_root = self.items_root
        agent_dir: str = str(items.get("dir", "")).strip()

        raw_inputs: list = items.get("input", [])
        if not isinstance(raw_inputs, list):
            raw_inputs = []
        raw_outputs: list = items.get("output", [])
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
            "AGENT_ARTIFACTS_INPUT_COMMENTS": str(items.get("input_comments", "") or ""),
            "AGENT_ARTIFACTS_OUTPUT_COMMENTS": str(items.get("output_comments", "") or ""),
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
        # Re-expose items at top level so template_partials can read them.
        # Fallback to legacy ``artifacts`` for backward compatibility.
        if "items" not in config:
            items_from_defaults = defaults.get("items")
            if items_from_defaults:
                config["items"] = items_from_defaults
            elif "artifacts" not in config:
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
        # In agentic mode the planner orchestrates stage progression, so worker
        # agents should not expose forward handoff buttons.
        if self.workflow_mode == "agentic" and agent_role != "planner":
            return []

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

        stage_by_role = {
            str(stage.get("role", "")).strip(): stage for stage in self.workflow_stages
        }
        if agent_role not in stage_by_role:
            return []

        dependencies_by_role: dict[str, list[str]] = {}
        ordered_roles = [str(stage.get("role", "")).strip() for stage in self.workflow_stages]
        role_set = set(ordered_roles)
        for index, role in enumerate(ordered_roles):
            stage = stage_by_role.get(role, {})
            if "depends_on" in stage:
                raw_depends_on = stage.get("depends_on", [])
                depends_on = raw_depends_on if isinstance(raw_depends_on, list) else []
                normalized = []
                for dep in depends_on:
                    dep_role = str(dep).strip()
                    if dep_role and dep_role in role_set and dep_role not in normalized:
                        normalized.append(dep_role)
                dependencies_by_role[role] = normalized
            elif index > 0:
                dependencies_by_role[role] = [ordered_roles[index - 1]]
            else:
                dependencies_by_role[role] = []

        next_roles = [
            role for role in ordered_roles if agent_role in dependencies_by_role.get(role, [])
        ]
        primary_next_role = next_roles[0] if next_roles else ""

        stage_handoffs: list[dict[str, str]] = stage_by_role[agent_role].get("handoffs", [])
        if not isinstance(stage_handoffs, list):
            stage_handoffs = []

        # If workflow stages are configured but this stage has no explicit
        # handoffs block, fall back to the agent's own default prompt.
        if not stage_handoffs:
            if not handoff_prompt.strip():
                return []
            if not next_roles:
                return []
            return [
                {
                    "label": f"Go to next stage: {next_role.capitalize()}",
                    "agent": next_role,
                    "prompt": handoff_prompt.strip(),
                }
                for next_role in next_roles
            ]

        result: list[dict[str, str]] = []
        agent_override_applied = False

        for h in stage_handoffs:
            if not isinstance(h, dict):
                continue
            h_agent = str(h.get("agent", "") or "").strip()
            target_agent = h_agent or primary_next_role
            if not target_agent:
                continue

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

        :param raw_outputs: List of strings or dicts from ``items.output``.
        :param agent_dir: Subdirectory for this agent (e.g. ``"architecture"``).
            When empty, output paths are used verbatim.
        :returns: List of ``{"path": ..., "notes": ..., "baseline": ...}`` dicts.
        """
        doc_root = self.items_root
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

        Produces a single-column ``Item`` table when no entry has notes,
        or a two-column ``Item | Notes`` table when any entry does.
        All rows are padded to equal column widths.
        """
        cells = [f"`{e['path']}`" for e in entries]
        notes_cells = [str(e.get("notes", "")) for e in entries]
        has_notes = any(notes_cells)

        if has_notes:
            art_w = max(len("Item"), *(len(c) for c in cells))
            notes_w = max(len("Notes"), *(len(n) for n in notes_cells))
            lines = [
                f"| {'Item':<{art_w}} | {'Notes':<{notes_w}} |",
                f"| {'-' * art_w} | {'-' * notes_w} |",
                *(
                    f"| {cell:<{art_w}} | {note:<{notes_w}} |"
                    for cell, note in zip(cells, notes_cells)
                ),
            ]
        else:
            col_w = max(len("Item"), *(len(c) for c in cells))
            lines = [
                f"| {'Item':<{col_w}} |",
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

        Renders a table of output items flagged with ``baseline: true``.
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
