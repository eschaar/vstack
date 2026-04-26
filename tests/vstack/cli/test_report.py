"""Tests for BaseReport and StatusReport rendering."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from vstack.cli.report import BaseReport, StatusReport
from vstack.cli.service import CommandService


class TestBaseReport:
    """Test cases for BaseReport YAML serialization."""

    def test_yaml_handles_nested_empty_map_and_scalar_list(self) -> None:
        """YAML serializer handles empty nested maps and mixed-scalar lists."""
        rendered = BaseReport.to_yaml([{}, "hello", 2, True, None])
        assert "-" in rendered
        assert '"hello"' in rendered
        assert "- 2" in rendered
        assert "- true" in rendered
        assert "- null" in rendered

    def test_yaml_scalar_fallback_for_plain_value(self) -> None:
        """Scalar-only input returns a JSON-quoted string."""
        assert BaseReport.to_yaml("plain") == '"plain"'


class TestStatusReport:
    """Test cases for StatusReport rendering."""

    def test_render_missing_manifest_json_and_yaml(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Missing-manifest renderer supports json and yaml output formats."""
        install_dir = Path("/tmp/install")

        def color(_code: str, text: str) -> str:
            return text

        assert (
            StatusReport.render_missing_manifest(
                output_format="json",
                install_dir=install_dir,
                error="boom",
                color=color,
            )
            == 1
        )
        assert '"error": "boom"' in capsys.readouterr().out

        assert (
            StatusReport.render_missing_manifest(
                output_format="yaml",
                install_dir=install_dir,
                error="boom",
                color=color,
            )
            == 1
        )
        assert "error:" in capsys.readouterr().out

    def test_render_text_output_handles_markers_and_exit_codes(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Text renderer prints per-entry markers and returns issue-based exit codes."""

        class _Service:
            @staticmethod
            def label(path: Path) -> str:
                return f"label:{path}"

        svc = cast(CommandService, _Service())

        reports = [
            {
                "type": "skill",
                "counts": {
                    "managed": 1,
                    "managed_legacy": 1,
                    "modified": 1,
                    "missing": 0,
                    "unknown": 0,
                    "untracked": 0,
                },
                "issues": 1,
                "warnings": 1,
                "entries": [
                    {"state": "managed", "message": "managed entry"},
                    {"state": "modified", "message": "modified entry"},
                    {"state": "absent", "message": "absent entry"},
                ],
            }
        ]

        def color(_code: str, text: str) -> str:
            return text

        exit_with_issues = StatusReport.render_text_output(
            service=svc,
            reports=reports,
            install_dir=Path("/tmp/install"),
            verbose=False,
            total_issues=1,
            color=color,
        )
        out1 = capsys.readouterr().out
        assert exit_with_issues == 1
        assert "legacy warning" in out1
        assert "modified entry" in out1
        assert "managed entry" not in out1

        exit_clean = StatusReport.render_text_output(
            service=svc,
            reports=reports,
            install_dir=Path("/tmp/install"),
            verbose=True,
            total_issues=0,
            color=color,
        )
        out2 = capsys.readouterr().out
        assert exit_clean == 0
        assert "managed entry" in out2
        assert "all tracked artifacts match the manifest" in out2

    def test_render_text_output_raises_on_bad_counts_type(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Raises TypeError when counts is not a dict."""

        class _Service:
            @staticmethod
            def label(path: Path) -> str:
                return str(path)

        svc = cast(CommandService, _Service())

        def color(_code: str, text: str) -> str:
            return text

        with pytest.raises(TypeError, match="expected dict for 'counts', got list"):
            StatusReport.render_text_output(
                service=svc,
                reports=[{"type": "skill", "counts": [], "entries": []}],
                install_dir=Path("/tmp/install"),
                verbose=False,
                total_issues=0,
                color=color,
            )

    def test_render_text_output_raises_on_bad_entries_type(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Raises TypeError when entries is not a list."""

        class _Service:
            @staticmethod
            def label(path: Path) -> str:
                return str(path)

        svc = cast(CommandService, _Service())

        def color(_code: str, text: str) -> str:
            return text

        with pytest.raises(TypeError, match="expected list for 'entries', got dict"):
            StatusReport.render_text_output(
                service=svc,
                reports=[
                    {
                        "type": "skill",
                        "counts": {
                            "managed": 0,
                            "managed_legacy": 0,
                            "modified": 0,
                            "missing": 0,
                            "unknown": 0,
                            "untracked": 0,
                        },
                        "entries": {},
                    }
                ],
                install_dir=Path("/tmp/install"),
                verbose=False,
                total_issues=0,
                color=color,
            )

    def test_render_text_output_raises_on_bad_entry_type(
        self,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Raises TypeError when an individual entry is not a dict."""

        class _Service:
            @staticmethod
            def label(path: Path) -> str:
                return str(path)

        svc = cast(CommandService, _Service())

        def color(_code: str, text: str) -> str:
            return text

        with pytest.raises(TypeError, match="expected dict for entry, got str"):
            StatusReport.render_text_output(
                service=svc,
                reports=[
                    {
                        "type": "skill",
                        "counts": {
                            "managed": 0,
                            "managed_legacy": 0,
                            "modified": 0,
                            "missing": 0,
                            "unknown": 0,
                            "untracked": 0,
                        },
                        "entries": ["bad"],
                    }
                ],
                install_dir=Path("/tmp/install"),
                verbose=False,
                total_issues=0,
                color=color,
            )
