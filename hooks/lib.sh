#!/usr/bin/env bash
# Shared helpers for the additive hooks only (skill-nudge).
# shell-safety.sh intentionally does NOT source this file — a bug here must
# only ever degrade an additive hook to a no-op, never silently disable the
# one blocking guard.

# Load project-local settings (frontmatter only if env var not already set)
AGENT_SDLC_SETTINGS_FILE="${CLAUDE_PROJECT_DIR:-.}/.claude/claude-agent-sdlc.local.md"
if [[ -z "${AGENT_SDLC_SKILL_NUDGE:-}" ]]; then
  if [[ -f "$AGENT_SDLC_SETTINGS_FILE" ]]; then
    FRONTMATTER=$(sed -n '/^---$/,/^---$/{ /^---$/d; p; }' "$AGENT_SDLC_SETTINGS_FILE" 2>/dev/null || true)
    if [[ -n "$FRONTMATTER" ]]; then
      NUDGE_VAL=$(echo "$FRONTMATTER" | grep '^skill_nudge:' | sed 's/skill_nudge: *//' 2>/dev/null || true)
      if [[ "$NUDGE_VAL" == "false" ]]; then
        export AGENT_SDLC_SKILL_NUDGE=0
      elif [[ "$NUDGE_VAL" == "true" ]]; then
        export AGENT_SDLC_SKILL_NUDGE=1
      fi
    fi
  fi
fi


agent_sdlc_json_escape() {
  # Escapes $1 for embedding as a JSON string value (no surrounding quotes).
  # Node is a guaranteed prerequisite for this plugin environment (same fallback as shell-safety.sh)
  node -e 'process.stdout.write(JSON.stringify(process.argv[1]).slice(1, -1))' "$1" 2>/dev/null
}

agent_sdlc_skill_exists() {
  # agent_sdlc_skill_exists <skill-name> — checks the plugin's own bundled
  # skills (shipped at $CLAUDE_PLUGIN_ROOT/skills/), not the consuming repo's.
  local name="$1"
  local dir="${CLAUDE_PLUGIN_ROOT:-.}/skills/$name"
  [ -f "$dir/SKILL.md" ]
}

agent_sdlc_enum_skills() {
  # agent_sdlc_enum_skills — lists all skill directory names by globbing
  # $CLAUDE_PLUGIN_ROOT/skills/*/SKILL.md, sorted, one per line.
  # Returns empty if no skills found or glob fails.
  local root="${CLAUDE_PLUGIN_ROOT:-.}"
  local skill_files
  # ponytail: glob may produce zero matches or no skills/ dir at all
  skill_files=$(find "$root/skills" -maxdepth 2 -name "SKILL.md" 2>/dev/null | sort || true)
  if [ -z "$skill_files" ]; then
    return 0
  fi
  while IFS= read -r file; do
    local d="${file%/SKILL.md}"
    printf '%s\n' "${d##*/}"
  done <<< "$skill_files"
}
