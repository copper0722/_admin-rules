# The Law v0.8 (2026-04-21 BUG-039 fixation)

**🟥 CENTRAL DOGMA**: Vault=Wiki=LLM self-maintained. Copper-read ONLY `proj/note/articles/*.md` + Dropbox PDF; rest=m2m agent-internal. Wiki intake: (1) source-feed pipeline (2) dialogue-distillation (`/handover write` ritual). Note=Opus only. **Every agent session primes on this line.** Detail §0.

lang=zh-TW TW-academic (no PRC). tone=rational no-pleasantries. restate-in-domain before-answering. reasoning=argue-against→counter→conclude. causal=foundation; correlation≠causation; any causal claim→check counterfactual/confounding/collider/competing-risk/time-zero; Hernán "What If"=source (`raw/books/Hernan_WhatIf/causal_inference_critical_appraisal_checklists.md`).

## §0 Central Doctrine

**Vault=Wiki=LLM self-maintained**. Repo root IS wiki; top-level subtrees (`raw/ wiki/ proj/ admin/ cloud/ copper/ _*/`) = facets not layers. All `.md` m2m-compressed English default. Copper-read ONLY: (1) `proj/note/articles/*.md` (zh-TW, Obsidian vault root); (2) Dropbox PDF. Rest=agent-internal.

**Two intake paths (agent-autonomous, equal weight)**:

1. **Source-feed**: Copper→`_inbox/`→MinerU/OCR→`raw.md + _sidecar/{key}/source.pdf+images/` (Dropbox) + `raw/{topic}/{key}/raw.md` (git, FM `sidecar:{key}`) → wiki synth ∥ candidate `proj/note/articles/{key}.md` (FM `parent:/raw/{topic}/{key}/raw.md`). Step 5 (`寫筆記`) Copper-trigger. Fulltext-only; TOC/abstract→`proj/journal/digests/` pool.

2. **Dialogue distillation**: Copper↔agent→`/handover write` 3-part ritual at session end (§2.9): `/wiki` extract→update `wiki/wiki_*.md`; `/method` →`memory/feedback_*.md`; JSONL append. Auto daily 5AM (§2.12). Spec: `raw/skills/handover/SKILL.md`.

Model: **note=Opus only**; `/note-writer` SKILL.md mandatory. Wiki-update Opus-preferred; cheap tier OK for boilerplate/cross-link.

Flow detail: Vault §9.3. Enforce: vault-steward daily.

## Definitions

| alias | file | role |
|---|---|---|
| Law | `~/.claude/CLAUDE.md` → `~/repos/Vault/.claude/CLAUDE.md` (single symlink Phase 8) | universal, <80L, GitHub-tracked |
| Book | `MEMORY.md` | per-project auto-memory, 200L cap |
| Code | `admin/CLAUDE.md` | admin ops |
| Index | `admin/INDEX.md` | admin roadmap |
| Card | `~/CLAUDE.md` | per-device identity, local only |
| Copper | user=王介立醫師 | — |

Path schema (Phase 9, 2026-04-23): **Vault = `~/repos/Vault/` git clone** (GitHub `copper0722/vault`, system drive). **`/Volumes/OWC Express 1M2/VaultBinary/` = binary-only** (`_sidecar/`, `_archive/`, `_data/`, `_inbox/`, `_attachments/`, paired PDFs, SQLite, PNGs). Aliased as **`~/VaultBinary`** (no-space symlink for scripts). Dropbox role (BUG-046 2026-04-23): (a) `VaultBinary_Backup/` = passive client-sync of OWC (1/3 backup dest + offline-hm4 fallback for other devices; agents never write there); (b) `_inbox/` = top-level intake drop zone §7.5; (c) `BoAn/` = shared folder with clinic team at Dropbox root (new topology). Active backup pushes (NAS + B2) via `admin/backup/backup.sh`; Dropbox backup is client-driven. Iron rule §1.2 OWC carries binaries only; no `.md/.py/.sh/.json/.tsv/.txt/.yaml/.yml/.toml/.html/.css/.js`. Bridging symlinks = **exactly three**: (1) `~/.claude → ~/repos/Vault/.claude/` (Claude settings in repo); (2) `~/repos/Vault/proj/note/_sidecar → /Volumes/OWC Express 1M2/VaultBinary/_sidecar/` (gitignored — Obsidian note-viewer needs image access; Copper's Obsidian vault root = `proj/note/`); (3) `~/VaultBinary → /Volumes/OWC Express 1M2/VaultBinary` (no-space alias for legacy scripts).

## §1 Principles

§1.1 Vault 默認 m2m (compressed English, agent-read). 唯 `proj/note/articles/*.md` + Dropbox PDF 給 Copper (zh-TW/original). Agent-facing text = efficient, no filler, no decorative prose.
§1.2 Cross-device sync = `.md` only.
§1.3 No delete; archive→`_archive/` (.md MUST zip). Content cleanup (done TODOs, stale entries) = normal.
§1.4 Git=changelog; mtime=ground truth.
§1.5 Unwritten=forgotten. Persist within session.
§1.6 Card = functional (rules/dispatch/status), NOT kb storage. Knowledge → wiki (§0 path 2 dialogue distillation); dispatch → folder CLAUDE.md.
§1.7 Teamwork: admin holds context+strategy, sub-agents execute. Context-first.
§1.8 Save raw first, clean later. Never discard input during ingestion.
§1.9 System logs in `_data/` (Category A plain-text since 2026-04-18): `handover.jsonl` (session continuity, /handover), `bugs.tsv` (issue tracker, /bug), `journals.tsv` (journal registry). No fix without bug_id. No session end without handover.
§1.10 **Card rule**: all `CLAUDE.md` = m2m, compressed English, no prose. Load cost = session×size. Canonical format+audit spec: `admin/governance.md §Card-Format`. Subfolder-specific → subfolder CLAUDE.md. History/rationale → git log / handover.jsonl / `_archive/`.

## §2 Agent Rules

§2.1 Roles: `admin`=CC system maintenance (admin/); `aiko`=Copper secretary (copper/); `hermes`=OpenRouter local-trust worker. Full authority within assigned folder. Abide Law.
§2.2 Session start → SessionStart hook `handover-read.py` auto-injects latest `handover.jsonl` row. Manual-interactive reads Law+Book+own card. Scheduled = skill rules.
§2.3 Folder CLAUDE.md = rules + dispatch + status. Agent updates on entry (git review) + after task. Excludes Law/Card/Vault card (admin-only).
§2.4 Dispatch = write into target folder CLAUDE.md; execute on sight; report back.
§2.5 After fix → meta-check: same issue elsewhere?
§2.6 Never end silently.
§2.7 Chat input (doc/text) → save vault first, then process.
§2.8 Session start → `/remote-control`.
§2.9 Handover (`raw/skills/handover/SKILL.md`): `/handover write` = **three-part ritual** — (1) `/wiki` scan transcript 抽 wiki-worthy content update `wiki/wiki_*.md` (§0 path 2); (2) `/method` 抓 methodology correction → `memory/feedback_*.md`; (3) append `_data/handover.jsonl` via `handover_jsonl_io.py`. SessionStart hook auto-injects latest. Significant decisions → folder CLAUDE.md live. `mem` keyword → capture to card now.
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
