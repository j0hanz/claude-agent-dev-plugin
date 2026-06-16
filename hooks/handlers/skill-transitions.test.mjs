import { test } from 'node:test';
import assert from 'node:assert/strict';
import { checkBash, checkWrite } from './skill-transitions.mjs';

test('checkBash() true-positive: test keyword + passing output', () => {
  const input = {
    tool_input: { command: 'npm test' },
    tool_response: '3 passing (42ms)',
  };
  const result = checkBash(input);
  assert.ok(result);
  assert.match(result, /verification-before-completion/);
});

test('checkBash() false-positive guard: cat command without test keyword', () => {
  const input = {
    tool_input: { command: 'cat app.js' },
    tool_response: '3 passing (42ms)',
  };
  const result = checkBash(input);
  assert.equal(result, null);
});

test('checkBash() on failure output: test keyword but no passing pattern', () => {
  const input = {
    tool_input: { command: 'npm test' },
    tool_response: '2 tests failed\nFAIL: src/index.test.js',
  };
  const result = checkBash(input);
  assert.equal(result, null);
});

test('checkWrite() returns planning nudge for .specs.md write', () => {
  const input = {
    tool_input: { file_path: 'feat.specs.md' },
  };
  const result = checkWrite(input);
  assert.ok(result);
  assert.match(result, /planning/);
  assert.match(result, /\.specs\.md/);
});

test('checkWrite() returns TDD nudge for .plan.md write', () => {
  const input = {
    tool_input: { file_path: 'feat.plan.md' },
  };
  const result = checkWrite(input);
  assert.ok(result);
  assert.match(result, /test-driven-development/);
  assert.match(result, /\.plan\.md/);
});

test('checkWrite() returns null for unrelated file', () => {
  const input = {
    tool_input: { file_path: 'src/index.js' },
  };
  const result = checkWrite(input);
  assert.equal(result, null);
});
