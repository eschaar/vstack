"""Tests for CLI entrypoint dispatch behavior."""

from __future__ import annotations

import importlib

import pytest

main_module = importlib.import_module("vstack.main")


class _Args:
    """Minimal parsed-argument object for main() dispatch tests."""

    def __init__(
        self,
        command: str,
        only: list[str] | None = None,
        force: bool = False,
        update: bool = False,
        dry_run: bool = False,
        use_global: bool = False,
        source: bool = True,
        output: bool = True,
    ) -> None:
        """Initialize instance state."""
        self.command = command
        self.only = only
        self.force = force
        self.update = update
        self.dry_run = dry_run
        self.use_global = use_global
        self.source = source
        self.output = output


class _CLI:
    """Test double for the CLI command handler."""

    def __init__(self) -> None:
        """Initialize instance state."""
        self.called: tuple[str, tuple, dict] | None = None

    def validate(self, **kwargs):
        """Validate."""
        self.called = ("validate", tuple(), kwargs)
        return 7

    def verify(self, *args, **kwargs):
        """Verify."""
        self.called = ("verify", args, kwargs)
        return 8

    def install(self, *args, **kwargs):
        """Install."""
        self.called = ("install", args, kwargs)
        return 9

    def uninstall(self, *args, **kwargs):
        """Uninstall."""
        self.called = ("uninstall", args, kwargs)
        return 10


class TestMain:
    """Test cases for the CLI entrypoint."""

    def test_resolve_only_for_scope_returns_requested_only_for_non_global(self) -> None:
        """Test that non-global commands keep the explicit type filter."""
        args = _Args("install", only=["skill"], use_global=False)

        assert main_module._resolve_only_for_scope(args) == ["skill"]

    def test_main_dispatch_validate(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that main dispatch validate."""
        cli = _CLI()
        parser = type("P", (), {"parse_args": lambda self: _Args("validate")})()

        monkeypatch.setattr(main_module, "build_parser", lambda: parser)
        monkeypatch.setattr(main_module, "CommandLineInterface", lambda templates_root: cli)
        monkeypatch.setattr(
            main_module.sys, "exit", lambda code: (_ for _ in ()).throw(SystemExit(code))
        )

        with pytest.raises(SystemExit) as exc:
            main_module.main()

        assert exc.value.code == 7
        assert cli.called == ("validate", tuple(), {"only": None})

    def test_main_dispatch_install(self, monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
        """Test that main dispatch install."""
        cli = _CLI()
        seen: dict[str, object] = {}

        def _build_cli(templates_root):
            """Internal helper to build cli."""
            seen["templates_root"] = templates_root
            return cli

        args = _Args("install", only=["skill"], force=True, update=False, dry_run=True)
        parser = type("P", (), {"parse_args": lambda self: args})()

        monkeypatch.setattr(main_module, "build_parser", lambda: parser)
        monkeypatch.setattr(main_module, "resolve_targets", lambda _args: tmp_path)
        monkeypatch.setattr(main_module, "CommandLineInterface", _build_cli)
        monkeypatch.setattr(
            main_module.sys, "exit", lambda code: (_ for _ in ()).throw(SystemExit(code))
        )

        with pytest.raises(SystemExit) as exc:
            main_module.main()

        assert exc.value.code == 9
        assert seen["templates_root"] == main_module.TEMPLATES_ROOT
        assert cli.called == (
            "install",
            (tmp_path,),
            {
                "only": ["skill"],
                "force": True,
                "update": False,
                "dry_run": True,
            },
        )

    def test_main_global_install_defaults_to_supported_types(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path
    ) -> None:
        """Test that global install defaults to non-skill profile artifacts."""
        cli = _CLI()
        args = _Args("install", only=None, use_global=True)
        parser = type("P", (), {"parse_args": lambda self: args})()

        monkeypatch.setattr(main_module, "build_parser", lambda: parser)
        monkeypatch.setattr(main_module, "resolve_targets", lambda _args: tmp_path)
        monkeypatch.setattr(main_module, "CommandLineInterface", lambda templates_root: cli)
        monkeypatch.setattr(
            main_module.sys, "exit", lambda code: (_ for _ in ()).throw(SystemExit(code))
        )

        with pytest.raises(SystemExit) as exc:
            main_module.main()

        assert exc.value.code == 9
        assert cli.called == (
            "install",
            (tmp_path,),
            {
                "only": ["agent", "instruction", "prompt", "skill"],
                "force": False,
                "update": False,
                "dry_run": False,
            },
        )

    def test_resolve_only_for_scope_returns_requested_only_for_global_allowed_types(self) -> None:
        """Test that allowed global type filters are passed through unchanged."""
        args = _Args("install", only=["agent", "prompt"], use_global=True)

        assert main_module._resolve_only_for_scope(args) == ["agent", "prompt"]

    def test_main_global_install_rejects_unknown_type(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path
    ) -> None:
        """Test that global install rejects unsupported artifact types."""
        cli = _CLI()
        args = _Args("install", only=["unknown"], use_global=True)
        parser = type("P", (), {"parse_args": lambda self: args})()

        monkeypatch.setattr(main_module, "build_parser", lambda: parser)
        monkeypatch.setattr(main_module, "resolve_targets", lambda _args: tmp_path)
        monkeypatch.setattr(main_module, "CommandLineInterface", lambda templates_root: cli)
        monkeypatch.setattr(
            main_module.sys, "exit", lambda code: (_ for _ in ()).throw(SystemExit(code))
        )

        with pytest.raises(SystemExit) as exc:
            main_module.main()

        assert exc.value.code == 1
        assert cli.called is None

    def test_main_dispatch_verify_includes_only_filter(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path
    ) -> None:
        """Test that verify receives source/output flags and scope type filter."""
        cli = _CLI()
        args = _Args("verify", use_global=True, source=False, output=True)
        parser = type("P", (), {"parse_args": lambda self: args})()

        monkeypatch.setattr(main_module, "build_parser", lambda: parser)
        monkeypatch.setattr(main_module, "resolve_targets", lambda _args: tmp_path)
        monkeypatch.setattr(main_module, "CommandLineInterface", lambda templates_root: cli)
        monkeypatch.setattr(
            main_module.sys, "exit", lambda code: (_ for _ in ()).throw(SystemExit(code))
        )

        with pytest.raises(SystemExit) as exc:
            main_module.main()

        assert exc.value.code == 8
        assert cli.called == (
            "verify",
            tuple(),
            {
                "install_dir": tmp_path,
                "source": False,
                "output": True,
                "only": ["agent", "instruction", "prompt", "skill"],
            },
        )

    def test_main_dispatch_uninstall(self, monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
        """Test that uninstall resolves the target directory and dispatches correctly."""
        cli = _CLI()
        args = _Args("uninstall")
        parser = type("P", (), {"parse_args": lambda self: args})()

        monkeypatch.setattr(main_module, "build_parser", lambda: parser)
        monkeypatch.setattr(main_module, "resolve_targets", lambda _args: tmp_path)
        monkeypatch.setattr(main_module, "CommandLineInterface", lambda templates_root: cli)
        monkeypatch.setattr(
            main_module.sys, "exit", lambda code: (_ for _ in ()).throw(SystemExit(code))
        )

        with pytest.raises(SystemExit) as exc:
            main_module.main()

        assert exc.value.code == 10
        assert cli.called == ("uninstall", (tmp_path,), {})
