import io
import json
from pathlib import Path

import pytest

from agent_checks.cli import main


def _hook(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    root: Path,
    payload: object,
) -> tuple[int, str]:
    text = payload if isinstance(payload, str) else json.dumps(payload)
    monkeypatch.setattr("sys.stdin", io.StringIO(text))
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(root))
    code = main(["config-guard"])
    return code, capsys.readouterr().err


def _edit(root: Path, rel: str, tool: str = "Edit") -> dict[str, object]:
    return {"tool_name": tool, "tool_input": {"file_path": str(root / rel)}, "cwd": str(root)}


@pytest.mark.parametrize(
    "rel",
    [
        "pyproject.toml",
        "node/pyproject.toml",
        ".pre-commit-config.yaml",
        ".github/workflows/ci.yml",
        ".claude/settings.json",
        ".agent-lint/baseline.json",
    ],
)
@pytest.mark.parametrize("tool", ["Edit", "Write", "MultiEdit"])
def test_protected_path_blocks(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    rel: str,
    tool: str,
) -> None:
    code, err = _hook(monkeypatch, capsys, tmp_path, _edit(tmp_path, rel, tool))
    assert code == 2
    assert rel in err


def test_unprotected_path_allowed(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    assert _hook(monkeypatch, capsys, tmp_path, _edit(tmp_path, "src/app.py")) == (0, "")


def test_path_outside_project_allowed(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    payload = {"tool_name": "Write", "tool_input": {"file_path": "/elsewhere/pyproject.toml"}}
    assert _hook(monkeypatch, capsys, tmp_path, payload)[0] == 0


def test_unknown_tool_allowed(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    payload = {"tool_name": "Read", "tool_input": {"file_path": str(tmp_path / "pyproject.toml")}}
    assert _hook(monkeypatch, capsys, tmp_path, payload)[0] == 0


def test_malformed_json_errors_without_blocking(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    code, err = _hook(monkeypatch, capsys, tmp_path, "{not json")
    assert code == 1
    assert err


def test_extra_protected_paths_from_config(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.agent-checks]\nprotected-paths = ["tools/mutmut_changed.sh"]\n'
    )
    payload = _edit(tmp_path, "tools/mutmut_changed.sh")
    assert _hook(monkeypatch, capsys, tmp_path, payload)[0] == 2


@pytest.mark.parametrize("payload", ["[1]", '"text"'])
def test_non_object_input_errors_without_blocking(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    payload: str,
) -> None:
    assert _hook(monkeypatch, capsys, tmp_path, payload)[0] == 1


def test_invalid_pyproject_still_blocks_default_paths(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    (tmp_path / "pyproject.toml").write_text("not = [toml\n")
    assert _hook(monkeypatch, capsys, tmp_path, _edit(tmp_path, "pyproject.toml"))[0] == 2
