"""AC101: comment blocks longer than the limit (default 2 lines)."""

import argparse
import re
from collections.abc import Iterable, Iterator
from pathlib import Path

from agent_checks.comments import Comment, comments
from agent_checks.report import Violation

DIRECTIVE = re.compile(
    r"^#\s*(!|noqa\b|type:|pragma\b|shellcheck\b|fmt:|ruff:|mypy:|pylint:|-\*-)", re.IGNORECASE
)


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--max", type=int, default=None)


def _blocks(found: Iterable[Comment]) -> Iterator[tuple[int, int]]:
    """Yield (first line, length) for each run of consecutive full-line comments."""
    start, last = 0, -1
    for comment in found:
        if not comment.full_line or DIRECTIVE.match(comment.text):
            continue
        if comment.line != last + 1:
            if start:
                yield start, last - start + 1
            start = comment.line
        last = comment.line
    if start:
        yield start, last - start + 1


def check(path: Path, args: argparse.Namespace) -> Iterator[Violation]:
    limit = args.max or args.config.get("max-comment-lines", 2)
    for start, length in _blocks(comments(path)):
        if length > limit:
            yield Violation(
                path,
                start,
                "AC101",
                f"comment block is {length} lines, max {limit}",
                "keep only the why in 1-2 lines; move history to the commit message",
            )
