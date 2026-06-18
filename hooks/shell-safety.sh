#!/usr/bin/env bash
# PreToolUse(Bash) guard — blocks a short, explicit list of catastrophic command
# patterns. Self-contained (no lib.sh dependency): a bug in the shared helper
# library used by the additive handlers must never silently disable this guard.
#
# Best-effort only — not a general security control. Matches are structural
# (first command word + flag set on each ;/&&/||/| segment), not raw substring
# search, so a denylist word appearing inside a quoted string or commit message
# does not trigger a block. Narrow by design: favors under-blocking over
# over-blocking, since a false-positive block breaks a downstream user's
# unrelated workflow in a repo this plugin's author doesn't control.
set -euo pipefail

OVERRIDE_VAR="AGENT_DEV_SKIP_SHELL_SAFETY"
if [ "${!OVERRIDE_VAR:-0}" = "1" ]; then
  exit 0
fi

input=$(cat)
command=$(printf '%s' "$input" | jq -r '.tool_input.command // empty' 2>/dev/null || true)

if [ -z "$command" ]; then
  exit 0
fi

deny() {
  local reason="$1"
  printf '%s\n' "{\"hookSpecificOutput\": {\"permissionDecision\": \"deny\"}, \"systemMessage\": \"[agent-dev:shell-safety] Blocked: ${reason}. Set ${OVERRIDE_VAR}=1 to override.\"}" >&2
  exit 2
}

has_char() {
  # has_char <flags> <char> — true if <char> appears anywhere in <flags>
  case "$1" in
  *"$2"*) return 0 ;;
  *) return 1 ;;
  esac
}

# Split on ; && || | into segments — best-effort, not a full shell parser.
IFS=$'\n' read -r -d '' -a segments < <(printf '%s\0' "$command" | tr ';|' '\n' | sed -E 's/&&|\|\|/\n/g') || true

for segment in "${segments[@]}"; do
  # trim leading/trailing whitespace
  trimmed="$(printf '%s' "$segment" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')"
  [ -z "$trimmed" ] && continue

  # rm -rf / rm -fr against a root-like target: /, /*, ~, $HOME
  if [[ "$trimmed" =~ ^rm[[:space:]]+(-[A-Za-z]*) ]]; then
    flags="${BASH_REMATCH[1]}"
    if has_char "$flags" r && has_char "$flags" f; then
      if [[ "$trimmed" =~ (^|[[:space:]])(/|/\*|~|\$HOME)([[:space:]]|$) ]]; then
        deny "recursive force-delete of a root-level path ('$trimmed')"
      fi
    fi
  fi

  # git push --force / -f explicitly targeting main or master
  if [[ "$trimmed" =~ ^git[[:space:]]+push[[:space:]] ]]; then
    if [[ "$trimmed" =~ (^|[[:space:]])(--force|-f)([[:space:]]|$) ]] \
      && [[ "$trimmed" =~ (^|[[:space:]/:])(main|master)([[:space:]]|$) ]]; then
      deny "force-push targeting main/master ('$trimmed')"
    fi
  fi

  # git clean with -f, -d, and -x all present (repo-wide untracked+ignored wipe)
  if [[ "$trimmed" =~ ^git[[:space:]]+clean[[:space:]]+(-[A-Za-z]*) ]]; then
    flags="${BASH_REMATCH[1]}"
    if has_char "$flags" f && has_char "$flags" d && has_char "$flags" x; then
      deny "git clean -fdx wipes untracked and ignored files repo-wide ('$trimmed')"
    fi
  fi
done

exit 0
