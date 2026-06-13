# compute, model-tier & external-model policy

> **Peak-hour / peak-window throttling is ABOLISHED (Copper directive 2026-05-22).**
> There is NO time-of-day restriction on Claude Code work — CC runs whenever
> there is work to do. Anthropic removed Pro/Max peak-hour limits (2026-05-07);
> the lingering "peak window 21:00-02:00" belief was a stale wrong cognition and
> a major bug. Gate scheduled LLM jobs on token budget only, never on clock
> hour. Reintroducing any clock-hour gate is a regression — do not.

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

**Primary external axis — Gemini Pro via Antigravity CLI (Copper directive 2026-06-13)**：
- **Gemini Pro (Gemini 3 Pro) = 日常 pipeline 主軸外部模型**；預設模式 = **Google Search grounding**（「先以 google search 為主，但其它也都可以」）。
- 走 **OAuth CLI**（file-based creds，cron/SSH-safe，非 macOS Keychain）：`agy`（Antigravity CLI）優先 = forward path（Gemini CLI 於 2026-06-18 停止對 Google AI Pro/Ultra 服務），未登入時 fall back 現役 `gemini` CLI。**無 API-key 路徑**（generativelanguage 金鑰未部署於任何 Copper-personal Mac）。
- 確定性 wrapper：`.script/gemini-pro.py`（auto backend、預設 model `gemini-3-pro-preview`、grounding 預設開、`--json`）。pipeline lane / skill 一律呼叫 wrapper，不直接呼叫底層 CLI。
- 此 directive **不撤銷**下方 Gemma/Codex 限制；它新增主軸，並把「web-grounded search」預設 worker 由 cloud Gemma 換成 Gemini Pro。

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
