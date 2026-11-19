from conftest import Run, Write


def test_three_line_block_fails(write: Write, run: Run) -> None:
    path = write("a.py", "x = 1\n# one\n# two\n# three\ny = 2\n")
    code, out = run("comment-length", path)
    assert code == 1
    assert f"{path}:2: AC101" in out


def test_two_line_block_passes(write: Write, run: Run) -> None:
    path = write("a.py", "# one\n# two\nx = 1\n")
    assert run("comment-length", path) == (0, "")


def test_directive_lines_do_not_count(write: Write, run: Run) -> None:
    text = "#!/usr/bin/env python\n# noqa: E501\n# type: ignore[misc]\n# pragma: no cover\n# why\n"
    assert run("comment-length", write("a.py", text))[0] == 0


def test_strings_and_docstrings_ignored(write: Write, run: Run) -> None:
    text = 'def f():\n    """\n    # a\n    # b\n    # c\n    """\n    s = "# d"\n'
    assert run("comment-length", write("a.py", text))[0] == 0


def test_trailing_comments_do_not_join_block(write: Write, run: Run) -> None:
    text = "x = 1  # a\n# b\n# c\ny = 2  # d\n"
    assert run("comment-length", write("a.py", text))[0] == 0


def test_shell_files(write: Write, run: Run) -> None:
    path = write("a.sh", "#!/bin/sh\n# one\n# two\n# three\necho '# not a comment'\n")
    code, out = run("comment-length", path)
    assert code == 1
    assert f"{path}:2: AC101" in out


def test_max_option(write: Write, run: Run) -> None:
    path = write("a.py", "# one\n# two\n")
    assert run("comment-length", "--max", "1", path)[0] == 1


def test_max_from_pyproject(write: Write, run: Run) -> None:
    write("pyproject.toml", "[tool.agent-checks]\nmax-comment-lines = 3\n")
    path = write("a.py", "# one\n# two\n# three\n")
    assert run("comment-length", path)[0] == 0


def test_unparseable_file_is_reported(write: Write, run: Run) -> None:
    path = write("a.py", "x = (\n")
    code, out = run("comment-length", path)
    assert code == 1
    assert f"{path}:1: AC001" in out


def test_stub_docstring_is_not_a_comment(write: Write, run: Run) -> None:
    text = 'def f() -> None:\n    """\n    # a\n    # b\n    # c\n    """\n'
    assert run("comment-length", write("a.pyi", text))[0] == 0


def test_config_from_the_files_own_project(write: Write, run: Run) -> None:
    write("pkg/pyproject.toml", "[tool.agent-checks]\nmax-comment-lines = 3\n")
    assert run("comment-length", write("pkg/a.py", "# one\n# two\n# three\n"))[0] == 0
