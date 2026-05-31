#!/usr/bin/env node
// Central hook dispatcher.
//
//   node runner.mjs <domain> <action>   — run handlers/<domain>.mjs#<action>
//   node runner.mjs --selfcheck         — verify every registered hook resolves
//
// It reads the event JSON on stdin, dynamically imports the handler module,
// calls the named exported action, records telemetry, and emits whatever the
// handler returns. A handler may return:
//   • a string  → wrapped as additionalContext for the current event
//   • an object → emitted verbatim as the hook's JSON output
//   • nullish   → no output (pure side effect)
//
// Invariant: the runner ALWAYS exits 0. A broken hook must never interrupt the
// agent — errors go to telemetry and (when CLAUDE_HOOKS_DEBUG=1) stderr.

import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { readStdin, writeTelemetry, debug, asContext } from './utils.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));

async function loadHandler(domain) {
  const url = new URL(`./handlers/${domain}.mjs`, import.meta.url);
  return import(url.href);
}

/** Validate that every hook registered in hooks.json resolves to a real action. */
async function selfcheck() {
  let config;
  try {
    config = JSON.parse(await readFile(join(HERE, 'hooks.json'), 'utf8'));
  } catch (err) {
    process.stderr.write(`selfcheck: cannot read hooks.json — ${err.message}\n`);
    return 1;
  }

  const seen = new Set();
  for (const groups of Object.values(config.hooks ?? {})) {
    for (const group of groups) {
      for (const h of group.hooks ?? []) {
        const m = /runner\.mjs"?\s+(\S+)\s+(\S+)/.exec(h.command ?? '');
        if (m) seen.add(`${m[1]} ${m[2]}`);
      }
    }
  }

  let ok = true;
  for (const entry of [...seen].sort()) {
    const [domain, action] = entry.split(' ');
    try {
      const mod = await loadHandler(domain);
      if (typeof mod[action] !== 'function') throw new Error(`missing export "${action}"`);
      process.stdout.write(`  ok   ${entry}\n`);
    } catch (err) {
      ok = false;
      process.stdout.write(`  FAIL ${entry} — ${err.message}\n`);
    }
  }
  process.stdout.write(ok ? '\nAll hooks resolve.\n' : '\nSome hooks failed to resolve.\n');
  return ok ? 0 : 1;
}

async function main() {
  const [, , domain, action] = process.argv;

  if (domain === '--selfcheck') {
    process.exit(await selfcheck());
  }

  if (!domain || !action) {
    debug('usage: runner.mjs <domain> <action>');
    return; // exit 0 — nothing to do, never disrupt the workflow
  }

  const input = await readStdin();
  const event = input.hook_event_name || '';
  const started = Date.now();
  let status = 'ok';
  let errMessage;

  try {
    const mod = await loadHandler(domain);
    const fn = mod[action];
    if (typeof fn !== 'function') throw new Error(`handler ${domain}.${action} not found`);

    const result = await fn(input, { event, domain, action });

    if (typeof result === 'string') {
      const out = asContext(event, result);
      if (out) process.stdout.write(JSON.stringify(out));
    } else if (result && typeof result === 'object') {
      process.stdout.write(JSON.stringify(result));
    }
  } catch (err) {
    status = 'error';
    errMessage = String(err?.message || err);
    debug(`${domain}.${action} threw`, errMessage);
  }

  writeTelemetry({
    domain,
    action,
    event,
    ms: Date.now() - started,
    status,
    ...(errMessage ? { error: errMessage } : {}),
  });
}

main()
  .catch((err) => debug('runner fatal', String(err)))
  .finally(() => process.exit(0));
