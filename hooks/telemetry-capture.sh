#!/usr/bin/env bash
# PostToolUse hook — additive only. Appends one human-readable line per tool
# call to .claude/telemetry.log, consumed by monitors/monitors.json's
# telemetry-watcher (raw tail, no JSON-parsing contract). Respects
# AGENT_DEV_TELEMETRY=0 to opt out; documented in README/AGENTS.md for
# install-time transparency. lib.sh sourcing failure degrades to a no-op.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/lib.sh" 2>/dev/null || exit 0

input=$(cat)
tool=$(printf '%s' "$input" | jq -r '.tool_name // "unknown"' 2>/dev/null || echo unknown)

agent_dev_telemetry_append "PostToolUse" "$tool" "ok" || true
exit 0
