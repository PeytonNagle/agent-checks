"""AC201: comments that point at a chat, plan or step instead of the code."""

import argparse
import re
from collections.abc import Iterator
from functools import cache
from pathlib import Path

from agent_checks.comments import comments
from agent_checks.report import Violation

DEFAULT_PATTERNS = (
    r"\bas (we )?discussed\b",
    r"\bper (the|our) (plan|chat|conversation|discussion)\b",
    r"\boption [A-D]\b",
    r"\b(step|phase) \d+ (of|in|from) (the|our|this|your) (plan|chat|conversation)\b",
    r"\bper (step|phase) \d+\b",
    r"\bas you (asked|requested|suggested)\b",
)


@cache
def _regex(extra: tuple[str, ...]) -> re.Pattern[str]:
    return re.compile("|".join(f"(?:{p})" for p in (*DEFAULT_PATTERNS, *extra)), re.IGNORECASE)


def check(path: Path, args: argparse.Namespace) -> Iterator[Violation]:
    regex = _regex(tuple(args.config.get("chat-patterns", [])))
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
