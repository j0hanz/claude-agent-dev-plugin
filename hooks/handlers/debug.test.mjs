import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, existsSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { execFileSync } from 'node:child_process';
import { scan } from './debug.mjs';

const ORIGINAL = process.env.CLAUDE_PROJECT_DIR;

test.afterEach(() => {
  if (ORIGINAL === undefined) delete process.env.CLAUDE_PROJECT_DIR;
  else process.env.CLAUDE_PROJECT_DIR = ORIGINAL;
});

test('scan() returns null immediately when stop_hook_active is set', () => {
  assert.equal(scan({ stop_hook_active: true }), null);
});

test('scan() returns null when not inside a git repository', () => {
  const dir = mkdtempSync(join(tmpdir(), 'agentdev-debug-nogit-'));
  process.env.CLAUDE_PROJECT_DIR = dir;
  assert.equal(scan(), null);
});

test('scan() returns null when the working diff is clean', () => {
  const dir = mkdtempSync(join(tmpdir(), 'agentdev-debug-clean-'));
  process.env.CLAUDE_PROJECT_DIR = dir;
  execFileSync('git', ['init', '-q'], { cwd: dir });
  execFileSync('git', ['config', 'user.email', 'test@test.com'], { cwd: dir });
  execFileSync('git', ['config', 'user.name', 'Test'], { cwd: dir });
  writeFileSync(join(dir, 'app.js'), 'const x = 1;\n');
  execFileSync('git', ['add', '.'], { cwd: dir });
  execFileSync('git', ['commit', '-m', 'init', '--no-verify'], { cwd: dir });

  assert.equal(scan(), null);
});

test('scan() detects console.log in uncommitted changes and writes to log', () => {
  const dir = mkdtempSync(join(tmpdir(), 'agentdev-debug-found-'));
  process.env.CLAUDE_PROJECT_DIR = dir;
  execFileSync('git', ['init', '-q'], { cwd: dir });
  execFileSync('git', ['config', 'user.email', 'test@test.com'], { cwd: dir });
  execFileSync('git', ['config', 'user.name', 'Test'], { cwd: dir });
  writeFileSync(join(dir, 'app.js'), 'const x = 1;\n');
  execFileSync('git', ['add', '.'], { cwd: dir });
  execFileSync('git', ['commit', '-m', 'init', '--no-verify'], { cwd: dir });

  writeFileSync(join(dir, 'app.js'), 'const x = 1;\nconsole.log(x);\n');

  const result = scan();
  assert.equal(result, null); // always returns null (additive only)

  const logPath = join(dir, '.claude/debug-scan.log');
  assert.ok(existsSync(logPath), 'debug-scan.log should be created on findings');
  const entry = JSON.parse(readFileSync(logPath, 'utf8').trim().split('\n').at(-1));
  assert.ok(entry.findings.length > 0, 'should have at least one finding');
  assert.equal(entry.findings[0].kind, 'console.log');
  assert.ok(entry.timestamp, 'log entry should have a timestamp field');
});

test('scan() detects TODO markers in uncommitted changes', () => {
  const dir = mkdtempSync(join(tmpdir(), 'agentdev-debug-todo-'));
  process.env.CLAUDE_PROJECT_DIR = dir;
  execFileSync('git', ['init', '-q'], { cwd: dir });
  execFileSync('git', ['config', 'user.email', 'test@test.com'], { cwd: dir });
  execFileSync('git', ['config', 'user.name', 'Test'], { cwd: dir });
  writeFileSync(join(dir, 'app.js'), 'const x = 1;\n');
  execFileSync('git', ['add', '.'], { cwd: dir });
  execFileSync('git', ['commit', '-m', 'init', '--no-verify'], { cwd: dir });

  writeFileSync(join(dir, 'app.js'), 'const x = 1;\n// TODO: remove this\n');

  scan();

  const logPath = join(dir, '.claude/debug-scan.log');
  assert.ok(existsSync(logPath));
  const entry = JSON.parse(readFileSync(logPath, 'utf8').trim().split('\n').at(-1));
  assert.ok(entry.findings.some((f) => f.kind === 'TODO/FIXME marker'));
});
