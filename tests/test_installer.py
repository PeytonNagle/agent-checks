import json
import subprocess
from pathlib import Path

import pytest
import tomlkit

from agent_checks.installer import plan, run

EXPECTED = [
    ".claude/hooks/lint-changed.sh",
    ".claude/hooks/lint-file.sh",
    ".claude/settings.json",
    ".github/workflows/agent-checks.yml",
    ".pre-commit-config.yaml",
    "pyproject.toml",
]


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "demo"\n')
    return tmp_path


def _files(root: Path) -> list[str]:
    return sorted(
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if ".git/" not in p.as_posix() + "/" and p.is_file()
    )


def test_fresh_repo_gets_every_file(repo: Path) -> None:
    run(repo, dry_run=False, assume_yes=True)
    assert _files(repo) == EXPECTED
    lint = tomlkit.parse((repo / "pyproject.toml").read_text())["tool"]["ruff"]["lint"]
    assert "C901" in lint["select"]
    assert lint["mccabe"]["max-complexity"] == 10
    settings = json.loads((repo / ".claude/settings.json").read_text())
    assert {"PreToolUse", "PostToolUse", "Stop"} <= settings["hooks"].keys()
    assert any("pyproject.toml" in rule for rule in settings["permissions"]["deny"])


def test_existing_config_keeps_comments_and_unrelated_keys(repo: Path) -> None:
    (repo / "pyproject.toml").write_text(
        '[project]\nname = "demo"\n\n[tool.ruff.lint]\n# keep me\nselect = ["E", "Q"]\n'
    )
    (repo / ".claude").mkdir()
    (repo / ".claude/settings.json").write_text(
        '{"model": "opus", "permissions": {"allow": ["Bash(ls)"]}}'
    )
    run(repo, dry_run=False, assume_yes=True)
    text = (repo / "pyproject.toml").read_text()
    assert "# keep me" in text
    assert '"Q"' in text
    settings = json.loads((repo / ".claude/settings.json").read_text())
    assert settings["model"] == "opus"
    assert settings["permissions"]["allow"] == ["Bash(ls)"]


def test_second_run_changes_nothing(repo: Path) -> None:
    run(repo, dry_run=False, assume_yes=True)
    assert plan(repo).changes == {}


def test_dry_run_writes_nothing(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    before = (repo / "pyproject.toml").read_text()
    run(repo, dry_run=True, assume_yes=False)
    assert _files(repo) == ["pyproject.toml"]
    assert (repo / "pyproject.toml").read_text() == before
    assert "+++ .pre-commit-config.yaml" in capsys.readouterr().out


def test_conflicting_value_is_shown(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (repo / "pyproject.toml").write_text("[tool.ruff.lint.mccabe]\nmax-complexity = 15\n")
    run(repo, dry_run=True, assume_yes=False)
    out = capsys.readouterr().out
    assert "-max-complexity = 15" in out
    assert "+max-complexity = 10" in out


def test_declined_file_is_not_written(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _: "n")
    run(repo, dry_run=False, assume_yes=False)
    assert _files(repo) == ["pyproject.toml"]


def test_multiline_strings_are_untouched(repo: Path) -> None:
    (repo / "pyproject.toml").write_text('[tool.x]\ns = """\nfoo\n[bar]\n"""\n')
    run(repo, dry_run=False, assume_yes=True)
    doc = tomlkit.parse((repo / "pyproject.toml").read_text())
    assert doc["tool"]["x"]["s"] == "foo\n[bar]\n"


def test_existing_newer_pin_and_hook_alias_kept(repo: Path) -> None:
    (repo / ".pre-commit-config.yaml").write_text(
        "repos:\n  - repo: https://github.com/astral-sh/ruff-pre-commit\n"
        "    rev: v0.20.0\n    hooks:\n      - id: ruff\n"
    )
    run(repo, dry_run=False, assume_yes=True)
    text = (repo / ".pre-commit-config.yaml").read_text()
    assert "v0.20.0" in text
    assert "ruff-check" not in text


def test_complete_array_keeps_its_layout(repo: Path) -> None:
    from agent_checks.installer import merge
    from agent_checks.installer import targets as t

    items = ", ".join(f'"{code}"' for code in t.RUFF_SELECT)
    text = f"[tool.ruff.lint]\nselect = [{items}]\n"
    assert f"select = [{items}]" in merge.pyproject(text)


def test_upgrade_replaces_the_pinned_guard_command() -> None:
    from agent_checks.installer import merge
    from agent_checks.installer import targets as t

    old = t.GUARD_COMMAND.replace(t.CHECKS_REV, "v0.0.1")
    text = json.dumps({"hooks": {"PreToolUse": [{"hooks": [{"type": "command", "command": old}]}]}})
    groups = json.loads(merge.claude_settings(text))["hooks"]["PreToolUse"]
    commands = [h["command"] for g in groups for h in g["hooks"]]
    assert commands == [t.GUARD_COMMAND]
