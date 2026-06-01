import test from 'node:test';
import assert from 'node:assert';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const scriptPath = path.join(
  path.dirname(import.meta.url.replace('file:///', '')),
  'lint_diagram.js',
);

test('lint_diagram fails on > 20 nodes', () => {
  const hugeDiagram = `graph TD\n${Array.from({ length: 25 }, (_, i) => `A${i}-->B${i}`).join('\n')}`;
  const testFile = path.join(
    path.dirname(import.meta.url.replace('file:///', '')),
    'test_huge.mmd',
  );
  fs.writeFileSync(testFile, hugeDiagram);

  try {
    execFileSync(process.execPath, [scriptPath, testFile]);
    assert.fail('Should have thrown error');
  } catch (err) {
    assert.match(err.stdout.toString(), /Fail: Diagram exceeds 20 nodes/);
  } finally {
    fs.unlinkSync(testFile);
  }
});
