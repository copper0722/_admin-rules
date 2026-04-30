# db-lookup

## Agent data lookup order (§8.4)
Always query in this order; stop when answer found:

1. `agent_lookup.db` (`_data/`) — cross-DB search: any key (NHI code, ATC code, drug permit, citation key) → all DBs/tables containing it + row preview + cross-DB relations; 104K keys indexed
2. `db_registry.db` (`_data/`) — which .db has what tables/columns
3. `proj/projects.db` — project meta-management (status, web update, scripts, TODO counts)
4. individual .db via path returned from above
5. file search → `rg` / `find`
6. bibliographic metadata → Zotero API + frontmatter (citations.db deleted)
7. **System ledgers**: query the configured private backend for handover, bugs, journals, scheduler, and audit state. Public rules must not publish hostnames, DSNs, replication topology, or private fallback paths.

## Write authority
- The private runtime declares write authority per database.
- Public rules may define normalization, provenance, and audit principles, but not private database endpoints.
- Prefer structured backends over ad hoc CSV/TSV for canonical state.
