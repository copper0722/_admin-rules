---
name: handover
description: "Session handover — read or write records in `_data/handover.jsonl` (Category A plain-text master, since 2026-04-18). Use when user says /handover, 'handover', 'session end', '交接', '收工', /ho, /HO. Write mode triggers THREE-part ritual: /wiki (knowledge extraction) + /method (methodology reflection) + /handover (JSONL append)."
---

# /handover

Session continuity via `_data/handover.jsonl`. Same file across main vault and BoAn.

**Usage:**
- `/handover` or `/ho` or `/HO` → read latest, resume
- `/handover write` (or `write`/`end`/`收工` subject) → full three-part ritual (wiki + method + handover JSONL)

---

## THREE-PART WRITE RITUAL (Copper directive 2026-04-15)

When writing (not reading), execute all three in sequence:

### Part 1 — /wiki (Knowledge extraction)

Scan this session's transcript for:
- New knowledge / fact / method worth adding to vault wiki
- Corrections or additions to existing wiki content
- Cross-link opportunities between wikis mentioned in the session

For each candidate:
- Locate relevant `wiki/wiki_*.md`
- Update or create per HR-5 source-type routing + frontmatter rules (`wiki/CLAUDE.md`)
- Register new wikis in `wiki/CLAUDE.md` index if applicable

If no wiki-worthy content → skip silently, no empty wiki files.

### Part 2 — /method (Methodology reflection)

Scan session for Copper corrections / guidance about:
- Wiki methodology (EBM Guyatt, Causal Hernán)
- Article appraisal (READ/SKIM/SKIP)
- Source verification (OCR fidelity, cross-ref authoritative source)
- Data accuracy (derived vs confirmed, flag precision)
- Note format (KEY TAKEAWAYS first, bilingual headings)
- Routine-vs-gap filtering (journal digest)
- Any methodological principle Copper pushed back on

For each correction:
- Append a dated bullet to closest existing `memory/feedback_*.md`
- OR create new feedback memory if no match
- Register new memories in that folder's `MEMORY.md` index (one-line hook)

If no correction → skip silently.

### Part 3 — /handover (JSONL append)

Append one record to `_data/handover.jsonl` (schema below).

---

## STORAGE

`_data/handover.jsonl` — append-only, UTF-8, one JSON object per line. Category A plain-text master per Law §8.4 (migrated 2026-04-18 from `handover.db` SQLite; retired copy in `_archive/handover_sqlite_retired_20260418.zip`).

| Field | Type | Description |
|---|---|---|
| `id` | int | auto-filled on append (= prior max id + 1) |
| `date` | string | session date YYYY-MM-DD |
| `device` | string | hm4 / cmb / cmp / cm1 / ward-lt / st99 / PC-06 / cloud |
| `agent` | string | agent model + context |
| `operator` | string | Wang / Chou / auto / launchd / hermes |
| `role` | string | session role (see Role table). **REQUIRED** for new rows — drives filtered read |
| `topic` | string | session summary title |
| `completed` | string | what was done (newline-separated items) |
| `decisions` | string | key decisions (newline-separated items) |
| `blocked` | string | what is blocked (newline-separated items) |
| `next_priorities` | string | priorities for next session (newline-separated items) |
| `created_at` | string | auto-filled ISO timestamp |

Text fields remain newline-separated plain text (same convention as the legacy SQLite schema — callers do not need to re-split arrays).

### Role column

Role segments the feed so each session type reads only its own handovers.

| role | scope | session name prefixes |
|---|---|---|
| `admin` | system maintenance, vault infra, automation | `admin_*`, `admin-*` |
| `tsn` | TSN 學會、talk prep、slides | `tsn-*`, `tsn_*`, `TSN*` |
| `wiki` | journal digest, NEJM/Nature ingest, wikify pipeline | `wiki-*`, `wiki_*` |
| `secretary` | Copper 個人事務 (calendar, finance, family, gmail) | `secretary-*`, `aiko-*` (aiko = agent alias) |
| `clinic` | BoAn EMR, dialysis, patient data | `clinic-*`, `boan-*`, `emr-*` |
| `meta` | SessionEnd no-op / ritual handover-write sessions | auto-set when topic matches `SessionEnd%`, `No-op%`, etc. |

Derivation: split `session_name` by `[-_\s]`, take first segment, lowercase, map via `handover-read.py:ROLE_CANON`. Unknown prefix → NULL → read falls back to latest overall.

---

## READ (default)

Driven by `handover-read.py` (SessionStart hook). Filters by role derived from `session_name` (passed via hook stdin JSON).

1. Derive role from session_name prefix (see Role table).
2. Scan `_data/handover.jsonl` newest → oldest. First record with matching `role` wins. If no match → fall back to latest record overall (with `[role=X MISS → latest overall]` tag in header).
3. Display: id, date, device, agent, role tag, operator, topic, then:
   - BLOCKED first
   - Next priorities
   - Decisions
   - Completed (summary)
4. Carry-forward: last 3 sessions' next_priorities (within same role) not found in latest completed.

Interactive read (from shell or skill):
```bash
python3 ~/Vault/repos/vault-scripts/db-exporters/handover_jsonl_io.py latest --role admin
python3 ~/Vault/repos/vault-scripts/db-exporters/handover_jsonl_io.py tail -n 3 --role admin
python3 ~/Vault/repos/vault-scripts/db-exporters/handover_jsonl_io.py tail -n 3 --agent vault-steward
```

---

## WRITE (session end)

1. Detect device: `scutil --get ComputerName` (macOS) or hostname.
2. Append one record via the helper script (uses `fcntl.flock` for append-safety):

```bash
python3 ~/Vault/repos/vault-scripts/db-exporters/handover_jsonl_io.py append <<'JSON'
{
  "date": "2026-04-18",
  "device": "hm4",
  "agent": "Opus 4.7 (1M context)",
  "operator": "auto",
  "role": "admin",
  "topic": "one-line summary",
  "completed": "item one\nitem two",
  "decisions": "decision with reason",
  "blocked": null,
  "next_priorities": "action items for next session"
}
JSON
```

Helper auto-fills `id` and `created_at`.

**Required:**
- `date`: YYYY-MM-DD
- `device`: auto-detected
- `agent`: model name
- `operator`: Wang / Chou / auto / launchd / hermes
- `role`: one of `admin` / `tsn` / `wiki` / `secretary` / `clinic` / `meta` — derive from session_name prefix. Do NOT leave NULL for new rows.
- `topic`: 1-sentence summary
- `completed`: everything done (one item per line)
- `next_priorities`: action items for next session (one per line)

**Optional:**
- `decisions`: include WHY (one per line)
- `blocked`: what + who can unblock (one per line)

**Rules:**
- `completed` = specific, comprehensive. Every file/task/action.
- `next_priorities` = actionable by cold-start agent on any device.
- Cross-device tasks: prefix with device name.
- Git commit after append: `handover: #{id} — {topic}`.

---

## Cross-device access

- **hm4** (Dropbox-native sync): direct JSONL read/append.
- **cm1** (SMB mount `/Volumes/dropbox-personal/Vault/`): direct JSONL read; append ONLY if no concurrent hm4 writer (rare — cm1 is typically read-only auditor).
- **Cloud CC** (sandbox, no filesystem): reads JSONL via clone in the GitHub mirror (`.cloud/data/handovers.jsonl`); appends via PENDING md block in `_data/handover.db.md` if direct append unavailable — local `handover-md-sync.py --drain` consumes next cycle.

Legacy SQLite master (`_data/handover.db`) retired 2026-04-18 per dispatch Phase 1.1. No reader should touch it; zipped copy in `_archive/handover_sqlite_retired_20260418.zip` for 30 days then deleted per Law §1.3.

---

## EXAMPLE

One-line JSONL record (pretty-printed here for readability):

```json
{
  "id": 169,
  "date": "2026-04-18",
  "device": "hm4",
  "agent": "Opus 4.7 (1M context)",
  "operator": "auto",
  "role": "admin",
  "topic": "Redundancy purge dispatch — Phase 1 DB portability",
  "completed": "Migrated handover.db → handover.jsonl (167 rows)\nPatched handover-read.py + handover-md-sync.py\nPatched vault-steward / aiko-briefing / cloud-admin prompts\nRewrote /handover SKILL.md",
  "decisions": "Category A = small+text JSONL/TSV; hm4 remains single-writer; cloud CC appends via JSONL directly or PENDING fallback",
  "blocked": null,
  "next_priorities": "Phase 1.2 bugs.db → bugs.tsv\nPhase 1.3 journals.db → journals.tsv\nPhase 1.4 Category C snapshot cron",
  "created_at": "2026-04-18 12:51:00"
}
```
