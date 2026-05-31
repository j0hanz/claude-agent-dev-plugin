import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const RUNNER = fileURLToPath(new URL('./runner.mjs', import.meta.url));

/** Run the runner with a given argv + stdin payload; return its stdout. */
function runHook(args, payload) {
  const dir = mkdtempSync(join(tmpdir(), 'agentdev-runner-'));
  return execFileSync('node', [RUNNER, ...args], {
    input: JSON.stringify(payload),
    encoding: 'utf8',
    env: { ...process.env, CLAUDE_PROJECT_DIR: dir, AGENT_DEV_TELEMETRY: '0' },
  }).trim();
}

test('--selfcheck resolves every registered hook', () => {
  const out = execFileSync('node', [RUNNER, '--selfcheck'], { encoding: 'utf8' });
  assert.match(out, /All hooks resolve\./);
  assert.doesNotMatch(out, /FAIL/);
});

test('a returned string is wrapped as additionalContext for the event', () => {
  const out = runHook(['brainstorm-nudge', 'nudge'], {
    hook_event_name: 'UserPromptSubmit',
    prompt: 'build a new authentication feature',
    session_id: 'sess-1',
  });
  const parsed = JSON.parse(out);
  assert.equal(parsed.hookSpecificOutput.hookEventName, 'UserPromptSubmit');
  assert.match(parsed.hookSpecificOutput.additionalContext, /brainstorming/);
});

test('a handler returning null produces no output', () => {
  const out = runHook(['explorer', 'breadcrumb'], {
    hook_event_name: 'PreToolUse',
    tool_name: 'Bash',
    tool_input: { command: 'ls' },
  });
  assert.equal(out, '');
});

test('an unknown handler never throws and emits nothing (exit 0)', () => {
  const out = runHook(['does-not-exist', 'nope'], { hook_event_name: 'Stop' });
  assert.equal(out, '');
});

test('a slash-command prompt is not nudged', () => {
  const out = runHook(['brainstorm-nudge', 'nudge'], {
    hook_event_name: 'UserPromptSubmit',
    prompt: '/build something',
    session_id: 'sess-2',
  });
  assert.equal(out, '');
});
