import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { debug } from '../io.mjs';

// Resolved relative to this file so it works regardless of process cwd.
const PLUGIN_ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const GUIDE = join(PLUGIN_ROOT, 'skills', 'using-agent-dev-skills', 'SKILL.md');
const MAX_CHARS = 10000; // platform cap on injected context

function enabled() {
  return process.env.AGENT_DEV_SKILLS_ANNOUNCE !== '0';
}

function stripFrontmatter(md) {
  const lines = md.split('\n');
  if (lines[0]?.trim() !== '---') return md;
  let i = 1;
  while (i < lines.length && lines[i].trim() !== '---') i++;
  return lines.slice(i + 1).join('\n');
}

// SessionStart: injects the skill routing guide as additive context.
export function announce() {
  if (!enabled()) return null;

  let body;
  try {
    body = stripFrontmatter(readFileSync(GUIDE, 'utf8')).trim();
  } catch (err) {
    debug('skills.announce: cannot read routing guide', String(err));
    return null;
  }
  if (!body) return null;

  const header =
    'The agent-dev plugin ships the skills mapped below. When a task matches ' +
    'one, invoke it with the Skill tool rather than improvising; for overlaps ' +
    'and sequencing, this routing guide is authoritative.';

  const content = (header + '\n\n' + body).slice(0, MAX_CHARS - 26);
  return `<IMPORTANT>\n${content}\n</IMPORTANT>`;
}
