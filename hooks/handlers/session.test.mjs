import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const ORIGINAL = process.env.CLAUDE_PROJECT_DIR;

async function withProjectDir(dir, fn) {
  process.env.CLAUDE_PROJECT_DIR = dir;
  try {
    // Fresh import each time so getProjectDir() re-reads the env at call time.
    const mod = await import('./session.mjs');
    return await fn(mod);
  } finally {
    if (ORIGINAL === undefined) delete process.env.CLAUDE_PROJECT_DIR;
    else process.env.CLAUDE_PROJECT_DIR = ORIGINAL;
  }
}

test('start() returns null outside a git repository', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'agentdev-nogit-'));
  await withProjectDir(dir, ({ start }) => {
    assert.equal(start(), null);
  });
});

test('start() injects branch and commit context inside this repo', async () => {
  // The plugin repo itself is a git repo — use the package root two levels up.
  const repoRoot = fileURLToPath(new URL('../../', import.meta.url));
  await withProjectDir(repoRoot, ({ start }) => {
    const out = start();
    assert.ok(out, 'expected context output inside a git repo');
    assert.match(out, /Repository context/);
    assert.match(out, /Branch:|Working tree:|Recent commits:/);
  });
});
