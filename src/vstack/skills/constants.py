"""Constants for skill template and partial locations."""

from __future__ import annotations

from vstack.constants import TEMPLATES_ROOT

#: Source template filename.
SKILL_TMPL_NAME = "template.md"

#: Subdirectory name under ``templates/`` holding skill source templates.
SKILL_TEMPLATES_SUBDIR = "skills"

#: Subdirectory name under the install root (e.g. ``.github/``) for skill output.
SKILL_OUTPUT_SUBDIR = "skills"

SKILLS_TEMPLATES_DIR = TEMPLATES_ROOT / SKILL_TEMPLATES_SUBDIR
SKILLS_PARTIALS_DIR = TEMPLATES_ROOT / SKILL_TEMPLATES_SUBDIR / "_partials"
