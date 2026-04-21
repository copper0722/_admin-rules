---
name: audit
description: "Sequential vault audit loop L1→L2→L3→L4→L1... Each level fixes previous findings then audits own scope. Cron or manual. MANDATORY TRIGGERS: /audit, audit, vault audit, weekly audit."
argument-hint: "[L1|L2|L3|L4|loop|all]"
---

# /audit — Sequential Vault Integrity Audit

Continuous loop: L1→L2→L3→L4→L1→... Each pass: fix previous level's findings → audit own scope → report.

## Execution Model

| mode | trigger | behavior |
|---|---|---|
| `/audit L2` | manual | run single level |
| `/audit loop` | cron Tue 3-8AM | sequential L1→L2→L3→L4, repeat if time remains |
| `/audit all` | manual | full L1→L4 single pass |

## Loop Protocol

```
Start at L{N} (state from admin/_admin_state.md `last_audit_level`):
  1. Read admin/audit/CLAUDE.md → find L{N-1}'s latest report
  2. FIX all mechanical issues from L{N-1} (stale counts, misplaced files, broken paths)
     Skip judgment calls — report only
  3. EXECUTE L{N} audit checks (see Checklist below)
  4. Write L{N} report section in admin/audit/CLAUDE.md (replace previous)
  5. Update admin/_admin_state.md: last_audit_level=N, last_audit=datetime
  6. Advance: N = (N % 4) + 1 → loop to step 1
  7. Stop when: time budget exceeded OR Copper interrupts OR full cycle complete
```

## Level Checklists

### L1 — Governance (Law, Book, Code, Index, Vault Rules)
- Stale §-refs: grep section numbers → verify exist
- Contradictions: cross-compare definitions, codecs, counts
- Line limits: Law <80L, Book <200L
- Outdated facts: project/skill/device counts vs actual
- Broken paths: spot-check 5 referenced files
- Cross-file consistency: definitions, tables must match
- Spot-check: always _bootstrap.md + rotate 4 referenced files

### L2 — Cards (all CLAUDE.md, excl _archive/)
- §1.1 M2M language compliance
- §10.9 structure: ## TODO + ## Changelog + ## Notes
- TODO format: type:mode (date) compliance
- Oversized >150L → recommend split
- Card vs folder drift: git log --since=7d vs card claims
- Dispatch status: [x]>3d clean, [ ] no activity 7d flag
- Stale paths, wrong counts, removed features

### L3 — Structure (raw/, kb/, proj/*, copper/)
- Folder >15 items → flag condense
- §9.1 missing summary (.md >500L without summary: frontmatter)
- §9.2 oversized (.md >2000L → flag split)
- Broken wikilinks
- Frontmatter integrity (raw/articles/: title, citationKey, tags)
- Non-.md violations outside sidecar/data/
- §10.10 misplaced files, unprocessed raw, semantic duplicates

### L4 — Data Integrity (SQLite, scripts, cron, automation)
- DB 3NF compliance
- Sidecar .db.md exists for every .db
- Script descriptions (§10.7): .py docstring, .sh comment
- Cron/launchd health: parse /tmp/*.log for ERROR
- Dashboard-scanner mtime freshness
- Git autocommit functioning

## Output

Each level writes to `admin/audit/CLAUDE.md`:
```markdown
### L{N} Report ({date}, round {R})

**Fixed from L{N-1}**: {count} items
**Findings**: {count} — {severity breakdown}
- [severity] {finding}: {detail}
**Burned**: {vault-todo item executed, if time remained}
```

Append one-line to Changelog: `{date} | L{N} r{R}: {summary}`

## Rules
- M2M compressed English output
- Fix mechanical issues silently. Report judgment calls.
- Never skip a level in loop — sequential is the point (each level QAs the previous)
- Codex review: on L4, run `codex exec` for code quality second opinion (if available)
- Time budget: ~45min per level in cron mode

Input: $ARGUMENTS
