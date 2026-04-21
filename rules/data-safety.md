# data-safety

## No deletion (§1.3)
- never delete files; archive to `_archive/` instead
- archived .md MUST be zipped (unsearchable = resource saving)
- unzipped .md in `_archive/` = pending review: read → extract useful info → zip
- content cleanup (done TODOs, stale entries) = normal maintenance, allowed

## Save raw first (§1.8)
- receive input → save raw immediately, process/clean later
- never discard input data during ingestion
- secondary analysis/cleaning only by explicit command

## Git + mtime (§1.4)
- git = change log (audit trail)
- filesystem mtime = real-time ground truth; trust mtime over commit timestamps

## Session continuity (§1.9)
- `/handover write` → append `_data/handover.jsonl` (Category A plain-text master since 2026-04-18)
- SessionStart hook auto-injects latest handover into context
- Folder CLAUDE.md = rules + status board, not handover data
