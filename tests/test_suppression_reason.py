import pytest
from conftest import Run


@pytest.mark.parametrize(
    "line",
    [
        "import os  # noqa",
        "import os  # noqa: F401",
        "x: int = 'a'  # type: ignore",
        "x: int = 'a'  # type: ignore[assignment]",
        "def f():  # pragma: no cover",
        "eval(s)  # nosec B307",
    ],
)
def test_python_suppression_without_reason_fails(write, run: Run, line: str) -> None:
    path = write("a.py", line + "\n")
    code, out = run("suppression-reason", path)
    assert code == 1
    assert f"{path}:1: AC401" in out


@pytest.mark.parametrize(
    "line",
    [
        "import os  # noqa: F401  # re-exported for plugins",
        "x: int = 'a'  # type: ignore[assignment]  # stub is wrong upstream",
        "def f():  # pragma: no cover  # only runs on the Pi",
    ],
)
def test_python_suppression_with_code_and_reason_passes(write, run: Run, line: str) -> None:
    assert run("suppression-reason", write("a.py", line + "\n")) == (0, "")


def test_bare_noqa_with_reason_still_fails(write, run: Run) -> None:
    assert run("suppression-reason", write("a.py", "import os  # noqa  # because\n"))[0] == 1


def test_shellcheck_without_reason_fails(write, run: Run) -> None:
    path = write("a.sh", "# shellcheck disable=SC2086\necho $x\n")
    assert run("suppression-reason", path)[0] == 1


def test_shellcheck_with_reason_passes(write, run: Run) -> None:
    path = write("a.sh", "# shellcheck disable=SC2086 # word splitting is intended\necho $x\n")
    assert run("suppression-reason", path)[0] == 0


def test_suppression_text_in_string_ignored(write, run: Run) -> None:
    assert run("suppression-reason", write("a.py", 'x = "# noqa"\n'))[0] == 0
