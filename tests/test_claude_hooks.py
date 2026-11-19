import json
import shutil
import subprocess
from pathlib import Path

import pytest

HOOKS = Path(__file__).parents[1] / "src" / "agent_checks" / "claude_hooks"
REPO = Path(__file__).parents[1]


@pytest.fixture
def project(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".pre-commit-config.yaml").write_text(
        f"repos:\n- repo: {REPO}\n  rev: HEAD\n  hooks:\n  - id: comment-length\n"
    )
    (tmp_path / "clean.py").write_text("X = 1\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@t",
            "commit",
            "-qm",
            "i",
        ],
        check=True,
    )
    return tmp_path


def _run(script: str, root: Path, payload: dict[str, object]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["sh", str(HOOKS / script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env={"CLAUDE_PROJECT_DIR": str(root), "PATH": "/usr/bin:/bin:" + _bin_dirs()},
        check=False,
    )


def _bin_dirs() -> str:
    found = [shutil.which(tool) for tool in ("pre-commit", "python3", "git")]
    return ":".join(str(Path(f).parent) for f in found if f)


def test_lint_file_reports_violation(project: Path) -> None:
    bad = project / "bad.py"
    bad.write_text("# one\n# two\n# three\n")
    result = _run("lint-file.sh", project, {"tool_input": {"file_path": str(bad)}})
    assert result.returncode == 2
    assert "AC101" in result.stderr


def test_lint_file_passes_clean_file(project: Path) -> None:
    result = _run("lint-file.sh", project, {"tool_input": {"file_path": str(project / "clean.py")}})
    assert result.returncode == 0, result.stderr


def test_lint_file_ignores_missing_path(project: Path) -> None:
    result = _run("lint-file.sh", project, {"tool_input": {}})
    assert result.returncode == 0


def test_lint_changed_reports_untracked_violation(project: Path) -> None:
    (project / "new.py").write_text("# one\n# two\n# three\n")
    result = _run("lint-changed.sh", project, {"stop_hook_active": False})
    assert result.returncode == 2
    assert "AC101" in result.stderr


def test_lint_changed_reports_modified_violation(project: Path) -> None:
    (project / "clean.py").write_text("# one\n# two\n# three\nX = 1\n")
    result = _run("lint-changed.sh", project, {"stop_hook_active": False})
    assert result.returncode == 2


def test_lint_changed_skips_when_already_continuing(project: Path) -> None:
    (project / "new.py").write_text("# one\n# two\n# three\n")
    result = _run("lint-changed.sh", project, {"stop_hook_active": True})
    assert result.returncode == 0


def test_lint_changed_passes_with_no_changes(project: Path) -> None:
    result = _run("lint-changed.sh", project, {"stop_hook_active": False})
    assert result.returncode == 0, result.stderr


FIXER = """\
- repo: local
  hooks:
  - id: fixer
    name: fixer
    language: system
    types: [python]
    entry: python3 -c "import sys; [open(f, 'w').write('X = 1\\n') for f in sys.argv[1:]]"
"""


def test_lint_file_passes_once_a_formatter_fixed_the_file(project: Path) -> None:
    with (project / ".pre-commit-config.yaml").open("a") as config:
        config.write(FIXER)
    messy = project / "clean.py"
    messy.write_text("X=1\n")
    result = _run("lint-file.sh", project, {"tool_input": {"file_path": str(messy)}})
    assert result.returncode == 0, result.stderr
    assert messy.read_text() == "X = 1\n"


def test_lint_file_reads_notebook_path(project: Path) -> None:
    bad = project / "bad.py"
    bad.write_text("# one\n# two\n# three\n")
    result = _run("lint-file.sh", project, {"tool_input": {"notebook_path": str(bad)}})
    assert result.returncode == 2


def test_lint_changed_from_a_subdirectory(project: Path) -> None:
    (project / "sub").mkdir()
    (project / "sub/new.py").write_text("# one\n# two\n# three\n")
    (project / "clean.py").write_text("# one\n# two\n# three\nX = 1\n")
    result = _run("lint-changed.sh", project / "sub", {"stop_hook_active": False})
    assert result.returncode == 2
    assert "sub/new.py" in result.stderr
    assert "clean.py" in result.stderr
