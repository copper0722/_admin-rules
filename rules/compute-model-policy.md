# compute, model-tier & external-model policy

> **Peak-hour / peak-window throttling is ABOLISHED (Copper directive 2026-05-22).**
> There is NO time-of-day restriction on Claude Code work — CC runs whenever
> there is work to do. Anthropic removed Pro/Max peak-hour limits (2026-05-07);
> the lingering "peak window 21:00-02:00" belief was a stale wrong cognition and
> a major bug. Do not gate scheduled LLM jobs on clock hour; reintroducing
> any clock-hour gate is a regression. The token-budget gate + the q30m
> auto-routine lane it gated were retired 2026-06-29 — no token-budget
> gating remains.

## Tool priority order
- Obsidian/dashboard = human UI; CC = agent work
- OCR: no local engine (DT4 retired 2026-04-09). Flag as manual if needed.

## Model tier burn order
- default: use lowest capable tier (haiku → sonnet → opus)
- escalate tier only when task explicitly requires it (long context, complex reasoning)
- scheduled tasks (cron/skills) = haiku unless context size forces sonnet

## Effort levels (Opus 4.7+, settings.json = xhigh)
- `low`/`medium`: cost/latency-sensitive, less capable on hard tasks
- `high`: concurrent sessions, balanced intelligence + cost
- `xhigh` (default): most coding + vault work, strong autonomy without token runaway
- `max`: genuinely hard problems only — diminishing returns, overthinking risk
- `/effort` interactive slider to adjust per-session. 4.6 sessions fall back to `high` when `xhigh` set

## External model policy (Copper directive 2026-04-16, scoped exception 2026-04-18, primary-axis 2026-06-13)

**Primary external axis — Antigravity 額度優先、吃乾抹淨 (Copper directive 2026-06-13)**：
- **日常 pipeline 主軸 = Antigravity 額度**；以 **Gemini 3.1 Pro (High)** 為主、預設 **Google Search grounding**。**優先把 Antigravity 額度吃乾抹淨**：兩個訂閱帳號（`copper.wang` + `hemodialysis.taiwan`）round-robin 輪替 + per-account quota cooldown，兩帳號都榨乾/cooling 後才 fallback。
- 路徑（全 OAuth、file-based creds、cron/SSH-safe、**無 macOS Keychain、無 API-key**）：
  1. `agy -p`（Antigravity CLI）輪替 2 帳號。帳號以 **HOME profile 隔離**（agy creds 落 `$HOME/.gemini/antigravity-cli/antigravity-oauth-token`；帳號#2 跑在 `HOME=~/.agy-profiles/hemodialysis`，靠 `~/.agy-profiles/<acct>/.local/bin/agy` symlink 指回真 binary）。agy 互動式登入需一次性 browser OAuth（`agy` TUI 選 Google OAuth → 貼 code）。forward path——Gemini CLI 於 2026-06-18 停止對 AI Pro/Ultra 服務。
  2. 兩帳號 exhausted/cooling → fallback `gemini -p`（model `gemini-3-pro-preview`，`~/.gemini/oauth_creds.json` 現役）。
- 確定性 wrapper：`.script/gemini-pro.py`（auto rotation + cooldown、`--status` / `--account` / `--backend` / `--json`、grounding 預設開）。pipeline lane / skill 一律呼叫 wrapper，不直接呼叫底層 CLI。
- agy 也能用 **Claude Sonnet/Opus 4.6 (Thinking)、GPT-OSS 120B**（同一份 Antigravity 額度）；且 agy 本身是 full agentic coding CLI（worktree / 改檔 / MCP / skills / subagents），可做 local agent work。
- 此 directive **不撤銷**下方 Gemma 4 / Codex call-out 限制；它新增主軸並把「web-grounded search」預設 worker 由 cloud Gemma 換成 Antigravity。

**Default rule (interactive sessions + ad-hoc agent work)**：
- **禁止 vault 內 call out cloud Gemma 4** (Google AI API gemma-4-31b-it)
- **禁止 vault 內 call out Codex** (OpenAI gpt-5.4)
- **local Gemma 4** (Ollama gemma4:31b-it-q4_K_M, localhost:11434) = 允許 background continuous worker (summarize / classify / tag)
- `gemma-cloud.py -g` 僅 Copper 手動用（cloud Gemma 4；web-grounded search 已由 Gemini Pro `gemini-pro.py` 取代，見上方主軸）

**Scoped exception — stewardship routines (2026-04-18)**：
- admin CC 的排程 stewardship routines（`admin/cloud-routines/*.md` prompts 驅動，launchd fires `steward-wiki` / `steward-note` / `steward-repos`）**可** orchestrate 4 種 worker: self (CC Opus/Sonnet) + Codex + cloud Gemma 4 + local Gemma 4
- 目的：cost-aware 分派（code review → Codex；web-grounded search → **Gemini Pro / Antigravity (`gemini-pro.py`)**；pattern match → local Gemma；EBM/Causal 判斷 → CC 自己）
- 範圍：僅限 `steward-*` 系列 launchd job；其他 agent session 仍受默認規則
- 呼叫方式由 private ops repo 定義；public rules must not hardcode private script paths or credentials.
- Hermes 自用路徑不受影響

## Compute hygiene
- one sync per resource (§8.1); no duplicate pipelines
- agent search = ripgrep (faster than Dataview); Dataview = human-facing dashboards only (§8.6)
- .md > 500L → read `summary:` frontmatter first; full read only if needed (§9.1)
