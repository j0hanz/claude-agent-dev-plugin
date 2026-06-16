import test from 'node:test';
import assert from 'node:assert';
import { extractImports } from './extractor.mjs';

test('extracts named imports', () => {
  const content = `import { a } from './a';`;
  const imports = extractImports(content);
  assert.deepStrictEqual(imports, ['./a']);
});

test('extracts type imports', () => {
  const content = `import type { B } from '../b';`;
  const imports = extractImports(content);
  assert.deepStrictEqual(imports, ['../b']);
});

test('extracts default imports', () => {
  const content = `import defaultExport from 'package';`;
  const imports = extractImports(content);
  assert.deepStrictEqual(imports, ['package']);
});

test('extracts require calls', () => {
  const content = `require('fs');`;
  const imports = extractImports(content);
  assert.deepStrictEqual(imports, ['fs']);
});
