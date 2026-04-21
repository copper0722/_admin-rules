# agent-behavior

## Boot / session start (§2.2, §2.8, §2.11)
- read Law + Book (MEMORY.md) + Card (~/CLAUDE.md) on boot/reboot
- enable /remote-control; Copper accesses via https://claude.ai/code
- session end = /handover → write `## Last Session Handover` to folder CLAUDE.md
- next session reads card → seamless resume; NOT /exit

## Card maintenance (§2.3, §2.4)
- folder CLAUDE.md = living report + dispatch board
- update on entry (git review) AND after task completion
- excludes: Law, Card, Vault CLAUDE.md (admin-maintained)
- dispatch = write directly into target folder CLAUDE.md; execute on sight; report back

## Task execution (§2.5, §2.6, §2.7)
- after deploy/fix → meta-check: same issue elsewhere?
- never end silently; always report
- document/text received in chat → save to vault first, then process

## Session persistence (§2.9)
- `/handover write` → append `_data/handover.jsonl` (plain-text, one JSON object per line; auto id + created_at)
- SessionStart hook auto-reads latest handover → injected into context
- auto: significant decisions/changes → write to folder CLAUDE.md
- keyword: Copper says `mem` → capture to folder CLAUDE.md immediately
- **§2.12 daily 5AM cycle**: every new session sets `/loop 30m` → at 5AM: `/handover write` → /clear → reboot.
- **§2.13 PIM access rules**: AppleScript-first (0 token). Calendar = Google Calendar MCP (AppleScript auth unreliable). **MCP = fallback** for all PIM when AppleScript fails. Priority: AppleScript → MCP. On CC update → test AppleScript; if broken → fall back to MCP silently.

## Retrieval before answering (§2.10)
- factual question → search before saying "I don't know"
- order: (1) own folder CLAUDE.md → (2) aiko/memory/event-log.md → (3) aiko/memory-briefing.md → (4) grep vault → (5) web search
- vault first, web last; non-specific question = Copper knows it's in vault
- `recall {topic}` → check own card; missing → fix card

## Teamwork (§1.7)
- dispatch work to sub-agents matched by ability level
- admin holds context + strategy; sub-agents execute
- context-first: gather before dispatching
