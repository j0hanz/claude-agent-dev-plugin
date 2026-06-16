import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import fsPromises from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';

const ORIGINAL = process.env.CLAUDE_PROJECT_DIR;

async function withProjectDir(dir, fn) {
  process.env.CLAUDE_PROJECT_DIR = dir;
  try {
    const mod = await import('./webcache.mjs');
    return await fn(mod);
  } finally {
    if (ORIGINAL === undefined) delete process.env.CLAUDE_PROJECT_DIR;
    else process.env.CLAUDE_PROJECT_DIR = ORIGINAL;
  }
}

let originalFetch;

function setupFetch() {
  originalFetch = globalThis.fetch;
}

function teardownFetch() {
  globalThis.fetch = originalFetch;
}

test('check() returns null when cache file is absent', async () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'webcache-test-'));
  try {
    await withProjectDir(tmpDir, async ({ check }) => {
      const input = { tool_input: { url: 'https://example.com/api' } };
      const result = await check(input);
      assert.equal(result, null);
    });
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

test('check() returns block on mocked 304', async () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'webcache-test-'));
  try {
    await withProjectDir(tmpDir, async ({ check }) => {
      const cacheDir = path.join(tmpDir, '.claude', 'webcache');
      await fsPromises.mkdir(cacheDir, { recursive: true });

      const cacheFile = path.join(cacheDir, '37c82ad45a5353188d3b3dbfed2e808b.json');
      await fsPromises.writeFile(
        cacheFile,
        JSON.stringify({
          url: 'https://example.com/api',
          etag: '"abc123"',
          last_modified: 'Mon, 01 Jan 2024 00:00:00 GMT',
          content: 'cached content',
          fetched_at: Date.now(),
        }),
      );

      setupFetch();
      globalThis.fetch = async (url) => {
        assert.equal(url, 'https://example.com/api');
        return new Response(null, { status: 304 });
      };

      const input = { tool_input: { url: 'https://example.com/api' } };
      const result = await check(input);
      assert.ok(result);
      assert.equal(result.decision, 'block');
      assert.ok(result.reason.includes('[webcache] Cache hit'));
      assert.ok(result.reason.includes('304'));
      teardownFetch();
    });
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

test('check() returns null on 200 response', async () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'webcache-test-'));
  try {
    await withProjectDir(tmpDir, async ({ check }) => {
      const cacheDir = path.join(tmpDir, '.claude', 'webcache');
      await fsPromises.mkdir(cacheDir, { recursive: true });

      const cacheFile = path.join(cacheDir, '37c82ad45a5353188d3b3dbfed2e808b.json');
      await fsPromises.writeFile(
        cacheFile,
        JSON.stringify({
          url: 'https://example.com/api',
          etag: '"abc123"',
          content: 'cached content',
          fetched_at: Date.now(),
        }),
      );

      setupFetch();
      globalThis.fetch = async () => new Response(null, { status: 200 });

      const input = { tool_input: { url: 'https://example.com/api' } };
      const result = await check(input);
      assert.equal(result, null);
      teardownFetch();
    });
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

test('check() returns null on timeout', async () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'webcache-test-'));
  try {
    await withProjectDir(tmpDir, async ({ check }) => {
      const cacheDir = path.join(tmpDir, '.claude', 'webcache');
      await fsPromises.mkdir(cacheDir, { recursive: true });

      const cacheFile = path.join(cacheDir, '37c82ad45a5353188d3b3dbfed2e808b.json');
      await fsPromises.writeFile(
        cacheFile,
        JSON.stringify({
          url: 'https://example.com/api',
          etag: '"abc123"',
          content: 'cached content',
          fetched_at: Date.now(),
        }),
      );

      setupFetch();
      globalThis.fetch = async () => {
        const err = new Error('timeout');
        err.name = 'AbortError';
        throw err;
      };

      const input = { tool_input: { url: 'https://example.com/api' } };
      const result = await check(input);
      assert.equal(result, null);
      teardownFetch();
    });
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

test('store() writes cache file when validators present', async () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'webcache-test-'));
  try {
    await withProjectDir(tmpDir, async ({ store }) => {
      setupFetch();
      globalThis.fetch = async () => {
        return new Response(null, {
          status: 200,
          headers: {
            ETag: '"abc123"',
            'Last-Modified': 'Mon, 01 Jan 2024 00:00:00 GMT',
          },
        });
      };

      const input = {
        tool_input: { url: 'https://example.com/api' },
        tool_response: 'response content',
      };
      const result = await store(input);
      assert.equal(result, null);

      const cacheDir = path.join(tmpDir, '.claude', 'webcache');
      const files = await fsPromises.readdir(cacheDir);
      assert.ok(files.length > 0);

      const cached = JSON.parse(await fsPromises.readFile(path.join(cacheDir, files[0]), 'utf-8'));
      assert.equal(cached.content, 'response content');
      assert.equal(cached.etag, '"abc123"');
      teardownFetch();
    });
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

test('store() skips when neither ETag nor Last-Modified present', async () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'webcache-test-'));
  try {
    await withProjectDir(tmpDir, async ({ store }) => {
      setupFetch();
      globalThis.fetch = async () => new Response(null, { status: 200, headers: {} });

      const input = {
        tool_input: { url: 'https://example.com/api' },
        tool_response: 'response content',
      };
      const result = await store(input);
      assert.equal(result, null);

      const cacheDir = path.join(tmpDir, '.claude', 'webcache');
      const files = await fsPromises.readdir(cacheDir).catch(() => []);
      assert.equal(files.length, 0);
      teardownFetch();
    });
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

test('store() handles timeout silently', async () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'webcache-test-'));
  try {
    await withProjectDir(tmpDir, async ({ store }) => {
      setupFetch();
      globalThis.fetch = async () => {
        const err = new Error('timeout');
        err.name = 'AbortError';
        throw err;
      };

      const input = {
        tool_input: { url: 'https://example.com/api' },
        tool_response: 'response content',
      };
      const result = await store(input);
      assert.equal(result, null);
      teardownFetch();
    });
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});
