import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import fsPromises from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import { protect, expand, restore } from './fileguard.mjs';

const ORIGINAL = process.env.CLAUDE_PROJECT_DIR;

async function withProjectDir(dir, fn) {
  process.env.CLAUDE_PROJECT_DIR = dir;
  try {
    const mod = await import('./fileguard.mjs');
    return await fn(mod);
  } finally {
    if (ORIGINAL === undefined) delete process.env.CLAUDE_PROJECT_DIR;
    else process.env.CLAUDE_PROJECT_DIR = ORIGINAL;
  }
}

test('protect() with markers → placeholder on disk', async () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'fileguard-test-'));
  try {
    await withProjectDir(tmpDir, async ({ protect }) => {
      const testFile = path.join(tmpDir, 'test.js');
      const originalContent = `// start
// fileguard-start: generated code
const x = 42;
// fileguard-end
// end`;
      await fsPromises.writeFile(testFile, originalContent);

      const input = { tool_input: { file_path: 'test.js' } };
      await protect(input);

      const newContent = await fsPromises.readFile(testFile, 'utf-8');
      assert.ok(newContent.includes('FGBLOCK_'));
      assert.ok(!newContent.includes('const x = 42'));
    });
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

test('protect() without markers → file unchanged', async () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'fileguard-test-'));
  try {
    await withProjectDir(tmpDir, async ({ protect }) => {
      const testFile = path.join(tmpDir, 'test.js');
      const originalContent = `function hello() {
  console.log('world');
}`;
      await fsPromises.writeFile(testFile, originalContent);

      const input = { tool_input: { file_path: 'test.js' } };
      await protect(input);

      const newContent = await fsPromises.readFile(testFile, 'utf-8');
      assert.equal(newContent, originalContent);
    });
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

test('protect() on .claude/ path → no-op', async () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'fileguard-test-'));
  try {
    await withProjectDir(tmpDir, async ({ protect }) => {
      const claudeDir = path.join(tmpDir, '.claude');
      await fsPromises.mkdir(claudeDir, { recursive: true });
      const testFile = path.join(claudeDir, 'test.js');
      await fsPromises.writeFile(testFile, 'some content');

      const input = { tool_input: { file_path: '.claude/test.js' } };
      const result = await protect(input);
      assert.equal(result, null);
    });
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

test('expand() restores block text', async () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'fileguard-test-'));
  try {
    await withProjectDir(tmpDir, async ({ protect, expand }) => {
      const testFile = path.join(tmpDir, 'test.js');
      const blockContent = `// fileguard-start: test block
const generated = true;
// fileguard-end`;
      const originalContent = `before
${blockContent}
after`;
      await fsPromises.writeFile(testFile, originalContent);

      // Protect first
      await protect({ tool_input: { file_path: 'test.js' } });
      let protectedContent = await fsPromises.readFile(testFile, 'utf-8');
      assert.ok(protectedContent.includes('FGBLOCK_'));

      // Now expand
      await expand({ tool_input: { file_path: 'test.js' } });
      const expandedContent = await fsPromises.readFile(testFile, 'utf-8');
      assert.ok(expandedContent.includes('const generated = true'));
    });
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

test('restore() returns file to original and empties cache', async () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'fileguard-test-'));
  try {
    await withProjectDir(tmpDir, async ({ protect, restore }) => {
      const testFile = path.join(tmpDir, 'test.js');
      const blockContent = `// fileguard-start: test block
const original = true;
// fileguard-end`;
      const originalContent = `start
${blockContent}
end`;
      await fsPromises.writeFile(testFile, originalContent);

      // Protect
      await protect({ tool_input: { file_path: 'test.js' } });

      // Restore
      await restore();

      const restoredContent = await fsPromises.readFile(testFile, 'utf-8');
      assert.ok(restoredContent.includes('const original = true'));

      // Check cache is empty
      const guardDir = path.join(tmpDir, '.claude', 'fileguard');
      const files = await fsPromises.readdir(guardDir).catch(() => []);
      assert.equal(files.filter((f) => f.endsWith('.block.json')).length, 0);
    });
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});
