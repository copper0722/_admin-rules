---
type: data
name: cm1-audit
description: "Public template for an independent daily drift audit. Private device names, mounts, database endpoints, and dispatch paths belong in the private operations repo."
argument-hint: "[today|weekly|since=YYYY-MM-DD]"
---

# /cm1-audit - independent drift audit template

This public skill describes the audit shape only. A private deployment must provide device names, mount paths, handover backend, scheduler registration, and notification targets.

## Purpose

Run an independent daily audit from a secondary device or fallback worker. The auditor detects drift and writes findings to the configured private dispatch/handover backend; it does not silently mutate production state.

## Scope

**In scope**

- Missing files referenced by active instruction cards.
- Scheduler registry drift.
- Repeated scheduled-job failures.
- Handover freshness.
- Stale exported snapshots or generated status files.
- Excessive sync conflicts.
- Broken symlinks in the bounded workspace.
- Root-level folder pollution in the bounded workspace.
- Open bug/audit backlog trend.

**Out of scope**

- Medical/content quality review unless explicitly assigned.
- Direct scheduler mutation.
- Direct database writes from unreliable mounts.
- Editing other agents' cards without a private dispatch or approval path.

## Daily protocol

### Phase 1 - Read context

```bash
pwd
git status --short
git log --since="25 hours ago" --pretty=format:"%h %ai %s" | head -30
```

Read the configured handover backend and the project-local `AGENTS.md` chain.

### Phase 2 - Drift detection

Run each check and record evidence:

| # | check | method |
|---|---|---|
| 1 | instruction-card references exist | grep referenced files, verify with bounded `ls` |
| 2 | scheduler registration | compare scheduler inventory with registry |
| 3 | scheduler failures | scan bounded logs for `ERROR`, `FAIL`, `Traceback` |
| 4 | inbox/orphan backlog | count age and volume under configured inbox |
| 5 | handover freshness | parse latest handover timestamp |
| 6 | generated snapshot freshness | compare expected artifacts with mtime SLA |
| 7 | sync conflicts | count conflict-file patterns in bounded workspace |
| 8 | broken symlinks | bounded `find <workspace> -type l ! -exec test -e {} ; -print` |
| 9 | root pollution | compare top-level entries with allowed list |
| 10 | open audit backlog | count open findings and aging |

### Phase 3 - Write dispatch

Write findings through the configured private backend with:

```markdown
# Dispatch: Daily drift audit YYYY-MM-DD

## HIGH
- **{check}: {finding}** - path: `{path}`; evidence: `{line/cmd output}`; suggested fix: `{action}`

## MED
- ...

## LOW
- ...

## Healthy
- ...
```

Severity:

- HIGH = data-loss risk, blocked pipeline, missing active dependency, repeated failure.
- MED = drift affecting agent reasoning or scheduled reliability.
- LOW = cosmetic or cleanup.

## Constraints

- Search only bounded workspaces.
- Do not expose private mount paths, hostnames, database names, credentials, or notification targets in public rules.
- Public repo output is a template; private repo owns deployment details.
