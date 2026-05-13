# PG large open-data verification pattern

Use this when a user asks whether a download/API protocol matches an already-imported large corpus.

## Core lesson

Do not start by scanning the filesystem for JSONL/CSV/Parquet if the user's system canonicalizes structured data in PostgreSQL. First identify the canonical PG schema and verify row counts, catalog metadata, resource identifiers, and expected-vs-ingested totals.

## Verification workflow

1. List candidate schemas/tables:

```sql
select n.nspname||'.'||c.relname
from pg_class c
join pg_namespace n on n.oid=c.relnamespace
where c.relkind in ('r','p','m','v')
  and (
    n.nspname ilike '%open%'
    or n.nspname ilike '%nhi%'
    or n.nspname ilike '%tfda%'
    or c.relname ilike '%iode%'
    or c.relname ilike '%nhi%'
    or c.relname ilike '%tfda%'
  )
order by 1;
```

2. Inspect table list and columns for the target schema:

```sql
select tablename
from pg_tables
where schemaname = '<schema>'
order by tablename;

select table_name, column_name, data_type
from information_schema.columns
where table_schema = '<schema>'
order by table_name, ordinal_position;
```

3. Count rows table-by-table. Generate SQL first if many tables:

```sql
select format(
  'select %L as table_name, count(*)::bigint as rows from %I.%I;',
  table_name, table_schema, table_name
)
from information_schema.tables
where table_schema = '<schema>' and table_type = 'BASE TABLE'
order by table_name;
```

4. For catalog-backed open data, compare expected vs ingested counts:

```sql
select coalesce(sum(number_of_data),0)::bigint as expected_rows,
       count(*) filter (where number_of_data is not null) as datasets_with_counts,
       count(*) as datasets
from <schema>.<dataset_metadata_table>;

select resource_id, count(*)::bigint as rows
from <schema>.<records_table>
group by resource_id
order by rows desc
limit 25;
```

5. Only after PG verification should you reconcile against source API protocol, raw files, or download logs.

## Session example: Taiwan NHI/TFDA open data

Copper pointed out that the live corpus was in PG, specifically `tw_health_open`, not in filesystem dumps. The schema contained:

- `nhi_iode_catalog`
- `nhi_iode_dataset`
- `nhi_iode_records`
- `nhi_drug_formulary`
- `nhi_facility`
- `nhi_payment_standard`
- `tfda_catalog`
- `tfda_drug_permit`
- `tfda_drug_ingredient`
- `tfda_records`

Observed counts during the session:

- `nhi_iode_catalog`: 350
- `nhi_iode_dataset`: 350
- `nhi_iode_records`: 17,253,838
- `nhi_drug_formulary`: 224,261
- `nhi_facility`: 36,497
- `nhi_payment_standard`: 6,055
- `tfda_drug_permit`: 66,299
- `tfda_drug_ingredient`: 125,874
- `tfda_records`: 0

The `nhi_iode_dataset.number_of_data` sum was 29,492,875, so the live import was partially complete relative to the catalog estimate, not necessarily the user's informal “~40M” projection. Future answers should say “partially matches / verify current counts” rather than claiming full alignment from protocol alone.

## Answering pattern

Good answer shape:

- “Yes, this protocol matches the PG corpus at the source-family level: NHI IODE + TFDA OpenData.”
- “But the actual current PG counts are X, not necessarily the projected Y.”
- “The high-volume table is `<schema>.<records_table>`; specialized normalized tables are derived/subsets.”
- “Here are the exact SQL checks used.”

Avoid:

- searching only `~/Downloads` or repo files for a large corpus when PG is canonical;
- equating API protocol coverage with a completed ingest;
- claiming all TFDA data is present when normalized TFDA tables are populated but generic `tfda_records` is empty.
