# zshrc.shared.sh - cross-device interactive shell baseline.
# Source this from device-local ~/.zshrc. Keep secrets and device-only paths out.

[ -n "${ZSH_VERSION:-}" ] || return 0 2>/dev/null || exit 0
[[ -o interactive ]] || return 0 2>/dev/null || exit 0

export COPPER_ZSHRC_SHARED=1

if [[ -z "${PROMPT:-}" || "${PROMPT}" == "%m%# " || "${PROMPT}" == "%# " || "${PROMPT}" == "%n@%m %1~ %# " ]]; then
  _copper_prompt_device="${DEVICE:-$(hostname -s 2>/dev/null || printf local)}"
  PROMPT="%F{cyan}${_copper_prompt_device}%f:%~ %# "
  PS1="$PROMPT"
  unset _copper_prompt_device
fi

[[ -n "${PS1:-}" ]] || PS1="$PROMPT"

if [[ -x "$HOME/.claude/statusline.sh" ]]; then
  claude-statusline-check() {
    printf '{}' | "$HOME/.claude/statusline.sh"
  }
fi
