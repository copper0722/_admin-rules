#!/usr/bin/env bash
# install-zshenv.sh — deploy parity ~/.zshenv block ensuring DEVICE export
# and tx-aliases.sh source. Idempotent: replaces only the marker-bracketed
# block, leaves user's other lines intact.
#
# Usage: bash install-zshenv.sh <device-name>
#
# Devices: hm4 / hmj / cm1 / mbp / mba per Tailscale DNSName short label.
# Each device needs DEVICE=<name> in ~/.zshenv so tx-aliases.sh's cc/cx/hm
# helpers can route local-vs-remote correctly. Without DEVICE, cc fails fast
# with `tx: $DEVICE not set`.
set -euo pipefail

device="${1:?usage: $0 <device-name>}"
target="${ZSHENV_PATH:-$HOME/.zshenv}"

case "$device" in
    hm4|hmj|cm1|mbp|mba|boa) ;;
    *) echo "install-zshenv: unknown device '$device' (expected hm4/hmj/cm1/mbp/mba/boa)" >&2; exit 2 ;;
esac

begin="# >>> copper device parity >>>"
end="# <<< copper device parity <<<"

mkdir -p "$(dirname "$target")"
touch "$target"

tmp="$(mktemp)"
awk -v b="$begin" -v e="$end" '
  $0 == b { skip = 1; next }
  $0 == e { skip = 0; next }
  !skip { print }
' "$target" > "$tmp"

{
  printf '%s\n' "$begin"
  printf 'export DEVICE=%s\n' "$device"
  printf 'source "$HOME/repos/_admin-rules/shell/tx-aliases.sh"\n'
  printf '%s\n\n' "$end"
  cat "$tmp"
} > "$target"

rm -f "$tmp"
echo "installed: DEVICE=$device + tx-aliases.sh source in $target"
