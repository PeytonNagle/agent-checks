"""Command line entry point: `agent-checks <check> FILES...`."""

import argparse
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path

from agent_checks import chat_refs, comment_length, config_guard, func_length, suppression_reason
from agent_checks.report import Violation, load_config

FileCheck = Callable[[Path, argparse.Namespace], Iterable[Violation]]
AddArguments = Callable[[argparse.ArgumentParser], None]

FILE_CHECKS: dict[str, tuple[FileCheck, AddArguments]] = {
    "comment-length": (comment_length.check, comment_length.add_arguments),
    "chat-refs": (chat_refs.check, chat_refs.add_arguments),
    "func-length": (func_length.check, func_length.add_arguments),
    "suppression-reason": (suppression_reason.check, suppression_reason.add_arguments),
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-checks")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, (_, add_arguments) in FILE_CHECKS.items():
        cmd = sub.add_parser(name)
        add_arguments(cmd)
        cmd.add_argument("files", nargs="*", type=Path)
    sub.add_parser("config-guard", help="Claude Code PreToolUse hook; reads JSON on stdin")
    return parser


def _run_file_check(args: argparse.Namespace) -> int:
    args.config = load_config()
    check, _ = FILE_CHECKS[args.command]
    violations = [v for path in args.files for v in check(path, args)]
    for violation in violations:
        print(violation)
    return 1 if violations else 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "config-guard":
        return config_guard.main()
    return _run_file_check(args)
