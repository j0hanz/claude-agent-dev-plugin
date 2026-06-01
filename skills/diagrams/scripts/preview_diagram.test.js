import test from 'node:test';
import assert from 'node:assert';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const scriptPath = path.join(
  path.dirname(import.meta.url.replace('file:///', '')),
  'preview_diagram.js',
);

test('preview_diagram generates URL and HTML file', () => {
  const testFile = path.join(
    path.dirname(import.meta.url.replace('file:///', '')),
    'test_diagram.mmd',
  );
  fs.writeFileSync(testFile, 'graph TD\nA-->B');

  try {
    const output = execFileSync(process.execPath, [scriptPath, testFile]).toString();
    assert.match(output, /https:\/\/kroki\.io\/mermaid\/svg\//);
    assert.match(output, /preview\.html/);
  } finally {
    fs.unlinkSync(testFile);
  }
});
