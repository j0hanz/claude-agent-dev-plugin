import { extractPythonImportsWithPositions } from './extract-python.mjs';

/**
 * Extract import specifiers from source content.
 * @param {string} fileContent
 * @param {'js'|'py'|'go'} [lang] - auto-detected if omitted
 * @returns {string[]}
 */
export function extractImports(fileContent, lang) {
  return extractImportsWithPositions(fileContent, lang).map((m) => m.specifier);
}

/**
 * Like {@link extractImports} but also returns each match's character offset,
 * so callers can compute line numbers without scanning line-by-line (which
 * misses multiline `import { ... } from '...'` statements).
 * @param {string} fileContent
 * @param {'js'|'py'|'go'} [lang]
 * @returns {Array<{ specifier: string, index: number }>}
 */
export function extractImportsWithPositions(fileContent, lang) {
  if (lang === 'py') return extractPythonImportsWithPositions(fileContent);
  if (lang === 'go') return extractGoImportsWithPositions(fileContent);

  const results = [];
  // Match `import ... from '...'` or `import '...'` (may span multiple lines)
  const importRegex = /import(?:[\s.*{},_a-zA-Z0-9]+from\s+)?['"](.*?)['"]/g;
  // Match `require('...')`
  const requireRegex = /require\(['"](.*?)['"]\)/g;

  let match;
  while ((match = importRegex.exec(fileContent)) !== null) {
    results.push({ specifier: match[1], index: match.index });
  }
  while ((match = requireRegex.exec(fileContent)) !== null) {
    results.push({ specifier: match[1], index: match.index });
  }
  return results;
}

/**
 * Extract Go import targets, handling both forms:
 *   import "fmt"
 *   import alias "github.com/x/y"
 *   import (
 *     "fmt"
 *     alias "github.com/x/y"
 *   )
 * @param {string} fileContent
 * @returns {Array<{ specifier: string, index: number }>}
 */
function extractGoImportsWithPositions(fileContent) {
  const results = [];

  // Block form: import ( ... ) — extract each quoted path inside.
  const blockRegex = /import\s*\(([\s\S]*?)\)/g;
  let m;
  while ((m = blockRegex.exec(fileContent)) !== null) {
    const inner = m[1];
    const innerStart = m.index + m[0].indexOf(inner);
    const strRegex = /(?:[\w.]+\s+)?"([^"]+)"/g;
    let s;
    while ((s = strRegex.exec(inner)) !== null) {
      results.push({ specifier: s[1], index: innerStart + s.index });
    }
  }

  // Single form: import "pkg" or import alias "pkg" (the `(` of the block form
  // is followed by no quote, so the block matches above are not re-counted here).
  const singleRegex = /import\s+(?:[\w.]+\s+)?"([^"]+)"/g;
  while ((m = singleRegex.exec(fileContent)) !== null) {
    results.push({ specifier: m[1], index: m.index });
  }

  return results;
}

/** Detect language from file extension. Returns 'js', 'py', or 'go'. */
export function detectLang(filePath) {
  if (filePath.endsWith('.py')) return 'py';
  if (filePath.endsWith('.go')) return 'go';
  return 'js';
}
