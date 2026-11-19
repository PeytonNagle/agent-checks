#!/bin/sh
# Claude Code Stop hook: keep Claude working while changed files fail the repo's pre-commit hooks.
set -u
active=$(python3 -c 'import json, sys; print(json.load(sys.stdin).get("stop_hook_active", False))') || exit 1
[ "$active" = "True" ] && exit 0
cd "${CLAUDE_PROJECT_DIR:-.}" || exit 1
files=$({ git diff --name-only --diff-filter=d HEAD 2>/dev/null; git ls-files --others --exclude-standard; } | sort -u)
[ -n "$files" ] || exit 0
if command -v pre-commit >/dev/null 2>&1; then set -- pre-commit; else set -- uvx pre-commit; fi
if ! out=$(printf '%s\n' "$files" | tr '\n' '\0' | xargs -0 "$@" run --files 2>&1); then
  printf 'Changed files still fail the checks. Fix them before stopping:\n%s\n' "$out" >&2
  exit 2
fi
