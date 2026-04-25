---
type: data
name: bug
description: "Bugs merged into handover (Copper directive 2026-04-25). Use handover.bug column — no separate bugs table. To report: INSERT handover with bug='...', topic='bug: ...'. To fix: write done field (same or later handover row, typically by Codex daily review). MANDATORY TRIGGERS: /bug, bug, vault malformation, broken config, bad data, 'handover bug'."
---

# /bug — handover.bug column

`bugs` table dropped 2026-04-25; 57 historical bugs migrated to `handover` (agent='bug-migration'). Backup: `~/pg-backups-2026-04-25/bugs_pre_migrate.csv` on hmj.

## Report a bug

```bash
python3 ~/repos/_admin-private/.script/db-exporters/handover_pg_io.py append <<'JSON'
{
  "date": "2026-04-25",
  "device": "hm4",
  "agent": "claude-opus-4-7[1m]",
  "operator": "Wang",
  "role": "admin",
  "topic": "bug: short title <80c",
  "bug": "what's wrong + how discovered + expected vs actual",
  "comment": "severity=major | component=admin"
}
JSON
```

## List open bugs

```sql
SELECT id, date, device, topic, bug
FROM handover
WHERE bug IS NOT NULL AND done IS NULL
ORDER BY id DESC;
```

## Fix a bug

Two options:

1. **Same row (immediate fix)**: report + fix in single handover row — fill both `bug` and `done`
2. **Later row (Codex daily review or follow-up)**: new handover with `done='reference to original handover #N + fix description'`; original row's `bug` stays

```sql
-- mark fixed via UPDATE on original row (rare; usually new row instead)
UPDATE handover SET done='fix description', comment=COALESCE(comment,'') || ' | fixed_at=' || NOW()::text
WHERE id = ?;
```

## Severity / component / status

Encode in `comment` field as pipe-delimited tags:
`severity=critical|major|minor | component=admin|wiki|hooks|... | status=open|fixing|fixed|wontfix`

## Auto-report triggers (agent obligation)

When agent encounters during normal work:
- Hook returns error
- Script in CLAUDE.md missing
- DB path / config broken
- CLAUDE.md references deleted/moved files
- Cron log shows ERROR
- Broken symlink
- Frontmatter missing required fields

→ Report bug immediately. Fix if trivial. Defer (next_priorities + bug fields) if complex.

## Cross-device

Always write to PG hmj single-writer (handover_pg_io auto). pglogical replicates to cm1. mbp/mba: same — PG via Tailscale. Cloud CC offline: jsonl fallback (handover_pg_io auto-falls back), bridge drains.

Input: $ARGUMENTS
