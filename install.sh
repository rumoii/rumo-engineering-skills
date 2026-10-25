#!/usr/bin/env sh
set -eu

REMOTE_URL="${RUMO_SKILLS_REMOTE:-https://github.com/rumoii/rumo-engineering-skills.git}"
REPO_PATH="${RUMO_SKILLS_REPO:-}"
PROFILES_REPO="${RUMO_SKILL_PROFILES_REPO:-}"
PROFILES_REPO_EXPLICIT=0
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
CLAUDE_HOME_DIR="${CLAUDE_HOME:-$HOME/.claude}"
AGENTS_HOME_DIR="${AGENTS_HOME:-$HOME/.agents}"
CODEX_HOME_EXPLICIT=0
CLAUDE_HOME_EXPLICIT=0
AGENTS_HOME_EXPLICIT=0
[ -n "${CODEX_HOME:-}" ] && CODEX_HOME_EXPLICIT=1
[ -n "${CLAUDE_HOME:-}" ] && CLAUDE_HOME_EXPLICIT=1
[ -n "${AGENTS_HOME:-}" ] && AGENTS_HOME_EXPLICIT=1
RUN_PULL=1
DRY_RUN=0
REPLACE_FOREIGN_LINKS=0
BASELINE_MODE=refresh
BASELINE_FLAGS=0
BASELINE_MISSING=""
EXTRAS_REQUEST=""
REMOVE_EXTRAS_REQUEST=""
LIST_EXTRAS=0
UNINSTALL=0
LINK_SUMMARY=""
PULL_COMPLETED=0

warn_post_pull_failure() {
  status=$?
  if [ "$status" -ne 0 ] && [ "$PULL_COMPLETED" -eq 1 ]; then
    echo 'Repository pull completed, but installation did not finish; existing skill links may already serve updated content.' >&2
  fi
  exit "$status"
}
trap warn_post_pull_failure EXIT

usage() {
  printf '%s\n' \
    'Usage: ./install.sh [options]' \
    '  --repo <path>        Local skills repository.' \
    '  --profiles-repo <p>  Optional private project profiles repository.' \
    '  --codex-home <path>  Codex home directory.' \
    '  --claude-home <path> Claude Code home directory.' \
    '  --agents-home <path> Shared agent skills home directory.' \
    '  --remote <url>       Clone URL used when the repository is absent.' \
    '  --extras <a,b>       Also install these optional skills.' \
    '  --remove-extras <a,b> Remove these optional skills.' \
    '  --list-extras        List optional skills without changing anything.' \
    '  --no-pull            Do not update an existing checkout.' \
    '  --dry-run            Print operations without changing links.' \
    '  --replace-foreign-links  Replace same-name links from another repository.' \
    '  --baseline           Add the always-on baseline block to CLAUDE.md and AGENTS.md' \
    '                       of each detected Claude Code and Codex home.' \
    '  --remove-baseline    Remove that block.' \
    '  --uninstall          Remove the rumo-* links into this repository and the baseline' \
    '                       block from each detected client; keep the repository and profiles.'
}

need_value() {
  [ "$#" -ge 2 ] || { printf 'Missing value for %s; nothing was changed.\n' "$1" >&2; usage >&2; exit 1; }
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo) need_value "$@"; REPO_PATH="$2"; shift 2 ;;
    --profiles-repo) need_value "$@"; PROFILES_REPO="$2"; PROFILES_REPO_EXPLICIT=1; shift 2 ;;
    --codex-home) need_value "$@"; CODEX_HOME_DIR="$2"; CODEX_HOME_EXPLICIT=1; shift 2 ;;
    --claude-home) need_value "$@"; CLAUDE_HOME_DIR="$2"; CLAUDE_HOME_EXPLICIT=1; shift 2 ;;
    --agents-home) need_value "$@"; AGENTS_HOME_DIR="$2"; AGENTS_HOME_EXPLICIT=1; shift 2 ;;
    --remote) need_value "$@"; REMOTE_URL="$2"; shift 2 ;;
    --extras) need_value "$@"; EXTRAS_REQUEST="$EXTRAS_REQUEST,$2"; shift 2 ;;
    --remove-extras) need_value "$@"; REMOVE_EXTRAS_REQUEST="$REMOVE_EXTRAS_REQUEST,$2"; shift 2 ;;
    --list-extras) LIST_EXTRAS=1; shift ;;
    --no-pull) RUN_PULL=0; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --replace-foreign-links) REPLACE_FOREIGN_LINKS=1; shift ;;
    --baseline) BASELINE_MODE=install; BASELINE_FLAGS=$((BASELINE_FLAGS + 1)); shift ;;
    --remove-baseline) BASELINE_MODE=remove; BASELINE_FLAGS=$((BASELINE_FLAGS + 1)); shift ;;
    --uninstall) UNINSTALL=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; usage >&2; exit 1 ;;
  esac
done

sync_baseline() {
  target=$1
  [ -f "$BASELINE_SCRIPT" ] || return 0
  set -- "$BASELINE_SCRIPT" --target "$target" "--$BASELINE_MODE"
  [ "$DRY_RUN" -eq 0 ] || set -- "$@" --dry-run
  if command -v python3 >/dev/null 2>&1; then action=$(python3 "$@") || action=failed
  else action=$(python "$@") || action=failed
  fi
  case "$action" in
    added|updated|removed)
      if [ "$DRY_RUN" -eq 1 ]; then echo "Would update baseline ($action): $target"
      else echo "Baseline ($action): $target"
      fi ;;
    absent) [ "$BASELINE_MODE" != refresh ] || BASELINE_MISSING="${BASELINE_MISSING:+$BASELINE_MISSING, }$target" ;;
    unchanged) ;;
    *) echo "Baseline block update failed for $target; skill links were already synced." >&2; exit 1 ;;
  esac
}

run() {
  if [ "$DRY_RUN" -eq 1 ]; then
    printf '+'
    for arg in "$@"; do printf ' %s' "$arg"; done
    printf '\n'
  else
    "$@"
  fi
}

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
[ -n "$REPO_PATH" ] || { [ -d "$SCRIPT_DIR/skills" ] && REPO_PATH="$SCRIPT_DIR" || REPO_PATH="$HOME/.rumo-engineering-skills"; }

split_names() {
  printf '%s\n' "$1" | tr ',' '\n' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e '/^$/d'
}

list_contains() {
  [ -n "$1" ] && printf '%s\n' "$1" | grep -Fxq -- "$2"
}

NEWLINE='
'

# Names are newline-separated; iterate line by line so a name with inner
# whitespace stays one (invalid) name instead of splitting into valid ones.
check_extra_names() {
  set -f
  saved_ifs=$IFS
  IFS=$NEWLINE
  for name in $EXTRA_NAMES $REMOVE_EXTRA_NAMES; do
    case "$name" in
      *[[:space:]]*|rumo-*/*|rumo-*\\*) known=0 ;;
      rumo-*) if [ -d "$REPO_PATH/extras/$name" ]; then known=1; else known=0; fi ;;
      *) known=0 ;;
    esac
    if [ "$known" -eq 0 ]; then
      echo "Unknown optional skill: $name. Run with --list-extras to see available names; nothing was changed." >&2
      exit 1
    fi
  done
  IFS=$saved_ifs
  set +f
}

EXTRA_NAMES=$(split_names "$EXTRAS_REQUEST")
REMOVE_EXTRA_NAMES=$(split_names "$REMOVE_EXTRAS_REQUEST")
set -f
saved_ifs=$IFS
IFS=$NEWLINE
for name in $EXTRA_NAMES; do
  if list_contains "$REMOVE_EXTRA_NAMES" "$name"; then
    echo "$name was passed to both --extras and --remove-extras; nothing was changed." >&2
    exit 1
  fi
done
IFS=$saved_ifs
set +f
if [ "$BASELINE_FLAGS" -gt 1 ]; then
  echo '--baseline and --remove-baseline cannot be combined; nothing was changed.' >&2
  exit 1
fi
if [ "$UNINSTALL" -eq 1 ] && { [ -n "$EXTRA_NAMES$REMOVE_EXTRA_NAMES" ] || [ "$BASELINE_FLAGS" -gt 0 ] || [ "$PROFILES_REPO_EXPLICIT" -eq 1 ] || [ "$REPLACE_FOREIGN_LINKS" -eq 1 ] || [ "$LIST_EXTRAS" -eq 1 ]; }; then
  echo '--uninstall cannot be combined with options that install or configure skills; nothing was changed.' >&2
  exit 1
fi
PYTHON_INSTALL_HINT='Install Python 3 (macOS or Linux: your package manager; Windows: winget install --id Python.Python.3.12), then rerun.'

if [ "$LIST_EXTRAS" -eq 1 ]; then
  [ -d "$REPO_PATH/skills" ] || { echo "Skills repository not found: $REPO_PATH. Install once before listing optional skills." >&2; exit 1; }
  found=0
  for extra_dir in "$REPO_PATH"/extras/rumo-*; do
    [ -d "$extra_dir" ] || continue
    if [ "$found" -eq 0 ]; then echo 'Optional skills (install with --extras <name>[,<name>]):'; found=1; fi
    description=$(sed -n 's/^description:[[:space:]]*//p' "$extra_dir/SKILL.md" | head -n 1 | sed -e 's/^"//' -e 's/"$//' -e 's/\. .*/./')
    printf '  %s  %s\n' "$(basename "$extra_dir")" "$description"
  done
  [ "$found" -eq 1 ] || echo "No optional skills are available in $REPO_PATH."
  exit 0
fi

resolve_link_target() {
  link_path="$1"
  target=$(readlink "$link_path")
  case "$target" in
    /*) candidate="$target" ;;
    *) candidate="$(dirname "$link_path")/$target" ;;
  esac
  if [ -d "$candidate" ]; then
    CDPATH= cd -- "$candidate" && pwd -P
  else
    printf '%s\n' "$candidate"
  fi
}

is_owned_target() {
  case "$1" in
    "$REPO_PATH"/skills/*|"$REPO_PATH"/extras/*) return 0 ;;
  esac
  return 1
}

SYNC_CODEX=0
SYNC_CLAUDE=0
SYNC_AGENTS=0
if [ "$CODEX_HOME_EXPLICIT" -eq 1 ] || command -v codex >/dev/null 2>&1 || [ -d "$CODEX_HOME_DIR" ]; then SYNC_CODEX=1; fi
if [ "$CLAUDE_HOME_EXPLICIT" -eq 1 ] || command -v claude >/dev/null 2>&1 || [ -d "$CLAUDE_HOME_DIR" ]; then SYNC_CLAUDE=1; fi
if [ "$AGENTS_HOME_EXPLICIT" -eq 1 ] || [ -d "$AGENTS_HOME_DIR" ] || command -v grok >/dev/null 2>&1 || [ -d "$HOME/.grok" ]; then SYNC_AGENTS=1; fi

remove_owned_links() {
  skills_dir="$1"
  removed=0
  for link_path in "$skills_dir"/rumo-*; do
    [ -L "$link_path" ] || continue
    if is_owned_target "$(resolve_link_target "$link_path")"; then
      run rm "$link_path"
      removed=$((removed + 1))
    fi
  done
  if [ "$DRY_RUN" -eq 1 ]; then echo "$removed skill links would be removed from $skills_dir"
  else echo "$removed skill links removed from $skills_dir"
  fi
}

# Uninstall needs neither Git nor a valid checkout, so it runs before both checks.
if [ "$UNINSTALL" -eq 1 ]; then
  if [ "$SYNC_CODEX" -eq 0 ] && [ "$SYNC_CLAUDE" -eq 0 ] && [ "$SYNC_AGENTS" -eq 0 ]; then
    echo 'No supported agent client was detected; nothing to uninstall.'
    exit 0
  fi
  [ ! -d "$REPO_PATH" ] || REPO_PATH=$(CDPATH= cd -- "$REPO_PATH" && pwd -P)
  BASELINE_SCRIPT="$REPO_PATH/skills/rumo-coding-guidelines/scripts/baseline_block.py"
  [ "$SYNC_CODEX" -eq 0 ] || remove_owned_links "$CODEX_HOME_DIR/skills"
  [ "$SYNC_CLAUDE" -eq 0 ] || remove_owned_links "$CLAUDE_HOME_DIR/skills"
  [ "$SYNC_AGENTS" -eq 0 ] || remove_owned_links "$AGENTS_HOME_DIR/skills"
  BASELINE_MODE=remove
  if command -v python3 >/dev/null 2>&1 || command -v python >/dev/null 2>&1; then
    [ "$SYNC_CODEX" -eq 0 ] || sync_baseline "$CODEX_HOME_DIR/AGENTS.md"
    [ "$SYNC_CLAUDE" -eq 0 ] || sync_baseline "$CLAUDE_HOME_DIR/CLAUDE.md"
  elif [ "$SYNC_CODEX" -eq 1 ] || [ "$SYNC_CLAUDE" -eq 1 ]; then
    echo 'Python 3 was not found; remove any rumo-engineering-skills:baseline block from AGENTS.md or CLAUDE.md by hand.'
  fi
  if [ "$DRY_RUN" -eq 1 ]; then
    echo 'Dry run finished; nothing was changed.'
    exit 0
  fi
  echo 'Rumo skills uninstalled.'
  echo "Kept: the repository at $REPO_PATH, ~/.rumo-engineering-skills/config.json, and any project profiles. Delete them by hand if you no longer need them."
  exit 0
fi

command -v git >/dev/null 2>&1 || {
  echo 'Git is required. Install it (macOS: xcode-select --install; Linux: your package manager; Windows: winget install --id Git.Git), then rerun. Nothing was changed.' >&2
  exit 1
}
[ ! -d "$REPO_PATH/skills" ] || check_extra_names
if [ -e "$REPO_PATH/.git" ]; then
  if [ "$RUN_PULL" -ne 0 ]; then
    run git -C "$REPO_PATH" pull --ff-only
    [ "$DRY_RUN" -eq 1 ] || PULL_COMPLETED=1
  fi
elif [ ! -d "$REPO_PATH/skills" ]; then
  run mkdir -p "$(dirname "$REPO_PATH")"
  run git clone "$REMOTE_URL" "$REPO_PATH"
  [ "$DRY_RUN" -eq 0 ] || exit 0
fi
REPO_PATH=$(CDPATH= cd -- "$REPO_PATH" && pwd -P)

validator="$REPO_PATH/scripts/verify_skills.py"
[ -f "$validator" ] || { echo "Validator not found: $validator" >&2; exit 1; }
if command -v python3 >/dev/null 2>&1; then python3 "$validator" --repo-root "$REPO_PATH"
elif command -v python >/dev/null 2>&1; then python "$validator" --repo-root "$REPO_PATH"
else echo "Python 3 is required to validate skills before installation. $PYTHON_INSTALL_HINT No skill links were changed." >&2; exit 1
fi
check_extra_names
BASELINE_SCRIPT="$REPO_PATH/skills/rumo-coding-guidelines/scripts/baseline_block.py"
if [ "$BASELINE_MODE" != refresh ] && [ ! -f "$BASELINE_SCRIPT" ]; then
  echo "Baseline helper not found: $BASELINE_SCRIPT; nothing was changed." >&2
  exit 1
fi

# Print default skills, requested extras, and extras this checkout already installed here.
desired_sources() {
  skills_dir="$1"
  for skill_dir in "$REPO_PATH"/skills/rumo-*; do
    if [ -d "$skill_dir" ]; then printf '%s\n' "$skill_dir"; fi
  done
  selected="$EXTRA_NAMES"
  for link_path in "$skills_dir"/rumo-*; do
    [ -L "$link_path" ] || continue
    name=$(basename "$link_path")
    target=$(resolve_link_target "$link_path")
    case "$target" in
      "$REPO_PATH"/extras/*)
        if [ -d "$REPO_PATH/extras/$name" ]; then
          selected="$selected
$name"
        fi
        ;;
    esac
  done
  printf '%s\n' "$selected" | sed '/^$/d' | sort -u | while IFS= read -r name; do
    if ! list_contains "$REMOVE_EXTRA_NAMES" "$name"; then
      printf '%s\n' "$REPO_PATH/extras/$name"
    fi
  done
}

removal_notice() {
  name="$1"
  if list_contains "$REMOVE_EXTRA_NAMES" "$name"; then
    echo "Removed optional skill $name."
    return 0
  fi
  if [ -d "$REPO_PATH/extras/$name" ]; then
    echo "$name is optional now; reinstall it with --extras $name."
    return 0
  fi
  echo "Removed stale link $name."
}

preflight_links() {
  skills_dir="$1"
  status=0
  desired=$(desired_sources "$skills_dir")
  old_ifs=$IFS
  IFS='
'
  set -f
  for source_dir in $desired; do
    link_path="$skills_dir/$(basename "$source_dir")"
    if [ -L "$link_path" ]; then
      target=$(resolve_link_target "$link_path")
      if [ "$target" != "$source_dir" ] && ! is_owned_target "$target" && [ "$REPLACE_FOREIGN_LINKS" -eq 0 ]; then
        echo "Conflict: $link_path points to $target (expected $source_dir); use --replace-foreign-links to replace it." >&2
        status=1
      fi
    elif [ -e "$link_path" ]; then
      echo "Conflict: $link_path exists as a real file or directory; move or rename it, then rerun." >&2
      status=1
    fi
  done
  set +f
  IFS=$old_ifs
  return "$status"
}

sync_links() {
  skills_dir="$1"
  desired=$(desired_sources "$skills_dir")
  desired_names=$(printf '%s\n' "$desired" | sed 's|.*/||')
  run mkdir -p "$skills_dir"
  old_ifs=$IFS
  IFS='
'
  set -f
  for source_dir in $desired; do
    link_path="$skills_dir/$(basename "$source_dir")"
    if [ -L "$link_path" ]; then run rm "$link_path"
    elif [ -e "$link_path" ]; then echo "Skip non-link: $link_path"; continue
    fi
    run ln -s "$source_dir" "$link_path"
  done
  set +f
  IFS=$old_ifs
  for link_path in "$skills_dir"/rumo-*; do
    [ -L "$link_path" ] || continue
    name=$(basename "$link_path")
    if list_contains "$desired_names" "$name"; then continue; fi
    target=$(resolve_link_target "$link_path")
    if is_owned_target "$target"; then
      removal_notice "$name"
      run rm "$link_path"
    fi
  done
  linked=$(printf '%s\n' "$desired" | sed '/^$/d' | wc -l | tr -d ' ')
  LINK_SUMMARY="${LINK_SUMMARY}$linked skills linked in $skills_dir$NEWLINE"
}

PREFLIGHT_STATUS=0
[ "$SYNC_CODEX" -eq 0 ] || preflight_links "$CODEX_HOME_DIR/skills" || PREFLIGHT_STATUS=1
[ "$SYNC_CLAUDE" -eq 0 ] || preflight_links "$CLAUDE_HOME_DIR/skills" || PREFLIGHT_STATUS=1
[ "$SYNC_AGENTS" -eq 0 ] || preflight_links "$AGENTS_HOME_DIR/skills" || PREFLIGHT_STATUS=1
if [ "$SYNC_CODEX" -eq 0 ] && [ "$SYNC_CLAUDE" -eq 0 ] && [ "$SYNC_AGENTS" -eq 0 ]; then
  echo 'No supported agent client was detected; no links were changed.' >&2
  echo 'Pass --codex-home, --claude-home, or --agents-home to choose a target explicitly.' >&2
  exit 1
fi
[ "$PREFLIGHT_STATUS" -eq 0 ] || { echo 'Skill link preflight failed; no links were changed.' >&2; exit 1; }

if [ "$PROFILES_REPO_EXPLICIT" -eq 1 ]; then
  config_script="$REPO_PATH/skills/rumo-project-profile/scripts/profile_config.py"
  if [ "$DRY_RUN" -eq 1 ]; then
    if command -v python3 >/dev/null 2>&1; then python3 "$config_script" --profiles-repo "$PROFILES_REPO" --dry-run
    elif command -v python >/dev/null 2>&1; then python "$config_script" --profiles-repo "$PROFILES_REPO" --dry-run
    else echo "Python 3 is required to configure the profiles repository. $PYTHON_INSTALL_HINT No skill links were changed." >&2; exit 1
    fi
  elif command -v python3 >/dev/null 2>&1; then python3 "$config_script" --profiles-repo "$PROFILES_REPO"
  elif command -v python >/dev/null 2>&1; then python "$config_script" --profiles-repo "$PROFILES_REPO"
  else echo "Python 3 is required to configure the profiles repository. $PYTHON_INSTALL_HINT No skill links were changed." >&2; exit 1
  fi
fi

if [ "$SYNC_CODEX" -eq 1 ]; then sync_links "$CODEX_HOME_DIR/skills"
else echo 'Codex was not detected; skipping.'
fi
if [ "$SYNC_CLAUDE" -eq 1 ]; then sync_links "$CLAUDE_HOME_DIR/skills"
else echo 'Claude Code was not detected; skipping.'
fi
if [ "$SYNC_AGENTS" -eq 1 ]; then sync_links "$AGENTS_HOME_DIR/skills"
else echo 'A shared agent client was not detected; skipping.'
fi
[ "$SYNC_CODEX" -eq 0 ] || sync_baseline "$CODEX_HOME_DIR/AGENTS.md"
[ "$SYNC_CLAUDE" -eq 0 ] || sync_baseline "$CLAUDE_HOME_DIR/CLAUDE.md"

if [ "$DRY_RUN" -eq 1 ]; then
  echo 'Dry run finished; nothing was changed.'
  exit 0
fi
echo "Rumo skills installed from $REPO_PATH"
printf '%s' "$LINK_SUMMARY"
if [ "$REPO_PATH" != "$SCRIPT_DIR" ]; then
  echo "Recommended: set RUMO_SKILLS_REPO=$REPO_PATH so later runs from another copy of this script use the same checkout."
fi
echo 'Next: start a new agent session, then run /rumo-setup (Claude Code) or $rumo-setup (Codex) to choose agents, models, and reasoning effort.'
if [ -n "$PROFILES_REPO" ]; then echo "Project profiles: $PROFILES_REPO"
else echo 'Optionally set RUMO_SKILL_PROFILES_REPO to a private profiles checkout.'
fi
if [ -n "$BASELINE_MISSING" ]; then
  echo "Optional: rerun with --baseline to keep the core rules always on in $BASELINE_MISSING; see README."
fi
if [ "$BASELINE_MODE" = install ] && [ "$SYNC_AGENTS" -eq 1 ]; then
  echo 'Clients reading only the shared agents directory have no user-level instruction file here; paste skills/rumo-coding-guidelines/references/agents-snippet.md into their instructions by hand.'
fi
