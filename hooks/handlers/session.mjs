// SessionStart handler — injects live repository context so the agent starts
// each session already oriented, instead of spending its first turns probing
// git. This belongs in a hook (not CLAUDE.md) because the content changes every
// session: branch, uncommitted work, and recent commits.

import { sh } from '../io.mjs';

/**
 * Build a compact orientation block for the current repo state.
 * Returns a string (injected as additionalContext) or null when not a git repo.
 */
export function start() {
  const inside = sh('git', ['rev-parse', '--is-inside-work-tree'], { timeout: 3000 });
  if (inside !== 'true') return null;

  const branch = sh('git', ['rev-parse', '--abbrev-ref', 'HEAD'], { timeout: 3000 });
  const status = sh('git', ['status', '--porcelain'], { timeout: 5000 });
  const changed = status ? status.split('\n').filter(Boolean) : [];
  const log = sh('git', ['log', '-5', '--pretty=format:%h %s'], { timeout: 5000 });

  const lines = ['## Repository context (auto-injected)'];
  if (branch) {
    lines.push(`Branch: \`${branch}\``);
  } else {
    lines.push('Branch: [git branch unavailable]');
  }

  if (changed.length) {
    lines.push(`Uncommitted changes: ${changed.length} file(s)`);
    const preview = changed.slice(0, 10).map((l) => `  ${l}`);
    lines.push(...preview);
    if (changed.length > 10) lines.push(`  …and ${changed.length - 10} more`);
  } else if (status === null) {
    lines.push('Uncommitted changes: [git status unavailable — may have changes]');
  } else {
    lines.push('Working tree: clean');
  }

  if (log) {
    lines.push('Recent commits:');
    lines.push(...log.split('\n').map((l) => `  ${l}`));
  } else {
    lines.push('Recent commits: [git log unavailable]');
  }

  // Stashes
  const stashes = sh('git', ['stash', 'list', '--format=%gd: %s'], { timeout: 5000 });
  lines.push('Stashes:');
  if (stashes) {
    const stashLines = stashes.split('\n').filter(Boolean).slice(0, 5);
    lines.push(...stashLines.map((l) => `  ${l}`));
    if (stashes.split('\n').filter(Boolean).length > 5) {
      lines.push(`  …and ${stashes.split('\n').filter(Boolean).length - 5} more`);
    }
  } else {
    lines.push('  none');
  }

  // Upstream divergence
  const divergence = sh('git', ['rev-list', '--count', '--left-right', 'HEAD...@{u}'], {
    timeout: 5000,
  });
  lines.push('Upstream:');
  if (divergence) {
    const [ahead, behind] = divergence.trim().split('\t');
    lines.push(`  ${ahead} ahead / ${behind} behind`);
  } else {
    lines.push('  no tracking branch');
  }

  // Runtime versions
  const nodeVersion = sh(process.execPath, ['--version'], { timeout: 3000 });
  const pythonVersion =
    sh('python', ['--version'], { timeout: 3000 }) ||
    sh('python3', ['--version'], { timeout: 3000 });
  lines.push('Runtime:');
  if (nodeVersion) lines.push(`  Node: ${nodeVersion}`);
  if (pythonVersion) lines.push(`  Python: ${pythonVersion}`);

  const output = lines.join('\n');
  return output.slice(0, 2000);
}
