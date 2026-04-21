---
name: bug
description: "Vault issue tracker — report, fix, and close bugs in _data/bugs.tsv (Category A plain text since 2026-04-18). Use when agent finds vault malformation, broken config, bad data, or user says /bug."
---

# /bug

Vault = repo. Malformation found → report first, fix second, record stays.

**Usage:**
- `/bug report` → register new bug (returns BUG-XXX)
- `/bug fix BUG-XXX` → fix the bug, record what was done
- `/bug list` → show open bugs
- `/bug BUG-XXX` → show detail
- `/bug wontfix BUG-XXX {reason}` → close without fix

Master storage = `_data/bugs.tsv`. SQLite master retired 2026-04-18 (see `_archive/bugs_sqlite_retired_20260418.zip`).

Canonical helper:
```bash
python3 ~/Vault/repos/vault-scripts/db-exporters/bugs_tsv_io.py <subcommand>
```

---

## FILE SCHEMA (`_data/bugs.tsv`)

Tab-separated, UTF-8, 12 columns. Tab + newline in any cell are replaced with single space at write time (lossy formatting, preserved info).

| # | column | type | description |
|---|---|---|---|
| 1 | `id` | int | auto-increment |
| 2 | `bug_id` | string | `BUG-{NNN}` zero-padded |
| 3 | `title` | string | < 80 chars |
| 4 | `severity` | enum | `critical` / `major` / `minor` |
| 5 | `component` | string | vault area (admin, wiki, ref, copper, proj, _data, cron, hooks, law, scripts) |
| 6 | `description` | string | what's wrong + how discovered + expected vs actual |
| 7 | `fix_description` | string | filled on fix/wontfix |
| 8 | `status` | enum | `open` / `fixing` / `fixed` / `wontfix` |
| 9 | `reported_by` | string | `{agent}@{device}` |
| 10 | `fixed_by` | string | `{agent}@{device}` |
| 11 | `reported_at` | string | ISO timestamp |
| 12 | `fixed_at` | string | ISO timestamp |

If any cell becomes > 2000 chars, spin body out to `_data/bugs/{bug_id}.md` and reduce the TSV cell to a pointer (`see _data/bugs/{bug_id}.md`).

---

## REPORT

Agent discovers vault malformation (broken link, bad schema, orphan file, config error, wrong path, stale data, missing sidecar, etc.) → MUST report before fixing.

```bash
python3 ~/Vault/repos/vault-scripts/db-exporters/bugs_tsv_io.py report <<'JSON'
{
  "title": "memory-retrieve.py uses wrong DB path since vault rename",
  "severity": "critical",
  "component": "hooks",
  "description": "what's wrong + how discovered + expected vs actual",
  "reported_by": "admin@hm4"
}
JSON
```

Helper auto-assigns `bug_id` + `id` + `reported_at`, sets `status=open`, prints `🐛 BUG-{NNN} reported: {title}`.

**Severity guide:**
- `critical`: data loss risk, pipeline halted, hook/cron broken, DB corruption
- `major`: wrong output, missing required fields, broken cross-references, stale config
- `minor`: naming convention violation, cosmetic, non-blocking inconsistency

---

## FIX

No fix without bug_id. This is the law.

1. `python3 .../bugs_tsv_io.py show BUG-NNN` → read bug.
2. `python3 .../bugs_tsv_io.py set-status BUG-NNN fixing` (optional — marks in-progress).
3. Do the fix.
4. Close:
   ```bash
   python3 ~/Vault/repos/vault-scripts/db-exporters/bugs_tsv_io.py fix BUG-NNN \
     --fixed-by admin@hm4 --message "what was changed (files, lines, commands)"
   ```
5. Meta-check (§2.5): same issue elsewhere? If yes → report new BUG for each instance.
6. Prints `✅ BUG-{NNN} fixed: {fix_description}`.

---

## LIST

```bash
python3 ~/Vault/repos/vault-scripts/db-exporters/bugs_tsv_io.py list --status open
python3 ~/Vault/repos/vault-scripts/db-exporters/bugs_tsv_io.py list --severity critical --status open
python3 ~/Vault/repos/vault-scripts/db-exporters/bugs_tsv_io.py list --json           # machine-readable
```

Output header: `{open} open, {fixing} in progress, {fixed} resolved total`.

Sort order: `severity (critical→major→minor)` then `reported_at` asc.

---

## WONTFIX

For bugs that are by design or not worth fixing:

```bash
python3 ~/Vault/repos/vault-scripts/db-exporters/bugs_tsv_io.py wontfix BUG-NNN \
  "reason for closing without fix" --fixed-by admin@hm4
```

Prints `⏭ BUG-{NNN} wontfix: {reason}`.

---

## AUTO-REPORT TRIGGERS

Agent SHOULD auto-report when encountering during normal work:

- Hook returns error on session start/end
- Script referenced in CLAUDE.md doesn't exist
- DB path in config doesn't resolve
- Sidecar .db.md missing for a .db file
- CLAUDE.md references deleted/moved files
- Cron log shows ERROR/FAIL
- Broken symlink in vault
- Frontmatter missing required fields (on touch)

Report immediately, fix if trivial, defer if complex.

---

## Cross-device access

- **hm4** (Dropbox-native): direct TSV read/write via helper.
- **cm1** (SMB mount): direct TSV read; write only when hm4 offline (avoid concurrent writers).
- **Cloud CC** (sandbox): writes a new bug by dropping a `{bug_id}.json` file into `_data/bugs_inbox/` — local cron drains on next vault-steward run.

Direct TSV edit via Obsidian/vim is fine for triage; helper enforces atomic rewrite (tmp + rename) so concurrent helper-writes don't corrupt. Concurrent hand-edit + helper-write DOES risk corruption — avoid.

---

## EXAMPLE

Report:

```bash
python3 ~/Vault/repos/vault-scripts/db-exporters/bugs_tsv_io.py report <<'JSON'
{
  "title": "memory-retrieve.py uses wrong DB path since vault rename",
  "severity": "critical",
  "component": "hooks",
  "description": "memory-retrieve.py hardcodes ~/copper/admin/memory/memory.db. Path broke after vault rename (copper→Vault) on 2026-04-02. SessionStart RAG retrieval silently fails every session. Discovered during memory.db audit.",
  "reported_by": "admin@hm4"
}
JSON
# → 🐛 BUG-018 reported: memory-retrieve.py uses wrong DB path since vault rename
```

Fix:

```bash
python3 ~/Vault/repos/vault-scripts/db-exporters/bugs_tsv_io.py fix BUG-018 \
  --fixed-by admin@hm4 \
  --message "Deleted memory.db system entirely. Replaced with handover.jsonl + /handover skill. Hook now uses ~/Vault/_data/handover.jsonl."
# → ✅ BUG-018 fixed: ...
```
