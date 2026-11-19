# agent-checks

Deterministic checks that keep agent-written code small, sparingly commented and honest about suppressions.

| Hook id | Code | Fails when |
| --- | --- | --- |
| `comment-length` | AC101 | a block of full-line comments runs over 2 lines |
| `chat-refs` | AC201 | a comment points at a chat or plan ("as discussed", "Option B", "step 3") |
| `func-length` | AC301 | a function body (after its docstring) runs over 40 lines |
| `suppression-reason` | AC401 | a `noqa`, `type: ignore`, `nosec`, `pragma: no cover` or `shellcheck disable` lacks a code or a trailing `# reason` |
| `config-guard` | — | Claude Code tries to Edit or Write lint, CI or hook config (PreToolUse hook) |

Every message ends with the fix, so an agent reading it knows what to do next.

## Configure

```toml
[tool.agent-checks]
max-comment-lines = 2
max-function-lines = 40
chat-patterns = ["\\bticket-less\\b"]
protected-paths = ["tools/release.sh"]
```

## Run

```sh
uvx --from git+https://github.com/PeytonNagle/agent-checks agent-checks comment-length src/*.py
```
