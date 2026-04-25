---
type: data
name: bug
description: "Vault issue tracker — report, fix, and close bugs in PG `vault_main.bugs` on hmj:5432 (canonical since 2026-04-25 per Copper directive; replicated to cm1 via pglogical). Use when agent finds vault malformation, broken config, bad data, or user says /bug."
---

# /bug

Vault = repo. Malformation found → report first, fix second, record stays.

**Usage:**
- `/bug report` → register new bug (returns `BUG-{NNN}`)
- `/bug fix BUG-XXX` → fix the bug, record what was done
- `/bug list` → show open bugs
- `/bug BUG-XXX` → show detail
- `/bug wontfix BUG-XXX {reason}` → close without fix

**Master storage** = PG `vault_main.bugs` on hmj:5432 (Phase-9d 2026-04-25; generalises BUG-053 + BUG-056).
- Local DML to `vault_main.bugs` on hmj; pglogical replicates to cm1.
- Legacy `~/VaultBinary/_data/bugs.tsv` archived 2026-04-25 to `_archive/2026-04-25_phase9d_category_a_retire/` (frozen at BUG-037; PG took over from BUG-038).
- Pre-PG SQLite master `bugs.db` retired 2026-04-18 (`_archive/bugs_sqlite_retired_20260418.zip`).

**Canonical access** = `ssh hmj "psql -h localhost -p 5432 -U copper -d vault_main"`. cm1 can also read locally (replica). For WRITE: always target hmj (single-writer); pglogical 2.x replicates DML automatically.

---

## TABLE SCHEMA (`vault_main.bugs`)

13 columns. All TEXT except `_pg_id` (BIGINT auto). Identical column set to legacy TSV plus PG primary key.

| # | column | type | description |
|---|---|---|---|
| 1 | `_pg_id` | bigint | auto-sequence PK |
| 2 | `id` | text | matches numeric of `bug_id` (e.g. `55`) |
| 3 | `bug_id` | text | `BUG-{NNN}` zero-padded |
| 4 | `title` | text | < 80 chars |
| 5 | `severity` | text | `critical` / `major` / `minor` |
| 6 | `component` | text | vault area (admin, wiki, raw, copper, proj, _data, cron, hooks, law, scripts, governance) |
| 7 | `description` | text | what's wrong + how discovered + expected vs actual |
| 8 | `fix_description` | text | filled on fix/wontfix |
| 9 | `status` | text | `open` / `fixing` / `partial` / `fixed` / `wontfix` |
| 10 | `reported_by` | text | `{agent}@{device}` |
| 11 | `fixed_by` | text | `{agent}@{device}` |
| 12 | `reported_at` | text | ISO timestamp |
| 13 | `fixed_at` | text | ISO timestamp |

If `description` or `fix_description` exceeds reasonable readability, spin body out to `_admin-private/admin/bugs/{bug_id}.md` and reduce the cell to a pointer. PG TEXT has no hard cap so this is purely a hygiene rule.

---

## REPORT

Agent discovers vault malformation → MUST report before fixing.

```bash
# 1. Get next bug_id
NEXT=$(ssh hmj "psql -h localhost -p 5432 -U copper -d vault_main -tAc \"SELECT 'BUG-' || lpad((COALESCE(MAX(NULLIF(regexp_replace(bug_id,'[^0-9]','','g'),''))::int,0)+1)::text, 3, '0') FROM bugs;\"")
echo "next: $NEXT"

# 2. INSERT (use $tag$ ... $tag$ dollar-quoting for descriptions with apostrophes)
REPORTED_AT=$(date -Iseconds)
ssh hmj "psql -h localhost -p 5432 -U copper -d vault_main" <<SQL
INSERT INTO bugs (id, bug_id, title, severity, component, description, status, reported_by, reported_at) VALUES (
  '${NEXT#BUG-}',  -- numeric portion
  '$NEXT',
  'short title <80c',
  'major',
  'component',
  \$desc\$what's wrong + how discovered + expected vs actual\$desc\$,
  'open',
  'admin@hm4',
  '$REPORTED_AT'
);
SQL
echo "🐛 $NEXT reported"
```

**Severity guide:**
- `critical`: data loss risk, pipeline halted, hook/cron broken, DB corruption
- `major`: wrong output, missing required fields, broken cross-references, stale config
- `minor`: naming convention violation, cosmetic, non-blocking inconsistency

---

## FIX

No fix without bug_id. This is the law.

```bash
# 1. Read bug
ssh hmj "psql -h localhost -p 5432 -U copper -d vault_main -c \"SELECT bug_id, status, severity, title FROM bugs WHERE bug_id = 'BUG-NNN';\""

# 2. (optional) Mark in-progress
ssh hmj "psql -h localhost -p 5432 -U copper -d vault_main -c \"UPDATE bugs SET status='fixing' WHERE bug_id = 'BUG-NNN';\""

# 3. Do the fix.

# 4. Close
FIXED_AT=$(date -Iseconds)
ssh hmj "psql -h localhost -p 5432 -U copper -d vault_main" <<SQL
UPDATE bugs SET
  status = 'fixed',
  fix_description = \$fix\$what was changed (files, lines, commands)\$fix\$,
  fixed_by = 'admin@hm4',
  fixed_at = '$FIXED_AT'
WHERE bug_id = 'BUG-NNN';
SQL
echo "✅ BUG-NNN fixed"
```

5. **Meta-check (Law §2.5)**: same issue elsewhere? If yes → report new BUG for each instance.

`partial` status is also valid — when only part of the issue is fixed and rest is pending. Use `fix_description` to record what's done + what's still open.

---

## LIST

```bash
# Open bugs
ssh hmj "psql -h localhost -p 5432 -U copper -d vault_main -c \"SELECT bug_id, severity, title FROM bugs WHERE status IN ('open','fixing','partial') ORDER BY CASE severity WHEN 'critical' THEN 1 WHEN 'major' THEN 2 WHEN 'minor' THEN 3 END, reported_at ASC;\""

# Open critical only
ssh hmj "psql -h localhost -p 5432 -U copper -d vault_main -c \"SELECT bug_id, title FROM bugs WHERE status IN ('open','fixing','partial') AND severity='critical' ORDER BY reported_at ASC;\""

# JSON for machine consumers
ssh hmj "psql -h localhost -p 5432 -U copper -d vault_main -tAc \"SELECT json_agg(row_to_json(bugs)) FROM bugs WHERE status='open';\""
```

---

## WONTFIX

For bugs that are by design or not worth fixing:

```bash
ssh hmj "psql -h localhost -p 5432 -U copper -d vault_main" <<SQL
UPDATE bugs SET
  status = 'wontfix',
  fix_description = \$reason\$reason for closing without fix\$reason\$,
  fixed_by = 'admin@hm4',
  fixed_at = '$(date -Iseconds)'
WHERE bug_id = 'BUG-NNN';
SQL
```

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

| device | read | write |
|---|---|---|
| **hm4** | direct local psql or `ssh hmj psql` | `ssh hmj psql` (single-writer rule §3.4) |
| **hmj** | direct local psql | direct local psql (PG primary) |
| **cm1** | direct local psql (pglogical replica) OR `ssh hmj` | `ssh hmj psql` (no app-layer write to replica) |
| **mbp/mba** | `ssh hmj psql` when online | `ssh hmj psql` when online; offline → JSONL fallback (TBD spec; bridge drains on reconnect) |
| **Cloud CC** | no PG reach (sandbox) | append `bug-{ts}.json` to `_admin-private/admin/bugs_inbox/` (or similar drop-zone); local cron drains to PG on next sweep |

Concurrent writes are safe — PG handles row-level locks.

---

## EXAMPLE

Report:

```bash
NEXT="BUG-058"
ssh hmj "psql -h localhost -p 5432 -U copper -d vault_main" <<SQL
INSERT INTO bugs (id, bug_id, title, severity, component, description, status, reported_by, reported_at) VALUES (
  '58', '$NEXT',
  'memory-retrieve.py uses wrong DB path since vault rename',
  'critical', 'hooks',
  \$d\$memory-retrieve.py hardcodes ~/copper/admin/memory/memory.db. Path broke after vault rename (copper→Vault) on 2026-04-02. SessionStart RAG retrieval silently fails every session. Discovered during memory.db audit.\$d\$,
  'open', 'admin@hm4', '$(date -Iseconds)'
);
SQL
```

Fix:

```bash
ssh hmj "psql -h localhost -p 5432 -U copper -d vault_main" <<SQL
UPDATE bugs SET
  status = 'fixed',
  fix_description = \$f\$Deleted memory.db system entirely. Replaced with PG vault_main.handover + /handover skill. Hook now reads PG with JSONL fallback.\$f\$,
  fixed_by = 'admin@hm4',
  fixed_at = '$(date -Iseconds)'
WHERE bug_id = 'BUG-058';
SQL
```

---

## Legacy helper (retired)

`_admin-private/.script/db-exporters/bugs_tsv_io.py` was the TSV writer pre-Phase-9d. Retained for historical TSV reading only — DO NOT USE for new bugs (writes to archived path). A PG-canonical helper `bugs_pg_io.py` may be authored later for ergonomic CLI parity with `handover_pg_io.py`; until then, use direct psql as above.
