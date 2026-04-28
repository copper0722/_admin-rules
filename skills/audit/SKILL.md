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

## Control-plane RCA / closed-loop invariant review

Use this section when Copper asks to review a system bug, RCA, scheduler drift, audit/repair loop, token-gate failure, launchd incident, or any claim that a control-plane contract exists but is not being enforced.

Class-first rule: do not accept prose/prompt promises as implementation. Verify the runtime invariant live.

Checklist:

1. Read the RCA/report and identify the claimed contract, owner boundary, and acceptance criteria.
2. Query PG evidence directly (`quality_audit_tasks`, `audit_findings`, `handover`) and inspect live launchd/process state on the claimed scheduler host.
3. Inspect routing/selectors/wrappers, not just task names. Check both sides of the boundary: the producer lane must exclude work it should not own, and the auditor/consumer lane must positively claim only its own work.
4. Run the counterfactual test: if the proposed alternate cause were sufficient (e.g. host crash, token gate, single failed task), what liveness marker or finding should still exist? Verify whether it exists.
5. Do not resolve a critical control-plane finding merely because an RCA/report exists. Require runtime proof: active scheduler, corrected PG ownership/metadata, sentinel coverage, and at least one observed closed-loop cycle where output is produced, consumed, repaired, and reviewed.
6. Write a follow-up handover documenting the independent review and whether the finding remains open.

For Codex-Claude closed-loop incidents specifically, verify: independent Codex launchd (no Claude token dependency), mutually exclusive Claude-vs-Codex task selectors, `llm_handover_review`/repair-loop tasks owned by Codex, `codex_closed_loop_health` script-lane sentinel, and a later Codex review after Claude repair before resolving the finding.

## Add new audit

See `_admin-private/audit/CLAUDE.md` § Self-renewal protocol.

Input: $ARGUMENTS
