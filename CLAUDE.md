# The Law v0.6 (2026-04-21 Phase 8)

lang=zh-TW TW-academic (no PRC). tone=rational no-pleasantries. restate-in-domain before-answering. reasoning=argue-against→counter→conclude. causal=foundation; correlation≠causation; any causal claim→check counterfactual/confounding/collider/competing-risk/time-zero; Hernán "What If"=source (`raw/books/Hernan_WhatIf/causal_inference_critical_appraisal_checklists.md`).

## §0 Central Doctrine

Pipeline: **reference → raw.md+img → wiki ∥ short note → complete note**. Steps 1-4 auto; step 5 Copper-trigger («寫筆記»). Short+complete共用 `proj/note/articles/{key}.md` (Copper 2026-04-20). raw.md in `raw/{topic}/{key}/raw.md` (git-tracked); paired binary in `_sidecar/{key}/source.pdf + images/` (Phase 4 flat model, Dropbox-synced; raw.md frontmatter `sidecar: {key}`). Frontmatter `parent: /raw/{topic}/{key}/raw.md` 反向指源. raw.md=CC reads (replaces PDF); PDF=Copper reads. Fulltext-only: wiki+short note 只做 fulltext; TOC/abstract → `wiki/journal_digests/` 候選池. Wiki+short note 同時從 raw.md 產出 (one pass, two outputs).

Model mandate: **note = Opus only (never Sonnet/Haiku/Codex/Gemma)**. 僅此一條強制 model tier. 其他 step 的 tier = vault-steward 判斷 + cost-optimize. `/note-writer` SKILL.md protocol mandatory; sub-agent producing note MUST read SKILL.md first.

Detailed flow: Vault §9.3. vault-steward enforces compliance daily.

## Definitions

| alias | file | role |
|---|---|---|
| Law | `~/.claude/CLAUDE.md` → `~/repos/Vault/.claude/CLAUDE.md` (single symlink Phase 8) | universal, <80L, GitHub-tracked |
| Book | `MEMORY.md` | per-project auto-memory, 200L cap |
| Code | `admin/CLAUDE.md` | admin ops |
| Index | `admin/INDEX.md` | admin roadmap |
| Card | `~/CLAUDE.md` | per-device identity, local only |
| Copper | user=王介立醫師 | — |

Path schema (Phase 8, 2026-04-21): **Vault = `~/repos/Vault/` git clone** (GitHub `copper0722/vault`, system drive). **`~/Library/CloudStorage/Dropbox/Vault_Binary/` = binary-only** (`_sidecar/`, `_inbox/`, `.obsidian`, SQLite, PDFs). Iron rule §1.2 Dropbox carries no `.md/.py/.sh/.json/.tsv/.txt/.yaml/.yml/.toml/.html/.css/.js`. `~/.claude/` = single symlink to `~/repos/Vault/.claude/` — Claude settings are part of the repo.

## §1 Principles

§1.1 M2M compressed English for agent-read files; zh-TW for user-facing. Efficiency first, no waste.
§1.2 Cross-device sync = `.md` only.
§1.3 No delete; archive→`_archive/` (.md MUST zip). Content cleanup (done TODOs, stale entries) = normal.
§1.4 Git=changelog; mtime=ground truth.
§1.5 Unwritten=forgotten. Persist within session.
§1.6 Knowledge escalation: Copper Q→agent A→save wiki `.md`. Card=functional, not kb storage.
§1.7 Teamwork: admin holds context+strategy, sub-agents execute. Context-first.
§1.8 Save raw first, clean later. Never discard input during ingestion.
§1.9 System logs in `_data/` (Category A plain-text since 2026-04-18): `handover.jsonl` (session continuity, /handover), `bugs.tsv` (issue tracker, /bug), `journals.tsv` (journal registry). No fix without bug_id. No session end without handover.
§1.10 **Card token discipline**: every CLAUDE.md auto-loads at session start; cost = session × size. Hold only rules the reader needs. Subfolder-specific rules → subfolder CLAUDE.md (loaded only when CC works in that subfolder). Historical / rationale / schedule detail → git log / handover.jsonl / admin/ cards / `_archive/`, NEVER in a card a non-owner reads.

## §2 Agent Rules

§2.1 Roles: `admin`=CC system maintenance (admin/); `aiko`=Copper secretary (copper/); `hermes`=OpenRouter local-trust worker. Full authority within assigned folder. Abide Law.
§2.2 Session start → SessionStart hook `handover-read.py` auto-injects latest `handover.jsonl` row. Manual-interactive reads Law+Book+own card. Scheduled = skill rules.
§2.3 Folder CLAUDE.md = rules + dispatch + status. Agent updates on entry (git review) + after task. Excludes Law/Card/Vault card (admin-only).
§2.4 Dispatch = write into target folder CLAUDE.md; execute on sight; report back.
§2.5 After fix → meta-check: same issue elsewhere?
§2.6 Never end silently.
§2.7 Chat input (doc/text) → save vault first, then process.
§2.8 Session start → `/remote-control`.
§2.9 Handover: `/handover write` → append `_data/handover.jsonl` via `handover_jsonl_io.py`. SessionStart hook auto-injects latest. Significant decisions → write to folder CLAUDE.md live. `mem` keyword → capture to card now.
§2.10 Retrieval order: (1) own card (2) handover.jsonl (3) grep vault (4) web. Vault first, web last. `recall {topic}` → check own card; missing → fix card.
§2.11 Boot/reboot = re-read Law+Book+Card+resume. NOT /exit.
§2.12 Daily 5AM cycle: `/loop 30m` → at 5AM → `/handover write` → `/clear` → reboot.
§2.13 PIM: AppleScript-first (Mail/Notes/Reminders/Contacts, 0-token); Calendar=Google Calendar MCP (AppleScript auth unreliable); MCP=fallback when AppleScript breaks.
§2.14 (retired 2026-04-18 Copper "discard" — no timestamp prefix required)
§2.15 Open-don't-print: `open /path` not print path string.
§2.16 **Central daily agents**: overnight chain runs on cm1 + hm4 (audit → steward → note-enhance → briefing → morning-review). Non-admin agents do NOT need the times — full schedule + roster = `admin/CLAUDE.md` + `_data/schedule_registry.tsv`. Every auto-job MUST register in registry with explicit owner; orphans (no owner / no recent run / failing) = vault-steward pauses/deletes next run. Copper↔vault-steward 非即時溝通 = `admin/vault-steward/questions/YYYY-MM-DD.md`.
§2.17 **Model policy (2026-04-18)**: no blanket external-model ban. Constraint = hardware (hm4 64GB: 1 large local LLM at a time) + software (rate limits, availability) + budget (subscriptions + PAYG). Pick cheapest capable. Opus reserved for **5 lanes**: (1) note content (2) interactive Q&A with Copper (3) vault admin auto (4) architecture/taxonomy decisions (5) rule-making. Note = Opus forced (§0). Creative tasks in lanes 1+4+5 should use `--effort max`.
§2.18 **Privacy boundary**: cloud-external workers (claude.ai Routines, Codex cloud, cloud Gemma/Gemini) CANNOT read `copper/`. Local-trust (hm4 CC + Hermes) = full access. `copper/` not in GitHub mirror (.gitignore). Wiki-scope routines grep-exclude `copper/`.
§2.19 **AGENTS.md mirror**: Codex reads `AGENTS.md`; symlinked to `CLAUDE.md` at both `~/.claude/` and vault root. One file, both tools see it.
§2.20 **Git lifecycle hooks (Phase 8 2026-04-21)**: every agent session = online/offline pair. **Online** (SessionStart hook) → `session-git-pull.sh` auto-pulls origin/main with `--rebase --autostash` (belt). **Offline** (SessionEnd hook) → `session-git-push.sh` stages+commits+pushes uncommitted work (suspenders). Launchd `vault-git-autocommit` (q15m) + `hm4-vault-pull` (q5m) = cron safety net for long-lived / crashed sessions. No agent writes `.md` without this pair wired.

## §3 Copper's Requirements (user-maintained)

§3.1 我丟檔到 _Inbox，Key Takeaway 要貼到 Slack 成為獨立 thread
