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
EXTRAS_REQUEST=""
REMOVE_EXTRAS_REQUEST=""
LIST_EXTRAS=0

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
    '  --replace-foreign-links  Replace same-name links from another repository.'
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo) REPO_PATH="$2"; shift 2 ;;
    --profiles-repo) PROFILES_REPO="$2"; PROFILES_REPO_EXPLICIT=1; shift 2 ;;
    --codex-home) CODEX_HOME_DIR="$2"; CODEX_HOME_EXPLICIT=1; shift 2 ;;
    --claude-home) CLAUDE_HOME_DIR="$2"; CLAUDE_HOME_EXPLICIT=1; shift 2 ;;
    --agents-home) AGENTS_HOME_DIR="$2"; AGENTS_HOME_EXPLICIT=1; shift 2 ;;
    --remote) REMOTE_URL="$2"; shift 2 ;;
    --extras) EXTRAS_REQUEST="$EXTRAS_REQUEST,$2"; shift 2 ;;
    --remove-extras) REMOVE_EXTRAS_REQUEST="$REMOVE_EXTRAS_REQUEST,$2"; shift 2 ;;
    --list-extras) LIST_EXTRAS=1; shift ;;
    --no-pull) RUN_PULL=0; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --replace-foreign-links) REPLACE_FOREIGN_LINKS=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; usage >&2; exit 1 ;;
  esac
done

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

check_extra_names() {
  set -f
  for name in $EXTRA_NAMES $REMOVE_EXTRA_NAMES; do
    case "$name" in
      rumo-*/*|rumo-*\\*) known=0 ;;
      rumo-*) if [ -d "$REPO_PATH/extras/$name" ]; then known=1; else known=0; fi ;;
      *) known=0 ;;
    esac
    if [ "$known" -eq 0 ]; then
      echo "Unknown optional skill: $name. Run with --list-extras to see available names; nothing was changed." >&2
      exit 1
    fi
  done
  set +f
}

EXTRA_NAMES=$(split_names "$EXTRAS_REQUEST")
REMOVE_EXTRA_NAMES=$(split_names "$REMOVE_EXTRAS_REQUEST")
set -f
for name in $EXTRA_NAMES; do
  if list_contains "$REMOVE_EXTRA_NAMES" "$name"; then
    echo "$name was passed to both --extras and --remove-extras; nothing was changed." >&2
    exit 1
  fi
done
set +f

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

command -v git >/dev/null 2>&1 || { echo 'Git is required.' >&2; exit 1; }
[ ! -d "$REPO_PATH/skills" ] || check_extra_names
if [ -d "$REPO_PATH/.git" ]; then
  [ "$RUN_PULL" -eq 0 ] || run git -C "$REPO_PATH" pull --ff-only
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
else echo 'Python 3 is required.' >&2; exit 1
fi
check_extra_names


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
      echo "Conflict: $link_path exists as a real file or directory." >&2
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
}

PREFLIGHT_STATUS=0
if [ "$CODEX_HOME_EXPLICIT" -eq 1 ] || command -v codex >/dev/null 2>&1 || [ -d "$CODEX_HOME_DIR" ]; then
  SYNC_CODEX=1
  preflight_links "$CODEX_HOME_DIR/skills" || PREFLIGHT_STATUS=1
else
  SYNC_CODEX=0
fi
if [ "$CLAUDE_HOME_EXPLICIT" -eq 1 ] || command -v claude >/dev/null 2>&1 || [ -d "$CLAUDE_HOME_DIR" ]; then
  SYNC_CLAUDE=1
  preflight_links "$CLAUDE_HOME_DIR/skills" || PREFLIGHT_STATUS=1
else
  SYNC_CLAUDE=0
fi
if [ "$AGENTS_HOME_EXPLICIT" -eq 1 ] || command -v grok >/dev/null 2>&1 || [ -d "$HOME/.grok" ]; then
  SYNC_AGENTS=1
  preflight_links "$AGENTS_HOME_DIR/skills" || PREFLIGHT_STATUS=1
else
  SYNC_AGENTS=0
fi
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
    else echo 'Python 3 is required to configure the profiles repository.' >&2; exit 1
    fi
  elif command -v python3 >/dev/null 2>&1; then python3 "$config_script" --profiles-repo "$PROFILES_REPO"
  elif command -v python >/dev/null 2>&1; then python "$config_script" --profiles-repo "$PROFILES_REPO"
  else echo 'Python 3 is required to configure the profiles repository.' >&2; exit 1
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

echo "Rumo skills installed from $REPO_PATH"
echo "Set RUMO_SKILLS_REPO=$REPO_PATH for later updates."
if [ -n "$PROFILES_REPO" ]; then echo "Project profiles: $PROFILES_REPO"
else echo 'Optionally set RUMO_SKILL_PROFILES_REPO to a private profiles checkout.'
fi
