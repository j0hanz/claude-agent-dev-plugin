import { test } from 'node:test';
import assert from 'node:assert/strict';
import { writeFileSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { onWrite } from './format.mjs';

const ORIGINAL = process.env.CLAUDE_PROJECT_DIR;

function freshDir() {
  const dir = mkdtempSync(join(tmpdir(), 'agentdev-format-'));
  process.env.CLAUDE_PROJECT_DIR = dir;
  return dir;
}

test.afterEach(() => {
  if (ORIGINAL === undefined) delete process.env.CLAUDE_PROJECT_DIR;
  else process.env.CLAUDE_PROJECT_DIR = ORIGINAL;
});

test('onWrite() returns null with missing or empty input', () => {
  assert.equal(onWrite(), null);
  assert.equal(onWrite({}), null);
  assert.equal(onWrite({ tool_input: {} }), null);
});

test('onWrite() returns null for a non-existent file path', () => {
  assert.equal(onWrite({ tool_input: { file_path: '/does/not/exist.js' } }), null);
});

test('onWrite() returns null for an unsupported file extension', () => {
  freshDir();
  const file = join(process.env.CLAUDE_PROJECT_DIR, 'notes.txt');
  writeFileSync(file, 'hello world\n');
  assert.equal(onWrite({ tool_input: { file_path: file } }), null);
});

test('onWrite() returns null for a JS file (runs Prettier or skips gracefully)', () => {
  freshDir();
  const file = join(process.env.CLAUDE_PROJECT_DIR, 'index.mjs');
  writeFileSync(file, 'const x = 1;\n');
  assert.equal(onWrite({ tool_input: { file_path: file } }), null);
});

test('onWrite() returns null for a JSON file', () => {
  freshDir();
  const file = join(process.env.CLAUDE_PROJECT_DIR, 'data.json');
  writeFileSync(file, '{"a":1}\n');
  assert.equal(onWrite({ tool_input: { file_path: file } }), null);
});

test('onWrite() returns null for a Markdown file', () => {
  freshDir();
  const file = join(process.env.CLAUDE_PROJECT_DIR, 'README.md');
  writeFileSync(file, '# Hello\n');
  assert.equal(onWrite({ tool_input: { file_path: file } }), null);
});

test('onWrite() returns null for a Python file (runs ruff or skips gracefully)', () => {
  freshDir();
  const file = join(process.env.CLAUDE_PROJECT_DIR, 'script.py');
  writeFileSync(file, 'x = 1\n');
  assert.equal(onWrite({ tool_input: { file_path: file } }), null);
});
