---
type: data
name: audit
description: "Public audit-loop contract. Private task queues, scripts, database endpoints, and scheduler details are intentionally omitted."
---

# /audit - Public Contract

An audit loop detects recurrent system or content-quality failures, records findings in the configured private issue queue, and requires verified repair before resolution.

## Invariants

- Do not accept prose promises as implementation.
- Verify the runtime behavior that is claimed.
- Do not resolve a finding until the fix is observed.
- Keep private scheduler names, hostnames, database endpoints, Slack routes, and script paths out of public rules.

## Finding Shape

```json
{
  "audit_name": "short stable name",
  "scope": "repo/module/path",
  "severity": "info|warning|major|critical",
  "evidence": "specific observable failure",
  "expected": "contract that should hold",
  "repair_owner": "role or lane",
  "resolved_at": null
}
```

Private implementations may map this contract to their own database, queue, or issue tracker.

