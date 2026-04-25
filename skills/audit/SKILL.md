---
type: data
name: audit
description: "Run the integrated audit program. Pulls task from PG vault_main.quality_audit_tasks queue, executes handler in _admin-private/audit/scripts/, writes findings to audit_findings. Two tracks: mechanical (script→LLM-fix) + semantic (LLM-audit→LLM-fix). MANDATORY TRIGGERS: /audit, audit, vault audit."
---

# /audit — Integrated audit program

Master plan: `~/repos/_admin-private/audit/CLAUDE.md` (read first; everything below is summary).

## Quick actions

```bash
# manual fire (one task)
bash ~/repos/_admin-private/audit/scripts/dispatcher.sh

# query open findings
psql -h hmj -U copper -d vault_main -c "
  SELECT id, audit_name, scope, metric_value, threshold
  FROM audit_findings WHERE resolved_at IS NULL
  ORDER BY severity DESC, metric_value DESC LIMIT 20;
"

# resolve a finding after fix
psql -h hmj -U copper -d vault_main -c "
  UPDATE audit_findings
  SET resolved_at = now(), resolved_by = '${USER}@$(hostname -s)', resolution_note = '...'
  WHERE id = ?;
"
```

## Add new audit

See `_admin-private/audit/CLAUDE.md` § Self-renewal protocol.

Input: $ARGUMENTS
