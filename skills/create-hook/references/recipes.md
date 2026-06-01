# Hook Recipes, Debugging & Security

Ready-to-paste patterns, troubleshooting, and security review. For per-event schemas see [events.md](events.md).

## Table of Contents

- [Recipes](#recipes)
  - [Notify when Claude needs input](#notify-when-claude-needs-input)
  - [Auto-format on edit](#auto-format-on-edit)
  - [Block edits to protected files](#block-edits-to-protected-files)
  - [Block dangerous Bash commands](#block-dangerous-bash-commands)
  - [Inject context at session start / after compact](#inject-context-at-session-start--after-compact)
  - [Add context to a prompt](#add-context-to-a-prompt)
  - [Audit tool use / config changes](#audit-tool-use--config-changes)
  - [Keep Claude working until a condition holds](#keep-claude-working-until-a-condition-holds)
  - [Auto-approve a specific permission](#auto-approve-a-specific-permission)
  - [Reload env on directory/file change](#reload-env-on-directoryfile-change)
- [Debugging](#debugging)
- [Security considerations](#security-considerations)

---

## Recipes

### Notify when Claude needs input

`Notification` event. macOS / Linux / Windows variants:

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "osascript -e 'display notification \"Claude needs your attention\" with title \"Claude Code\"'"
          }
        ]
      }
    ]
  }
}
```

- Linux: `"notify-send 'Claude Code' 'Claude Code needs your attention'"`
- Windows: `"powershell.exe -Command \"[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); [System.Windows.Forms.MessageBox]::Show('Claude needs your attention','Claude Code')\""`

Narrow with matcher `permission_prompt` or `idle_prompt` to fire only on those.

### Auto-format on edit

`PostToolUse` + `Edit|Write`. Extract the path from stdin and format it:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write"
          }
        ]
      }
    ]
  }
}
```

Project scope (`.claude/settings.json`) so the team shares it. Requires `jq`.

### Block edits to protected files

`PreToolUse` + `Edit|Write`, script exits 2. Save `.claude/hooks/protect-files.sh`:

```bash
#!/usr/bin/env bash
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
PROTECTED=(".env" "package-lock.json" ".git/")
for p in "${PROTECTED[@]}"; do
  if [[ "$FILE_PATH" == *"$p"* ]]; then
    echo "Blocked: $FILE_PATH matches protected pattern '$p'" >&2
    exit 2
  fi
done
exit 0
```

`chmod +x .claude/hooks/protect-files.sh`, then:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/protect-files.sh" }
        ]
      }
    ]
  }
}
```

Note: only catches the file tools. Files written via `Bash` (`>`, `sed -i`) bypass this — also match `Bash` or add a `Stop`-time scan if coverage must be total.

### Block dangerous Bash commands

`PreToolUse` + `Bash`, optionally scoped with `if`:

```bash
#!/usr/bin/env bash
INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command')
if echo "$CMD" | grep -Eq 'rm +-rf +/|drop +table'; then
  echo "Blocked: destructive command" >&2
  exit 2
fi
exit 0
```

Use `"if": "Bash(rm *)"` in the handler to only spawn the process for `rm` subcommands. Reference implementation: <https://github.com/anthropics/claude-code/blob/main/examples/hooks/bash_command_validator_example.py>

### Inject context at session start / after compact

`SessionStart`; stdout becomes context. Matcher `compact` re-injects after compaction:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "compact",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Reminder: use Bun not npm. Run bun test before committing.'"
          }
        ]
      }
    ]
  }
}
```

Swap `echo` for dynamic output like `git log --oneline -5`. For _every_ session, prefer `CLAUDE.md`.

### Add context to a prompt

`UserPromptSubmit` — exit 0 with stdout, or JSON `additionalContext`. Exit 2 (+ stderr) blocks and erases the prompt.

### Audit tool use / config changes

Append-only logging. Tool use:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.command' >> ~/.claude/command-log.txt"
          }
        ]
      }
    ]
  }
}
```

Config changes (`ConfigChange`, matcher filters by source):

```json
{
  "hooks": {
    "ConfigChange": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "jq -c '{ts: now|todate, source: .source, file: .file_path}' >> ~/claude-config-audit.log"
          }
        ]
      }
    ]
  }
}
```

### Keep Claude working until a condition holds

`Stop` hook. Deterministic (exit 2 + stderr to continue) or judgment via `prompt`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Check if all tasks are complete. If not, respond {\"ok\": false, \"reason\": \"what remains\"}."
          }
        ]
      }
    ]
  }
}
```

For a `command` Stop hook, **always** short-circuit on `stop_hook_active`:

```bash
INPUT=$(cat)
[ "$(echo "$INPUT" | jq -r '.stop_hook_active')" = "true" ] && exit 0
# ... checks; exit 2 + stderr to keep working
```

Use `agent` type when the check must run tests / read files.

### Auto-approve a specific permission

`PermissionRequest` + a **narrow** matcher, JSON `allow`:

```json
{
  "hooks": {
    "PermissionRequest": [
      {
        "matcher": "ExitPlanMode",
        "hooks": [
          {
            "type": "command",
            "command": "echo '{\"hookSpecificOutput\":{\"hookEventName\":\"PermissionRequest\",\"decision\":{\"behavior\":\"allow\"}}}'"
          }
        ]
      }
    ]
  }
}
```

Never use `.*` or empty matcher here — it auto-approves every prompt including writes and shell. Does not fire in `-p` mode (use `PreToolUse` there). To also switch mode, add `decision.updatedPermissions: [{"type":"setMode","mode":"acceptEdits","destination":"session"}]`.

### Reload env on directory/file change

Pair `SessionStart` + `CwdChanged`, both writing to `$CLAUDE_ENV_FILE`:

```json
{
  "hooks": {
    "SessionStart": [
      { "hooks": [{ "type": "command", "command": "direnv export bash > \"$CLAUDE_ENV_FILE\"" }] }
    ],
    "CwdChanged": [
      { "hooks": [{ "type": "command", "command": "direnv export bash > \"$CLAUDE_ENV_FILE\"" }] }
    ]
  }
}
```

Or watch specific files with `FileChanged` + matcher `.envrc|.env`.

---

## Debugging

**Hook not firing**

- `/hooks` → confirm it appears under the right event.
- Matcher is case-sensitive and must match the tool name exactly.
- Right event? (`PreToolUse` before vs `PostToolUse` after.)
- `PermissionRequest` in `-p` mode never fires — use `PreToolUse`.

**"<hook> hook error" in transcript** — script exited non-zero unexpectedly. Reproduce:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"ls"}}' | ./my-hook.sh; echo $?
```

- "command not found" → use absolute paths / `$CLAUDE_PROJECT_DIR`, or add `"args": []` for exec form (no shell).
- "jq: command not found" → install jq or parse JSON with Python/Node.
- Not running at all → `chmod +x`.

**"/hooks shows nothing"** — invalid JSON (no trailing commas/comments), wrong file location, or watcher missed the edit (restart session).

**"JSON validation failed" but output looks valid** — a shell profile (`~/.bashrc`, Git Bash) prints to stdout in non-interactive shells and corrupts the JSON. Guard profile echoes:

```bash
if [[ $- == *i* ]]; then echo "Shell ready"; fi
```

**Stop hook hit the block cap** — Claude overrides after 8 consecutive blocks. Check `stop_hook_active` and exit 0 early; raise with `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`.

**Full debug log** — `claude --debug-file /tmp/claude.log` then `tail -f /tmp/claude.log`; or `/debug` mid-session. `Ctrl+O` shows the per-hook transcript summary.

---

## Security considerations

Hooks run **arbitrary shell with your full user permissions**, automatically, on data the model controls. Treat every hook as code review surface.

- **Review before deploying** shared/committed hooks — `.claude/settings.json` is executable config in the repo.
- **Validate and quote all input.** `tool_input` fields (paths, commands) are attacker-influenceable. Quote variables (`"$VAR"`), avoid `eval`, never interpolate raw input into shell.
- **Use absolute paths** and pin interpreters; don't trust `$PATH`.
- **Hooks tighten, never loosen.** A hook `deny` blocks even in `bypassPermissions`; a hook `allow` cannot override a settings deny rule. Enforce policy via deny, not allow.
- **Keep auto-approve matchers narrow.** A broad `PermissionRequest` allow silently approves writes and shell commands.
- **Don't leak secrets.** For `http` hooks, gate header env vars with `allowedEnvVars`; keep secret-bearing hooks in `settings.local.json` (gitignored), not committed settings.
- **Mind latency.** Hooks run on their event's hot path; use `async: true` for fire-and-forget side effects, and set tight `timeout`s.
- **Avoid loops.** `Stop`/`SubagentStop` hooks that block must honor `stop_hook_active`.
