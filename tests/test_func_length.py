from conftest import Run


def _func(name: str, body_lines: int, indent: str = "") -> str:
    body = "".join(f"{indent}    x{i} = {i}\n" for i in range(body_lines))
    return f"{indent}def {name}():\n{body}"


def test_body_over_limit_fails(write, run: Run) -> None:
    path = write("a.py", _func("long", 41))
    code, out = run("func-length", path)
    assert code == 1
    assert f"{path}:1: AC301" in out
    assert "long" in out


def test_body_at_limit_passes(write, run: Run) -> None:
    assert run("func-length", write("a.py", _func("ok", 40)))[0] == 0


def test_docstring_and_decorators_excluded(write, run: Run) -> None:
    text = '@dec\n@dec2\ndef f():\n    """Doc.\n\n    More.\n    """\n'
    text += "".join(f"    x{i} = {i}\n" for i in range(40))
    assert run("func-length", write("a.py", text))[0] == 0


def test_methods_and_async(write, run: Run) -> None:
    text = "class C:\n" + _func("m", 41, "    ") + "async " + _func("a", 41)
    code, out = run("func-length", write("a.py", text))
    assert code == 1
    assert out.count("AC301") == 2


def test_nested_function_counted_on_its_own(write, run: Run) -> None:
    inner = _func("inner", 30, "    ")
    text = "def outer():\n" + inner + "".join(f"    y{i} = {i}\n" for i in range(15))
    code, out = run("func-length", write("a.py", text))
    assert code == 1
    assert "outer" in out
    assert "inner" not in out


def test_max_lines_option(write, run: Run) -> None:
    assert run("func-length", "--max-lines", "5", write("a.py", _func("f", 6)))[0] == 1
