from collections.abc import Callable
from pathlib import Path

import pytest

from agent_checks.cli import main

Run = Callable[..., tuple[int, str]]


@pytest.fixture
def write(tmp_path: Path) -> Callable[[str, str], Path]:
    def _write(name: str, text: str) -> Path:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    return _write


@pytest.fixture
def run(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Run:
    monkeypatch.chdir(tmp_path)

    def _run(*args: str | Path) -> tuple[int, str]:
        code = main([str(a) for a in args])
        return code, capsys.readouterr().out

    return _run
