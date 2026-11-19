"""AC301: function bodies longer than the limit (default 40 lines)."""

import argparse
import ast
from collections.abc import Iterator
from pathlib import Path

from agent_checks.comments import is_python
from agent_checks.report import Violation

Function = ast.FunctionDef | ast.AsyncFunctionDef


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--max-lines", type=int, default=None)


def _body_lines(node: Function) -> int:
    """Lines from the first statement after any docstring to the end of the function."""
    body = node.body
    has_docstring = (
        isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    )
    if has_docstring:
        body = body[1:]
    if not body:
        return 0
    end = node.end_lineno or body[-1].lineno
    return end - body[0].lineno + 1


def check(path: Path, args: argparse.Namespace) -> Iterator[Violation]:
    text = path.read_text()
    if not is_python(path, text):
        return
    limit = (
        args.max_lines if args.max_lines is not None else args.config.get("max-function-lines", 40)
    )
    for node in ast.walk(ast.parse(text, filename=str(path))):
        if isinstance(node, Function):
            length = _body_lines(node)
            if length > limit:
                yield Violation(
                    path,
                    node.lineno,
                    "AC301",
                    f"function {node.name!r} body is {length} lines, max {limit}",
                    "split it by responsibility into smaller named functions",
                )
