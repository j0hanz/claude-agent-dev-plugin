import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const runnerPath = pathToFileURL(path.resolve(__dirname, '../bin/multi-agent-runner.mjs')).href;

function getTmpPlanPath() {
  const rand = Math.random().toString(36).substring(2, 10);
  return path.resolve(__dirname, `tmp-plan-${Date.now()}-${rand}.md`);
}

test('parses markdown plan correctly', async () => {
  const planContent = `# Plan
- [ ] Task 1: Touch \`src/auth.ts\` and \`tests/auth.test.ts\` (depends on: none)
- [ ] Task 2: Touch \`src/db.ts\` (depends on: Task 1)
`;
  const tmpPlan = getTmpPlanPath();
  fs.writeFileSync(tmpPlan, planContent, 'utf-8');

  try {
    const { initPlan } = await import(`${runnerPath}?t=${Date.now()}`);
    const state = initPlan(tmpPlan);

    assert.strictEqual(state.lanes.length, 2);
    assert.strictEqual(state.lanes[0].id, 'lane-1');
    assert.deepEqual(state.lanes[0].filesTouched, ['src/auth.ts', 'tests/auth.test.ts']);
    assert.deepEqual(state.lanes[0].dependsOn, []);

    assert.strictEqual(state.lanes[1].id, 'lane-2');
    assert.deepEqual(state.lanes[1].filesTouched, ['src/db.ts']);
    assert.deepEqual(state.lanes[1].dependsOn, ['lane-1']);
  } finally {
    if (fs.existsSync(tmpPlan)) fs.unlinkSync(tmpPlan);
  }
});

test('throws error if plan file does not exist', async () => {
  const { initPlan } = await import(`${runnerPath}?t=${Date.now()}`);
  const nonExistentPath = path.resolve(__dirname, `does-not-exist-${Date.now()}.md`);
  assert.throws(() => {
    initPlan(nonExistentPath);
  }, /Plan file does not exist/);
});

test('robustly parses dependencies', async () => {
  const planContent = `# Plan
- [ ] Task 1: Touch \`src/a.ts\` (depends on: none)
- [ ] Task 2: Touch \`src/b.ts\` (depends on: lane-1)
- [ ] Task 3: Touch \`src/c.ts\` (depends on: TASK 2, lane-99)
`;
  const tmpPlan = getTmpPlanPath();
  fs.writeFileSync(tmpPlan, planContent, 'utf-8');

  try {
    const { initPlan } = await import(`${runnerPath}?t=${Date.now()}`);
    const state = initPlan(tmpPlan);

    assert.strictEqual(state.lanes.length, 3);
    assert.deepEqual(state.lanes[0].dependsOn, []);
    assert.deepEqual(state.lanes[1].dependsOn, ['lane-1']);
    assert.deepEqual(state.lanes[2].dependsOn, ['lane-2']);
  } finally {
    if (fs.existsSync(tmpPlan)) fs.unlinkSync(tmpPlan);
  }
});

test('robustly parses titles ignoring file list and depends on', async () => {
  const planContent = `# Plan
- [ ] Task 1: Touch \`src/a.ts\` (depends on: none)
- [ ] Task 2 Touch \`src/b.ts\` (depends on: Task 1)
- [ ] Implement database integration \`src/db.ts\` and \`tests/db.test.ts\` (depends on: lane-1)
`;
  const tmpPlan = getTmpPlanPath();
  fs.writeFileSync(tmpPlan, planContent, 'utf-8');

  try {
    const { initPlan } = await import(`${runnerPath}?t=${Date.now()}`);
    const state = initPlan(tmpPlan);

    assert.strictEqual(state.lanes.length, 3);
    assert.strictEqual(state.lanes[0].title, 'Task 1');
    assert.strictEqual(state.lanes[1].title, 'Task 2 Touch');
    assert.strictEqual(state.lanes[2].title, 'Implement database integration');
  } finally {
    if (fs.existsSync(tmpPlan)) fs.unlinkSync(tmpPlan);
  }
});