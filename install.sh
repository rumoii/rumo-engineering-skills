#!/usr/bin/env sh
set -eu

REMOTE_URL="${RUMO_SKILLS_REMOTE:-https://github.com/rumoii/rumo-engineering-skills.git}"
REPO_PATH="${RUMO_SKILLS_REPO:-}"
PROFILES_REPO="${RUMO_SKILL_PROFILES_REPO:-}"
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
CLAUDE_HOME_DIR="${CLAUDE_HOME:-$HOME/.claude}"
AGENTS_HOME_DIR="${AGENTS_HOME:-$HOME/.agents}"
CLAUDE_HOME_EXPLICIT=0
AGENTS_HOME_EXPLICIT=0
[ -n "${CLAUDE_HOME:-}" ] && CLAUDE_HOME_EXPLICIT=1
[ -n "${AGENTS_HOME:-}" ] && AGENTS_HOME_EXPLICIT=1
RUN_PULL=1
DRY_RUN=0
REPLACE_FOREIGN_LINKS=0

usage() {
  printf '%s\n' \
    'Usage: ./install.sh [options]' \
    '  --repo <path>        Local skills repository.' \
    '  --profiles-repo <p>  Optional private project profiles repository.' \
    '  --codex-home <path>  Codex home directory.' \
    '  --claude-home <path> Claude Code home directory.' \
    '  --agents-home <path> Shared agent skills home directory.' \
    '  --remote <url>       Clone URL used when the repository is absent.' \
    '  --no-pull            Do not update an existing checkout.' \
    '  --dry-run            Print operations without changing links.' \
    '  --replace-foreign-links  Replace same-name links from another repository.'
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo) REPO_PATH="$2"; shift 2 ;;
    --profiles-repo) PROFILES_REPO="$2"; shift 2 ;;
    --codex-home) CODEX_HOME_DIR="$2"; shift 2 ;;
    --claude-home) CLAUDE_HOME_DIR="$2"; CLAUDE_HOME_EXPLICIT=1; shift 2 ;;
    --agents-home) AGENTS_HOME_DIR="$2"; AGENTS_HOME_EXPLICIT=1; shift 2 ;;
    --remote) REMOTE_URL="$2"; shift 2 ;;
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

command -v git >/dev/null 2>&1 || { echo 'Git is required.' >&2; exit 1; }
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

preflight_links() {
  skills_dir="$1"
  status=0
  for skill_dir in "$REPO_PATH"/skills/rumo-*; do
    [ -d "$skill_dir" ] || continue
    skill_name=$(basename "$skill_dir")
    link_path="$skills_dir/$skill_name"
    if [ -L "$link_path" ]; then
      target=$(resolve_link_target "$link_path")
      if [ "$target" != "$skill_dir" ] && [ "$REPLACE_FOREIGN_LINKS" -eq 0 ]; then
        echo "Conflict: $link_path points to $target (expected $skill_dir); use --replace-foreign-links to replace it." >&2
        status=1
      fi
    elif [ -e "$link_path" ]; then
      echo "Conflict: $link_path exists as a real file or directory." >&2
      status=1
    fi
  done
  return "$status"
}

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

sync_links() {
  skills_dir="$1"
  run mkdir -p "$skills_dir"
  for skill_dir in "$REPO_PATH"/skills/rumo-*; do
    [ -d "$skill_dir" ] || continue
    skill_name=$(basename "$skill_dir")
    link_path="$skills_dir/$skill_name"
    if [ -L "$link_path" ]; then run rm "$link_path"
    elif [ -e "$link_path" ]; then echo "Skip non-link: $link_path"; continue
    fi
    run ln -s "$skill_dir" "$link_path"
  done
  for link_path in "$skills_dir"/rumo-*; do
    [ -L "$link_path" ] || continue
    target=$(resolve_link_target "$link_path")
    case "$target" in
      "$REPO_PATH"/skills/*) [ -d "$target" ] || run rm "$link_path" ;;
    esac
  done
}

PREFLIGHT_STATUS=0
preflight_links "$CODEX_HOME_DIR/skills" || PREFLIGHT_STATUS=1
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
[ "$PREFLIGHT_STATUS" -eq 0 ] || { echo 'Skill link preflight failed; no links were changed.' >&2; exit 1; }

sync_links "$CODEX_HOME_DIR/skills"
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
