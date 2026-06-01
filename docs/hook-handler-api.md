# Hook Handler API

Complete reference for writing hook handlers in the agent-dev plugin.

## Overview

Hook handlers are Node.js ES modules that respond to lifecycle events (SessionStart, UserPromptSubmit, PostToolUse, etc.). All handlers route through `hooks/runner.mjs`, which enforces a consistent pattern:

```bash
node hooks/runner.mjs <domain> <action> [args...]
```

The runner dynamically imports `hooks/handlers/<domain>.mjs` and calls the named `<action>()` function.

## Handler Structure

### Minimal Example

```javascript
// hooks/handlers/example.mjs

export async function nudge() {
  // Perform work
  console.log('Output to inject into context');

  // Always exit cleanly
  process.exit(0);
}
```

Invoked as: `node hooks/runner.mjs example nudge`

### Full Example with Async Work

```javascript
// hooks/handlers/fetch-docs.mjs

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const pluginRoot = path.resolve(__dirname, '../..');

export async function fetchContext() {
  try {
    // Async work
    const data = await someAsyncOperation();

    // Output goes to stdout
    console.log(JSON.stringify(data));

    // Optional: log to telemetry
    const telemetryFile = path.join(pluginRoot, '.claude', 'telemetry.log');
    fs.appendFileSync(telemetryFile, `${new Date().toISOString()}: fetch-docs executed\n`);
  } catch (error) {
    // Log errors but still exit cleanly
    console.error(`[error] ${error.message}`);
  }

  process.exit(0);
}
```

## Core Rules

### 1. Additive Only

Handlers **must not block user interaction**. They:

- Write to stdout (context injection)
- Exit with code 0
- Never use `process.stdin` or interactive prompts
- Never throw uncaught errors

### 2. Runner Dispatch Pattern

Every handler is invoked through `hooks/runner.mjs`. The runner:

- Dynamically imports `hooks/handlers/<domain>.mjs`
- Calls `export async function <action>()`
- Captures stdout
- Enforces exit(0)

**Never put hook logic outside the handler.**

### 3. Environment Variables

Handlers receive no special environment variables. To access plugin root:

```javascript
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const pluginRoot = path.resolve(__dirname, '../..');
```

### 4. Timeout Handling

Each hook in `hooks.json` specifies a timeout (e.g., `"timeout": 10`). If your handler exceeds the timeout, it will be killed. Design for quick execution:

- **SessionStart hooks**: ~1-2 seconds
- **PreToolUse hooks**: ~0.5 seconds (async: true allows background work)
- **PostToolUse hooks**: ~2-5 seconds
- **UserPromptSubmit hooks**: ~1-2 seconds

## Event Types

### SessionStart

Fired when Claude Code starts or resumes. Load context and inject session variables.

```javascript
// hooks/handlers/session.mjs

export async function start() {
  // Fetch or compute data
  const sessionInfo = getSessionState();

  // Output formatted for context injection
  console.log(`## Session Context\n\n${sessionInfo}`);
  process.exit(0);
}
```

**Used for**: Loading session state, injecting guides, preparing context.

### UserPromptSubmit

Fired after user sends a message. Nudge toward specific workflows.

```javascript
// hooks/handlers/brainstorm-nudge.mjs

export async function nudge() {
  const userMsg = process.env.USER_MESSAGE;

  if (shouldNudgeBrainstorm(userMsg)) {
    console.log(
      '💡 **Consider brainstorming first:** Run `/brainstorm "..."` to validate assumptions before implementing.',
    );
  }

  process.exit(0);
}
```

**Used for**: Workflow nudges, reminders, context-sensitive tips.

### PreToolUse

Fired before a tool is called (Glob, Grep, Read, WebFetch, etc.). Enrich context or pre-fetch data.

```javascript
// hooks/handlers/explorer.mjs

export async function breadcrumb() {
  const toolName = process.env.TOOL_NAME;

  if (toolName === 'WebFetch') {
    // Log URL being fetched (for post-analysis)
    const url = process.env.TOOL_URL;
    console.log(`📌 Fetching: ${url}`);
  }

  process.exit(0);
}
```

**Used for**: Context enrichment, pre-fetching, tracking (async: true for background work).

### PostToolUse

Fired after a tool succeeds (Edit, Write, Read, etc.). Auto-format, lint, or validate output.

```javascript
// hooks/handlers/format.mjs

export async function onWrite() {
  const filePath = process.env.TOOL_OUTPUT_PATH;

  // Auto-format the written file
  if (filePath && filePath.endsWith('.js')) {
    await runPrettier(filePath);
  }

  process.exit(0);
}
```

**Used for**: Auto-formatting, linting, validation.

### PostToolUseFailure

Fired when a tool fails (e.g., Bash exit code non-zero). Surface debugging tools.

```javascript
// hooks/handlers/diagnose-nudge.mjs

export async function onFailure() {
  console.log('🔍 **Use the diagnose skill:** `/diagnose` to debug systematically.');
  process.exit(0);
}
```

**Used for**: Error recovery nudges, debugging suggestions.

### Stop / SessionEnd

Fired when Claude Code stops or session ends. Clean up, flush state, scan for artifacts.

```javascript
// hooks/handlers/debug.mjs

export async function scan() {
  // Scan for debug artifacts (console.log, TODO, etc.)
  const artifacts = await findDebugArtifacts();

  if (artifacts.length > 0) {
    console.log(`⚠️ Debug artifacts found:\n${artifacts.join('\n')}`);
  }

  process.exit(0);
}
```

**Used for**: Cleanup, state flushing, artifact scanning.

## Telemetry

To log hook execution timings:

```javascript
const startTime = Date.now();

// Do work...

const duration = Date.now() - startTime;
const telemetryFile = path.join(pluginRoot, '.claude', 'telemetry.log');

try {
  fs.appendFileSync(
    telemetryFile,
    `${new Date().toISOString()} | hook-domain.action | ${duration}ms\n`,
  );
} catch {
  // Telemetry failure should not crash the handler
}

process.exit(0);
```

Check telemetry with: `cat .claude/telemetry.log | tail -20`

## Testing Handlers

### Unit Tests

Use `node --test` for handler tests:

```javascript
// hooks/handlers/example.test.mjs

import test from 'node:test';
import assert from 'node:assert';

test('nudge handler outputs context', async () => {
  // Mock stdout
  const originalLog = console.log;
  let output = '';
  console.log = (msg) => {
    output += msg;
  };

  try {
    // Import and call handler
    const { nudge } = await import('./example.mjs');
    // Call handler logic directly (don't use process.exit in tests)
    const result = await nudge();

    // Assert
    assert(output.includes('expected text'));
  } finally {
    console.log = originalLog;
  }
});
```

### Integration Tests

Test hooks firing end-to-end:

```bash
node tests/integration/test-hooks-fire.mjs
```

This spawns the hook runner and validates stdout output.

### Manual Testing

To test a handler locally:

```bash
node hooks/runner.mjs <domain> <action>
```

For example:

```bash
node hooks/runner.mjs brainstorm-nudge nudge
# Should output nudge text if conditions are met
```

## Hook Configuration (hooks.json)

Hook definitions live in `hooks/hooks.json`. Each entry maps an event to handlers:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|clear",
        "hooks": [
          {
            "type": "command",
            "command": "node \"${CLAUDE_PLUGIN_ROOT}/hooks/runner.mjs\" session start",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### Configuration Fields

| Field     | Required | Type    | Description                                       |
| --------- | -------- | ------- | ------------------------------------------------- |
| `matcher` | No       | string  | Regex to match event context (omit to always run) |
| `type`    | Yes      | string  | `"command"` (only supported type)                 |
| `command` | Yes      | string  | Shell command to execute                          |
| `timeout` | Yes      | number  | Max seconds before killing hook                   |
| `async`   | No       | boolean | `true` to run in background without waiting       |

### `${CLAUDE_PLUGIN_ROOT}` Substitution

Always use `${CLAUDE_PLUGIN_ROOT}` for plugin paths, never hardcoded paths:

```json
"command": "node \"${CLAUDE_PLUGIN_ROOT}/hooks/runner.mjs\" domain action"
```

## Common Patterns

### Conditional Logic

```javascript
export async function nudge() {
  const shouldRun = checkCondition();

  if (shouldRun) {
    console.log('Nudge text');
  }

  process.exit(0);
}
```

### Reading User Context

```javascript
export async function action() {
  // Hook handlers don't receive args directly, but can read environment
  // Set by the Claude Code harness
  const userMessage = process.env.USER_MESSAGE || '';

  if (userMessage.includes('keyword')) {
    console.log('Context');
  }

  process.exit(0);
}
```

### File System Operations

```javascript
import fs from 'fs';
import path from 'path';

export async function action() {
  const file = path.join(pluginRoot, '.claude', 'state.json');

  try {
    const state = JSON.parse(fs.readFileSync(file, 'utf-8'));
    // Use state...
  } catch {
    // File doesn't exist or is invalid
  }

  process.exit(0);
}
```

## Debugging Hooks

### Enable Hook Debug Logging

```bash
export CLAUDE_HOOKS_DEBUG=1
# Now run Claude Code normally
# Hooks will log to stdout
```

### Check Telemetry

```bash
cat .claude/telemetry.log
```

### Run Handler Directly

```bash
node hooks/runner.mjs <domain> <action>
```

### Inspect Handler Source

```bash
cat hooks/handlers/<domain>.mjs
```

## Best Practices

1. **Keep handlers fast** — Slow hooks block the user
2. **Always exit(0)** — Even on errors, exit cleanly
3. **Use `${CLAUDE_PLUGIN_ROOT}`** — Never hardcoded paths
4. **Test both unit and integration** — Handlers interact with the harness
5. **Document side effects** — If writing files or logs, note that
6. **Avoid stdio competition** — Only use `console.log()` for output
7. **Handle missing environment** — Don't assume env vars exist

## Migration Guide

### From Older Hook Patterns

If you're refactoring older hooks:

**Before**:

```javascript
// hooks/handler.js (CommonJS, mixed logic)
module.exports = {
  nudge: () => {
    // Mixed sync/async
  },
};
```

**After**:

```javascript
// hooks/handlers/example.mjs (ESM, explicit async)
export async function nudge() {
  // ... handler logic
  process.exit(0);
}
```

**Key changes**:

- Use `.mjs` (ES modules)
- Use `export async function`
- Always `process.exit(0)`
- Place in `hooks/handlers/<domain>.mjs`
