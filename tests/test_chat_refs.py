import pytest
from conftest import Run, Write


@pytest.mark.parametrize(
    "comment",
    [
        "as discussed above",
        "per the plan",
        "per our conversation",
        "Option B is faster",
        "step 3 of the rollout",
        "Phase 2 only",
        "as you asked",
    ],
)
def test_default_patterns_fail(write: Write, run: Run, comment: str) -> None:
    path = write("a.py", f"x = 1  # {comment}\n")
    code, out = run("chat-refs", path)
    assert code == 1
    assert f"{path}:1: AC201" in out


def test_strings_are_ignored(write: Write, run: Run) -> None:
    assert run("chat-refs", write("a.py", 'x = "as discussed"\n'))[0] == 0


def test_word_boundaries(write: Write, run: Run) -> None:
    assert run("chat-refs", write("a.py", "# the stepper motor, optional\n"))[0] == 0


def test_case_insensitive(write: Write, run: Run) -> None:
    assert run("chat-refs", write("a.py", "# AS DISCUSSED\n"))[0] == 1


def test_shell_comments(write: Write, run: Run) -> None:
    assert run("chat-refs", write("a.sh", "echo hi  # per the plan\n"))[0] == 1


def test_extra_patterns_from_config(write: Write, run: Run) -> None:
    write("pyproject.toml", '[tool.agent-checks]\nchat-patterns = ["\\\\bticket-less\\\\b"]\n')
    assert run("chat-refs", write("a.py", "# ticket-less fix\n"))[0] == 1
