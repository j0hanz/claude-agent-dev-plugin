import fs from 'node:fs';
import path from 'node:path';
import { extractImports, detectLang } from './utils/extractor.mjs';
import { findCycles } from './utils/graph.mjs';
import { walkDir } from './utils/walk.mjs';

/**
 * Resolve a relative import to candidate on-disk paths, per language.
 * The previous implementation only tried `.ts`/index.ts, so fan-out and cycle
 * detection silently returned empty for JS, Python, and Go projects.
 * @param {string} fromFile  File containing the import
 * @param {string} imp       Relative import specifier (starts with '.')
 * @param {'js'|'py'|'go'} lang
 * @returns {string[]}
 */
function importCandidates(fromFile, imp, lang) {
  const fromDir = path.dirname(fromFile);

  if (lang === 'py') {
    // Leading dots are package levels: one dot = current package (same dir),
    // each extra dot = one parent up.
    let dots = 0;
    while (imp[dots] === '.') dots++;
    const rest = imp.slice(dots).split('.').filter(Boolean);
    let base = fromDir;
    for (let d = 1; d < dots; d++) base = path.dirname(base);
    const resolved = path.join(base, ...rest);
    return [`${resolved}.py`, path.join(resolved, '__init__.py')];
  }

  // js / go (Go rarely uses relative file imports, but handle them gracefully)
  const resolved = path.resolve(fromDir, imp);
  const candidates = [];
  if (/\.[^./\\]+$/.test(path.basename(imp))) {
    // Import already carries an extension, e.g. './b.js' (ESM/Node style).
    candidates.push(resolved);
    // TS allows a '.js' specifier to resolve to the '.ts' source.
    const noExt = resolved.replace(/\.[^.]+$/, '');
    candidates.push(`${noExt}.ts`, `${noExt}.tsx`);
  }
  candidates.push(
    `${resolved}.ts`,
    `${resolved}.tsx`,
    `${resolved}.js`,
    `${resolved}.jsx`,
    `${resolved}.mjs`,
    `${resolved}.cjs`,
    `${resolved}.go`,
    path.join(resolved, 'index.ts'),
    path.join(resolved, 'index.tsx'),
    path.join(resolved, 'index.js'),
    path.join(resolved, 'index.jsx'),
    path.join(resolved, 'index.mjs'),
  );
  return candidates;
}

export function runLocalityCheck(
  targetDir,
  exclude = [
    'node_modules',
    '.test.',
    '.spec.',
    '.git',
    '.svn',
    '.hg',
    '.pytest_cache',
    '.tox',
    '__pycache__',
    '.venv',
    'venv',
    '.env',
    'dist',
    'build',
    'coverage',
    '.coverage',
    '.next',
    '.nuxt',
    '.cache',
    '.parcel',
    '.npm',
    '.yarn',
    'target',
    '.gradle',
    '.m2',
    '.pytest',
    '.mypy_cache',
    '.ruff_cache',
    '.vscode',
    '.idea',
    '.DS_Store',
  ],
) {
  const files = walkDir(targetDir, exclude);
  const graph = {};

  for (const file of files) {
    const content = fs.readFileSync(file, 'utf8');
    const lang = detectLang(file);
    const imports = extractImports(content, lang);
    graph[file] = [];

    for (const imp of imports) {
      // Only care about relative imports for locality
      if (!imp.startsWith('.')) continue;
      for (const candidate of importCandidates(file, imp, lang)) {
        try {
          fs.statSync(candidate);
          graph[file].push(candidate);
          break;
        } catch {
          // not found, try next candidate
        }
      }
    }
  }

  const cycles = findCycles(graph);

  // Calculate Fan-out
  const fanOut = Object.entries(graph)
    .map(([file, deps]) => ({ file, count: deps.length }))
    .sort((a, b) => b.count - a.count);

  return { cycles, fanOut };
}

// CLI entry point
if (
  process.argv[1] &&
  (process.argv[1] === new URL(import.meta.url).pathname ||
    process.argv[1].endsWith('check-locality.mjs'))
) {
  const dir = process.argv[2] || 'src';
  console.log(`Checking locality in ${dir}...`);
  try {
    const { cycles, fanOut } = runLocalityCheck(path.resolve(process.cwd(), dir));
    console.log('\n--- Circular Dependencies ---');
    cycles.forEach((cycle, i) => {
      console.log(`\nCycle ${i + 1}:`);
      cycle.forEach((c) => console.log(`  - ${path.relative(process.cwd(), c)}`));
    });
    if (cycles.length === 0) console.log('None found.');

    console.log('\n--- Top 5 Fan-out (Highest Imports) ---');
    fanOut.slice(0, 5).forEach((f) => {
      console.log(`  - ${path.relative(process.cwd(), f.file)} (${f.count} imports)`);
    });
  } catch (e) {
    if (e.code === 'ENOENT') {
      console.error(`Directory not found: ${dir}`);
    } else {
      console.error(e);
    }
  }
}
