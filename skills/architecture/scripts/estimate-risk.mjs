import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { walkDir } from './utils/walk.mjs';
import { extractImports, detectLang } from './utils/extractor.mjs';

/**
 * Estimate refactoring risk for a list of target files.
 *
 * Risk factors:
 *  - callerCount:  how many other files import this file (fan-in)
 *  - hasTests:     whether a test file exists for this module
 *  - churn:        git commits touching this file in the last 90 days
 *
 * Risk level:
 *  HIGH   = callerCount > 5 OR (callerCount > 2 AND no tests)
 *  MEDIUM = callerCount 2–5 OR (no tests AND low churn)
 *  LOW    = callerCount <= 1 AND has tests
 *
 * @param {string[]} targetFiles  Absolute paths of files to score
 * @param {string}   rootDir      Root directory to scan for callers
 * @returns {Array<{file, risk, callerCount, hasTests, churn, rationale}>}
 */
export function estimateRisk(targetFiles, rootDir) {
  const absRoot = path.resolve(rootDir);
  const allFiles = walkDir(absRoot);

  // Build reverse graph: for each target, how many files import it?
  const callerCounts = {};
  for (const tf of targetFiles) callerCounts[tf] = 0;

  for (const src of allFiles) {
    if (targetFiles.includes(src)) continue;
    let content;
    try {
      content = fs.readFileSync(src, 'utf8');
    } catch {
      continue;
    }
    const lang = detectLang(src);
    const imports = extractImports(content, lang);
    for (const imp of imports) {
      if (!imp.startsWith('.')) continue;
      const resolved = path.resolve(path.dirname(src), imp);
      for (const tf of targetFiles) {
        // Match the import to this target by exact path, extension-stripped
        // equality (extensionless import), or `<dir>/index.*`. A raw startsWith
        // over-counts files whose path is merely a prefix of another
        // (e.g. user.ts vs userService.ts).
        const tfNoExt = tf.replace(/\.[^.]+$/, '');
        const isIndex = path.basename(tfNoExt) === 'index';
        if (resolved === tf || resolved === tfNoExt || (isIndex && resolved === path.dirname(tf))) {
          callerCounts[tf]++;
        }
      }
    }
  }

  const results = [];
  for (const tf of targetFiles) {
    const callers = callerCounts[tf] || 0;
    // Per-file test detection: does a test file exist for *this* module?
    // (The previous global `allFiles.some(...)` returned the same value for
    // every target whenever the repo had any test anywhere.)
    const baseName = path.basename(tf).replace(/\.[^.]+$/, '');
    const hasTests = allFiles.some((f) => {
      if (f === tf) return false;
      const fb = path.basename(f);
      return (
        fb.startsWith(`${baseName}.test.`) ||
        fb.startsWith(`${baseName}.spec.`) ||
        fb.startsWith(`${baseName}_test.`) ||
        fb === `test_${baseName}.py`
      );
    });

    let churn = 0;
    try {
      // execFileSync (no shell) so paths/args with special chars can't be
      // reinterpreted by the shell.
      const log = execFileSync('git', ['log', '--oneline', '--since=90 days ago', '--', tf], {
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'pipe'],
      });
      churn = log.trim().split('\n').filter(Boolean).length;
    } catch {
      // git not available
    }

    let risk, rationale;
    if (callers > 5 || (callers > 2 && !hasTests)) {
      risk = 'HIGH';
      rationale =
        callers > 5
          ? `${callers} callers — touching this breaks many dependents`
          : `${callers} callers and no test coverage`;
    } else if (callers > 1 || (!hasTests && churn > 3)) {
      risk = 'MEDIUM';
      rationale = !hasTests
        ? `No tests — changes are hard to validate safely`
        : `${callers} callers — moderate blast radius`;
    } else {
      risk = 'LOW';
      rationale = `${callers} caller(s)${hasTests ? ', has test coverage' : ''}`;
    }

    results.push({
      file: path.relative(process.cwd(), tf),
      risk,
      callerCount: callers,
      hasTests,
      churn,
      rationale,
    });
  }

  return results;
}

// CLI entry point
if (
  process.argv[1] &&
  (process.argv[1] === new URL(import.meta.url).pathname ||
    process.argv[1].endsWith('estimate-risk.mjs'))
) {
  const files = process.argv.slice(2);
  if (files.length < 2) {
    console.error('Usage: node estimate-risk.mjs <root-dir> <file1> [file2 ...]');
    process.exit(1);
  }
  const rootDir = files[0];
  const targets = files.slice(1).map((f) => path.resolve(f));

  const results = estimateRisk(targets, rootDir);
  console.log('\n--- Refactoring Risk Estimate ---\n');
  console.table(
    results.map((r) => ({
      Risk: r.risk,
      File: r.file,
      Callers: r.callerCount,
      'Has Tests': r.hasTests ? 'yes' : 'no',
      'Git Churn (90d)': r.churn,
      Rationale: r.rationale,
    })),
  );
}
