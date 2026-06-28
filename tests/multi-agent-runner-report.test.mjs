import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { renderStatusTable } from '../bin/multi-agent-runner.mjs';

test('renders state table as clean Markdown', () => {
  const state = {
    lanes: [
      {
        id: 'lane-1',
        title: 'Auth Check',
        status: 'COMPLETED',
        verdict: 'DONE',
        reviews: { spec: { verdict: 'SPEC_PASS' }, quality: { verdict: 'QUALITY_PASS' } }
      }
    ]
  };

  const output = renderStatusTable(state);
  assert.ok(output.includes('| Lane | Title | Status | Spec | Quality |'));
  assert.ok(output.includes('| lane-1 | Auth Check | COMPLETED | SPEC_PASS | QUALITY_PASS |'));
});

test('step command fails when --update is missing a payload', () => {
  const stateDir = path.resolve('.claude');
  const statePath = path.join(stateDir, 'multi_agent_state.json');
  const dirExisted = fs.existsSync(stateDir);
  const fileExisted = fs.existsSync(statePath);
  let oldContent = '';
  if (fileExisted) {
    oldContent = fs.readFileSync(statePath, 'utf-8');
  }

  try {
    if (!dirExisted) {
      fs.mkdirSync(stateDir, { recursive: true });
    }
    fs.writeFileSync(statePath, JSON.stringify({ lanes: [] }), 'utf-8');

    const result = spawnSync('node', ['bin/multi-agent-runner.mjs', 'step', '--update'], {
      encoding: 'utf-8',
    });
    assert.strictEqual(result.status, 1);
    assert.ok(result.stderr.includes('Error: Missing payload for --update parameter.'));
  } finally {
    if (fileExisted) {
      fs.writeFileSync(statePath, oldContent, 'utf-8');
    } else {
      try {
        fs.unlinkSync(statePath);
      } catch {}
      if (!dirExisted) {
        try {
          fs.rmdirSync(stateDir);
        } catch {}
      }
    }
  }
});

test('step command fails when --update payload is malformed JSON', () => {
  const stateDir = path.resolve('.claude');
  const statePath = path.join(stateDir, 'multi_agent_state.json');
  const dirExisted = fs.existsSync(stateDir);
  const fileExisted = fs.existsSync(statePath);
  let oldContent = '';
  if (fileExisted) {
    oldContent = fs.readFileSync(statePath, 'utf-8');
  }

  try {
    if (!dirExisted) {
      fs.mkdirSync(stateDir, { recursive: true });
    }
    fs.writeFileSync(statePath, JSON.stringify({ lanes: [] }), 'utf-8');

    const result = spawnSync('node', ['bin/multi-agent-runner.mjs', 'step', '--update', '{invalid-json'], {
      encoding: 'utf-8',
    });
    assert.strictEqual(result.status, 1);
    assert.ok(result.stderr.includes('Error: Malformed JSON payload for --update.'));
  } finally {
    if (fileExisted) {
      fs.writeFileSync(statePath, oldContent, 'utf-8');
    } else {
      try {
        fs.unlinkSync(statePath);
      } catch {}
      if (!dirExisted) {
        try {
          fs.rmdirSync(stateDir);
        } catch {}
      }
    }
  }
});
