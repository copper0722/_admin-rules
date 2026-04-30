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
