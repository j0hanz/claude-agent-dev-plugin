# Hook Events — Full Catalog

Authoritative per-event reference: input fields, output/decision schema, matcher values, and exit-code-2 behavior. Full guide: <https://code.claude.com/docs/en/hooks>

## Table of Contents

- [Quick reference — all events](#quick-reference--all-events)
- [Configuration schema](#configuration-schema)
- [Matcher patterns](#matcher-patterns)
- [Handler types](#handler-types)
- [Common input fields](#common-input-fields)
- [Exit codes](#exit-codes)
- [JSON output — universal fields](#json-output--universal-fields)
- [Decision control — quick reference](#decision-control--quick-reference)
- [Detailed per-event reference](#detailed-per-event-reference)
- [Prompt & agent hooks](#prompt--agent-hooks)
- [Environment variables](#environment-variables)
- [Permission update entries](#permission-update-entries)
- [Tool defer](#tool-defer-pretooluse)

---

## Quick reference — all events

| Event                 | When                                               | Matcher field                   | Can block | Async |
| --------------------- | -------------------------------------------------- | ------------------------------- | --------- | ----- |
| `SessionStart`        | Session begins or resumes                          | `source`                        | No        | No    |
| `Setup`               | `--init-only`, or `--init`/`--maintenance` in `-p` | CLI flag (`init`·`maintenance`) | No        | No    |
| `InstructionsLoaded`  | CLAUDE.md / rules file loaded                      | `load_reason`                   | No        | Yes   |
| `UserPromptSubmit`    | Prompt submitted, before Claude processes          | —                               | Yes       | No    |
| `UserPromptExpansion` | Typed command expands into a prompt                | command name                    | Yes       | No    |
| `PreToolUse`          | Before tool call executes                          | `tool_name`                     | Yes       | No    |
| `PermissionRequest`   | Permission dialog shown to user                    | `tool_name`                     | Yes       | No    |
| `PermissionDenied`    | Auto-mode classifier denies tool call              | `tool_name`                     | No        | No    |
| `PostToolUse`         | After tool call succeeds                           | `tool_name`                     | No\*      | No    |
| `PostToolUseFailure`  | After tool call fails                              | `tool_name`                     | No        | No    |
| `PostToolBatch`       | After a batch of parallel tool calls resolves      | —                               | No        | No    |
| `Notification`        | Claude Code sends a notification                   | `notification_type`             | No        | Yes   |
| `MessageDisplay`      | While assistant message text is displayed          | —                               | No        | No    |
| `SubagentStart`       | Subagent spawned via Agent tool                    | `agent_type`                    | No        | No    |
| `SubagentStop`        | Subagent finishes                                  | `agent_type`                    | Yes       | No    |
| `TaskCreated`         | Task created via TaskCreate                        | —                               | Yes       | No    |
| `TaskCompleted`       | Task marked as completed                           | —                               | Yes       | No    |
| `Stop`                | Claude finishes responding                         | —                               | Yes       | No    |
| `StopFailure`         | Turn ends due to API error                         | `error`                         | No        | No    |
| `TeammateIdle`        | Agent team teammate going idle                     | —                               | Yes       | No    |
| `ConfigChange`        | Config file changes during session                 | `source`                        | Yes       | No    |
| `CwdChanged`          | Working directory changes                          | —                               | No        | No    |
| `FileChanged`         | Watched file changes on disk                       | `filename` (basename)           | No        | No    |
| `WorktreeCreate`      | Worktree being created                             | —                               | Yes       | No    |
| `WorktreeRemove`      | Worktree being removed                             | —                               | No        | No    |
| `PreCompact`          | Before context compaction                          | `trigger`                       | No        | No    |
| `PostCompact`         | After context compaction                           | `trigger`                       | No        | No    |
| `Elicitation`         | MCP server requests user input                     | MCP server name                 | Yes       | No    |
| `ElicitationResult`   | User responds to MCP elicitation                   | MCP server name                 | Yes       | No    |
| `SessionEnd`          | Session terminates                                 | `reason`                        | No        | No    |

\* `PostToolUse` can feed back `decision: "block"` to Claude, but the tool has already executed.

---

## Configuration schema

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "./check.sh",
            "timeout": 30,
            "if": "Bash(rm *)"
          }
        ]
      }
    ]
  }
}
```

When multiple hooks match an event, all run in parallel and identical commands are deduplicated. Every hook's command runs to completion before outputs are merged — one hook's `deny` does not stop sibling hooks' side effects. For `PreToolUse`, the most restrictive decision wins: `deny` > `defer` > `ask` > `allow`. `additionalContext` from every hook is concatenated.

---

## Matcher patterns

| Event(s)                                                                                                                                                        | Matches on                              | Example values                                                                                                                  |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `PermissionDenied`                                                                      | tool name                               | `Bash` · `Edit\|Write` · `mcp__.*`                                                                                              |
| `SessionStart`                                                                                                                                                  | session source                          | `startup` · `resume` · `clear` · `compact`                                                                                      |
| `Setup`                                                                                                                                                         | CLI flag                                | `init` · `maintenance`                                                                                                          |
| `SessionEnd`                                                                                                                                                    | exit reason                             | `clear` · `resume` · `logout` · `prompt_input_exit` · `bypass_permissions_disabled` · `other`                                   |
| `Notification`                                                                                                                                                  | notification type                       | `permission_prompt` · `idle_prompt` · `auth_success` · `elicitation_dialog` · `elicitation_complete` · `elicitation_response`   |
| `SubagentStart`, `SubagentStop`                                                                                                                                 | agent type                              | `general-purpose` · `Explore` · `Plan` · custom names                                                                           |
| `PreCompact`, `PostCompact`                                                                                                                                     | trigger                                 | `manual` · `auto`                                                                                                               |
| `ConfigChange`                                                                                                                                                  | config source                           | `user_settings` · `project_settings` · `local_settings` · `policy_settings` · `skills`                                          |
| `FileChanged`                                                                                                                                                   | file basename (literal, `\|`-separated) | `.envrc` · `.env`                                                                                                               |
| `StopFailure`                                                                                                                                                   | error type                              | `rate_limit` · `authentication_failed` · `billing_error` · `invalid_request` · `server_error` · `max_output_tokens` · `unknown` |
| `InstructionsLoaded`                                                                                                                                            | load reason                             | `session_start` · `nested_traversal` · `path_glob_match` · `include` · `compact`                                                |
| `UserPromptExpansion`                                                                                                                                           | command name                            | your skill/command names                                                                                                        |
| `Elicitation`, `ElicitationResult`                                                                                                                              | MCP server name                         | your MCP server names                                                                                                           |
| `UserPromptSubmit`, `PostToolBatch`, `Stop`, `TeammateIdle`, `TaskCreated`, `TaskCompleted`, `WorktreeCreate`, `WorktreeRemove`, `CwdChanged`, `MessageDisplay` | no matcher                              | always fires                                                                                                                    |

MCP tools follow `mcp__<server>__<tool>`. Use `mcp__memory__.*` to match all tools from a server. Matchers are case-sensitive.

### The `if` field (v2.1.85+)

Filters by tool name AND arguments using permission-rule syntax; the hook process only spawns on a match. Tool events only (`PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `PermissionDenied`). Examples: `"Bash(git *)"`, `"Edit(*.ts)"`. For compound Bash (`npm test && git push`), each subcommand is evaluated. Adding `if` to a non-tool event prevents the hook from running.

---

## Handler types

### Common fields (all types)

| Field           | Required | Description                                                                                                    |
| --------------- | -------- | -------------------------------------------------------------------------------------------------------------- |
| `type`          | Yes      | `"command"` · `"http"` · `"prompt"` · `"agent"` · `"mcp_tool"`                                                 |
| `if`            | No       | Permission-rule filter, e.g. `"Bash(git *)"`. Tool events only.                                                |
| `timeout`       | No       | Seconds before cancel. Defaults: command/http=600, prompt=30, agent=60. `UserPromptSubmit` caps command at 30. |
| `statusMessage` | No       | Custom spinner text while hook runs.                                                                           |
| `once`          | No       | Skills only. If `true`, runs once per session then removes itself.                                             |

### Command hook fields

| Field     | Required | Description                                                                               |
| --------- | -------- | ----------------------------------------------------------------------------------------- |
| `command` | Yes      | Shell command to execute.                                                                 |
| `async`   | No       | If `true`, runs in background (non-blocking).                                             |
| `shell`   | No       | `"bash"` (default) or `"powershell"`.                                                     |
| `args`    | No       | Switches to exec form (spawns script directly, no shell — avoids quoting/profile issues). |

### HTTP hook fields

| Field            | Required | Description                                                |
| ---------------- | -------- | ---------------------------------------------------------- |
| `url`            | Yes      | POST destination. Body = hook JSON input.                  |
| `headers`        | No       | Key-value headers. Supports `$VAR`/`${VAR}` interpolation. |
| `allowedEnvVars` | No       | Env var names permitted for interpolation in headers.      |

HTTP errors (non-2xx, timeouts) are non-blocking. To block, return 2xx with JSON decision fields. Status codes alone cannot block.

### Prompt / agent hook fields

| Field    | Required | Description                                                     |
| -------- | -------- | --------------------------------------------------------------- |
| `prompt` | Yes      | Text sent to model. Use `$ARGUMENTS` to inject hook JSON input. |
| `model`  | No       | Model override. Defaults to a fast model (Haiku).               |

---

## Common input fields

Delivered on stdin (command) or as POST body (http) for every event.

| Field             | Description                                                                              |
| ----------------- | ---------------------------------------------------------------------------------------- |
| `session_id`      | Current session identifier.                                                              |
| `transcript_path` | Path to conversation JSONL.                                                              |
| `cwd`             | Working directory when hook fires.                                                       |
| `hook_event_name` | Name of the event.                                                                       |
| `permission_mode` | `default`·`plan`·`acceptEdits`·`auto`·`dontAsk`·`bypassPermissions` — not on all events. |
| `agent_id`        | Subagent identifier (subagent calls only).                                               |
| `agent_type`      | Agent name (subagent or `--agent` mode).                                                 |

---

## Exit codes

| Code  | Effect                                                                                                                                      |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `0`   | Success. stdout parsed for JSON. Non-JSON stdout shown in verbose mode (except `UserPromptSubmit`/`SessionStart` where it becomes context). |
| `2`   | Blocking error. stdout ignored. stderr fed to Claude or shown to user (event-dependent).                                                    |
| other | Non-blocking error. stderr shown in verbose. Execution continues.                                                                           |

### Exit code 2 behavior per event

| Event                                                                                                                                                                                      | On exit 2                                        |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------ |
| `PreToolUse`                                                                                                                                                                               | Blocks the tool call.                            |
| `PermissionRequest`                                                                                                                                                                        | Denies the permission.                           |
| `UserPromptSubmit`                                                                                                                                                                         | Blocks prompt; erases it from context.           |
| `UserPromptExpansion`                                                                                                                                                                      | Blocks the expansion.                            |
| `Stop`                                                                                                                                                                                     | Prevents Claude from stopping.                   |
| `SubagentStop`                                                                                                                                                                             | Prevents subagent from stopping.                 |
| `TeammateIdle`                                                                                                                                                                             | Teammate receives stderr and continues working.  |
| `TaskCreated`                                                                                                                                                                              | Rolls back task creation; stderr fed to model.   |
| `TaskCompleted`                                                                                                                                                                            | Prevents task from being marked complete.        |
| `ConfigChange`                                                                                                                                                                             | Blocks config change (except `policy_settings`). |
| `Elicitation`                                                                                                                                                                              | Denies the elicitation.                          |
| `ElicitationResult`                                                                                                                                                                        | Response becomes decline.                        |
| `WorktreeCreate`                                                                                                                                                                           | Any non-zero exit fails creation.                |
| `PostToolUse`                                                                                                                                                                              | Shows stderr to Claude (tool already ran).       |
| `PostToolUseFailure`                                                                                                                                                                       | Shows stderr to Claude.                          |
| `StopFailure`                                                                                                                                                                              | Output/exit code ignored.                        |
| `PermissionDenied`                                                                                                                                                                         | Ignored. Use JSON `retry: true` instead.         |
| `Notification`, `Setup`, `SubagentStart`, `SessionStart`, `SessionEnd`, `CwdChanged`, `FileChanged`, `PreCompact`, `PostCompact`, `WorktreeRemove`, `InstructionsLoaded`, `MessageDisplay` | Non-blocking; stderr shown to user only.         |

---

## JSON output — universal fields

Print a JSON object to stdout on exit 0. Processed alongside event-specific fields.

| Field            | Default | Description                                                                                |
| ---------------- | ------- | ------------------------------------------------------------------------------------------ |
| `continue`       | `true`  | If `false`, Claude stops entirely after this hook. Overrides all event-specific decisions. |
| `stopReason`     | —       | Message shown to user when `continue` is `false`. Not shown to Claude.                     |
| `suppressOutput` | `false` | If `true`, hides stdout from verbose mode.                                                 |
| `systemMessage`  | —       | Warning shown to user.                                                                     |

Context injected via `additionalContext`, `systemMessage`, or plain stdout is capped at 10,000 characters.

---

## Decision control — quick reference

| Events                                                                                          | Pattern                        | Key fields                                                                                                   |
| ----------------------------------------------------------------------------------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------ |
| `UserPromptSubmit`, `PostToolUse`, `PostToolUseFailure`, `Stop`, `SubagentStop`, `ConfigChange` | Top-level `decision`           | `decision: "block"`, `reason`                                                                                |
| `TeammateIdle`, `TaskCreated`, `TaskCompleted`                                                  | Exit code or `continue: false` | Exit 2 = feedback to model. `{"continue":false}` = stop entirely.                                            |
| `PreToolUse`                                                                                    | `hookSpecificOutput`           | `permissionDecision` (allow/deny/ask/defer), `permissionDecisionReason`, `updatedInput`, `additionalContext` |
| `PermissionRequest`                                                                             | `hookSpecificOutput`           | `decision.behavior` (allow/deny), `updatedInput`, `updatedPermissions`, `message`, `interrupt`               |
| `PermissionDenied`                                                                              | `hookSpecificOutput`           | `retry: true`                                                                                                |
| `WorktreeCreate`                                                                                | Path return                    | stdout (command) or `hookSpecificOutput.worktreePath` (http)                                                 |
| `Elicitation`                                                                                   | `hookSpecificOutput`           | `action` (accept/decline/cancel), `content`                                                                  |
| `ElicitationResult`                                                                             | `hookSpecificOutput`           | `action`, `content` (override)                                                                               |
| All others                                                                                      | None                           | Side effects only (logging, cleanup).                                                                        |

---

## Detailed per-event reference

### `SessionStart`

Once per session begin/resume. Command hooks only. **Cannot block.**
Input: `source` (`startup`·`resume`·`clear`·`compact`), `model`, `agent_type?`.
Output: `hookSpecificOutput.additionalContext` (string added to context). Plain stdout also added as context. Write `export KEY=val` to `$CLAUDE_ENV_FILE` to persist env vars into Bash.

### `Setup`

Runs with `--init-only`, or `--init`/`--maintenance` in `-p` mode. One-time CI/script prep. Matcher = CLI flag. **Cannot block.**

### `InstructionsLoaded`

CLAUDE.md or `.claude/rules/*.md` loaded. **Async, observability only.**
Input: `file_path`, `memory_type` (`User`·`Project`·`Local`·`Managed`), `load_reason`, `globs?`, `trigger_file_path?`, `parent_file_path?`. No decision control.

### `UserPromptSubmit`

Before Claude processes a submitted prompt. No matcher. **Can block.**
Input: `prompt`.
Output: `decision: "block"` (+ `reason`, erases prompt), or `hookSpecificOutput.additionalContext` to inject context. Plain stdout on exit 0 also becomes context.

### `UserPromptExpansion`

A typed command expands into a prompt, before it reaches Claude. Matcher = command name. **Can block** the expansion.

### `PreToolUse`

Before a tool executes. Matches `tool_name`. **Can block.**
Input: `tool_name`, `tool_input` (tool-specific), `tool_use_id`.
`tool_input` by tool:

| Tool              | Fields                                                      |
| ----------------- | ----------------------------------------------------------- |
| `Bash`            | `command`·`description?`·`timeout?`·`run_in_background?`    |
| `Write`           | `file_path`·`content`                                       |
| `Edit`            | `file_path`·`old_string`·`new_string`·`replace_all?`        |
| `Read`            | `file_path`·`offset?`·`limit?`                              |
| `Glob`            | `pattern`·`path?`                                           |
| `Grep`            | `pattern`·`path?`·`glob?`·`output_mode?`·`-i?`·`multiline?` |
| `WebFetch`        | `url`·`prompt`                                              |
| `WebSearch`       | `query`·`allowed_domains?`·`blocked_domains?`               |
| `Agent`           | `prompt`·`description?`·`subagent_type?`·`model?`           |
| `AskUserQuestion` | `questions[]`·`answers?`                                    |

Output (`hookSpecificOutput`): `hookEventName: "PreToolUse"` (required), `permissionDecision` (`allow`/`deny`/`ask`/`defer`), `permissionDecisionReason` (allow/ask → user; deny → Claude), `updatedInput` (replaces tool input), `additionalContext`. Conflict resolution: `deny` > `defer` > `ask` > `allow`. `allow` skips the prompt but never overrides a settings deny rule. A hook `deny` blocks even in `bypassPermissions`.

### `PermissionRequest`

Permission dialog about to show. Matches `tool_name`. **Can block.** Does NOT fire in `-p` mode — use `PreToolUse` there.
Input: `tool_name`, `tool_input`, `permission_suggestions[]`.
Output (`hookSpecificOutput`): `hookEventName: "PermissionRequest"`, `decision.behavior` (`allow`/`deny`), `decision.updatedInput` (allow), `decision.updatedPermissions` (allow), `decision.message` (deny → Claude), `decision.interrupt` (deny; `true` stops Claude).

### `PermissionDenied`

Auto-mode classifier denied a tool call. Matches `tool_name`. **Cannot block.**
Input: `tool_name`, `tool_input`, `tool_use_id`, `reason`.
Output: `hookSpecificOutput.retry: true` (tells model it may retry).

### `PostToolUse`

After a tool succeeds. Matches `tool_name`. **Feedback only** (tool already ran).
Input: `tool_name`, `tool_input`, `tool_response`, `tool_use_id`.
Output: `decision: "block"` (+ `reason` → Claude), `hookSpecificOutput.additionalContext`, `hookSpecificOutput.updatedMCPToolOutput` (MCP only — replaces output).

### `PostToolUseFailure`

After a tool fails. Matches `tool_name`. **Cannot block.**
Input: `tool_name`, `tool_input`, `tool_use_id`, `error`, `is_interrupt?`.
Output: `hookSpecificOutput.additionalContext`.

### `PostToolBatch`

After a full batch of parallel tool calls resolves, before the next model call. No matcher.

### `Notification`

Claude Code sends a notification. **Async. Cannot block.**
Input: `message`, `title?`, `notification_type`.
Output: `hookSpecificOutput.additionalContext`.

### `MessageDisplay`

While assistant message text is displayed. No matcher. **Cannot block.**

### `SubagentStart`

Subagent spawned. Matches `agent_type`. **Cannot block.**
Input: `agent_id`, `agent_type`.
Output: `hookSpecificOutput.additionalContext` (added to subagent's context).

### `SubagentStop`

Subagent finishes. Matches `agent_type`. Same control as `Stop`. **Can block.**
Input: `agent_id`, `agent_type`, `agent_transcript_path`, `last_assistant_message`, `stop_hook_active`.
Output: `decision: "block"` (+ `reason`) → subagent continues.

### `TaskCreated`

Task being created via TaskCreate. No matcher. **Can block.**
Input: `task_id`, `task_subject`, `task_description?`, `teammate_name?`, `team_name?`.
Exit 2 = rolls back creation, stderr → model. `{"continue":false}` = stops teammate.

### `TaskCompleted`

Task being marked complete. No matcher. **Can block.** Same input fields as `TaskCreated`.
Exit 2 = task stays open, stderr → model. `{"continue":false}` = stops teammate.

### `Stop`

Claude finishes responding. No matcher. Not fired on user interrupt (API errors fire `StopFailure`). **Can block.**
Input: `stop_hook_active` (check to avoid loops), `last_assistant_message`.
Output: `decision: "block"` (+ required `reason` → why to continue).
Claude Code overrides a Stop hook after 8 consecutive blocks; raise with `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`. Always check `stop_hook_active` and exit 0 early when true.

### `StopFailure`

Turn ends due to API error. Matches error type. **Output ignored.**
Input: `error`, `error_details?`, `last_assistant_message`.

### `TeammateIdle`

Agent-team teammate about to go idle. No matcher. **Can block.**
Input: `teammate_name`, `team_name`.
Exit 2 = teammate gets stderr and continues. `{"continue":false}` = stops teammate.

### `ConfigChange`

Config file changes during session. Matches `source`. **Can block** (except `policy_settings`).
Input: `source`, `file_path?`.
Output: `decision: "block"` (+ `reason` → user).

### `CwdChanged`

Working directory changes. No matcher. Command hooks only. **Cannot block.**
Input: `old_cwd`, `new_cwd`.
Output: `hookSpecificOutput.watchPaths` (replaces dynamic FileChanged watch list). Has `$CLAUDE_ENV_FILE`.

### `FileChanged`

Watched file changes. Matcher = filename basename(s), `|`-separated literals. Command hooks only. **Cannot block.**
Input: `file_path`, `event` (`change`·`add`·`unlink`).
Output: `hookSpecificOutput.watchPaths` (updates dynamic watch list). Has `$CLAUDE_ENV_FILE`.

### `WorktreeCreate`

Worktree being created via `--worktree`/`isolation: "worktree"`. **Any non-zero exit fails creation.**
Input: `name`.
Output: absolute path to created worktree — stdout (command) or `hookSpecificOutput.worktreePath` (http).

### `WorktreeRemove`

Worktree being removed. **Cannot block.** Input: `worktree_path`.

### `PreCompact`

Before compaction. Matches `trigger`. **Cannot block.**
Input: `trigger` (`manual`·`auto`), `custom_instructions?` (manual `/compact` arg).

### `PostCompact`

After compaction. Matches `trigger`. **Cannot block.**
Input: `trigger`, `compact_summary`.

### `Elicitation`

MCP server requests user input. Matches MCP server name. **Can block.**
Input: `mcp_server_name`, `message`, `mode` (`form`·`url`), `requested_schema?`, `url?`, `elicitation_id?`.
Output (`hookSpecificOutput`): `action` (`accept`/`decline`/`cancel`), `content` (accept only).

### `ElicitationResult`

After user responds to MCP elicitation. Matches MCP server name. **Can block.**
Input: `mcp_server_name`, `action`, `content?`, `mode`, `elicitation_id?`.
Output (`hookSpecificOutput`): `action` (override), `content` (override, accept only).

### `SessionEnd`

Session terminates. Matches `reason`. Default timeout 1.5s. **Cannot block.**
Input: `reason` (`clear`·`resume`·`logout`·`prompt_input_exit`·`bypass_permissions_disabled`·`other`). Override timeout: `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS`.

---

## Prompt & agent hooks

**Prompt hooks** (`type: "prompt"`) send the hook input + your prompt to a fast model. Response schema:

```json
{ "ok": true, "reason": "..." }
```

`ok: true` = allow; `ok: false` = block (`reason` required). On `ok: false`: `Stop`/`SubagentStop` feed reason back so Claude keeps working; `PreToolUse` denies with reason as the tool error; `PostToolUse`/`UserPromptSubmit` end the turn with reason as a warning.

**Agent hooks** (`type: "agent"`, experimental) spawn a subagent with Read/Grep/Glob to verify against real codebase state. Same `ok`/`reason` schema, 60s default, up to 50 tool turns.

Supported events for both: `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `Stop`, `SubagentStop`, `TaskCompleted`, `TaskCreated`, `UserPromptSubmit`.

---

## Environment variables

| Variable                | Available in                              | Description                                                                     |
| ----------------------- | ----------------------------------------- | ------------------------------------------------------------------------------- |
| `$CLAUDE_PROJECT_DIR`   | All hooks                                 | Project root directory.                                                         |
| `${CLAUDE_PLUGIN_ROOT}` | Plugin hooks                              | Plugin installation directory.                                                  |
| `${CLAUDE_PLUGIN_DATA}` | Plugin hooks                              | Plugin persistent data directory.                                               |
| `$CLAUDE_ENV_FILE`      | `SessionStart`·`CwdChanged`·`FileChanged` | Write `export KEY=val` lines to persist env vars into subsequent Bash commands. |
| `$CLAUDE_CODE_REMOTE`   | All hooks                                 | `"true"` in remote web environments.                                            |

---

## Permission update entries

Used in `PermissionRequest` output `updatedPermissions` and mirrored in input `permission_suggestions`.

| `type`              | Additional fields                  | Effect                            |
| ------------------- | ---------------------------------- | --------------------------------- |
| `addRules`          | `rules[]`·`behavior`·`destination` | Adds allow/deny/ask rules.        |
| `replaceRules`      | `rules[]`·`behavior`·`destination` | Replaces all rules of a behavior. |
| `removeRules`       | `rules[]`·`behavior`·`destination` | Removes matching rules.           |
| `setMode`           | `mode`·`destination`               | Sets permission mode.             |
| `addDirectories`    | `directories[]`·`destination`      | Adds working directories.         |
| `removeDirectories` | `directories[]`·`destination`      | Removes working directories.      |

`destination`: `session` (in-memory) · `localSettings` (`.claude/settings.local.json`) · `projectSettings` (`.claude/settings.json`) · `userSettings` (`~/.claude/settings.json`).

---

## Tool defer (`PreToolUse`)

Requires v2.1.89+. Only in non-interactive (`-p`) mode, and only when Claude makes a single tool call in the turn. `permissionDecision: "defer"` exits the process with the tool call preserved:

```json
{
  "type": "result",
  "stop_reason": "tool_deferred",
  "session_id": "abc123",
  "deferred_tool_use": { "id": "toolu_01abc", "name": "AskUserQuestion", "input": {} }
}
```

Resume with `claude -p --resume <session-id>` and the same `--permission-mode`. The hook fires again; return `"allow"` with `updatedInput` to proceed. If the deferred tool is unavailable on resume: `stop_reason: "tool_deferred_unavailable"`, `is_error: true`.
