---
name: install
description: Install agent-checks into the current repository - lint thresholds, pre-commit hooks, Claude Code hooks and CI - then fix every violation so the repo starts clean. Use when the user asks to install or set up agent-checks.
---

# Install agent-checks

Work on a new branch. Never weaken a threshold or add a suppression to get a check passing.

1. Preview the changes:
   `uvx --from git+https://github.com/PeytonNagle/agent-checks@v0.1.1 agent-checks init --dry-run`
2. Show the user the diff and summarize it: which files change, and any existing threshold that gets stricter.
3. Once the user approves, apply it with the same command, using `--yes` instead of `--dry-run`.
4. Run `uvx pre-commit run --all-files` and fix every violation in the code:
   - long functions: split them by responsibility; if a function has no tests, add characterization tests first
   - long comments: keep only the why, in 1-2 lines
   - chat references: rewrite as a reason or delete
   - suppressions: fix the code, or add the code and a `# reason`
5. Run the project's own lint, type check and tests, and fix anything that fails.
6. Run `uvx --from git+https://github.com/MartinCastroAlvarez/agent-lint@bcf12b8cbd6a9e37638f4760d781454167e69c26 agent-lint init` to record the empty baseline, and commit `.agent-lint/`.
7. Commit and propose a PR. Ask the user before pushing.

After step 3, `config-guard` blocks edits to `pyproject.toml`, `.pre-commit-config.yaml`, `.github/workflows/` and `.claude/`. If one of those really needs to change, stop and ask the user to edit it.
