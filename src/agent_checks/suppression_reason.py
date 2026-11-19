"""AC401: lint suppressions must name a code and give a reason in a trailing comment."""

import argparse
import re
from collections.abc import Iterator
from pathlib import Path

from agent_checks.comments import comments
from agent_checks.report import Violation

CODE = r"[A-Z]+[0-9]+"
SUPPRESSIONS = {
    "noqa": re.compile(
        rf"#\s*(?:(?:ruff|flake8):\s*)?noqa\b(?P<codes>:\s*{CODE}(?:[,\s]+{CODE})*)?", re.IGNORECASE
    ),
    "type: ignore": re.compile(r"#\s*type:\s*ignore\b(?P<codes>\[[^\]]+\])?"),
    "pragma: no cover": re.compile(r"#\s*pragma:\s*no\s*cover(?P<codes>)"),
    "nosec": re.compile(rf"#\s*nosec\b(?P<codes>\s+{CODE}(?:[,\s]+{CODE})*)?"),
    "shellcheck disable": re.compile(
        r"#\s*shellcheck\s+disable\s*=\s*(?P<codes>SC\d+(?:,SC\d+)*)?"
    ),
}
REASON = re.compile(r"#\s*\S")
FIX = "write `# <tool>: <CODE>  # <why this is safe>`, or fix the code instead"


def add_arguments(parser: argparse.ArgumentParser) -> None:
    del parser


def _problem(text: str) -> str | None:
    for name, pattern in SUPPRESSIONS.items():
        found = pattern.search(text)
        if not found:
            continue
        if found.group("codes") is None:
            return f"bare `{name}` names no rule code"
        if not REASON.search(text, found.end()):
            return f"`{name}` has no reason"
    return None


def check(path: Path, args: argparse.Namespace) -> Iterator[Violation]:
    del args
    for comment in comments(path):
        problem = _problem(comment.text)
        if problem:
            yield Violation(path, comment.line, "AC401", problem, FIX)
