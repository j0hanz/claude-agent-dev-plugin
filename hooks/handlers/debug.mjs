// Stop handler — scans the session's uncommitted diff for leftover debug
// artifacts (console.log, debugger, breakpoints, test .only, scratch markers)
// and records a report. Additive only: it does NOT block the stop (that would
// trap the agent); it writes findings to .claude/debug-scan.log and, when
// debugging, surfaces them on stderr. The agent sees the report on the next
// SessionStart-style review, and a human can read the log.

import { sh, appendJsonl, debug as dbg } from '../io.mjs';

// pattern → human label. Kept conservative to minimize false positives.
const PROBES = [
  { re: /\bconsole\.(log|debug|trace)\s*\(/, label: 'console.log' },
  { re: /\bdebugger\s*;?/, label: 'debugger statement' },
  { re: /\b(?:describe|it|test)\.only\s*\(/, label: 'test .only (focused test)' },
  { re: /\b(?:fdescribe|fit)\s*\(/, label: 'focused test (fdescribe/fit)' },
  { re: /\b(?:pdb\.set_trace|breakpoint)\s*\(/, label: 'python breakpoint' },
  { re: /\/\/\s*@ts-ignore/, label: 'ts-ignore suppression' },
  { re: /\/\/\s*@ts-nocheck/, label: 'ts-nocheck suppression' },
  { re: /eslint-disable(?:-next-line)?/, label: 'eslint-disable annotation' },
  { re: /\bTODO\b|\bFIXME\b/, label: 'TODO/FIXME marker' },
  { re: /\bHACK\b|\bXXX\b/, label: 'HACK/XXX marker' },
];

/** Stop: scan added lines in the working diff for debug artifacts. */
export function scan(input = {}, context = {}) {
  // Re-entry guard: if Stop hook is already active in the event pipeline, skip.
  // This prevents duplicate scans when multiple Stop hooks run in parallel.
  if (input.stop_hook_active) return null;

  const eventName = context?.event;
  // For PostToolUse, scope the diff to only the file just written/edited so
  // pre-existing TODOs elsewhere in the repo don't nag on every write.
  const editedFile =
    eventName === 'PostToolUse'
      ? (input?.tool_input?.file_path ?? input?.tool_input?.path ?? null)
      : null;
  const diffArgs = editedFile
    ? ['diff', '--unified=0', '--no-color', '--', editedFile]
    : ['diff', '--unified=0', '--no-color'];
  const diff = sh('git', diffArgs, { timeout: 8000 });
  if (!diff) return null;

  let currentFile = '';
  const findings = [];
  for (const line of diff.split('\n')) {
    if (line.startsWith('+++ b/')) {
      currentFile = line.slice(6);
      continue;
    }
    if (!line.startsWith('+') || line.startsWith('+++')) continue; // added lines only
    const added = line.slice(1);
    for (const probe of PROBES) {
      if (probe.re.test(added)) {
        findings.push({ file: currentFile, kind: probe.label, line: added.trim().slice(0, 120) });
        break;
      }
    }
  }

  if (!findings.length) return null;

  appendJsonl('.claude/debug-scan.log', { timestamp: new Date().toISOString(), findings });
  dbg(`debug scan: ${findings.length} artifact(s) in working diff`);

  // Non-blocking visibility: stderr is shown in verbose mode and never disrupts
  // the agent or the user. We deliberately do not emit a blocking decision.
  process.stderr.write(
    `agent-dev: ${findings.length} possible debug artifact(s) in uncommitted changes ` +
      `(see .claude/debug-scan.log)\n`,
  );

  if (eventName === 'PostToolUse' || eventName === 'PostToolUseFailure') {
    const list = findings.map((f) => `  - ${f.file}: ${f.kind} ("${f.line}")`).join('\n');
    return `Warning: ${findings.length} possible debug artifact(s) or TODO marker(s) left in uncommitted changes:\n${list}\nPlease clean them up before completing the task.`;
  }

  return null;
}
