# db-lookup

## Agent data lookup order (§8.4)
Always query in this order; stop when answer found:

1. PostgreSQL domain tables declared by the private runtime card (handover,
   audit, schedule registry, raw index, journals, drug/gov references, project
   state). PG is canonical.
2. `wiki_raw.raw_index` for raw payload lookup by citation key, title, source
   type, tags, and `~/VaultBinary` relative path.
3. Zotero API + frontmatter for bibliographic metadata when PG lacks a row.
4. bounded file search → `rg` / `find` inside the relevant repo or
   `~/VaultBinary/{topic_path}`.
5. Historical SQLite/CSV/TSV exports only as read-only migration evidence; do
   not treat them as canonical and do not create new ones.
6. **System ledgers**: query the configured private backend for handover, bugs,
   journals, scheduler, and audit state. Public rules must not publish
   hostnames, DSNs, replication topology, or private fallback paths.

## Write authority
- The private runtime declares write authority per database.
- Public rules may define normalization, provenance, and audit principles, but not private database endpoints.
- Prefer structured PG-backed state over ad hoc CSV/TSV snapshots.
