"""Contract tests for the release publish workflow."""

from __future__ import annotations

from pathlib import Path

import yaml

WORKFLOW_PATH = Path(__file__).resolve().parents[2] / ".github/workflows/publish.yml"


class TestPublishWorkflow:
    """Verify publish workflow contracts for PyPI and Homebrew distribution."""

    def test_homebrew_job_is_gated_and_sequential(self) -> None:
        """Homebrew publish should run only after PyPI publish behind a feature flag."""
        workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))

        env = workflow["env"]
        assert env["HOMEBREW_TAP_ENABLED"] == "false"
        assert env["HOMEBREW_TAP_NAME"] == "eschaar/vstack"
        assert env["HOMEBREW_TAP_REPOSITORY"] == "eschaar/homebrew-vstack"
        assert env["HOMEBREW_FORMULA_NAME"] == "vstack"
        assert env["HOMEBREW_FULLY_QUALIFIED_FORMULA"] == "eschaar/vstack/vstack"

        homebrew_job = workflow["jobs"]["publish-homebrew"]
        assert homebrew_job["needs"] == "publish"

        job_if = homebrew_job["if"]
        assert "needs.publish.result == 'success'" in job_if
        assert "github.event.release.prerelease == false" in job_if
        assert "env.HOMEBREW_TAP_ENABLED == 'true'" in job_if

    def test_homebrew_job_verifies_sdist_and_dispatches_update(self) -> None:
        """Homebrew publish should verify sdist checksum before repository dispatch."""
        workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
        steps = workflow["jobs"]["publish-homebrew"]["steps"]

        verify_step = next(step for step in steps if step.get("id") == "verify_sdist")
        verify_script = verify_step["run"]
        assert "https://pypi.org/pypi/vstack/" in verify_script
        assert "sha256 mismatch between PyPI metadata and downloaded tarball" in verify_script

        dispatch_step = next(
            step for step in steps if step["name"] == "Dispatch formula update to Homebrew tap"
        )
        dispatch_script = dispatch_step["run"]
        assert "/dispatches" in dispatch_script
        assert "dispatch-body.json" in dispatch_script

        step_env = dispatch_step["env"]
        assert step_env["RELEASE_VERSION"] == "${{ github.event.release.tag_name }}"
        assert step_env["SDIST_URL"] == "${{ steps.verify_sdist.outputs.sdist_url }}"
        assert step_env["SDIST_SHA256"] == "${{ steps.verify_sdist.outputs.sdist_sha256 }}"

        summary_step = next(step for step in steps if step["name"] == "Publish Homebrew install UX summary")
        summary_script = summary_step["run"]
        assert "brew tap ${HOMEBREW_TAP_NAME} && brew install ${HOMEBREW_FORMULA_NAME}" in summary_script
        assert "brew install ${HOMEBREW_FORMULA_NAME}" in summary_script
        assert "brew install ${HOMEBREW_FULLY_QUALIFIED_FORMULA}" in summary_script
        assert "Homebrew/homebrew-core" in summary_script
