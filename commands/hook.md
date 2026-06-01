---
description: Validate all hooks, or create/fix a specific hook handler
argument-hint: [check | new <hook-name> | fix <handler-file>]
---

# Hook Management

Run the hook workflow for: $ARGUMENTS

- `check` — validate hooks.json wiring and all handlers in hooks/handlers/
- `new <name>` — scaffold a new hook handler using the hook-development skill
- `fix <file>` — diagnose and repair a broken hook handler

Dispatches all hooks through hooks/runner.mjs which dynamically imports hooks/handlers/`<domain>`.mjs. Misconfiguration silently breaks the hook lifecycle.

Hooks config: @hooks/hooks.json
Runner: @hooks/runner.mjs
Handlers: !`ls hooks/handlers/`

## Usage

- **check**: After adding or modifying a hook handler, or when hook behavior seems silently broken
- **new**: Scaffolding a handler for a new hook event (PreToolUse, PostToolUse, Stop, etc.)
- **fix**: A specific handler is throwing, not firing, or producing wrong output
- Before a release, to verify all hook wiring is intact

## Execution Steps

1. Parse the argument: `check` / `new` / `fix`
2. For `check`:
   - Read hooks/hooks.json and verify every handler path exists
   - Run the hook test suite and check hook-related test output
   - Report missing handlers or wiring mismatches
3. For `new <name>`:
   - Invoke the hook-development skill with the handler name
   - Register the new handler in hooks/hooks.json
4. For `fix <file>`:
   - Read the handler and identify the error
   - Apply fix with Edit tool
   - Re-run the hook test suite to confirm

Run: !`npm run test:node 2>&1 | tail -20`

> **Note**: Check `package.json` scripts if `npm run test:node` is unavailable — the test script name may differ.

## Troubleshooting

**`check` passes but hooks don't fire** — Verify the hook event name in hooks.json exactly matches the Claude Code hook event name (case-sensitive). Check runner.mjs for the dispatch mapping.

**`new` scaffolds a handler but it never executes** — Confirm the handler is registered in hooks.json and the event name is one Claude Code emits. Run `check` after `new` to verify wiring.

**handler.mjs throws a dynamic import error** — File path in hooks.json is wrong. Path must be relative to runner.mjs, not the project root.

**Tests pass but handler output is wrong** — Test may assert the wrong thing. Check the handler's output contract in hook event docs and compare against test assertions.

## Success Criteria

- For `check`: all handlers exist, no wiring gaps, tests pass
- For `new`: handler scaffolded, registered in hooks.json, test written
- For `fix`: handler repaired, test passes, no regressions
