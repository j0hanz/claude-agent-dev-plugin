import fs from 'node:fs';
import path from 'node:path';

/**
 * Recursively walk a directory, returning paths of TypeScript/JavaScript files.
 * @param {string} dir The directory to walk.
 * @param {string[]} exclude File/directory name substrings to exclude.
 * @param {Set<string>} [visited] Real paths already walked (cycle guard).
 * @returns {string[]} Resolved file paths.
 */
export function walkDir(dir, exclude = [], visited = new Set()) {
  let files = [];
  try {
    // Guard against symlink cycles (common in pnpm/yarn workspaces): track the
    // canonical path so we never recurse into the same real directory twice.
    let real;
    try {
      real = fs.realpathSync(dir);
    } catch {
      real = dir;
    }
    if (visited.has(real)) return files;
    visited.add(real);

    const list = fs.readdirSync(dir);
    for (const file of list) {
      if (exclude.some((ex) => file.includes(ex))) continue;
      const fullPath = path.join(dir, file);
      let stat;
      try {
        stat = fs.statSync(fullPath);
      } catch {
        // Skip files/dirs we can't read (permissions, symlinks, etc.)
        continue;
      }
      if (stat.isDirectory()) {
        files = files.concat(walkDir(fullPath, exclude, visited));
      } else if (
        fullPath.endsWith('.ts') ||
        fullPath.endsWith('.tsx') ||
        fullPath.endsWith('.js') ||
        fullPath.endsWith('.mjs') ||
        fullPath.endsWith('.py') ||
        fullPath.endsWith('.go')
      ) {
        files.push(fullPath);
      }
    }
  } catch {
    // Skip directories we can't read/traverse
  }
  return files;
}
