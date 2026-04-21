---
name: cm1-audit
description: "cm1 independent daily drift audit → dispatch to hm4. Designed for cm1 (SMB/NAS-mounted vault; SQLite writes unreliable over this mount so cm1 defaults to dispatch-hm4 for DB work). Use when Copper opens clinic Mac mini and types /cm1-audit, OR when launchd fires."
argument-hint: "[today|weekly|since=YYYY-MM-DD]"
---

# /cm1-audit — cm1 independent drift audit

cm1 = vault's **independent daily auditor** (Law §2.16). SMB/NAS-mounted vault — SQLite writes over this mount are unreliable (Dropbox+NAS+SMB 三層並發會損壞 DB)，非治理禁令而是物理限制。cm1 因此 de facto 走 "audit + dispatch" 路線：讀全庫，發現問題寫 dispatch 給 hm4 執行。Separation of powers: cm1 audits, hm4 executes fixes. Prevents self-review blindspot.

## Scope

**In** (flags drift → dispatch hm4):
- Law, Vault Rules, admin/CLAUDE.md, admin/INDEX.md, any folder CLAUDE.md — files mentioned but missing, stale timestamps, §9.1 / §9.2 line violations.
- `_data/schedule_registry.tsv` — cron/launchd entries not in registry (orphans) OR registry entries failing repeatedly.
- `_inbox/` orphans >7d (daily cleanup cron should drain; flag failure).
- `_data/handover.jsonl` freshness (latest entry >24h → agents not reporting).
- `_data/*.snapshot.tsv` age (stale → `export-category-c.sh` cron broken).
- `.obsidian/` conflict file count (>10 on cm1 side → device sync issue).
- Broken symlinks anywhere in Vault.
- Root-level file pollution (anything at Vault root outside the allowed set).

**Out of scope** (enforced by role):
- Content / wiki / note quality audits (that's vault-steward + note-writer).
- Medical / EBM checks (Opus lanes).
- SQLite / cron / launchd writes.
- Editing any folder CLAUDE.md (flag only; hm4 executes edit).

## Daily protocol

### Phase 1 — Read context (5 min)

```bash
# from cm1 SMB mount
cd /Volumes/dropbox-personal/Vault
# Law + Vault rules (auto-loaded by CC)
# Recent handover
tail -3 _data/handover.jsonl | python3 -c "import json,sys;[print(json.dumps(json.loads(l),indent=2,ensure_ascii=False)) for l in sys.stdin if l.strip()]"
# Recent commits
git log --since="25 hours ago" --pretty=format:"%h %ai %s" | head -30
# Recent bugs
python3 repos/vault-scripts/db-exporters/bugs_tsv_io.py list --status open
```

### Phase 2 — Drift detection (30 min)

Run each check → record finding if violated.

| # | check | method |
|---|---|---|
| 1 | Law length ≤80L | `wc -l ~/.claude/CLAUDE.md` (via Dropbox symlink on cm1) |
| 2 | Vault/CLAUDE.md refs exist | grep paths in file, verify with `ls`; flag missing |
| 3 | admin/CLAUDE.md + INDEX.md mentioned files exist | same pattern |
| 4 | folder CLAUDE.md drift | compare `git log --since=7d --stat -- {folder}/` vs card claims |
| 5 | `schedule_registry.tsv` orphans | `crontab -l` + `launchctl list com.copper.*` vs registry; flag unregistered jobs (cm1 cannot see crontab — document only jobs whose scripts exist but aren't registered) |
| 6 | `schedule_registry.tsv` failures | grep `/tmp/*.log` last 24h for `ERROR`, `FAIL`, `Traceback` |
| 7 | `_inbox/` orphan count | `ls _inbox/ --sort=time`; flag >20 items or any >7d |
| 8 | `handover.jsonl` freshness | `tail -1` → parse `created_at`; flag if >24h old |
| 9 | `*.snapshot.tsv` age | `ls _data/*.snapshot.tsv -l`; flag if mtime >36h |
| 10 | `.obsidian/` conflicts on cm1 | `find /Volumes/dropbox-personal/Vault/.obsidian -name '*衝突*' \| wc -l`; flag >10 |
| 11 | broken symlinks | `find /Volumes/dropbox-personal/Vault -type l ! -exec test -e {} \; -print \| head -30` |
| 12 | root pollution | `ls /Volumes/dropbox-personal/Vault/ \| grep -vE '^(_|admin/\|ref/\|proj/\|wiki/\|copper/\|BoAn/\|cloud/\|repos/\|CLAUDE\.md\|AGENTS\.md\|dashboard\.html\|dashboard-data\.json)$'` |
| 13 | bug backlog trend | count `open` bugs; flag if >10 or any older than 30d |
| 14 | handover agent silence | any agent with `agent='X'` that ran yesterday but no row today in `handover.jsonl` |

### Phase 3 — Write dispatch (5 min)

Output → `admin/_dispatch_hm4_audit_YYYYMMDD.md` with format:

```markdown
---
from: cm1 cm1-audit (YYYY-MM-DD)
to: hm4 admin (vault-steward)
priority: HIGH/MED/LOW
---

# Dispatch: Daily drift audit YYYY-MM-DD

## HIGH (fix today)
- **{check}: {finding}** — path: `{path}`; evidence: `{line/cmd output}`; suggested fix: `{action}`

## MED (fix this week)
- ...

## LOW (cleanup / cosmetic)
- ...

## Healthy (no action)
- Law length N lines (≤80 ✓)
- handover.jsonl latest: {id} {date} {agent}
- schedule_registry active: N / disabled: M
- (etc.)
```

Classify severity:
- HIGH = data loss risk, blocked pipeline, missing files referenced in active code, repeated failures
- MED = drift that affects agent reasoning (stale §-refs, oversized cards, stale snapshots)
- LOW = cosmetic (line counts slightly over target, minor pollution)

### Phase 4 — Commit + notify (2 min)

```bash
cd /Volumes/dropbox-personal/Vault
git add admin/_dispatch_hm4_audit_*.md
git commit -m "cm1-audit: YYYY-MM-DD drift report ({N} HIGH / {M} MED / {K} LOW)"
# git push handled by hm4's vault-git-autocommit (cm1 doesn't push)
```

If Slack MCP available, post 1-line summary to `#cloud-routines` (or Aiko DM):

```
🔎 cm1-audit YYYY-MM-DD — {N} HIGH / {M} MED / {K} LOW findings
Dispatch: admin/_dispatch_hm4_audit_YYYYMMDD.md
```

## Scheduling (revised 2026-04-18 16:00 — Copper directive)

**launchd daily 03:00 TST** (`admin/launchd/cm1/com.copper.cm1-audit.plist` → `cm1-audit.sh` → this skill). Requires: cm1 powered on + logged in + SMB mount `/Volumes/dropbox-personal/Vault/` mounted at 03:00.

Why 03:00: runs BEFORE 04:00 hm4 vault-steward. vault-steward reads this audit's dispatch file and executes fixes in same overnight window. hm4-morning-review (06:00) reads the combined output.

If cm1 is off/asleep at 03:00, launchd fires on next wake; audit may run late but still produces dispatch for next vault-steward cycle.

## Writing scope (enforced constraints)

cm1 CC can:
- Write `admin/_dispatch_hm4_audit_*.md` (append-only).
- Append `admin/vault-steward/questions/YYYY-MM-DD.md` entries IF the finding needs Copper judgment.
- Write to `_data/handover.jsonl` via `handover_jsonl_io.py append` (Category A helper — uses fcntl.flock, safe over SMB per §8.4).

cm1 CC CANNOT:
- Write SQLite (`_data/*.db`) — cm1 的 SMB/NAS 掛載無法穩定寫 SQLite（物理限制，non-governance）。任何 DB 寫入 → dispatch to hm4。
- Modify cron / launchd.
- Edit any folder CLAUDE.md directly (flag → dispatch → hm4 edits).
- Touch `copper/*` (personal data; cm1 respects Law §2.18).

## Budget

- Wall-clock: 45 min max (Phase 1 5 + Phase 2 30 + Phase 3 5 + Phase 4 2 + buffer).
- Token: 15k output.
- On hard failure (cannot read a file, cannot resolve path, etc.) → append to handover `blocked` field and exit; next day reviews.

## References

- Law §2.16 (three central daily agents)
- `admin/governance.md` §5 (admin loop) + §6.5 (cm1 as auditor)
- `ref/skills/audit/SKILL.md` (the weekly L1-L4 audit owned by vault-steward — different scope, different cadence)
- `admin/_dispatch_hm4_redundancy_purge_20260418.md` Phase 4.7 (original spec)
