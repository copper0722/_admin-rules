#!/usr/bin/env bash
set -euo pipefail

target="${1:-$HOME/.zshrc}"
begin="# >>> copper shared zshrc >>>"
end="# <<< copper shared zshrc <<<"

if [ -L "$target" ]; then
  echo "refusing to edit symlink: $target" >&2
  exit 2
fi

mkdir -p "$(dirname "$target")"
touch "$target"

tmp="$(mktemp)"
awk -v begin="$begin" -v end="$end" '
  $0 == begin { skip = 1; next }
  $0 == end { skip = 0; next }
  !skip { print }
' "$target" > "$tmp"

{
  printf '%s\n' "$begin"
  printf '%s\n' '[ -f "$HOME/repos/_admin-rules/shell/zshrc.shared.sh" ] && . "$HOME/repos/_admin-rules/shell/zshrc.shared.sh"'
  printf '%s\n' '[ -n "${PS1:-}" ] || PS1="%m:%~ %# "'
  printf '%s\n\n' "$end"
  cat "$tmp"
} > "$target"

rm -f "$tmp"
echo "installed shared zshrc block in $target"
