#!/usr/bin/env bash
# Claude Code config installer.
#
# Usage:
#   ./install.sh              # interactive, asks before overwriting
#   ./install.sh --force      # overwrite without asking
#   ./install.sh --dry-run    # print actions but don't write
#
# What it does:
#   1. Replaces __HOME__ placeholder in settings.json with your $HOME
#   2. Copies claude/* into ~/.claude/
#   3. Copies scripts/* into ~/scripts/
#   4. Optionally seeds an Obsidian vault at ~/notes/ from notes-template/
#   5. Optionally copies ~/CLAUDE.md (home-dir guide)
#
# It will NOT touch:
#   - your ~/.claude/projects/ (per-project memory)
#   - your ~/.claude/sessions/ (session history)
#   - any ~/.claude/settings.local.json that already exists

set -euo pipefail

DRY=0
FORCE=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    --force)   FORCE=1 ;;
    *) echo "unknown flag: $arg"; exit 1 ;;
  esac
done

REPO="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
SCRIPTS_DIR="$HOME/scripts"
NOTES_DIR="$HOME/notes"

say() { printf "\033[1;36m==>\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m!!\033[0m %s\n" "$*"; }
do_cmd() {
  if [ "$DRY" = 1 ]; then
    printf "[dry-run] %s\n" "$*"
  else
    eval "$*"
  fi
}

confirm() {
  [ "$FORCE" = 1 ] && return 0
  printf "%s [y/N] " "$1"
  read -r ans
  [ "$ans" = "y" ] || [ "$ans" = "Y" ]
}

backup_if_exists() {
  local target="$1"
  if [ -e "$target" ] && [ ! -L "$target" ]; then
    local backup="${target}.backup.$(date +%s)"
    do_cmd "mv \"$target\" \"$backup\""
    say "backed up existing $target → $backup"
  fi
}

say "Installing Claude Code config from $REPO"

# ---- 1. settings.json with __HOME__ substituted ----
say "Preparing claude/settings.json (substituting __HOME__ → $HOME)"
TMP_SETTINGS=$(mktemp)
sed "s|__HOME__|$HOME|g" "$REPO/claude/settings.json" > "$TMP_SETTINGS"

# ---- 2. ~/.claude/ ----
mkdir -p "$CLAUDE_DIR"
for sub in agents commands skills hooks rules docs mcp output-styles setup; do
  if [ -d "$CLAUDE_DIR/$sub" ] && [ "$FORCE" = 0 ]; then
    if ! confirm "Overwrite $CLAUDE_DIR/$sub ?"; then
      warn "skipping $sub"
      continue
    fi
  fi
  do_cmd "rm -rf \"$CLAUDE_DIR/$sub\""
  do_cmd "cp -R \"$REPO/claude/$sub\" \"$CLAUDE_DIR/$sub\""
  say "installed $CLAUDE_DIR/$sub"
done

# CLAUDE.md
if [ -f "$CLAUDE_DIR/CLAUDE.md" ] && [ "$FORCE" = 0 ]; then
  if confirm "Overwrite $CLAUDE_DIR/CLAUDE.md ?"; then
    backup_if_exists "$CLAUDE_DIR/CLAUDE.md"
    do_cmd "cp \"$REPO/claude/CLAUDE.md\" \"$CLAUDE_DIR/CLAUDE.md\""
  fi
else
  do_cmd "cp \"$REPO/claude/CLAUDE.md\" \"$CLAUDE_DIR/CLAUDE.md\""
fi

# settings.json — always backup if exists
backup_if_exists "$CLAUDE_DIR/settings.json"
do_cmd "cp \"$TMP_SETTINGS\" \"$CLAUDE_DIR/settings.json\""
say "installed $CLAUDE_DIR/settings.json"
rm -f "$TMP_SETTINGS"

# settings.local.json — only if missing
if [ ! -f "$CLAUDE_DIR/settings.local.json" ]; then
  do_cmd "cp \"$REPO/claude/settings.local.json\" \"$CLAUDE_DIR/settings.local.json\""
  say "installed $CLAUDE_DIR/settings.local.json (empty)"
else
  say "kept existing $CLAUDE_DIR/settings.local.json"
fi

# ---- 3. ~/scripts/ ----
mkdir -p "$SCRIPTS_DIR/hooks"
for f in "$REPO"/scripts/*; do
  [ -d "$f" ] && continue
  name="$(basename "$f")"
  target="$SCRIPTS_DIR/$name"
  if [ -e "$target" ] && [ "$FORCE" = 0 ]; then
    if ! confirm "Overwrite $target ?"; then continue; fi
  fi
  do_cmd "cp \"$f\" \"$target\""
  do_cmd "chmod +x \"$target\""
done
for f in "$REPO"/scripts/hooks/*; do
  name="$(basename "$f")"
  target="$SCRIPTS_DIR/hooks/$name"
  if [ -e "$target" ] && [ "$FORCE" = 0 ]; then
    if ! confirm "Overwrite $target ?"; then continue; fi
  fi
  do_cmd "cp \"$f\" \"$target\""
  do_cmd "chmod +x \"$target\""
done
say "installed $SCRIPTS_DIR (root + hooks/)"

# ---- 4. Obsidian vault seed (optional) ----
if [ ! -d "$NOTES_DIR" ]; then
  if confirm "Seed an empty Obsidian vault at $NOTES_DIR ?"; then
    do_cmd "mkdir -p \"$NOTES_DIR\""
    do_cmd "cp \"$REPO/notes-template/CLAUDE.md\" \"$NOTES_DIR/CLAUDE.md\""
    do_cmd "cp \"$REPO/notes-template/_atlas.md\" \"$NOTES_DIR/_atlas.md\""
    do_cmd "cp \"$REPO/notes-template/.gitignore\" \"$NOTES_DIR/.gitignore\""
    do_cmd "mkdir -p \"$NOTES_DIR/templates\" \"$NOTES_DIR/daily\" \"$NOTES_DIR/projects\" \"$NOTES_DIR/learning\" \"$NOTES_DIR/reference\" \"$NOTES_DIR/personal\" \"$NOTES_DIR/deadlines\" \"$NOTES_DIR/ideas\""
    do_cmd "cp \"$REPO/notes-template/templates/\"*.md \"$NOTES_DIR/templates/\""
    say "seeded $NOTES_DIR"
    warn "Initialize the vault as a git repo and push to your own remote: cd $NOTES_DIR && git init && git remote add origin <your-repo-url>"
  fi
else
  say "$NOTES_DIR already exists — skipping vault seed"
fi

# ---- 5. ~/CLAUDE.md (home-dir guide) ----
if [ -f "$REPO/home-CLAUDE.md" ]; then
  if [ ! -f "$HOME/CLAUDE.md" ] || confirm "Overwrite $HOME/CLAUDE.md ?"; then
    backup_if_exists "$HOME/CLAUDE.md"
    do_cmd "cp \"$REPO/home-CLAUDE.md\" \"$HOME/CLAUDE.md\""
    say "installed $HOME/CLAUDE.md"
  fi
fi

cat <<'EOF'

==> Install complete. Next steps:

  1. Open ~/.claude/CLAUDE.md and fill in the "About Me" section.
  2. Open ~/.claude/settings.json and either:
       - fill in your own PA_API_TOKEN / PA_API_URL for the personal-assistant MCP, OR
       - delete the entire "personal-assistant" block under mcpServers.
  3. If you seeded a notes vault, push it to a private GitHub repo so multi-machine sync works.
  4. Restart Claude Code (or run /reload-config).
  5. Read SETUP.md in this repo for what each piece does and how to customize.
EOF
