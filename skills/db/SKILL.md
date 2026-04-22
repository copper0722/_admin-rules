---
type: data
name: db
description: "Database management skill. Use when creating, modifying, querying, or auditing any SQLite database in the vault. Covers schema design, 3NF enforcement, sidecar docs, rebuild scripts, and import protocols. MANDATORY TRIGGERS: /db, create table, new database, schema change, import data, db audit, 建資料庫, add column, migration."
---

# Database Management

All vault SQLite databases follow §10.8 (3NF + vault rules). This skill provides the full protocol.

## §10.8 Core Rules (from Vault Rules)

1. **Third Normal Form (3NF).** Every non-key column depends on the key, the whole key, and nothing but the key. No derived/computable values stored — compute at query time.
2. **Every table MUST have a PRIMARY KEY.** Composite PKs for junction tables.
3. **EAV for heterogeneous multi-source data.** Variable attribute sets → `(entity_id, property_key, value)` + `properties` master table.
4. **Multi-source dedup at import, priority at query.** Same concept from different sources → one canonical key. Priority resolved at query time (`ROW_NUMBER() OVER (PARTITION BY key ORDER BY priority)`).
5. **`source` + `updated`** on every entity/reference table.
6. **All raw source data preserved.** Never discard input during ingestion (Law §1.8).

## Sidecar Documentation

Every `.db` file MUST have a sidecar `{name}.db.md` in the same directory.

```yaml
---
description: "one-line description"
source: "data origin URL or method"
schema_version: "YYYYMMDD"
writer: "hm4"
---
```

Body: all tables, PKs, source per column, rebuild command.

## Schema Design Protocol

When creating or modifying a database:

1. **Define purpose** — what question does this DB answer?
2. **Identify entities** — each real-world thing = one table
3. **Normalize to 3NF** — remove redundancy, derived fields
4. **Add metadata columns**: `source TEXT`, `updated TEXT DEFAULT CURRENT_TIMESTAMP`
5. **Create indexes** for frequent query patterns
6. **Write sidecar .db.md** immediately
7. **Write rebuild script** → `repos/vault-scripts/build-{name}.py` with docstring (§10.7)

## Import Protocol

```python
# Standard import pattern
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA foreign_keys=ON")

# Upsert pattern (preserve existing, update on conflict)
conn.execute("""
    INSERT INTO {table} ({cols}) VALUES ({placeholders})
    ON CONFLICT({pk}) DO UPDATE SET
        {col}=excluded.{col}, updated=CURRENT_TIMESTAMP
""")
conn.commit()
conn.close()
```

Rules:
- Always `WAL` journal mode (concurrent reads)
- Always `foreign_keys=ON`
- Upsert, never DELETE + re-INSERT (preserves history)
- Batch commits (every 1000 rows)
- Log import: `INSERT INTO import_log (source, rows, timestamp) VALUES (?, ?, datetime('now'))`

## Query Protocol

- Read-only access: `sqlite3.connect(f"file:{path}?mode=ro", uri=True)`
- Dashboard server uses read-only for all queries
- Only SELECT allowed from API endpoints (server.py enforces this)

## Current Vault Databases

| db | location | tables | description |
|---|---|---|---|
| memory.db | admin/memory/ | raw_sessions, compiled_memory, sync_log | Session memory system |
| fb.db | proj/fb/data/ | posts, media, comments, posts_fts, page_insights | FB fan page archive |
| food_db.db | proj/food-db/data/ | categories, properties, foods, food_properties, food_portions, calorie_factors, food_inputs | Multi-national food composition |
| clinic_drugs.db | proj/clinic/emr/data/ | drugs, nhi_drugs, ref_atc, ref_dosage_form, ref_pricing_form, ref_ingredient_code, ref_permit_ingredient, ref_permit | Clinic drug formulary |
| nhi_drug_formulary.db | proj/nhi/ | drugs, drug_ingredients | NHI drug list |
| nhi_drug_permits.db | proj/nhi/ | permits, permit_manufacturers | TFDA drug permits |
| nhi_payment_standard.db | proj/tsn/data/ | payment_standard | NHI payment codes |
| events.db | proj/rss-digest/data/ | events, feeds | RSS digest pipeline |
| transactions.db | copper/finance/ | transactions | Personal finance |

## Migration Protocol

When changing schema on existing DB:

1. **Never DROP TABLE.** Add columns (`ALTER TABLE ADD COLUMN`), never remove.
2. **Version in sidecar**: bump `schema_version` in .db.md
3. **Migration script**: write idempotent SQL (check before alter)
```python
# Check if column exists before adding
cols = [c[1] for c in conn.execute(f"PRAGMA table_info({table})").fetchall()]
if 'new_col' not in cols:
    conn.execute(f"ALTER TABLE {table} ADD COLUMN new_col TEXT")
```
4. **Backward compatible**: old code must still work after migration

## Audit Checklist (L4)

- [ ] Every table has PRIMARY KEY
- [ ] No derived/computed columns stored
- [ ] `source` + `updated` fields present
- [ ] Sidecar .db.md exists with correct frontmatter
- [ ] Rebuild script exists in repos/vault-scripts/
- [ ] WAL mode enabled
- [ ] Foreign keys defined where applicable
