import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import { getProjectDir, debug } from '../io.mjs';

const GUARD_DIR = () => path.join(getProjectDir(), '.claude', 'fileguard');
const MARKER_START = '// fileguard-start';
const MARKER_END = '// fileguard-end';

function computeHash(content) {
  return crypto.createHash('sha1').update(content).digest('hex');
}

export async function protect(input = {}) {
  const filePath = input?.tool_input?.file_path;
  if (!filePath) return null;

  // Skip files in fileguard or .claude directories
  if (filePath.includes('fileguard') || filePath.includes('.claude')) {
    return null;
  }

  try {
    const fullPath = path.join(getProjectDir(), filePath);
    const content = await fs.readFile(fullPath, 'utf-8');

    const startIdx = content.indexOf(MARKER_START);
    const endIdx = content.indexOf(MARKER_END);

    if (startIdx === -1 || endIdx === -1 || startIdx >= endIdx) {
      return null; // No markers or invalid structure
    }

    // Extract the block including markers
    const blockStart = content.lastIndexOf('\n', startIdx);
    const blockEnd = content.indexOf('\n', endIdx);
    const blockWithNewlines = content.substring(
      blockStart + 1,
      blockEnd === -1 ? undefined : blockEnd,
    );

    // Extract just the content between markers for hashing
    const contentStart = content.indexOf('\n', startIdx) + 1;
    const contentEnd = endIdx;
    const blockContent = content.substring(contentStart, contentEnd).trim();

    const fullHash = computeHash(blockContent);
    const shortHash = fullHash.slice(0, 8);
    const cacheKey = fullHash.slice(0, 16);

    // Extract reason from the marker line
    const reasonMatch = MARKER_START.match(/fileguard-start:\s*(.+)/);
    const reason = reasonMatch ? reasonMatch[1] : 'protected block';

    // Create the placeholder
    const placeholder = `// FGBLOCK_${shortHash}: ${reason}`;

    // Reconstruct file with placeholder
    const beforeBlock = content.substring(0, blockStart);
    const afterBlock = content.substring(blockEnd === -1 ? undefined : blockEnd);
    const newContent =
      beforeBlock + '\n' + placeholder + (afterBlock ? '\n' : '') + (afterBlock || '');

    // Write the cache file
    const guardDir = GUARD_DIR();
    await fs.mkdir(guardDir, { recursive: true });
    const cacheFile = path.join(guardDir, `${cacheKey}.block.json`);

    await fs.writeFile(
      cacheFile,
      JSON.stringify(
        { path: filePath, hash: shortHash, content: blockWithNewlines, reason },
        null,
        2,
      ),
    );

    // Write the protected file
    await fs.writeFile(fullPath, newContent, 'utf-8');
  } catch (err) {
    if (err.code !== 'ENOENT') {
      debug(`fileguard.protect: error processing ${filePath}: ${err.message}`);
    }
  }

  return null;
}

export async function expand(input = {}) {
  const filePath = input?.tool_input?.file_path;
  if (!filePath) return null;

  try {
    const fullPath = path.join(getProjectDir(), filePath);
    let content = await fs.readFile(fullPath, 'utf-8');

    // Find all FGBLOCK placeholders
    const fgblockPattern = /\/\/\s*FGBLOCK_([a-f0-9]+):\s*(.+)/g;
    let match;
    const replacements = [];

    while ((match = fgblockPattern.exec(content)) !== null) {
      const hash = match[1];
      const reason = match[2];
      replacements.push({ hash, reason, fullMatch: match[0] });
    }

    // For each placeholder, look up and restore the block
    for (const { hash, reason, fullMatch } of replacements) {
      // Find the cache file with matching hash
      const guardDir = GUARD_DIR();
      try {
        const files = await fs.readdir(guardDir);
        let found = false;
        for (const file of files) {
          if (file.endsWith('.block.json')) {
            const cacheContent = await fs.readFile(path.join(guardDir, file), 'utf-8');
            const cached = JSON.parse(cacheContent);
            if (cached.hash === hash) {
              content = content.replace(fullMatch, cached.content);
              found = true;

              // Re-add the placeholder after the block for next session
              const lines = content.split('\n');
              let insertIdx = -1;
              for (let i = 0; i < lines.length; i++) {
                if (
                  lines[i].includes(
                    cached.content.split('\n')[cached.content.split('\n').length - 1],
                  )
                ) {
                  insertIdx = i + 1;
                  break;
                }
              }
              if (insertIdx > 0) {
                lines.splice(insertIdx, 0, `// FGBLOCK_${hash}: ${reason}`);
                content = lines.join('\n');
              }
              break;
            }
          }
        }
        if (!found) {
          debug(`fileguard.expand: cache not found for FGBLOCK_${hash}`);
        }
      } catch {
        debug(`fileguard.expand: error reading cache for FGBLOCK_${hash}`);
      }
    }

    // Write expanded content back
    await fs.writeFile(fullPath, content, 'utf-8');
  } catch (err) {
    if (err.code !== 'ENOENT') {
      debug(`fileguard.expand: error processing ${filePath}: ${err.message}`);
    }
  }

  return null;
}

export async function restore() {
  try {
    const guardDir = GUARD_DIR();
    const files = await fs.readdir(guardDir);

    for (const file of files) {
      if (!file.endsWith('.block.json')) continue;

      const cacheFile = path.join(guardDir, file);
      const cacheContent = await fs.readFile(cacheFile, 'utf-8');
      const cached = JSON.parse(cacheContent);

      try {
        const fullPath = path.join(getProjectDir(), cached.path);
        let fileContent = await fs.readFile(fullPath, 'utf-8');

        // Find and replace the placeholder with the original block
        const placeholder = new RegExp(`\/\/\\s*FGBLOCK_${cached.hash}:\\s*[^\\n]*`);
        fileContent = fileContent.replace(placeholder, cached.content);

        // Write restored content
        await fs.writeFile(fullPath, fileContent, 'utf-8');
      } catch (err) {
        debug(`fileguard.restore: error restoring ${cached.path}: ${err.message}`);
      }

      // Delete the cache file
      try {
        await fs.unlink(cacheFile);
      } catch (err) {
        debug(`fileguard.restore: error deleting cache ${file}: ${err.message}`);
      }
    }
  } catch (err) {
    if (err.code !== 'ENOENT') {
      debug(`fileguard.restore: error reading guard directory: ${err.message}`);
    }
  }

  return null;
}
