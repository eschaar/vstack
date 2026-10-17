"""Regression tests for retiring managed prompts during skill installation."""

from argparse import Namespace
from pathlib import Path

import pytest

from vstack.cli.base import CommandContext
from vstack.cli.constants import RETIRED_PROMPT_SKILLS
from vstack.cli.init import InitCommand
from vstack.cli.install import InstallCommand
from vstack.cli.service import CommandService
from vstack.constants import TEMPLATES_ROOT
from vstack.manifest import ArtifactEntry, Manifest, content_hash
from vstack.models import CheckMessage, ValidationResult


@pytest.fixture
def service() -> CommandService:
    """Use shipped templates to test upgrades against actual replacement skills."""
    return CommandService(TEMPLATES_ROOT)


def track_prompts(service: CommandService, install_dir: Path, names: list[str]) -> Manifest:
    """Write a previous-release manifest and clean prompt files."""
    entries = []
    for name in names:
        relative_path = f"prompts/{name}.prompt.md"
        path = install_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        content = f"Legacy workflow: {name}\n"
        path.write_text(content, encoding="utf-8")
        entries.append(
            ArtifactEntry(
                name=name,
                file=relative_path,
                version="20260513001",
                checksum=content_hash(content),
                checksum_algorithm="sha256",
            )
        )
    manifest = Manifest(
        vstack_version="3.7.0",
        installed_at="2026-10-01T00:00:00Z",
        artifacts={"prompts": entries},
    )
    service.manifest_for(install_dir).write(manifest)
    return manifest


@pytest.mark.parametrize("command_cls", [InitCommand, InstallCommand])
def test_upgrade_replaces_all_builtin_prompts_and_is_repeatable(
    service: CommandService, tmp_path: Path, command_cls: type[InitCommand] | type[InstallCommand]
) -> None:
    """Both upgrade entry points install skills and retire all clean managed prompts."""
    install_dir = tmp_path / ".github"
    track_prompts(service, install_dir, list(RETIRED_PROMPT_SKILLS))
    personal_prompt = install_dir / "prompts" / "personal.prompt.md"
    personal_prompt.write_text("Personal workflow\n", encoding="utf-8")
    context = CommandContext(args=Namespace(), install_dir=install_dir, only=["skill"])

    command = command_cls(service)
    assert command.run(context=context) == 0
    assert command.run(context=context) == 0

    manifest = service.manifest_for(install_dir).read()
    assert manifest is not None
    assert "prompts" not in manifest.artifacts
    for old_name, skill in RETIRED_PROMPT_SKILLS.items():
        assert not (install_dir / "prompts" / f"{old_name}.prompt.md").exists()
        assert (install_dir / "skills" / skill / "SKILL.md").is_file()
        assert skill in manifest.names_for("skills")
    assert personal_prompt.read_text(encoding="utf-8") == "Personal workflow\n"


def test_fresh_install_does_not_generate_or_adopt_prompts(
    service: CommandService, tmp_path: Path
) -> None:
    """Untracked prompts remain outside vstack ownership on new installations."""
    install_dir = tmp_path / ".github"
    prompt = install_dir / "prompts" / "quick-review.prompt.md"
    prompt.parent.mkdir(parents=True)
    prompt.write_text("My workflow\n", encoding="utf-8")
    assert InitCommand.execute(service, install_dir, only=["skill"]) == 0
    manifest = service.manifest_for(install_dir).read()
    assert manifest is not None
    assert "prompts" not in manifest.artifacts
    assert list(prompt.parent.iterdir()) == [prompt]
    assert prompt.read_text(encoding="utf-8") == "My workflow\n"


def test_upgrade_dry_run_preserves_files_and_manifest(
    service: CommandService, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Dry-run simulates replacement installation and deletion without writing either."""
    install_dir = tmp_path / ".github"
    track_prompts(service, install_dir, ["quick-review"])
    manifest_file = service.manifest_for(install_dir).path
    original_manifest = manifest_file.read_bytes()
    prompt = install_dir / "prompts" / "quick-review.prompt.md"
    original_content = prompt.read_bytes()

    assert InitCommand.execute(service, install_dir, only=["skill"], dry_run=True) == 0
    assert manifest_file.read_bytes() == original_manifest
    assert prompt.read_bytes() == original_content
    assert not (install_dir / "skills").exists()
    output = capsys.readouterr().out
    assert "[dry-run]" in output
    assert "Migrating prompt/quick-review" in output


def test_non_skill_install_defers_prompt_migration(service: CommandService, tmp_path: Path) -> None:
    """Selecting another artifact family leaves old prompts tracked and untouched."""
    install_dir = tmp_path / ".github"
    track_prompts(service, install_dir, ["quick-review"])
    assert InitCommand.execute(service, install_dir, only=["instruction"]) == 0
    manifest = service.manifest_for(install_dir).read()
    assert manifest is not None
    assert manifest.names_for("prompts") == ["quick-review"]
    assert (install_dir / "prompts" / "quick-review.prompt.md").is_file()


@pytest.mark.parametrize(
    "case, expected_reason",
    [
        ("modified", "local changes detected"),
        ("no-checksum", "no stored checksum"),
        ("unknown-algorithm", "unknown checksum algorithm"),
        ("invalid-utf8", "file is unreadable"),
        ("directory", "file is unreadable"),
        ("unknown-prompt", "convert this custom workflow manually"),
        ("unsafe-path", "noncanonical legacy prompt path"),
        ("file-symlink", "symlinked legacy prompt path"),
        ("directory-symlink", "symlinked legacy prompt path"),
    ],
)
def test_unsafe_legacy_prompt_is_preserved_even_with_force_and_prune(
    service: CommandService,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    case: str,
    expected_reason: str,
) -> None:
    """No force mode bypasses ownership, path, or checksum migration safeguards."""
    install_dir = tmp_path / ".github"
    name = "custom-workflow" if case == "unknown-prompt" else "quick-review"
    manifest = track_prompts(service, install_dir, [name])
    entry = manifest.entries_for("prompts")[0]
    prompt = install_dir / entry.file
    outside = tmp_path / "outside.prompt.md"
    outside.write_text("Do not touch\n", encoding="utf-8")
    if case == "modified":
        prompt.write_text("Local changes\n", encoding="utf-8")
    elif case == "no-checksum":
        entry.checksum = None
        entry.checksum_algorithm = None
    elif case == "unknown-algorithm":
        entry.checksum_algorithm = "sha999"
    elif case == "invalid-utf8":
        prompt.write_bytes(b"\xff")
    elif case == "directory":
        prompt.unlink()
        prompt.mkdir()
    elif case == "unsafe-path":
        entry.file = "../outside.prompt.md"
        entry.checksum = content_hash("Do not touch\n")
    elif case == "file-symlink":
        prompt.unlink()
        prompt.symlink_to(outside)
        entry.checksum = content_hash("Do not touch\n")
    elif case == "directory-symlink":
        prompt.unlink()
        prompt.parent.rmdir()
        external_dir = tmp_path / "external-prompts"
        external_dir.mkdir()
        (external_dir / prompt.name).write_text("External workflow\n", encoding="utf-8")
        prompt.parent.symlink_to(external_dir, target_is_directory=True)
        entry.checksum = content_hash("External workflow\n")
    service.manifest_for(install_dir).write(manifest)

    assert InitCommand.execute(service, install_dir, only=["skill"], force=True, prune=True) == 0
    updated = service.manifest_for(install_dir).read()
    assert updated is not None
    assert updated.entries_for("prompts") == [entry]
    assert prompt.exists()
    assert outside.read_text(encoding="utf-8") == "Do not touch\n"
    output = capsys.readouterr().out
    assert expected_reason in output
    assert "--force does not remove them" in output
    assert "--force-name <" not in output


@pytest.mark.parametrize("collision", ["excluded", "untracked", "modified", "adopted"])
def test_unavailable_replacement_defers_cleanup_and_can_be_retried(
    service: CommandService,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    collision: str,
) -> None:
    """Install never deletes a prompt when its replacement was excluded or preserved."""
    install_dir = tmp_path / ".github"
    manifest = track_prompts(service, install_dir, ["quick-review"])
    replacement = install_dir / "skills" / "code-review" / "SKILL.md"
    if collision != "excluded":
        replacement.parent.mkdir(parents=True)
        replacement.write_text("Local skill\n", encoding="utf-8")
    if collision == "modified":
        manifest.artifacts["skills"] = [
            ArtifactEntry(
                name="code-review",
                file="skills/code-review/SKILL.md",
                checksum=content_hash("Original skill\n"),
            )
        ]
        service.manifest_for(install_dir).write(manifest)
    assert (
        InitCommand.execute(
            service,
            install_dir,
            only=["skill"],
            excluded_names={"skill": ["code-review"]} if collision == "excluded" else None,
            adopt_names=["skill/code-review"] if collision == "adopted" else None,
        )
        == 0
    )
    prompt = install_dir / "prompts" / "quick-review.prompt.md"
    assert prompt.is_file()
    current = service.manifest_for(install_dir).read()
    assert current is not None
    assert current.names_for("prompts") == ["quick-review"]
    assert "replacement skill/code-review is unavailable" in capsys.readouterr().out
    if collision != "excluded":
        assert replacement.read_text(encoding="utf-8") == "Local skill\n"
    assert (
        InitCommand.execute(service, install_dir, only=["skill"], force_names=["skill/code-review"])
        == 0
    )
    assert not prompt.exists()


def test_already_missing_prompt_is_removed_from_manifest(
    service: CommandService, tmp_path: Path
) -> None:
    """Interrupted upgrades are retryable when the old prompt was already deleted."""
    install_dir = tmp_path / ".github"
    track_prompts(service, install_dir, ["quick-review"])
    prompt = install_dir / "prompts" / "quick-review.prompt.md"
    prompt.unlink()
    assert InitCommand.execute(service, install_dir, only=["skill"], update=True) == 0
    manifest = service.manifest_for(install_dir).read()
    assert manifest is not None
    assert not manifest.entries_for("prompts")
    assert not prompt.parent.exists()


def test_failed_prompt_deletion_is_reported_and_retryable(
    service: CommandService,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A filesystem failure returns nonzero and keeps ownership for a later retry."""
    install_dir = tmp_path / ".github"
    track_prompts(service, install_dir, ["quick-review"])

    def fail_removal(**_kwargs: object) -> None:
        raise PermissionError("deletion denied")

    with monkeypatch.context() as patch:
        patch.setattr(InitCommand, "_remove_file_if_present", staticmethod(fail_removal))
        assert InitCommand.execute(service, install_dir, only=["skill"]) == 1
    output = capsys.readouterr()
    assert "ERROR: could not retire prompt/quick-review: deletion denied" in output.err
    assert "removed obsolete tracked artifact" not in output.out
    assert (install_dir / "prompts" / "quick-review.prompt.md").exists()
    manifest = service.manifest_for(install_dir).read()
    assert manifest is not None
    assert manifest.names_for("prompts") == ["quick-review"]
    assert "code-review" in manifest.names_for("skills")
    assert InitCommand.execute(service, install_dir, only=["skill"], update=True) == 0
    assert not (install_dir / "prompts" / "quick-review.prompt.md").exists()


def test_profile_scoped_upgrade_uses_the_same_safe_retirement(
    service: CommandService, tmp_path: Path
) -> None:
    """Existing profile installs migrate relative paths without a project scaffold."""
    install_dir = tmp_path / "User"
    track_prompts(service, install_dir, ["reasoning"])
    context = CommandContext(
        args=Namespace(use_global=True), install_dir=install_dir, only=["skill"]
    )
    assert InstallCommand(service).run(context=context) == 0
    assert not (install_dir / "prompts" / "reasoning.prompt.md").exists()
    assert (install_dir / "skills" / "reasoning" / "SKILL.md").exists()
    assert not (tmp_path / ".vstack").exists()


def test_source_validation_failure_does_not_retire_prompts(
    service: CommandService, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Failed generation does not trigger cleanup of the previous release's workflows."""
    install_dir = tmp_path / ".github"
    track_prompts(service, install_dir, ["quick-review"])
    gen = service.gen_for("skill")
    assert gen is not None
    monkeypatch.setattr(
        gen,
        "verify_input",
        lambda: ValidationResult(messages=[CheckMessage(level="fail", message="bad source")]),
    )
    assert InitCommand.execute(service, install_dir, only=["skill"]) == 1
    assert (install_dir / "prompts" / "quick-review.prompt.md").exists()
    manifest = service.manifest_for(install_dir).read()
    assert manifest is not None
    assert manifest.names_for("prompts") == ["quick-review"]


def test_retired_prompt_exclusions_warn_instead_of_blocking_upgrade(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Legacy exclusion keys no longer select a type, and explain their replacement."""
    from vstack.cli.interface import CommandLineInterface

    config = tmp_path / ".vstack" / "config.yaml"
    config.parent.mkdir()
    config.write_text("exclude:\n  prompts: all\n", encoding="utf-8")
    assert CommandLineInterface._read_exclude(tmp_path / ".github") == (frozenset(), {})
    assert "exclude.prompts is retired" in capsys.readouterr().err
