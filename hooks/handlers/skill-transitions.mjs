import { debug } from '../io.mjs';

export function checkWrite(input = {}) {
  const file = input.tool_input?.file_path || input.tool_input?.path;
  if (!file) return null;

  // 1. Spec write -> Planning transition
  if (file.endsWith('.specs.md')) {
    debug('Skill Transition detected: Specs written -> Planning next', file);
    return `[System Auto-Transition] The specification artifact (${file}) has been successfully written. You MUST now proceed to the next phase: invoke the 'planning' skill to generate the accompanying .plan.md before proceeding to implementation. Do not ask for user permission, proceed directly.`;
  }

  // 2. Planning -> TDD transition
  if (file.endsWith('.plan.md') || file.endsWith('.plan.json')) {
    debug('Skill Transition detected: Planning complete -> TDD next', file);
    return `[System Auto-Transition] The implementation plan artifact (${file}) has been successfully written. You MUST now proceed to the next phase: invoke the 'test-driven-development' skill to execute this plan. Do not ask for user permission, proceed directly to execution if the plan is complete.`;
  }

  return null;
}

export function checkBash(input = {}) {
  // 3. TDD -> Verification transition
  const command = input.tool_input?.command || '';
  const response = input.tool_response || '';

  // Guard 1: command must contain a test-like keyword
  const testKeywords = ['test', 'spec', 'jest', 'vitest', 'mocha', 'pytest', 'describe'];
  const hasTestKeyword = testKeywords.some((kw) => command.toLowerCase().includes(kw));
  if (!hasTestKeyword) return null;

  // Guard 2: output must match passing test pattern
  const passingPattern = /✓|✔|PASS(?:ED)?|\bpassed\b.*\d+|\d+\s+passing|ok\s+\d+/i;
  if (!passingPattern.test(String(response))) return null;

  return `[System Auto-Transition] Test execution completed successfully. If this concludes the final GREEN cycle of your implementation plan, you MUST now invoke the 'verification-before-completion' skill. Do not wait for user permission.`;
}
