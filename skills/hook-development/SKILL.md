---
name: hook-development
description: |
  Claude Code's event system for intercepting and shaping agent behavior at lifecycle points.
  Use when designing PreToolUse guards, PostToolUse formatters, SessionStart context loaders,
  Stop validators, or any hook-driven automation. Trigger on: "add a hook", "block this tool",
  "auto-format on save", "run tests before stop", "intercept file writes", or any mention of
  hooks.json. Key mindset: every hook adds latency — only hook when the risk reduction is worth it.
disable-model-invocation: false
---

# Hook Development for Claude Code Plugins

Claude Code hooks are a powerful event system that allows you to intercept and control the agent's behavior at key lifecycle points.

## Core Mindset

1. **Hooks are a Latency Tax.** Every hook adds 50–200ms. Is the risk reduction worth the wait?
2. **Deterministic > Semantic.** Prefer fast Command hooks for simple rules; use Prompt hooks only for reasoning.
3. **Fail Securely.** If a hook fails or hangs, it should fail in a way that doesn't compromise system integrity.
4. **No Hot-Reload.** You MUST restart Claude Code (`ctrl+c` and restart) to load changes to `hooks.json`.

---

## Planning Your Hook Strategy

Before writing JSON, follow this 3-step decision flow:

1.  **Goal Assessment:** What exactly are you trying to intercept or influence?
2.  **Determine Cadence:** Does this require "Once per Session", "Once per Turn", or "Every Tool Call" precision?
3.  **Choose Mechanism:**
    - **Deterministic (Command Hook):** Fast (<5ms), logic is purely scriptable (e.g., block `rm -rf`).
    - **Semantic (Prompt Hook):** Slower (200ms+), requires LLM reasoning (e.g., style checking).
    - **In-Tool (No Hook):** Can Claude fix this himself? If yes, **don't hook.**

---

## Hook Lifecycle Events

| Cadence              | Event                | Input Data (`stdin`) | Purpose                                                    |
| :------------------- | :------------------- | :------------------- | :--------------------------------------------------------- |
| **Once per Session** | `SessionStart`       | `is_resume`, `is_compact` | Load context, set env vars.                                |
|                      | `SessionEnd`         | None                 | Cleanup temporary files/connections.                       |
| **Once per Turn**    | `UserPromptSubmit`   | `prompt`             | Validate or transform user input.                          |
|                      | `Stop`               | `transcript`, `final_response` | Validate completeness (e.g., run tests).                  |
|                      | `StopFailure`        | `reason`             | React to interrupted/failed turns.                         |
| **Every Tool Call**  | `PreToolUse`         | `tool_name`, `tool_input` | Block/modify operations before run.                        |
|                      | `PostToolUse`        | `tool_name`, `tool_result` | Post-processing (formatting, logging).                     |
|                      | `PostToolUseFailure` | `tool_name`, `error` | Handle tool errors.                                        |
|                      | `PermissionRequest`  | `permission`, `command` | Auto-approve or custom-gate permissions.                  |

---

## Thinking Framework: Should I Hook?

**MANDATORY — READ ENTIRE FILE**: Before designing any hook architecture, read the decision trees in [`references/best-practices.md`](references/best-practices.md).

### The ROI Filter

- Is it **Deterministic** and **Fast** (< 5ms)? → Use **Command Hook**.
- Is it **Semantic** and worth **200ms**? → Use **Prompt Hook**.
- Can it be done **In-Tool** (let Claude fix errors)? → **Don't hook**.

### The NEVER List (Summary)

- **NEVER** hook file writes to validate syntax (Claude can fix it in-tool).
- **NEVER** assume hooks see each other (they run in parallel).
- **NEVER** use `eval` on tool inputs (security risk).
- **NEVER** use hardcoded absolute paths (use `${CLAUDE_PLUGIN_ROOT}`).
- **NEVER** configure a hook that prompts the user or blocks execution — `-p` and `/loop` flows run headless; interactive prompts silently stall automation.
- **NEVER** write a blocking hook when a non-blocking one solves it; prefer exit-0 (allow) or exit-2 (block) patterns over prompt hooks for deterministic rules.

---

## Hook Implementation Workflow

1. **Draft in settings** — Test in `~/.claude/settings.json` first.
2. **Choose Type**:
   - `command`: Local script/binary. Exit 0 to allow, exit 2 to block.
   - `prompt`: Single-turn LLM judgment call.
   - `http`: POST request to external API.
   - `mcp_tool`: Call a tool from a connected MCP server.
3. **Verify Output** — Ensure scripts output valid JSON on `stdout`.
4. **Audit & Lint** — Use the utility scripts in `scripts/`.

## Concrete Templates

### 1. Command Hook: Block dangerous commands
Save as `block-dangerous.sh`:
```bash
#!/bin/bash
# Read JSON from stdin
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')

if [[ "$COMMAND" == *"rm -rf /"* ]]; then
  echo '{"decision": "deny", "reason": "Dangerous command blocked"}'
  exit 2
fi
echo '{"decision": "approve"}'
exit 0
```
And in `hooks.json`:
```json
{
  "events": { "PreToolUse": ["./block-dangerous.sh"] }
}
```

### 2. Prompt Hook: Style Validator
In `hooks.json`:
```json
{
  "events": {
    "Stop": ["prompt:Check style compliance against internal guidelines..."]
  }
}
```

---

## Quick Schema Reference

| Command Decision Output | Format |
| :--- | :--- |
| **All Hooks** | `{"decision": "approve" | "deny" | "ask", "reason": "..."}` |
| **Exit Code (Command)** | Exit 0 (allow), Exit 2 (block) |

---

---

## Proven Patterns

**MANDATORY — READ ENTIRE FILE**: For implementation examples, read [`references/patterns.md`](references/patterns.md).

- **Pattern 1-2**: Security & Test Enforcement.
- **Pattern 3-4**: Context Loading & Auto-Formatting.
- **Pattern 9**: Staged Validation (Hybrid Command + Prompt for performance).
- **Pattern 10**: Opt-in hooks using flag files.

---

## Debugging

- Run with `claude --debug` to see hook input/output.
- Use `jq .` to validate script output format.
- Use `scripts/test-hook.sh` to isolate script logic from Claude Code.
