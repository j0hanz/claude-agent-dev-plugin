import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { nudge } from './brainstorm-nudge.mjs';

const ORIGINAL_DIR = process.env.CLAUDE_PROJECT_DIR;
const ORIGINAL_ENV = process.env.AGENT_DEV_BRAINSTORM_NUDGE;

function freshProject() {
  const dir = mkdtempSync(join(tmpdir(), 'agentdev-brainstorm-'));
  process.env.CLAUDE_PROJECT_DIR = dir;
  return dir;
}

test.afterEach(() => {
  if (ORIGINAL_DIR === undefined) delete process.env.CLAUDE_PROJECT_DIR;
  else process.env.CLAUDE_PROJECT_DIR = ORIGINAL_DIR;
  if (ORIGINAL_ENV === undefined) delete process.env.AGENT_DEV_BRAINSTORM_NUDGE;
  else process.env.AGENT_DEV_BRAINSTORM_NUDGE = ORIGINAL_ENV;
});

test('nudge() returns null when the feature is disabled', () => {
  freshProject();
  process.env.AGENT_DEV_BRAINSTORM_NUDGE = '0';
  assert.equal(
    nudge({ prompt: 'build a new authentication feature', session_id: 'sess-dis' }),
    null,
  );
});

test('nudge() returns null for slash commands', () => {
  freshProject();
  assert.equal(nudge({ prompt: '/build something', session_id: 'sess-slash' }), null);
});

test('nudge() returns null when the prompt has no build-intent', () => {
  freshProject();
  assert.equal(nudge({ prompt: 'fix the typo in the readme', session_id: 'sess-fix' }), null);
  assert.equal(
    nudge({ prompt: 'explain how this function works', session_id: 'sess-explain' }),
    null,
  );
});

test('nudge() returns a message for build-intent prompts', () => {
  freshProject();
  const result = nudge({ prompt: 'build a new authentication feature', session_id: 'sess-build' });
  assert.ok(result, 'expected a nudge message');
  assert.match(result, /brainstorming/);
});

test('nudge() returns a message for implement-intent prompts', () => {
  freshProject();
  const result = nudge({ prompt: 'implement a payment module', session_id: 'sess-impl' });
  assert.ok(result, 'expected a nudge message');
});

test('nudge() fires only once per session', () => {
  freshProject();
  const session = 'sess-once';
  const first = nudge({ prompt: 'build a new search feature', session_id: session });
  const second = nudge({ prompt: 'add a new api endpoint', session_id: session });
  assert.ok(first, 'first call should return a nudge');
  assert.equal(second, null, 'second call in same session should be suppressed');
});

test('nudge() returns null when the prompt signals design is already done', () => {
  freshProject();
  assert.equal(
    nudge({ prompt: 'build a feature, already have the spec', session_id: 'sess-spec' }),
    null,
  );
  assert.equal(
    nudge({ prompt: 'implement the plan we brainstormed', session_id: 'sess-bs' }),
    null,
  );
});
