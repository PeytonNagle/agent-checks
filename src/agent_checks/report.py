"""Shared violation output and `[tool.agent-checks]` config loading."""

import tomllib
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    code: str
    message: str
    fix: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.code} {self.message} (fix: {self.fix})"


@cache
def _config_at(folder: Path) -> dict[str, Any]:
    for candidate in (folder, *folder.parents):
        pyproject = candidate / "pyproject.toml"
        if pyproject.is_file():
            data = tomllib.loads(pyproject.read_text())
            section: dict[str, Any] = data.get("tool", {}).get("agent-checks", {})
            return section
    return {}


def load_config(start: Path | None = None) -> dict[str, Any]:
    """Return `[tool.agent-checks]` from the nearest pyproject.toml at or above `start`."""
    return _config_at((start or Path.cwd()).resolve())
