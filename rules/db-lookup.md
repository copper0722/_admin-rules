# db-lookup

## Agent data lookup order (§8.4)
Always query in this order; stop when answer found:

1. PostgreSQL domain tables declared by the private runtime card (handover,
   audit, schedule registry, raw index, journals, drug/gov references, project
   state). PG is canonical.
2. `wiki_raw.raw_index` for raw payload lookup by citation key, title, source
   type, tags, and corpus bundle path
   (`~/agent-share/<subtype>/<source_uid>/`; vault retired
   2026-05-22).
3. Zotero API + frontmatter for bibliographic metadata when PG lacks a row.
4. bounded file search → `rg` / `find` inside the relevant repo, usually
   `~/agent-share/<subtype>/` for knowledge-corpus payloads
   (vault retired 2026-05-22; corpus = canonical).
5. Historical SQLite/CSV/TSV exports only as read-only migration evidence; do
   not treat them as canonical and do not create new ones.
6. **System ledgers**: query the configured private backend for handover, bugs,
   journals, scheduler, and audit state. Public rules must not publish
   hostnames, DSNs, replication topology, or private fallback paths.

## Semantic / conceptual retrieval (knowledge corpus)

The numbered ladder above finds a *known* structured row. For a *conceptual*
clinical / medical question ("what does the corpus say about X"), prefer
semantic retrieval over ad-hoc `rg`: use the private runtime's unified
corpus-retrieve entrypoint, which runs three axes over the local corpus —
dense-vector (pgvector), full-text (Postgres FTS), and a textbook-TOC index —
merges/ranks them, and **logs every query** so retrieval efficacy is
measurable. Vector is the primary recall path for zh-TW (the FTS config does
not segment CJK). The concrete command, scope, and evidence layers live in the
private ops card; public rules keep the axis principle only.

## Write authority
- The private runtime declares write authority per database.
- Public rules may define normalization, provenance, and audit principles, but not private database endpoints.
- Prefer structured PG-backed state over ad hoc CSV/TSV snapshots.
