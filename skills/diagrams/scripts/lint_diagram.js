import fs from 'node:fs';

const filePath = process.argv[2];
if (!filePath) {
  console.error('Usage: node lint_diagram.js <file.mmd>');
  process.exitCode = 1;
  process.exit();
}

const content = fs.readFileSync(filePath, 'utf-8');
const lines = content.split('\n');
const nodeCount = lines.filter((l) => l.includes('-->') || l.match(/^[A-Za-z0-9_]+\[/)).length;

if (nodeCount > 20) {
  console.log('Fail: Diagram exceeds 20 nodes');
  process.exitCode = 1;
  process.exit();
}

if (
  content.includes('sequenceDiagram') &&
  content.includes('->>') &&
  (content.includes('Kafka') || content.includes('Queue'))
) {
  console.log('Fail: Synchronous arrow used with async keywords');
  process.exitCode = 1;
  process.exit();
}

if (content.includes('classDiagram') && !content.includes('<<')) {
  console.log('Fail: Class diagram missing DDD stereotypes');
  process.exitCode = 1;
  process.exit();
}

console.log('Pass');
