// Non-blocking PreToolUse hook: warns the documenter agent when it is about to
// write to a non-documentation file. The guard is advisory (exit 0) — it injects
// context so the agent reconsiders, never blocks execution.

import path from 'path';
import { createPreToolUse } from '../utils.mjs';

const DOC_EXTENSIONS = new Set(['.md', '.rst', '.txt', '.adoc', '.mdx']);

const DOC_DIRS = ['docs', 'doc', 'documentation', 'wiki', 'pages', '.github'];

function isDocFile(filePath) {
  if (!filePath) return true;
  const ext = path.extname(filePath).toLowerCase();
  if (DOC_EXTENSIONS.has(ext)) return true;
  const parts = filePath.replace(/\\/g, '/').split('/');
  return parts.some((part) => DOC_DIRS.includes(part.toLowerCase()));
}

export async function guardWrite(input) {
  const agentType = input?.agent_type;
  if (agentType && agentType !== 'documenter') return null;

  const filePath = input?.tool_input?.file_path;
  if (isDocFile(filePath)) return null;

  const warning =
    `> **Documenter guard:** You are about to write to \`${filePath}\`, which is not a documentation file.\n` +
    `> Your mandate is documentation only. If the source code needs changing, report it as a gap instead of editing the file.`;

  return createPreToolUse(input?.tool_input, warning);
}
