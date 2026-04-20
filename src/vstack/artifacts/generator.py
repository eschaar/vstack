"""Generic prompt-artifact generator.

:class:`GenericArtifactGenerator` renders, writes, and validates any family
of prompt artifacts (skills, agents, prompts, instructions, …) based on an
:class:`~vstack.artifacts.type_config.ArtifactTypeConfig` descriptor.

All type-specific behaviour — output filename pattern, frontmatter injection,
partial loading, auto-generated footer, required tokens — is expressed
entirely through the config rather than subclass overrides.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from vstack.artifacts.config import ArtifactTypeConfig
from vstack.artifacts.constants import AUTO_GEN_FOOTER
from vstack.artifacts.models import ArtifactResult, RenderedArtifact
from vstack.constants import VERSION
from vstack.frontmatter import FrontmatterParser, FrontmatterSerializer
from vstack.models import CheckMessage, ValidationResult

_PLACEHOLDER_RE = re.compile(r"\{\{([A-Z_]+)\}\}")
_META_COMMENT_RE = re.compile(r"<!--\s*VSTACK-META:\s*(\{.*?\})\s*-->")


class GenericArtifactGenerator:
    """Renders and validates one family of prompt artifacts.

    Args:
        type_config:     Descriptor for this artifact family.
        templates_root:  Root directory that contains per-type template subdirs
                         (e.g. the repo's ``templates/`` folder).
    """

    def __init__(self, type_config: ArtifactTypeConfig, templates_root: Path) -> None:
        """Bind a type configuration to its concrete template directories."""
        self.config = type_config
        self.templates_dir = templates_root / type_config.templates_dir
        self.partials_dir: Path | None = (
            self.templates_dir / type_config.partials_subdir
            if type_config.partials_subdir
            else None
        )
        self._partials: dict[str, str] | None = None

    # ── Placeholder resolution ────────────────────────────────────────────────

    @staticmethod
    def resolve_placeholders(text: str, resolvers: dict[str, str]) -> str:
        """Replace ``{{TOKEN}}`` placeholders using *resolvers*.

        Tokens with no matching resolver are left unchanged.
        """
        return _PLACEHOLDER_RE.sub(lambda m: resolvers.get(m.group(1), m.group(0)), text)

    @staticmethod
    def find_unresolved(text: str) -> list[str]:
        """Return a list of TOKEN names that remain unresolved in *text*."""
        return _PLACEHOLDER_RE.findall(text)

    @staticmethod
    def parse_generation_metadata(text: str) -> dict[str, str] | None:
        """Parse the ``VSTACK-META`` footer JSON, if present."""
        matches = _META_COMMENT_RE.findall(text)
        if not matches:
            return None
        try:
            data = json.loads(matches[-1])
        except json.JSONDecodeError:
            return None
        if not isinstance(data, dict):
            return None
        return {str(k): str(v) for k, v in data.items()}

    def _build_footer(self, artifact_name: str, artifact_version: str) -> str:
        """Build the AUTO-GENERATED footer plus machine-readable metadata."""
        meta = {
            "generator": "vstack",
            "vstack_version": VERSION,
            "artifact_type": self.config.type_name,
            "artifact_name": artifact_name,
            "artifact_version": artifact_version,
        }
        meta_json = json.dumps(meta, separators=(",", ":"), sort_keys=True)
        return f"{AUTO_GEN_FOOTER}<!-- VSTACK-META: {meta_json} -->\n"

    # ── Partials ──────────────────────────────────────────────────────────────

    def load_partials(self) -> dict[str, str]:
        """Load and cache partials from *partials_dir*.

        Each file stem is converted from lowercase-kebab to UPPER_SNAKE to
        form the resolver token: ``skill-context.md`` → ``SKILL_CONTEXT``.
        Returns an empty dict when *partials_dir* is ``None`` or missing.
        """
        if self._partials is None:
            self._partials = {}
            if self.partials_dir and self.partials_dir.exists():
                for path in sorted(self.partials_dir.glob("*.md")):
                    token = path.stem.upper().replace("-", "_")
                    self._partials[token] = path.read_text(encoding="utf-8").strip()
        return self._partials

    # ── Template discovery ────────────────────────────────────────────────────

    def find_templates(self) -> list[Path]:
        """Return sorted list of template *directories* under ``templates_dir``.

        A directory qualifies when it does not start with ``_`` and contains
        a file named ``config.template_filename`` (default ``template.md``).
        """
        if not self.templates_dir.exists():
            return []
        return sorted(
            p
            for p in self.templates_dir.iterdir()
            if p.is_dir()
            and not p.name.startswith("_")
            and (p / self.config.template_filename).exists()
        )

    def find_extra_files(self, tmpl_dir: Path) -> list[Path]:
        """Return all files in *tmpl_dir* that are not the template or config."""
        excluded = {self.config.template_filename, self.config.config_filename}
        return [p for p in tmpl_dir.iterdir() if p.is_file() and p.name not in excluded]

    # ── Per-artifact config ───────────────────────────────────────────────────

    def load_artifact_config(self, tmpl_dir: Path) -> dict:
        """Parse ``config.yaml`` from *tmpl_dir* if present.

        The file is parsed using the same minimal YAML subset as frontmatter.
        Returns an empty dict when the file does not exist.
        """
        config_file = tmpl_dir / self.config.config_filename
        if not config_file.exists():
            return {}
        raw = config_file.read_text(encoding="utf-8")
        return FrontmatterParser.parse_yaml(raw)

    # ── Rendering ─────────────────────────────────────────────────────────────

    def render(self, tmpl_dir: Path) -> RenderedArtifact:
        """Render a single template directory to a :class:`~vstack.artifacts.models.RenderedArtifact`.

        Precedence for frontmatter / metadata:
        1. ``config.yaml`` provides defaults.
        2. Frontmatter already present in ``template.md`` overrides config values.
        3. When *add_frontmatter* is ``True`` and the template has no frontmatter,
           frontmatter is generated from ``config.yaml``.
        """
        tmpl_file = tmpl_dir / self.config.template_filename
        content = tmpl_file.read_text(encoding="utf-8")

        # Resolve {{PLACEHOLDER}} tokens via partials
        resolved = self.resolve_placeholders(content, self.load_partials())

        # Split existing frontmatter from body
        parsed = FrontmatterParser.parse(resolved)
        existing_fm = parsed.metadata
        body = parsed.content

        # Merge: config.yaml provides defaults, template frontmatter wins
        artifact_config = self.load_artifact_config(tmpl_dir)
        meta: dict = {**artifact_config, **existing_fm} if existing_fm else dict(artifact_config)

        dir_name = tmpl_dir.name
        name = str(meta.get("name", dir_name))

        if existing_fm:
            # Template already has frontmatter — rebuild to normalise output format
            schema = self.config.frontmatter_schema
            if schema is None:
                raise ValueError(
                    f"{self.config.type_name}: frontmatter_schema must be set when add_frontmatter=True"
                )
            fm_str = FrontmatterSerializer().serialize(
                meta,
                schema,
                preserve_multiline=self.config.preserve_multiline_frontmatter,
            )
            body_str = body
        elif self.config.add_frontmatter and meta:
            # No frontmatter in template; generate it from config.yaml
            if "name" not in meta:
                meta["name"] = name
            schema = self.config.frontmatter_schema
            if schema is None:
                raise ValueError(
                    f"{self.config.type_name}: frontmatter_schema must be set when add_frontmatter=True"
                )
            fm_str = FrontmatterSerializer().serialize(
                meta,
                schema,
                preserve_multiline=self.config.preserve_multiline_frontmatter,
            )
            body_str = resolved  # full content (it contains no frontmatter)
        else:
            fm_str = ""
            body_str = resolved

        artifact_version = str((meta or {}).get("version") or VERSION)
        footer = self._build_footer(name, artifact_version) if self.config.auto_gen_footer else ""
        body_content = body_str.lstrip("\n")
        output = (fm_str + body_content + footer) if (fm_str or footer) else body_str

        return RenderedArtifact(
            name=name,
            content=output,
            source_path=tmpl_file,
            frontmatter=meta or None,
            unresolved=self.find_unresolved(output),
        )

    def render_all(self) -> list[RenderedArtifact]:
        """Render all templates to memory without writing any files."""
        return [self.render(d) for d in self.find_templates()]

    # ── Output path ───────────────────────────────────────────────────────────

    def output_path(self, name: str) -> str:
        """Compute the artifact path relative to *output_dir*.

        Example: ``"vision"`` → ``"vision/SKILL.md"`` (for skills).
        """
        return self.config.output_pattern.format(name=name)

    def install_relative_path(self, name: str) -> str:
        """Compute the artifact path relative to the install root (``.github/``).

        Example: ``"vision"`` → ``"skills/vision/SKILL.md"``.
        """
        return f"{self.config.output_subdir}/{self.output_path(name)}"

    # ── Generation ────────────────────────────────────────────────────────────

    def generate(self, output_dir: Path) -> ArtifactResult:
        """Render all templates, write output files, and return an :class:`~vstack.artifacts.models.ArtifactResult`.

        Extra files alongside ``template.md`` (e.g. ``example.sh``) are copied
        verbatim to the output directory.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        artifacts = self.render_all()
        for artifact in artifacts:
            out = output_dir / self.output_path(artifact.name)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(artifact.content, encoding="utf-8")
            for extra in self.find_extra_files(artifact.source_path.parent):
                shutil.copy2(extra, out.parent / extra.name)
        unresolved_warnings = [
            f"WARNING: {a.name}/{self.config.template_filename} has unresolved placeholders: {a.unresolved}"
            for a in artifacts
            if a.unresolved
        ]
        verification = self.verify_output(output_dir, [a.name for a in artifacts])
        return ArtifactResult(
            artifacts=artifacts,
            unresolved_warnings=unresolved_warnings,
            verification=verification,
        )

    # ── Validation ────────────────────────────────────────────────────────────

    def verify_input(self, expected_names: list[str] | None = None) -> ValidationResult:
        """Verify source templates before generation.

        Checks performed:
        * expected templates exist when ``expected_names`` is provided.
        * frontmatter metadata satisfies the configured schema (or required
            fallback fields when no schema is configured).
        * metadata ``name`` matches the template directory name.
        * placeholders used in template content are registered in
            ``ArtifactTypeConfig.placeholders`` (when configured) and mapped.
        """
        result = ValidationResult()
        templates = self.find_templates()
        tmpl_by_name = {d.name: d for d in templates}
        prefix = f"templates/{self.config.templates_dir}"

        def ok(msg: str) -> None:
            """Record a passing validation message."""
            result.messages.append(CheckMessage("pass", msg))

        def fail(msg: str) -> None:
            """Record a failing validation message."""
            result.messages.append(CheckMessage("fail", msg))

        if expected_names is not None:
            for name in expected_names:
                if name in tmpl_by_name:
                    ok(f"{prefix}/{name}/{self.config.template_filename} exists")
                else:
                    fail(f"{prefix}/{name}/{self.config.template_filename} MISSING")

        for name, tmpl_dir in tmpl_by_name.items():
            content = (tmpl_dir / self.config.template_filename).read_text(encoding="utf-8")
            artifact_config = self.load_artifact_config(tmpl_dir)
            parsed = FrontmatterParser.parse(content)
            existing_fm = parsed.metadata
            meta = {**artifact_config, **existing_fm} if existing_fm else artifact_config

            if self.config.add_frontmatter:
                schema = self.config.frontmatter_schema
                if schema is not None:
                    errors = schema.validate_meta(meta)
                    if errors:
                        for error in errors:
                            fail(f"{prefix}/{name}: {error}")
                    else:
                        ok(f"{prefix}/{name}: metadata valid")
                else:
                    missing = [k for k in ("name", "description") if not meta.get(k)]
                    if missing:
                        fail(f"{prefix}/{name}: MISSING required fields: {missing}")
                    else:
                        ok(f"{prefix}/{name}: valid metadata (name, description)")

                meta_name = str(meta.get("name", name))
                if meta_name != name:
                    fail(f"{prefix}/{name}: name mismatch (metadata says '{meta_name}')")
                else:
                    ok(f"{prefix}/{name}: name matches directory")

            if self.config.placeholders:
                used_tokens = sorted(set(self.find_unresolved(content)))
                for token in used_tokens:
                    template_ref = self.config.placeholders.get(token, "").strip()
                    if template_ref:
                        ok(f"{prefix}/{name}: placeholder {token} mapped to {template_ref}")
                    else:
                        fail(
                            f"{prefix}/{name}: unknown placeholder '{{{{{token}}}}}' "
                            "(not registered in placeholders)"
                        )

        return result

    def verify_output(
        self,
        output_dir: Path,
        expected_names: list[str] | None = None,
    ) -> ValidationResult:
        """Verify generated output files in *output_dir*.

        When *expected_names* is ``None``, all artifacts found in *output_dir*
        are checked instead.
        """
        result = ValidationResult()

        if expected_names is None:
            if not output_dir.exists():
                return result
            # Derive names from the output_pattern structure
            if "/" in self.config.output_pattern:
                # Subdirectory style: names are first-level dir names
                expected_names = [p.name for p in sorted(output_dir.iterdir()) if p.is_dir()]
            else:
                # Flat file style: names derived from filenames
                suffix = self.config.output_pattern.replace("{name}", "")
                expected_names = [
                    p.name.removesuffix(suffix) for p in sorted(output_dir.glob(f"*{suffix}"))
                ]

        def ok(msg: str) -> None:
            """Record a passing output-verification message."""
            result.messages.append(CheckMessage("pass", msg))

        def fail(msg: str) -> None:
            """Record a failing output-verification message."""
            result.messages.append(CheckMessage("fail", msg))

        for name in expected_names:
            out = output_dir / self.output_path(name)
            label = self.output_path(name)
            if not out.exists():
                fail(f"{label} MISSING")
                continue
            ok(f"{label} exists")
            content = out.read_text(encoding="utf-8")
            if self.config.add_frontmatter:
                if content.startswith("---\n"):
                    ok(f"{label}: has frontmatter")
                else:
                    fail(f"{label}: missing frontmatter")
            if self.config.auto_gen_footer:
                if "AUTO-GENERATED" in content:
                    ok(f"{label}: has AUTO-GENERATED footer")
                else:
                    fail(f"{label}: missing AUTO-GENERATED footer")
                if self.parse_generation_metadata(content) is not None:
                    ok(f"{label}: has VSTACK-META footer")
                else:
                    ok(f"{label}: missing VSTACK-META footer (legacy artifact accepted)")
            if self.config.fail_on_unresolved:
                unresolved = self.find_unresolved(content)
                if not unresolved:
                    ok(f"{label}: no unresolved placeholders")
                else:
                    fail(f"{label}: unresolved placeholders: {unresolved}")

        return result
