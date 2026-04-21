# db-lookup

## Agent data lookup order (§8.4)
Always query in this order; stop when answer found:

1. `agent_lookup.db` (`_data/`) — cross-DB search: any key (NHI code, ATC code, drug permit, citation key) → all DBs/tables containing it + row preview + cross-DB relations; 104K keys indexed
2. `db_registry.db` (`_data/`) — which .db has what tables/columns
3. `proj/projects.db` — project meta-management (status, web update, scripts, TODO counts)
4. individual .db via path returned from above
5. file search → `rg` / `find`
6. bibliographic metadata → Zotero API + frontmatter (citations.db deleted)
7. **System masters** (Law §1.9, Vault §8.4 Category A): `_data/handover.jsonl` (session continuity), `_data/bugs.tsv` (vault issue tracker), `_data/journals.tsv` (journal registry) — plain text, not data lookup. Agents read/write via `/handover` and `/bug` skills or the helpers in `repos/vault-scripts/db-exporters/`.

## Write authority
- hm4 = single-writer for main vault SQLite
- clinic DBs → BoAn vault owns writes; main vault = read-only via `~/Library/CloudStorage/Dropbox/Vault_Sidecar/_data/`
- all SQLite ops follow `/db` skill spec (3NF, PK, sidecar .db.md, import/migration/audit)
