# tx-aliases.sh — universal device/agent dispatch via tmux
# Sourced from each device's ~/.zshenv after `export DEVICE=<name>`.
#
# Usage:
#   cc                  → local: attach/create tmux `cc_${DEVICE}` in ~/repos
#   cc hm4              → ssh hm4: attach/create tmux `cc_hm4` in ~/repos
#   cc --resume         → local: pass `--resume` to claude
#   cc hm4 --resume     → ssh hm4: pass `--resume` to claude on hm4
#   cx, cx <device> ... → same pattern, codex      (session `cx_${device}`)
#   hm, hm <device> ... → same pattern, hermes     (session `hm_${device}`)
#
# Constraint: at most one session per app per device, hence `${prefix}_${device}`
# where prefix = invocation alias (cc/cx/hm), not the underlying binary name.

TX_DEVICES=(hm4 hmj cm1 mbp mba boa)

_tx_attach_or_create_local() {
  local session=$1 legacy_session=$2 cmd=$3
  local s
  for s in "$session" "$legacy_session"; do
    if tmux has-session -t "$s" 2>/dev/null; then
      if [ -n "$TMUX" ]; then
        tmux switch-client -t "$s"
      else
        tmux attach-session -t "$s"
      fi
      return
    fi
  done

  if [ -n "$TMUX" ]; then
    tmux new-session -d -s "$session" -c "$HOME/repos" "$cmd"
    tmux switch-client -t "$session"
  else
    tmux new-session -s "$session" -c "$HOME/repos" "$cmd"
  fi
}

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
  local prefix cmd
  case $app in
    claude)
      prefix=cc
      cmd="ulimit -Hn 2048 2>/dev/null; ulimit -Sn 2048 2>/dev/null; exec claude --dangerously-skip-permissions $*"
      ;;
    codex)
      prefix=cx
      cmd="exec codex $*"
      ;;
    hermes)
      prefix=hm
      cmd="hermes update; exec hermes $*"
      ;;
  esac
  local session="${prefix}_${target}"
  local legacy_session="${app}_${target}"

  if [ "$target" = "$DEVICE" ]; then
    _tx_attach_or_create_local "$session" "$legacy_session" "$cmd"
  else
    # Remote dispatch via Mosh (Copper directive 2026-05-24): mosh gives
    # client-side connection persistence — survives wifi/cellular switches,
    # client sleep/wake, IP changes — so iPad/laptop can resume tmux session
    # across days without re-dialing. Falls back to ssh if `mosh` not found
    # locally OR mosh-server not installed on the remote (mosh prints a
    # clear error in that case; user can install or fall back manually).
    local remote_cmd="if tmux has-session -t '$session' 2>/dev/null; then exec tmux attach-session -t '$session'; fi; if tmux has-session -t '$legacy_session' 2>/dev/null; then exec tmux attach-session -t '$legacy_session'; fi; exec tmux new-session -s '$session' -c \$HOME/repos \"$cmd\""
    if command -v mosh >/dev/null 2>&1; then
      mosh "$target" -- sh -c "$remote_cmd"
    else
      ssh -t "$target" "$remote_cmd"
    fi
  fi
}

# Drop any pre-existing cc/cx/hm alias before declaring the functions.
# Reason: zsh expands aliases at line-read time and they win over functions
# of the same name; previous .zshenv versions on some devices declared
# `alias cc='claude --effort max'` which shadowed this function and broke
# `cc <device>` dispatch. Idempotent: silently noop when no alias exists.
unalias cc cx hm 2>/dev/null || true

cc() { _tx claude "$@"; }
cx() { _tx codex "$@"; }
hm() { _tx hermes "$@"; }
