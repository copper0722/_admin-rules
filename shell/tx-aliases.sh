# tx-aliases.sh — universal device/agent dispatch via tmux
# Sourced from each device's ~/.zshenv after `export DEVICE=<name>`.
#
# Usage:
#   cc                  → local: attach/create tmux `claude_${DEVICE}` in ~/repos
#   cc hm4              → ssh hm4: attach/create tmux `claude_hm4` in ~/repos
#   cc --resume         → local: pass `--resume` to claude
#   cc hm4 --resume     → ssh hm4: pass `--resume` to claude on hm4
#   cx, cx <device> ... → same pattern, codex
#   hm, hm <device> ... → same pattern, hermes
#
# Constraint: at most one session per app per device, hence `${app}_${device}`.

TX_DEVICES=(hm4 hmj cm1 mbp mba boa)

_tx() {
  local app=$1; shift
  local target=""
  if [ -n "$1" ]; then
    for d in $TX_DEVICES; do
      if [ "$1" = "$d" ]; then target=$1; shift; break; fi
    done
  fi
  target=${target:-$DEVICE}
  if [ -z "$target" ]; then
    echo "tx: \$DEVICE not set; export DEVICE=<hm4|hmj|cm1|mbp|mba|boa> in ~/.zshenv" >&2
    return 1
  fi
  local session="${app}_${target}"
  local cmd="$app $*"

  if [ "$target" = "$DEVICE" ]; then
    if [ -n "$TMUX" ]; then
      tmux new-session -d -As "$session" -c "$HOME/repos" "$cmd" 2>/dev/null
      tmux switch-client -t "$session"
    else
      tmux new-session -As "$session" -c "$HOME/repos" "$cmd"
    fi
  else
    ssh -t "$target" "tmux new-session -As '$session' -c \$HOME/repos '$cmd'"
  fi
}

cc() { _tx claude "$@"; }
cx() { _tx codex "$@"; }
hm() { _tx hermes "$@"; }
