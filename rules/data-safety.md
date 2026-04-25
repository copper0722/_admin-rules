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
- `/handover write` → INSERT into PG `vault_main.handover` on hmj:5432 (canonical since 2026-04-25; pglogical→cm1)
- Local-only fallback: `_data/handover.jsonl` for cloud CC + offline mbp/mba; bridge script drains to PG when device reconnects
- SessionStart hook auto-injects latest handover into context (reads PG primary, falls back to JSONL)
- Folder CLAUDE.md = rules + status board, not handover data
