// PostToolUseFailure(Bash) handler — when a shell command fails, inject the
// structured-debugging skill as context alongside a trimmed error excerpt, so
// the agent reaches for a methodology instead of blind retries. Additive only:
// uses additionalContext, never blocks, fires only on repeated failures to avoid
// noise on one-off typos.

import { appendJsonl, readJsonlTail, trimJsonl } from '../utils.mjs';

const STATE = '.claude/state/diagnose-nudge.jsonl';
const THRESHOLD = 2; // nudge once this many Bash failures pile up in a session
const WINDOW = 2000; // read window — comfortably larger than any single session
const MAX_STATE = 2000; // bound the file so it can't grow unbounded

function errorExcerpt(input) {
  const r = input.tool_response;
  const text = typeof r === 'string' ? r : r?.stderr || r?.error || r?.output || '';
  return String(text).split('\n').filter(Boolean).slice(0, 3).join(' ⏎ ').slice(0, 240);
}

/** PostToolUseFailure: nudge toward the diagnose skill after repeated failures. */
export function onFailure(input = {}) {
  if (input.tool_name !== 'Bash') return null;

  const session = input.session_id || 'unknown';
  appendJsonl(STATE, { ts: new Date().toISOString(), session });
  trimJsonl(STATE, MAX_STATE);

  const sessionRecords = readJsonlTail(STATE, WINDOW).filter((r) => r.session === session);
  // A "nudged" marker — not exact equality on a count — decides whether we've
  // already nudged. Once the tail window slides past a session's early entries,
  // its count can skip the threshold value entirely and never fire (or re-fire).
  const alreadyNudged = sessionRecords.some((r) => r.nudged === true);
  const failureCount = sessionRecords.filter((r) => !r.nudged).length;
  if (alreadyNudged || failureCount < THRESHOLD) return null;

  appendJsonl(STATE, { ts: new Date().toISOString(), session, nudged: true });

  const excerpt = errorExcerpt(input);
  const msg =
    'Multiple Bash failures this session. Consider the `diagnose` skill — ' +
    'reproduce → isolate → hypothesize → fix, rather than retrying variants.';
  return excerpt ? `${msg}\nLast error: ${excerpt}` : msg;
}
