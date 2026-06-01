import test from 'node:test';
import assert from 'node:assert';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const scriptPath = path.join(
  path.dirname(import.meta.url.replace('file:///', '')),
  'scaffold_c4.js',
);

test('scaffold_c4 generates basic C4 from package.json', () => {
  const testDir = path.join(path.dirname(import.meta.url.replace('file:///', '')), 'test_proj');
  fs.mkdirSync(testDir, { recursive: true });
  fs.writeFileSync(
    path.join(testDir, 'package.json'),
    JSON.stringify({ dependencies: { express: '*', pg: '*' } }),
  );

  try {
    const output = execFileSync(process.execPath, [scriptPath, testDir]).toString();
    assert.match(output, /C4Context/);
    assert.match(output, /System\(app, "Application", "Main Application"\)/);
    assert.match(output, /SystemDb\(db, "Database", "Relational\/NoSQL Database"\)/);
  } finally {
    fs.rmSync(testDir, { recursive: true });
  }
});
