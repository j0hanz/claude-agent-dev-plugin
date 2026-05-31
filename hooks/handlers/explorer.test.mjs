import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { breadcrumb, replay, flush } from './explorer.mjs';

const ORIGINAL = process.env.CLAUDE_PROJECT_DIR;

function freshProject() {
  const dir = mkdtempSync(join(tmpdir(), 'agentdev-explorer-'));
  process.env.CLAUDE_PROJECT_DIR = dir;
  return dir;
}

test.afterEach(() => {
  if (ORIGINAL === undefined) delete process.env.CLAUDE_PROJECT_DIR;
  else process.env.CLAUDE_PROJECT_DIR = ORIGINAL;
});

test('breadcrumb records a grep target and replay surfaces it', () => {
  freshProject();
  assert.equal(
    breadcrumb({ tool_name: 'Grep', tool_input: { pattern: 'readStdin', path: 'hooks' } }),
    null,
  );
  const out = replay();
  assert.ok(out, 'expected replay output');
  assert.match(out, /Recently explored/);
  assert.match(out, /grep \/readStdin\//);
});

test('breadcrumb ignores tools with no searchable target', () => {
  freshProject();
  assert.equal(breadcrumb({ tool_name: 'Bash', tool_input: { command: 'ls' } }), null);
  assert.equal(replay(), null);
});

test('replay de-duplicates repeated searches', () => {
  freshProject();
  for (let i = 0; i < 3; i++)
    breadcrumb({ tool_name: 'Glob', tool_input: { pattern: '**/*.mjs' } });
  const out = replay();
  const occurrences = (out.match(/glob \*\*\/\*\.mjs/g) || []).length;
  assert.equal(occurrences, 1);
});

test('flush rotates the trail to its cap', () => {
  const dir = freshProject();
  for (let i = 0; i < 250; i++)
    breadcrumb({ tool_name: 'Read', tool_input: { file_path: `f${i}.txt` } });
  flush();
  const lines = readFileSync(join(dir, '.claude/explorer-breadcrumbs.log'), 'utf8')
    .split('\n')
    .filter(Boolean);
  assert.ok(lines.length <= 200, `expected <=200 lines after flush, got ${lines.length}`);
});
