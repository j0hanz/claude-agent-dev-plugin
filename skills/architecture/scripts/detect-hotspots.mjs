import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { runLocalityCheck } from './check-locality.mjs';
import { runBleedDetection } from './detect-bleed.mjs';
import { runGitCoupling } from './git-coupling.mjs';

/**
 * Composite Architectural Debt Score per file.
 *
 * Score = (fanOut * 2) + (bleedCount * 3) + (churnScore) + (sizeScore)
 *
 * fanOut:      number of imports (high = God module)
 * bleedCount:  infrastructure packages imported in domain code (high = Seam Test failure)
 * churnScore:  git commits touching this file, normalized to 0–5
 * sizeScore:   file line count / 100, capped at 5
 *
 * @param {string} dir           Target directory
 * @param {string[]} infraPkgs   Infrastructure packages to flag as bleed
 * @param {object} opts
 * @param {string} opts.since    Git --since window (default: "6 months ago")
 * @returns {Array<{file, score, fanOut, bleedCount, churn, lines, risk}>}
 */
export function runHotspotDetection(dir, infraPkgs = [], { since = '6 months ago' } = {}) {
  const absDir = path.resolve(dir);

  const { fanOut } = runLocalityCheck(absDir);
  const violations = infraPkgs.length > 0 ? runBleedDetection(absDir, infraPkgs) : [];
  const { fileChurn } = runGitCoupling(absDir, { since, minCount: 1 });

  // git reports paths relative to the repo root, not to absDir. fanOut/bleed
  // keys are absolute paths, so churn must be keyed by absolute paths too or
  // the join silently drops every file (churnScore always 0).
  let repoRoot = absDir;
  try {
    repoRoot = execFileSync('git', ['rev-parse', '--show-toplevel'], {
      cwd: absDir,
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
    }).trim();
  } catch {
    // not a git repo; fileChurn is empty anyway
  }
  const toAbs = (gitRelPath) => path.resolve(repoRoot, gitRelPath);

  // Build lookup maps
  const fanOutMap = Object.fromEntries(fanOut.map((f) => [f.file, f.count]));
  const bleedMap = {};
  for (const v of violations) {
    bleedMap[v.file] = (bleedMap[v.file] || 0) + 1;
  }
  const churnMap = Object.fromEntries(fileChurn.map((f) => [toAbs(f.file), f.commits]));
  const maxChurn = Math.max(...fileChurn.map((f) => f.commits), 1);

  // Union of all files
  const allFiles = new Set([
    ...fanOut.map((f) => f.file),
    ...violations.map((v) => v.file),
    ...fileChurn.map((f) => toAbs(f.file)),
  ]);

  const results = [];
  for (const file of allFiles) {
    if (!fs.existsSync(file)) continue;

    let lines = 0;
    try {
      lines = fs.readFileSync(file, 'utf8').split('\n').length;
    } catch {
      // unreadable — skip size score
    }

    const fo = fanOutMap[file] || 0;
    const bl = bleedMap[file] || 0;
    const rawChurn = churnMap[file] || 0;
    const churnScore = Math.round((rawChurn / maxChurn) * 5);
    const sizeScore = Math.min(Math.floor(lines / 100), 5);
    const score = fo * 2 + bl * 3 + churnScore + sizeScore;

    const risk = score >= 15 ? 'HIGH' : score >= 7 ? 'MEDIUM' : 'LOW';

    results.push({
      file: path.relative(process.cwd(), file),
      score,
      fanOut: fo,
      bleedCount: bl,
      churn: rawChurn,
      lines,
      risk,
    });
  }

  return results.sort((a, b) => b.score - a.score);
}

// CLI entry point
if (
  process.argv[1] &&
  (process.argv[1] === new URL(import.meta.url).pathname ||
    process.argv[1].endsWith('detect-hotspots.mjs'))
) {
  const dir = process.argv[2] || 'src';
  const infraArg =
    process.argv[3] || 'express,typeorm,prisma,fs,path,react,mongoose,sqlalchemy,django,flask';
  const infraPkgs = infraArg.split(',').filter(Boolean);
  const since = process.argv[4] || '6 months ago';

  console.log(`\nDetecting architectural hotspots in ${dir}...`);
  console.log(`Infrastructure packages: ${infraPkgs.join(', ')}`);
  console.log(`Git window: since ${since}\n`);

  const results = runHotspotDetection(path.resolve(process.cwd(), dir), infraPkgs, { since });

  if (results.length === 0) {
    console.log('No files found.');
    process.exit(0);
  }

  console.log('--- Architectural Debt Hotspots (ranked) ---\n');
  console.table(
    results.slice(0, 15).map((r) => ({
      Risk: r.risk,
      Score: r.score,
      File: r.file,
      'Fan-out': r.fanOut,
      'Infra Bleeds': r.bleedCount,
      'Git Churn': r.churn,
      Lines: r.lines,
    })),
  );

  const high = results.filter((r) => r.risk === 'HIGH');
  if (high.length > 0) {
    console.log(
      `\n⚠  ${high.length} HIGH-risk file(s) found. These are your top refactoring targets.`,
    );
  }
}
