---
type: data
name: handover
description: "Session handover contract. Public version intentionally omits private hosts, databases, paths, and schemas. MANDATORY TRIGGERS: /handover, handover, session end, 交接, 收工, /ho, /HO."
---

# /handover - Public Contract

Handover records preserve continuity between agent sessions. This public card defines the record semantics only. Private storage endpoints, database schemas, replication topology, scripts, and fallback paths belong in the private operations repo.

## Read Contract

At session start, read the latest relevant handover from the configured private runtime. Prioritize:

1. Blockers and unresolved bugs.
2. Next priorities.
3. Decisions and rationale.
4. Completed work summary.

## Write Contract

At session end, write one structured record:

```json
{
  "date": "YYYY-MM-DD",
  "device": "runtime-device",
  "agent": "agent/model",
  "operator": "human|auto",
  "role": "admin|wiki|secretary|clinic|meta|other",
  "topic": "one-line summary",
  "completed": "specific work completed",
  "decisions": "decisions with rationale",
  "blocked": "blockers, if any",
  "next_priorities": "actionable next steps"
}
```

## Rules

- Do not write private credentials, tokens, patient data, or proprietary source text into handover.
- If the configured private handover backend is unavailable, use the private fallback declared by the runtime environment.
- Public repos may describe the shape of handover records, not the private infrastructure that stores them.

