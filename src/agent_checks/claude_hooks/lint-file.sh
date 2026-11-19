#!/bin/sh
# Claude Code PostToolUse hook: run the repo's pre-commit hooks on the file just edited.
set -u
root=$(cd "${CLAUDE_PROJECT_DIR:-.}" && pwd -P) || exit 1
file=$(python3 -c 'import json, sys; t = json.load(sys.stdin).get("tool_input", {}); print(t.get("file_path") or t.get("notebook_path") or "")') || exit 1
[ -n "$file" ] && [ -f "$file" ] || exit 0
file=$(cd "$(dirname "$file")" && printf '%s/%s' "$(pwd -P)" "$(basename "$file")")
case "$file" in "$root"/*) ;; *) exit 0 ;; esac
cd "$root" || exit 1
if command -v pre-commit >/dev/null 2>&1; then set -- pre-commit; else set -- uvx pre-commit; fi
# The repo-wide agent-lint ratchet is too slow per edit; the Stop hook runs it.
# A formatter fails the run that rewrites the file, so only a second failure counts.
if ! SKIP=agent-lint "$@" run --files "$file" >/dev/null 2>&1 \
  && ! out=$(SKIP=agent-lint "$@" run --files "$file" 2>&1); then
  printf 'Checks failed on %s. Fix the code, not the config:\n%s\n' "$file" "$out" >&2
  exit 2
fi
