# db-lookup

## Agent data lookup order (§8.4)
Always query in this order; stop when answer found:

1. `agent_lookup.db` (`_data/`) — cross-DB search: any key (NHI code, ATC code, drug permit, citation key) → all DBs/tables containing it + row preview + cross-DB relations; 104K keys indexed
2. `db_registry.db` (`_data/`) — which .db has what tables/columns
3. `proj/projects.db` — project meta-management (status, web update, scripts, TODO counts)
4. individual .db via path returned from above
5. file search → `rg` / `find`
6. bibliographic metadata → Zotero API + frontmatter (citations.db deleted)
7. **System ledgers** (Law §1.9): PG `vault_main` on hmj:5432 — `handover` (session continuity, /handover), `bugs` (vault issue tracker, /bug), `journals` (journal registry), `schedule_registry` (cron + launchd). Per Copper directive 2026-04-25 these moved out of `_data/*.{tsv,jsonl}` and are now PG-canonical. Agents INSERT to hmj (pglogical replicates to cm1); JSONL/TSV files are stale snapshots used only by cloud CC + offline laptops, drained back to PG by bridge script.

## Write authority
- hm4 = single-writer for main vault SQLite
- clinic DBs → BoAn vault owns writes; main vault = read-only via `~/VaultBinary/_data/` (Phase 9 OWC path)
- all SQLite ops follow `/db` skill spec (3NF, PK, sidecar .db.md, import/migration/audit)
