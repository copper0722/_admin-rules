---
type: data
name: bug
description: "Public bug-reporting contract. Private database tables, hostnames, backup paths, and scripts are intentionally omitted."
---

# /bug - Public Contract

Report bugs as structured records in the configured private issue or handover backend.

## Required Fields

```json
{
  "topic": "bug: short title",
  "severity": "critical|major|minor",
  "component": "repo/module/system",
  "expected": "what should happen",
  "actual": "what happened",
  "evidence": "command/log/path/line reference",
  "next_action": "concrete repair step"
}
```

## Rules

- Fix trivial local bugs immediately.
- For non-trivial bugs, leave enough evidence for a cold-start agent to reproduce.
- Do not publish private paths, credentials, tokens, patient data, or proprietary source text in public bug records.
- Resolve only after verification.

