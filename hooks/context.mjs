/** Events whose plain `additionalContext` is injected into Claude's context. */
export const CONTEXT_EVENTS = new Set([
  'SessionStart',
  'UserPromptSubmit',
  'PreToolUse',
  'PostToolUse',
  'PostToolUseFailure',
]);

/**
 * Build the correct additive output object for an event so a handler can just
 * return a string. Returns null when the event can't inject context additively
 * (e.g. Stop, where injection requires blocking — which we never do).
 */
export function asContext(event, text) {
  if (!text || !CONTEXT_EVENTS.has(event)) return null;
  return { hookSpecificOutput: { hookEventName: event, additionalContext: text } };
}
