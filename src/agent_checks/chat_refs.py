"""AC201: comments that point at a chat, plan or step instead of the code."""

import argparse
import re
from collections.abc import Iterator
from pathlib import Path

from agent_checks.comments import comments
from agent_checks.report import Violation

DEFAULT_PATTERNS = (
    r"\bas (we )?discussed\b",
    r"\bper (the|our) (plan|chat|conversation|discussion)\b",
    r"\boption [A-D]\b",
    r"\bstep \d+\b",
    r"\bphase \d+\b",
    r"\bas you (asked|requested|suggested)\b",
)


def add_arguments(parser: argparse.ArgumentParser) -> None:
    del parser


def check(path: Path, args: argparse.Namespace) -> Iterator[Violation]:
    patterns = [*DEFAULT_PATTERNS, *args.config.get("chat-patterns", [])]
    regex = re.compile("|".join(f"(?:{p})" for p in patterns), re.IGNORECASE)
    for comment in comments(path):
        found = regex.search(comment.text)
        if found:
            yield Violation(
                path,
                comment.line,
                "AC201",
                f"comment refers to the conversation or plan ({found.group(0)!r})",
                "say why the code is this way; put history in the commit or PR",
            )
