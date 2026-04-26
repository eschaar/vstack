"""Tests for VerifyCommand."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from vstack.cli.base import CommandContext
from vstack.cli.service import CommandService
from vstack.cli.verify import VerifyCommand


class TestVerifyCommand:
    """Test cases for VerifyCommand."""

    def test_manifest_metadata_entry_returns_fail_on_unreadable_file(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Unreadable artifact files should return a failing ValidationResult."""

        artifact_path = tmp_path / "artifact.md"
        artifact_path.write_text("content", encoding="utf-8")

        def _raise_oserror(self: Path, encoding: str = "utf-8") -> str:
            del self, encoding
            raise OSError("permission denied")

        monkeypatch.setattr(Path, "read_text", _raise_oserror)

        service = cast(CommandService, SimpleNamespace(label=lambda path: str(path)))
        result = VerifyCommand._verify_manifest_metadata_entry(
            service=service,
            gen=SimpleNamespace(config=SimpleNamespace(type_name="skill")),
            manifest_data=SimpleNamespace(vstack_version="2.0.0"),
            entry=SimpleNamespace(name="verify", version="1.0.0"),
            artifact_path=artifact_path,
        )

        assert result.failures == 1
        assert result.messages[0].level == "fail"
        assert "could not read file during metadata verify" in result.messages[0].message
        assert str(artifact_path) in result.messages[0].message

    def test_output_returns_error_when_manifest_read_fails(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """_verify_output fails early when manifest parse reports an error."""

        class _ManifestFile:
            read_error = "bad manifest"

            def read(self):
                return None

        service = cast(
            CommandService,
            SimpleNamespace(manifest_for=lambda _install_dir: _ManifestFile()),
        )
        result = VerifyCommand._verify_output(
            service=service,
            install_dir=Path("/tmp/install"),
            gens=[],
            header=lambda _label: None,
            results=[],
        )
        assert result == 1
        assert "ERROR: bad manifest" in capsys.readouterr().err

    def test_output_skips_manifest_checks_when_manifest_missing(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """When no manifest exists, verify runs output checks and returns 0."""

        class _ManifestFile:
            read_error = None

            def read(self):
                return None

        class _Gen:
            class config:
                type_name = "skill"
                output_subdir = "skills"

            @staticmethod
            def verify_output(_out_dir: Path, _expected) -> object:
                from vstack.models import ValidationResult

                return ValidationResult()

        monkeypatch.setattr(
            "vstack.cli.verify.VerifyCommand._verify_manifest_checksums",
            staticmethod(
                lambda *_args, **_kwargs: (_ for _ in ()).throw(
                    AssertionError("must not be called")
                )
            ),
        )
        monkeypatch.setattr(
            "vstack.cli.verify.VerifyCommand._verify_manifest_metadata",
            staticmethod(
                lambda *_args, **_kwargs: (_ for _ in ()).throw(
                    AssertionError("must not be called")
                )
            ),
        )

        install_dir = tmp_path
        out_dir = install_dir / "skills"
        out_dir.mkdir(parents=True)

        service = cast(
            CommandService,
            SimpleNamespace(
                manifest_for=lambda _install_dir: _ManifestFile(),
                label=lambda path: str(path),
            ),
        )
        result = VerifyCommand._verify_output(
            service=service,
            install_dir=install_dir,
            gens=[_Gen()],
            header=lambda _label: None,
            results=[],
        )
        assert result == 0

    def test_execute_returns_output_exit_when_output_phase_fails(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """execute bubbles non-zero codes from the output verification phase."""
        monkeypatch.setattr(
            "vstack.cli.verify.VerifyCommand._verify_output",
            staticmethod(lambda **_kwargs: 7),
        )
        service = cast(CommandService, SimpleNamespace(generators=[]))
        assert (
            VerifyCommand.execute(
                service, install_dir=Path("/tmp/install"), source=False, output=True
            )
            == 7
        )

    def test_run_forwards_context_to_execute(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """run() unpacks CommandContext args and forwards them to execute()."""
        captured: dict[str, Any] = {}

        def _fake_execute(*args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs
            return 5

        monkeypatch.setattr("vstack.cli.verify.VerifyCommand.execute", staticmethod(_fake_execute))

        context = CommandContext(
            args=Namespace(source=False, output=True),
            install_dir=tmp_path,
            only=["instruction"],
        )
        assert VerifyCommand(service=cast(CommandService, object())).run(context=context) == 5
        assert captured["kwargs"]["source"] is False
        assert captured["kwargs"]["output"] is True
