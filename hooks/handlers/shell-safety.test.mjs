import { test } from 'node:test';
import assert from 'node:assert/strict';
import { check } from './shell-safety.mjs';

test('check() returns non-null for rm -rf', () => {
  const input = { tool_input: { command: 'rm -rf /tmp/data' } };
  const result = check(input);
  assert.ok(result);
  assert.match(result, /force-remove/);
  assert.doesNotMatch(result, /\/tmp\/data/);
});

test('check() returns non-null for git push --force', () => {
  const input = { tool_input: { command: 'git push --force origin main' } };
  const result = check(input);
  assert.ok(result);
  assert.match(result, /force-push/);
});

test('check() returns non-null for DROP TABLE', () => {
  const input = { tool_input: { command: 'DROP TABLE users;' } };
  const result = check(input);
  assert.ok(result);
  assert.match(result, /DROP TABLE/);
});

test('check() returns non-null for TRUNCATE TABLE', () => {
  const input = { tool_input: { command: 'TRUNCATE TABLE logs;' } };
  const result = check(input);
  assert.ok(result);
  assert.match(result, /TRUNCATE/);
});

test('check() returns non-null for git reset --hard', () => {
  const input = { tool_input: { command: 'git reset --hard HEAD~1' } };
  const result = check(input);
  assert.ok(result);
  assert.match(result, /hard reset/);
});

test('check() returns non-null for git checkout --', () => {
  const input = { tool_input: { command: 'git checkout -- src/app.js' } };
  const result = check(input);
  assert.ok(result);
  assert.match(result, /discard changes/);
});

test('check() returns null for safe commands', () => {
  assert.equal(check({ tool_input: { command: 'ls -la' } }), null);
  assert.equal(check({ tool_input: { command: 'git status' } }), null);
  assert.equal(check({ tool_input: { command: 'npm install' } }), null);
  assert.equal(check({ tool_input: { command: 'git push origin main' } }), null);
});

test('check() returns null when command is missing', () => {
  assert.equal(check({}), null);
  assert.equal(check({ tool_input: {} }), null);
});
