#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export function initPlan(filePath) {
  if (!fs.existsSync(filePath)) {
    throw new Error(`Plan file does not exist: ${filePath}`);
  }
  const content = fs.readFileSync(filePath, 'utf-8');
  const lanes = [];
  const lines = content.split('\n');
  let idCounter = 1;

  for (const line of lines) {
    if (line.trim().startsWith('- [ ]')) {
      // 1. Strip the markdown list/checkbox prefix
      let titleText = line.trim().replace(/^-\s*\[\s*[xX ]\s*\]\s*/, '');
      
      // 2. Ignore/remove the "(depends on: ...)" suffix
      titleText = titleText.replace(/\(depends on:[^)]*\)/i, '').trim();

      // 3. Ignore the file list by looking at colons and backticks
      const firstColon = titleText.indexOf(':');
      const firstBacktick = titleText.indexOf('`');
      if (firstColon !== -1 && (firstBacktick === -1 || firstColon < firstBacktick)) {
        titleText = titleText.substring(0, firstColon);
      } else if (firstBacktick !== -1) {
        titleText = titleText.substring(0, firstBacktick);
      }
      const title = titleText.trim() || `Task ${idCounter}`;
      
      // Extract code blocks / files
      const filesTouched = [];
      const codeMatches = line.matchAll(/`([^`]+)`/g);
      for (const m of codeMatches) {
        filesTouched.push(m[1]);
      }

      // Extract dependencies
      const dependsOn = [];
      const depMatch = line.match(/\(depends on:\s*([^)]+)\)/i);
      if (depMatch) {
        const deps = depMatch[1].split(',').map(d => d.trim()).filter(Boolean);
        for (const dep of deps) {
          if (dep.toLowerCase() !== 'none') {
            const laneMatch = dep.match(/lane[- ]?(\d+)/i);
            const taskMatch = dep.match(/task[- ]?(\d+)/i);
            if (laneMatch) {
              dependsOn.push(`lane-${laneMatch[1]}`);
            } else if (taskMatch) {
              dependsOn.push(`lane-${taskMatch[1]}`);
            }
          }
        }
      }

      lanes.push({
        id: `lane-${idCounter++}`,
        title,
        filesTouched,
        dependsOn,
        status: 'PENDING',
        role: 'Writer',
        verdict: null,
        commit: null,
        reviews: {
          spec: { verdict: null, runs: 0 },
          quality: { verdict: null, runs: 0 }
        }
      });
    }
  }

  // Verify that the target lane exists in the parsed lanes list
  for (const lane of lanes) {
    lane.dependsOn = lane.dependsOn.filter(depId => {
      return lanes.some(l => l.id === depId);
    });
  }

  return {
    planPath: filePath,
    status: 'IN_PROGRESS',
    lanes,
    history: [{ timestamp: new Date().toISOString(), event: 'INIT', message: `Initialized with ${lanes.length} lanes` }]
  };
}

export function saveState(state) {
  const stateDir = path.resolve('.claude');
  if (!fs.existsSync(stateDir)) {
    fs.mkdirSync(stateDir, { recursive: true });
  }
  const statePath = path.join(stateDir, 'multi_agent_state.json');
  fs.writeFileSync(statePath, JSON.stringify(state, null, 2), 'utf-8');
}

// CLI entrypoint handling
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const [,, command, arg] = process.argv;
  if (command === 'init' && arg) {
    const state = initPlan(arg);
    saveState(state);
    console.log(`Initialized multi-agent state in .claude/multi_agent_state.json`);
  }
}