# peak-hours

## Peak hour window (Copper directive 2026-04-20)

- **Peak = 21:00-02:00 TST** (5 hours, narrowed from prior 14:00-02:00). US-side prime usage → CC tokens ~2× cost + rate-limit pressure.
- **CC posture during peak = stay OFFLINE**. No new CC scheduled jobs in window. No interactive heavy CC work unless emergency. Existing schedules audited by vault-steward.
- **Non-CC workers absorb intensive work in peak window** (CC's quota saved for off-peak):
  - **Codex (gpt-5.4)** — code review, dep audit, adversarial review, fact-check
  - **Gemini CLI (Flash/Pro, free via sub)** — web search, grounded queries, n8n
  - **Hermes (OpenRouter)** — secretary, briefing, general
  - **Cloud Gemma 4** — quota-limited, fallback to Sonnet on 429
  - **Local Gemma 4 (Ollama)** — async housekeeping queue (summarize/tag/image-desc)
- **Vault-steward must keep CC schedules out of 21:00-02:00**; if a CC job's natural cadence lands in peak → either shift to nearest off-peak slot OR replace with non-CC equivalent.
- Burn window = Tue 03:00-09:00 only (off-peak, low-traffic day).
- Off-peak = 02:00-21:00 TST (19 hours) — preferred for any CC work.

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

## External model policy (Copper directive 2026-04-16, scoped exception 2026-04-18)

**Default rule (interactive sessions + ad-hoc agent work)**：
- **禁止 vault 內 call out cloud Gemma 4** (Google AI API gemma-4-31b-it)
- **禁止 vault 內 call out Codex** (OpenAI gpt-5.4)
- **local Gemma 4** (Ollama gemma4:31b-it-q4_K_M, localhost:11434) = 允許 background continuous worker (summarize / classify / tag)
- `gemma-cloud.py -g` 僅 Copper 手動用

**Scoped exception — stewardship routines (2026-04-18)**：
- admin CC 的排程 stewardship routines（`admin/cloud-routines/*.md` prompts 驅動，launchd fires `steward-wiki` / `steward-note` / `steward-repos`）**可** orchestrate 4 種 worker: self (CC Opus/Sonnet) + Codex + cloud Gemma 4 + local Gemma 4
- 目的：cost-aware 分派（code review → Codex；web-grounded search → cloud Gemma；pattern match → local Gemma；EBM/Causal 判斷 → CC 自己）
- 範圍：僅限 `steward-*` 系列 launchd job；其他 agent session 仍受默認規則
- 呼叫方式：`codex exec`、`python3 ~/repos/vault-scripts/gemma-cloud.py -g`、`curl localhost:11434/api/generate`
- Hermes 自用路徑不受影響

## Compute hygiene
- one sync per resource (§8.1); no duplicate pipelines
- agent search = ripgrep (faster than Dataview); Dataview = human-facing dashboards only (§8.6)
- .md > 500L → read `summary:` frontmatter first; full read only if needed (§9.1)
