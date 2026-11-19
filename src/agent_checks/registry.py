"""The per-file checks, by hook id; one list shared by the CLI and the installer."""

import argparse
from collections.abc import Callable, Iterable
from pathlib import Path

from agent_checks import chat_refs, comment_length, func_length, suppression_reason
from agent_checks.report import Violation

FileCheck = Callable[[Path, argparse.Namespace], Iterable[Violation]]
AddArguments = Callable[[argparse.ArgumentParser], None]

FILE_CHECKS: dict[str, tuple[FileCheck, AddArguments | None]] = {
    "comment-length": (comment_length.check, comment_length.add_arguments),
    "chat-refs": (chat_refs.check, None),
    "func-length": (func_length.check, func_length.add_arguments),
    "suppression-reason": (suppression_reason.check, None),
}
