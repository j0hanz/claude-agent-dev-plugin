#!/usr/bin/env bash
# SessionStart hook nudges towards bundled skills.
# Applies cooldown and dynamically lists available skills.
set -Eeuo pipefail
shopt -s inherit_errexit 2>/dev/null || true

cat >/dev/null 2>&1 || true # Drain unused stdin.

# Load project-local settings.
AGENT_SDLC_SETTINGS_FILE="${CLAUDE_PROJECT_DIR:-.}/.claude/claude-agent-sdlc.local.md"
if [[ -z "${AGENT_SDLC_SKILL_NUDGE:-}" ]]; then
  if [[ -f "$AGENT_SDLC_SETTINGS_FILE" ]]; then
    FRONTMATTER=$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$AGENT_SDLC_SETTINGS_FILE" 2>/dev/null || true)
    if [[ -n "$FRONTMATTER" ]]; then
      NUDGE_VAL=$(printf '%s\n' "$FRONTMATTER" | grep '^skill_nudge:' | sed 's/skill_nudge: *//' 2>/dev/null || true)
      if [[ "$NUDGE_VAL" == "false" ]]; then
        export AGENT_SDLC_SKILL_NUDGE=0
      elif [[ "$NUDGE_VAL" == "true" ]]; then
        export AGENT_SDLC_SKILL_NUDGE=1
      fi
    fi
  fi
fi

agent_sdlc_json_escape() {
  # Escapes string for JSON embedding.
  node -e 'process.stdout.write(JSON.stringify(process.argv[1]).slice(1, -1))' "$1" 2>/dev/null
}

agent_sdlc_enum_skills() {
  # Lists available skill directory names.
  local root="${CLAUDE_PLUGIN_ROOT:-.}"
  local skill_files
  # Avoid errors if no skills exist.
  local found=0
  while IFS= read -r -d '' file; do
    found=1
    local d="${file%/SKILL.md}"
    printf '%s\n' "${d##*/}"
  done < <(find "$root/skills" -maxdepth 2 -name "SKILL.md" -print0 2>/dev/null | sort -z || true)
  if [ "$found" -eq 0 ]; then
    return 0
  fi
}

# Determine bootstrap mode.
if [ "${AGENT_SDLC_SKILL_NUDGE:-1}" = "0" ]; then
  BOOTSTRAP_MODE="off"
else
  # Default to 'full'.
  BOOTSTRAP_MODE="${AGENT_SDLC_BOOTSTRAP_MODE:-full}"
fi

# Mode: off.
if [ "$BOOTSTRAP_MODE" = "off" ]; then
  exit 0
fi

STATE_DIR="${CLAUDE_PROJECT_DIR:-.}/.claude"
STATE_FILE="$STATE_DIR/skill-nudge-state"
COOLDOWN_SECONDS=86400 # 24h cooldown.

# Mode: cooldown.
if [ "$BOOTSTRAP_MODE" = "cooldown" ]; then
  now=$(date +%s)
  if [ -f "$STATE_FILE" ]; then
    last=$(cat "$STATE_FILE" 2>/dev/null || printf '0\n')
    last=${last//[^0-9]/}
    [ -z "$last" ] && last=0
    if [ $((now - last)) -lt "$COOLDOWN_SECONDS" ]; then
      exit 0
    fi
  fi
  mkdir -p "$STATE_DIR" 2>/dev/null || true
  printf '%s' "$now" >"$STATE_FILE" 2>/dev/null || true

  available=$(agent_sdlc_enum_skills)
  [ -z "$available" ] && exit 0
  list=$(printf '%s\n' "$available" | paste -sd ',' - | sed 's/,/, /g')
  message="[agent-sdlc:skill-nudge] This plugin includes skills for structured workflows: ${list}. They auto-trigger on matching tasks, or invoke directly with /skill-name."
  escaped=$(agent_sdlc_json_escape "$message")
  printf '%s\n' "{\"hookSpecificOutput\": {\"hookEventName\": \"SessionStart\", \"additionalContext\": \"${escaped}\"}}"
  exit 0
fi

# Mode: full.
if [ "$BOOTSTRAP_MODE" = "full" ]; then
  available=$(agent_sdlc_enum_skills)
  [ -z "$available" ] && exit 0
  list=$(printf '%s\n' "$available" | paste -sd ',' -)

  # Gate names.
  gates="Gate 0 Repository Onboarding, Gate 1 Task Definition, Gate 2 Scope & System, Gate 3 Execution Strategy, Gate 4 Quality & Delivery"

  message="<EXTREMELY_IMPORTANT>[agent-sdlc:skill-nudge] Before responding, check using-agent-sdlc-skills for routing: ${gates}. Bundled skills available this session: ${list}.</EXTREMELY_IMPORTANT>"
  escaped=$(agent_sdlc_json_escape "$message")
  printf '%s\n' "{\"hookSpecificOutput\": {\"hookEventName\": \"SessionStart\", \"additionalContext\": \"${escaped}\"}}"
  exit 0
fi

# Fallback for unknown modes.
exit 0
