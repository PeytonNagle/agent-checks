"""Claude Code PreToolUse hook that blocks agent edits to lint, CI and hook config."""

import json
import os
import sys
import tomllib
from fnmatch import fnmatch
from pathlib import Path
from typing import TextIO

from agent_checks.report import load_config

EDIT_TOOLS = frozenset({"Edit", "Write", "MultiEdit", "NotebookEdit"})
PROTECTED = (
    "pyproject.toml",
    "setup.cfg",
    "ruff.toml",
    ".ruff.toml",
    "mypy.ini",
    ".importlinter",
    ".pre-commit-config.yaml",
    ".github/workflows/*",
    ".claude/settings.json",
    ".claude/hooks/*",
    ".agent-lint/*",
    "CODEOWNERS",
)
BLOCKED = 2


def _is_protected(rel: Path, patterns: list[str]) -> bool:
    """A pattern without a slash matches the file name at any depth."""
    return any(fnmatch(rel.as_posix(), p) if "/" in p else fnmatch(rel.name, p) for p in patterns)


def _target(payload: dict[str, object], root: Path) -> Path | None:
    tool_input = payload.get("tool_input")
    if payload.get("tool_name") not in EDIT_TOOLS or not isinstance(tool_input, dict):
        return None
    raw = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not isinstance(raw, str):
        return None
    path = (root / raw).resolve()
    return path.relative_to(root) if path.is_relative_to(root) else None


def _extra_patterns(root: Path, stderr: TextIO) -> list[str]:
    try:
        extra: list[str] = load_config(root).get("protected-paths", [])
    except tomllib.TOMLDecodeError as error:
        print(f"config-guard: ignoring invalid pyproject.toml: {error}", file=stderr)
        return []
    return extra


def run(stdin: TextIO, stderr: TextIO) -> int:
    try:
        payload = json.load(stdin)
    except json.JSONDecodeError as error:
        print(f"config-guard: could not read hook input: {error}", file=stderr)
        return 1
    if not isinstance(payload, dict):
        print("config-guard: hook input is not a JSON object", file=stderr)
        return 1
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".").resolve()
    rel = _target(payload, root)
    if rel is None:
        return 0
    if not _is_protected(rel, list(PROTECTED)) and not _is_protected(
        rel, _extra_patterns(root, stderr)
    ):
        return 0
    print(
        f"config-guard: {rel} is protected lint, CI or hook config. Do not edit it to make a "
        "check pass; fix the code instead. If the config really must change, stop and ask "
        "the user to make the edit.",
        file=stderr,
    )
    return BLOCKED


def main() -> int:
    return run(sys.stdin, sys.stderr)
