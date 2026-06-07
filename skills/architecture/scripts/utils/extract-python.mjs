/**
 * Extract import targets from Python source.
 * Handles:
 *   import os
 *   import os.path
 *   from os import path
 *   from os.path import join, exists
 *   from .relative import something
 *   from ..parent import something
 *   from . import sibling
 */
export function extractPythonImports(fileContent) {
  return extractPythonImportsWithPositions(fileContent).map((m) => m.specifier);
}

/**
 * Like {@link extractPythonImports} but also returns each match's character
 * offset, so callers can compute line numbers for multiline-aware scanning.
 * @param {string} fileContent
 * @returns {Array<{ specifier: string, index: number }>}
 */
export function extractPythonImportsWithPositions(fileContent) {
  const results = [];

  // `import X` and `import X as Y` — capture the module name
  const importRegex = /^import\s+([\w.]+)/gm;
  // `from X import ...` — capture X (handles relative dots)
  const fromRegex = /^from\s+(\.{0,2}[\w.]*)\s+import/gm;

  let match;
  while ((match = importRegex.exec(fileContent)) !== null) {
    results.push({ specifier: match[1], index: match.index });
  }
  while ((match = fromRegex.exec(fileContent)) !== null) {
    // Relative imports start with '.' — preserve the dot so callers can detect them
    results.push({ specifier: match[1] || '.', index: match.index });
  }

  return results;
}

/**
 * Return the top-level package name from a Python import string.
 * e.g. "os.path" -> "os", "sqlalchemy.orm" -> "sqlalchemy"
 */
export function topLevelPackage(imp) {
  if (imp.startsWith('.')) return imp; // keep relative as-is
  return imp.split('.')[0];
}
