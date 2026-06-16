import { debug } from '../io.mjs';

const RISK_PATTERNS = [
  { re: /rm\s+-rf/, label: 'force-remove pattern' },
  { re: /git\s+push\s+(-f|--force)/, label: 'force-push pattern' },
  { re: /DROP\s+TABLE/i, label: 'SQL DROP TABLE' },
  { re: /TRUNCATE\s+TABLE/i, label: 'SQL TRUNCATE TABLE' },
  { re: /git\s+reset\s+--hard/, label: 'hard reset pattern' },
  { re: /git\s+checkout\s+--/, label: 'checkout -- discard changes' },
  { re: />\s*\/dev\/null.*rm/, label: 'redirect to null with rm' },
];

export function check(input = {}) {
  const command = input?.tool_input?.command;
  if (!command) return null;

  for (const pattern of RISK_PATTERNS) {
    if (pattern.re.test(command)) {
      return `Shell safety: detected a ${pattern.label} — confirm intent before this runs.`;
    }
  }

  return null;
}
