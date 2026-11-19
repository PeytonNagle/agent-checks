"""Merge the targets into existing config text, keeping comments and unrelated keys."""

import io
import json
from collections.abc import Iterable, Mapping
from typing import Any

import tomlkit
from ruamel.yaml import YAML
from tomlkit.items import Table

from agent_checks.installer import targets as t


def _table(parent: Any, created: list[Table], *keys: str) -> Table:
    """Return the nested table, creating missing ones and recording new leaves in `created`."""
    for key in keys:
        if key not in parent:
            parent[key] = tomlkit.table(is_super_table=key != keys[-1])
            if key == keys[-1]:
                created.append(parent[key])
        parent = parent[key]
    table: Table = parent
    return table


def _extend(table: Any, key: str, values: Iterable[str]) -> None:
    current = table.get(key)
    if current is None:
        table[key] = tomlkit.array()
        current = table[key]
    current.extend(v for v in values if v not in current)
    if len(current) > 4:
        current.multiline(True)


def _set_all(table: Any, values: Mapping[str, object]) -> None:
    for key, value in values.items():
        if table.get(key) != value:
            table[key] = value


def pyproject(text: str) -> str:
    doc = tomlkit.parse(text)
    created: list[Table] = []
    lint = _table(doc, created, "tool", "ruff", "lint")
    _set_all(lint, t.RUFF_LINT)
    _extend(lint, "select", t.RUFF_SELECT)
    _extend(lint, "ignore", t.RUFF_IGNORE)
    _set_all(_table(lint, created, "mccabe"), t.RUFF_MCCABE)
    _set_all(_table(lint, created, "pylint"), t.RUFF_PYLINT)
    mypy = _table(doc, created, "tool", "mypy")
    _set_all(mypy, t.MYPY)
    _extend(mypy, "enable_error_code", t.MYPY_ERROR_CODES)
    checks = _table(doc, created, "tool", "agent-checks")
    for key, value in t.AGENT_CHECKS.items():
        checks.setdefault(key, value)
    dumped = tomlkit.dumps(doc)
    for table in created:
        if table.as_string() + "[" in dumped:
            table.add(tomlkit.nl())
    return tomlkit.dumps(doc).rstrip("\n") + "\n"


ALIASES = {"ruff-check": {"ruff", "ruff-check"}}


def _repo_entry(
    repos: list[Any], url: str, rev: str, hook_ids: Iterable[str], *, keep_rev: bool = False
) -> None:
    """Add the repo and hooks; `keep_rev` leaves a pin the user already chose."""
    entry = next((r for r in repos if r.get("repo") == url), None)
    if entry is None:
        entry = {"repo": url, "rev": rev, "hooks": []}
        repos.append(entry)
    elif not keep_rev:
        entry["rev"] = rev
    hooks = entry.setdefault("hooks", [])
    have = {h.get("id") for h in hooks}
    hooks.extend({"id": h} for h in hook_ids if not ALIASES.get(h, {h}) & have)


def pre_commit(text: str) -> str:
    yaml = YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    data = yaml.load(text) or {}
    repos = data.setdefault("repos", [])
    _repo_entry(repos, t.CHECKS_URL, t.CHECKS_REV, t.CHECKS_HOOKS)
    _repo_entry(repos, t.RUFF_URL, t.RUFF_REV, ("ruff-check", "ruff-format"), keep_rev=True)
    _repo_entry(repos, t.AGENT_LINT_URL, t.AGENT_LINT_REV, ("agent-lint",))
    out = io.StringIO()
    yaml.dump(data, out)
    return out.getvalue()


def _hook(settings: dict[str, Any], event: str, matcher: str | None, command: str) -> None:
    groups = settings.setdefault("hooks", {}).setdefault(event, [])
    if any(h.get("command") == command for g in groups for h in g.get("hooks", [])):
        return
    group: dict[str, Any] = {"hooks": [{"type": "command", "command": command}]}
    if matcher:
        group = {"matcher": matcher, **group}
    groups.append(group)


def claude_settings(text: str) -> str:
    settings: dict[str, Any] = json.loads(text) if text.strip() else {}
    _hook(settings, "PreToolUse", t.EDIT_MATCHER, t.GUARD_COMMAND)
    _hook(settings, "PostToolUse", t.EDIT_MATCHER, t.LINT_FILE_COMMAND)
    _hook(settings, "Stop", None, t.LINT_CHANGED_COMMAND)
    deny = settings.setdefault("permissions", {}).setdefault("deny", [])
    deny.extend(r for g in t.PROTECTED_GLOBS if (r := f"Edit({g})") not in deny)
    return json.dumps(settings, indent=2) + "\n"
