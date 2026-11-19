"""`agent-checks init`: install the checks, hooks and CI into a repository."""

import difflib
import os
from dataclasses import dataclass, field
from importlib.resources import files
from pathlib import Path

from agent_checks.installer import merge
from agent_checks.installer import targets as t

SKIP_DIRS = frozenset({".git", ".venv", "venv", "node_modules", ".tox", "build", "dist"})


@dataclass
class Plan:
    root: Path
    changes: dict[Path, tuple[str, str]] = field(default_factory=dict)

    def add(self, rel: str | Path, old: str, new: str) -> None:
        if old != new:
            self.changes[self.root / rel] = (old, new)


def _read(path: Path) -> str:
    return path.read_text() if path.is_file() else ""


def _pyprojects(root: Path) -> list[Path]:
    found = []
    for folder, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
        if "pyproject.toml" in names:
            found.append(Path(folder, "pyproject.toml").relative_to(root))
    return found


def plan(root: Path) -> Plan:
    result = Plan(root)
    for rel in _pyprojects(root):
        old = _read(root / rel)
        result.add(rel, old, merge.pyproject(old))
    for name, merger in (
        (".pre-commit-config.yaml", merge.pre_commit),
        (".claude/settings.json", merge.claude_settings),
    ):
        old = _read(root / name)
        result.add(name, old, merger(old))
    for name in ("lint-file.sh", "lint-changed.sh"):
        new = files("agent_checks.claude_hooks").joinpath(name).read_text()
        result.add(f".claude/hooks/{name}", _read(root / ".claude/hooks" / name), new)
    workflow = ".github/workflows/agent-checks.yml"
    result.add(workflow, _read(root / workflow), t.WORKFLOW)
    return result


def _diff(rel: Path, old: str, new: str) -> str:
    lines = difflib.unified_diff(
        old.splitlines(keepends=True), new.splitlines(keepends=True), str(rel), str(rel)
    )
    return "".join(lines)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    if path.suffix == ".sh":
        path.chmod(0o755)


def run(root: Path, *, dry_run: bool, assume_yes: bool) -> int:
    root = root.resolve()
    changes = plan(root).changes
    for path, (old, new) in changes.items():
        rel = path.relative_to(root)
        print(_diff(rel, old, new))
        if dry_run:
            continue
        if assume_yes or input(f"Apply {rel}? [y/N] ").strip().lower() == "y":
            _write(path, new)
    if not changes:
        print("agent-checks is already installed; nothing to change.")
    elif not dry_run:
        print("Next: run `uvx pre-commit run --all-files` and fix every violation it reports.")
    return 0
