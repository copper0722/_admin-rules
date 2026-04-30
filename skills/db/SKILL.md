---
type: data
name: db
description: "Database management skill. Use when creating, modifying, querying, or auditing PostgreSQL-backed structured data. Covers schema design, 3NF, migrations, import protocols, and auditability."
---

# Database Management

This public skill describes database design principles only. Private DSNs, hostnames, credentials, table inventories, and migration targets belong in the private operations repo.

## Core Rules

1. Prefer PostgreSQL for canonical structured data.
2. Every table has a primary key.
3. Normalize to 3NF unless a documented read model is intentionally denormalized.
4. Use explicit foreign keys for durable relationships.
5. Store source/provenance and timestamps on imported entities.
6. Preserve raw input in an appropriate private/raw layer before transformation.
7. Migrations are idempotent and reviewable.
8. Destructive schema changes require an explicit archival/export plan.

## Schema Design Protocol

1. Define the question the schema answers.
2. Identify entities and relationships.
3. Choose primary keys and natural unique constraints.
4. Define foreign keys and conflict policy.
5. Add provenance fields (`source`, `origin`, `created_at`, `updated_at`) where appropriate.
6. Add indexes for known query patterns.
7. Write migration SQL plus a rollback or archive note.
8. Register the writer/reader scripts in the private scheduler or service registry when applicable.

## Import Protocol

- Use upsert semantics, not delete-and-reinsert, unless the import is a documented full rebuild.
- Batch writes inside transactions.
- Record import source, row count, started/finished time, and error state.
- Keep canonical writes in one owner path or use explicit lease/conflict policy.

## Migration Checklist

- [ ] Migration is idempotent.
- [ ] Existing readers remain compatible or are updated in the same change.
- [ ] Constraints match the intended conflict policy.
- [ ] Backfill script is bounded and logged.
- [ ] Verification query is included.
- [ ] Private deployment details are not committed to public repos.
