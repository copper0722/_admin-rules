# agent-behavior

## Boot / session start (§2.2, §2.8, §2.11)
- read Law + memory/book + current `AGENTS.md` card on boot/reboot
- enable /remote-control; Copper accesses via https://claude.ai/code
- session end = /handover -> write durable handover through the configured private backend; update folder `AGENTS.md` only for reusable state/rules
- next session reads card → seamless resume; NOT /exit

## Card maintenance (§2.3, §2.4)
- card = `AGENTS.md`; Law = workspace root `AGENTS.md`
- `CLAUDE.md` = Claude auto-injection shim/symlink, not editable card
- folder `AGENTS.md` = living report + dispatch board
- update on entry (git review) AND after task completion
- excludes: root Law card unless user explicitly asks
- dispatch = write directly into target folder `AGENTS.md`; execute on sight; report back
- card edits are agent-facing writes: compressed English M2M, not chat prose

## Task execution (§2.5, §2.6, §2.7)
- after deploy/fix → meta-check: same issue elsewhere?
- never end silently; always report
- document/text received in chat → save to vault first, then process

## Session persistence (§2.9)
- `/handover write` -> configured private handover backend; offline fallback must be drained later
- SessionStart hook auto-reads latest handover → injected into context
- auto: significant reusable decisions/rules → write to folder `AGENTS.md`
- keyword: Copper says `mem` → capture to folder `AGENTS.md` immediately
- **§2.12 daily 5AM cycle**: every new session sets `/loop 30m` → at 5AM: `/handover write` → /clear → reboot.
- **§2.13 PIM access rules**: Token-saving first. PIM/GUI automation should use a stable broker or API. Scheduled jobs must not depend on fragile interactive GUI state. On broker failure, write a handover blocker.

## Retrieval before answering (§2.10)
- factual question → search before saying "I don't know"
- order: (1) own folder `AGENTS.md` -> (2) configured memory/handover -> (3) bounded repo search -> (4) web search when current/source attribution matters
- local knowledge first, web last; use bounded search
- `recall {topic}` → check own card; missing → fix card

## Teamwork (§1.7)
- dispatch work to sub-agents matched by ability level
- admin holds context + strategy; sub-agents execute
- context-first: gather before dispatching

## Instruction design — card/skill/charter authoring craft

Distilled 2026-06-15 (prompt-engineering analysis of a leaked Claude/Fable-5 system prompt: the transferable value is the craft of HOW rules are written, not its product-policy content). Applies to every agent-facing instruction surface: Law, folder `AGENTS.md`, `SKILL.md`, claude-auto-routine charter, agent prompts. Purpose = turn fuzzy model judgment into deterministic, cross-session-consistent behavior. Law principle: «Instruction design».

1. **Quantified triggers over adjectives** — never "適度/謹慎/簡短/盡量/必要時". Use numbers/booleans: line count, call count, file size, confidence %, time-since. e.g. ">100 lines → outline-first", "<20 lines → inline", "信心 < X → search first".
2. **Effort ladder (complexity → budget)** — declare per task-type the expected tool-call / sub-agent count AND a cap; over cap → escalate tier or stop. Complements the token gate (total-cap); this is the per-task lever. Charter lanes should carry a "task-type → call/agent budget" table.
3. **Point-of-use self-check** — co-locate a 2-3 item checklist with the step it gates; do NOT bury it in a distant 守則 block. Rules next to the action get executed; preamble rules get skipped.
4. **Decision tables** — express routing/dispatch as scenario→action rows, not prose (e.g. `journal-fetch.py` flag table, corpus subtype routing). Removes branching ambiguity; reads like if/else.
5. **Named anti-pattern + do-X-not-Y** — every recurrent bug → one named, contrastive rule. Existing: archive-don't-rm, act-not-ask, clean-X-means-clean-X, governance-flip-with-data-move, survey-before-manufacture.
6. **Ask-budget = 1** — ambiguous task → ask once → proceed on best interpretation, recording the assumption; never re-loop "blocked-Copper" (see Law «Agent autonomy»). Don't ask for what a downstream step will prompt for anyway.
7. **Verify / stop conditions** — define what must be true before declaring "done": structural verify (title + sections + counts), not substring; deploy → hash-subdomain + production curl + cache purge; cite → local full-text + retraction check.
8. **Severity tiers** — tag rules HARD/UNCONDITIONAL (non-negotiable) vs default (overridable with reason) so the trade space is explicit. Reserve caps/HARD for the truly inviolable (data-safety, citation hygiene, security, login/Secure-Token secret).
9. **Batch independent ops** — emit independent tool calls in one turn; combine related reads/writes; never serialize what can parallelize.
10. **Scope-bound refusal** — when blocking, narrow the "no" to the harmful specific and preserve the useful remainder (BoAn / public-facing agents), not a blanket refusal.

Enforcement: prefer encoding a rule as a quantified trigger so a cron audit can check it; un-quantified rule-words in new cards are an audit-finding, not chat-policed (Law «Law design»).
