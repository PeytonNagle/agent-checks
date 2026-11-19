# agent-checks

Deterministic checks that keep agent-written code small, sparingly commented and honest about suppressions.

| Hook id | Code | Fails when |
| --- | --- | --- |
| `comment-length` | AC101 | a block of full-line comments runs over 2 lines |
| `chat-refs` | AC201 | a comment points at a chat or plan ("as discussed", "Option B", "per step 3") |
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

## Install into a repository

From Claude Code, install the plugin and run its skill, which previews the changes, applies them and fixes every violation:

```
/plugin install agent-checks --marketplace PeytonNagle/agent-checks
/agent-checks:install
```

Or run the installer yourself:

```sh
uvx --from git+https://github.com/PeytonNagle/agent-checks@v0.1.2 agent-checks init --dry-run
```

`init` merges the cited thresholds into each `pyproject.toml`, adds the hooks to `.pre-commit-config.yaml`, writes the Claude Code hooks to `.claude/`, and adds a CI workflow that runs pre-commit and the [agent-lint](https://github.com/MartinCastroAlvarez/agent-lint) ratchet. It keeps existing comments and keys, asks before each file unless you pass `--yes`, and a second run changes nothing.
