"""What `init` installs: the cited thresholds, hook pins and the CI workflow."""

from importlib.metadata import version

CHECKS_URL = "https://github.com/PeytonNagle/agent-checks"
CHECKS_REV = f"v{version('agent-checks')}"
CHECKS_HOOKS = ("comment-length", "chat-refs", "func-length", "suppression-reason")
AGENT_LINT_URL = "https://github.com/MartinCastroAlvarez/agent-lint"
AGENT_LINT_REV = "bcf12b8cbd6a9e37638f4760d781454167e69c26"
RUFF_URL = "https://github.com/astral-sh/ruff-pre-commit"
RUFF_REV = "v0.17.5"

RUFF_SELECT = (
    "E", "F", "I", "UP", "B", "C901", "PLR0911", "PLR0912", "PLR0913", "PLR0915", "PLR0917",
    "PLR1702", "BLE", "S110", "S112", "SIM", "RET", "PIE", "PERF", "C4", "RUF", "G", "LOG",
    "PGH", "T20", "DTZ", "ERA", "TRY", "ARG",
)  # fmt: skip
RUFF_IGNORE = ("TRY003",)
RUFF_LINT: dict[str, object] = {"preview": True, "explicit-preview-rules": True}
RUFF_MCCABE = {"max-complexity": 10}
RUFF_PYLINT = {
    "max-args": 5,
    "max-positional-args": 5,
    "max-returns": 6,
    "max-branches": 12,
    "max-statements": 50,
    "max-nested-blocks": 3,
}
MYPY: dict[str, object] = {"strict": True, "warn_unreachable": True}
MYPY_ERROR_CODES = ("ignore-without-code",)
AGENT_CHECKS = {"max-comment-lines": 2, "max-function-lines": 40}

PROTECTED_GLOBS = (
    "**/pyproject.toml",
    "**/.pre-commit-config.yaml",
    "**/.github/workflows/**",
    "**/.claude/settings.json",
    "**/.claude/hooks/**",
    "**/.agent-lint/**",
)
EDIT_MATCHER = "Edit|Write|MultiEdit|NotebookEdit"
GUARD_COMMAND = f"uvx --from git+{CHECKS_URL}@{CHECKS_REV} agent-checks config-guard"
LINT_FILE_COMMAND = '"$CLAUDE_PROJECT_DIR"/.claude/hooks/lint-file.sh'
LINT_CHANGED_COMMAND = '"$CLAUDE_PROJECT_DIR"/.claude/hooks/lint-changed.sh'

WORKFLOW = f"""\
name: agent-checks

on:
  pull_request:

jobs:
  checks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - uses: astral-sh/setup-uv@v6
      - name: pre-commit on changed files
        run: uvx pre-commit run --show-diff-on-failure --from-ref "origin/$BASE_REF" --to-ref HEAD
        env:
          BASE_REF: ${{{{ github.base_ref }}}}
      - name: agent-lint ratchet
        uses: MartinCastroAlvarez/agent-lint@{AGENT_LINT_REV}
        with:
          comment: "false"
"""
