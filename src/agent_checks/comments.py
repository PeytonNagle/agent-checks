"""Extract comments from Python and shell files."""

import io
import tokenize
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Comment:
    line: int
    text: str
    full_line: bool


def _python(text: str) -> Iterator[Comment]:
    for tok in tokenize.generate_tokens(io.StringIO(text).readline):
        if tok.type == tokenize.COMMENT:
            yield Comment(tok.start[0], tok.string, tok.line.lstrip().startswith("#"))


def _shell_comment_start(line: str) -> int:
    """Index of the `#` that opens a comment, or -1; quotes span one line only."""
    quote = ""
    for i, char in enumerate(line):
        if quote:
            quote = "" if char == quote else quote
        elif char in "'\"":
            quote = char
        elif char == "#" and (i == 0 or line[i - 1].isspace()):
            return i
    return -1


def _shell(text: str) -> Iterator[Comment]:
    for number, line in enumerate(text.splitlines(), 1):
        start = _shell_comment_start(line)
        if start >= 0:
            yield Comment(number, line[start:], not line[:start].strip())


def comments(path: Path) -> Iterator[Comment]:
    text = path.read_text()
    return _python(text) if path.suffix == ".py" else _shell(text)
