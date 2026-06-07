import { execFileSync } from 'node:child_process';
import path from 'node:path';

/**
 * Analyzes git history to find files that frequently change together.
 * Co-change coupling is the #1 signal static analysis cannot surface:
 * two files with no imports of each other can still be deeply coupled
 * if engineers always touch them in the same commit.
 *
 * @param {string} dir   Directory to scope the analysis to (relative or absolute)
 * @param {object} opts
 * @param {number} opts.minCount     Minimum co-change count to report (default: 3)
 * @param {number} opts.topN         Max pairs to return (default: 20)
 * @param {string} opts.since        Git --since arg, e.g. "6 months ago" (default: "6 months ago")
 * @returns {{ pairs: Array<{fileA, fileB, count}>, fileChurn: Array<{file, commits}> }}
 */
export function runGitCoupling(dir, { minCount = 3, topN = 20, since = '6 months ago' } = {}) {
  const absDir = path.resolve(dir);

  let log;
  try {
    // execFileSync (no shell) so `since`/`absDir` can't be reinterpreted by the
    // shell, and paths containing quotes/spaces don't break the invocation.
    log = execFileSync(
      'git',
      // `format:COMMIT` emits the literal marker "COMMIT" per commit; a bare
      // `--format=COMMIT` is rejected by git as an unknown pretty format.
      ['log', '--name-only', '--format=format:COMMIT', `--since=${since}`, '--', absDir],
      {
        cwd: absDir,
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'pipe'],
      },
    );
  } catch {
    return { pairs: [], fileChurn: [], error: 'Not a git repository or git not available.' };
  }

  // Parse commits into groups of files
  const commits = [];
  let current = [];
  for (const line of log.split('\n')) {
    const trimmed = line.trim();
    if (trimmed === 'COMMIT') {
      if (current.length > 0) commits.push(current);
      current = [];
    } else if (trimmed) {
      current.push(trimmed);
    }
  }
  if (current.length > 0) commits.push(current);

  // Count co-occurrences
  const pairCounts = {};
  const fileCounts = {};

  for (const files of commits) {
    for (const f of files) {
      fileCounts[f] = (fileCounts[f] || 0) + 1;
    }
    // Only count pairs within commits that touch >1 file
    if (files.length < 2) continue;
    for (let i = 0; i < files.length; i++) {
      for (let j = i + 1; j < files.length; j++) {
        const key = [files[i], files[j]].sort().join('|||');
        pairCounts[key] = (pairCounts[key] || 0) + 1;
      }
    }
  }

  const pairs = Object.entries(pairCounts)
    .filter(([, count]) => count >= minCount)
    .map(([key, count]) => {
      const [fileA, fileB] = key.split('|||');
      return { fileA, fileB, count };
    })
    .sort((a, b) => b.count - a.count)
    .slice(0, topN);

  const fileChurn = Object.entries(fileCounts)
    .map(([file, commits]) => ({ file, commits }))
    .sort((a, b) => b.commits - a.commits)
    .slice(0, topN);

  return { pairs, fileChurn };
}

// CLI entry point
if (
  process.argv[1] &&
  (process.argv[1] === new URL(import.meta.url).pathname ||
    process.argv[1].endsWith('git-coupling.mjs'))
) {
  const dir = process.argv[2] || '.';
  const minCount = parseInt(process.argv[3] || '3', 10);
  const since = process.argv[4] || '6 months ago';

  console.log(
    `Analyzing git co-change coupling in ${dir} (since: ${since}, min-count: ${minCount})...`,
  );

  const { pairs, fileChurn, error } = runGitCoupling(path.resolve(process.cwd(), dir), {
    minCount,
    since,
  });

  if (error) {
    console.error(`\nError: ${error}`);
    process.exit(1);
  }

  console.log('\n--- Co-Change Pairs (files that always change together) ---');
  if (pairs.length === 0) {
    console.log(`None found with co-change count >= ${minCount}.`);
  } else {
    console.table(
      pairs.map((p) => ({
        'File A': p.fileA,
        'File B': p.fileB,
        'Co-changes': p.count,
      })),
    );
    console.log(
      '\nHigh co-change count = hidden coupling. These files likely share a responsibility\nthat no import graph can reveal. Consider whether they belong in the same module.',
    );
  }

  console.log('\n--- Top File Churn (commits touching this file) ---');
  fileChurn.slice(0, 10).forEach((f) => {
    console.log(`  ${f.commits.toString().padStart(4)} commits  ${f.file}`);
  });
}
