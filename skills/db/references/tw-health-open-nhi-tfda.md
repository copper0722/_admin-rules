# Taiwan health open data: NHI IODE + TFDA OpenData

Use this reference when Copper asks about `tw_health_open`, NHI/TFDA open data crawlers, or making a public shareable `tw-health-open` repo.

## Source families

NHI IODE:

- Catalog discovery:
  `https://info.nhi.gov.tw/api/iode0000s01/SQL008_1?searchType=all`
- REST base:
  `https://info.nhi.gov.tw/api/iode0010/v1/rest`
- OpenAPI:
  `https://info.nhi.gov.tw/IODE0000/openapi.json`
- Datastore pattern:
  `https://info.nhi.gov.tw/api/iode0010/v1/rest/datastore/{resource_id}?limit=1000&offset={offset}`

TFDA OpenData:

- Export pattern:
  `https://data.fda.gov.tw/opendata/exportDataList.do?method=ExportData&InfoId={INFO_ID}&logType=3`
- Common InfoIds:
  - 36: 西藥許可證
  - 43: 西藥成分
  - 67: 醫療器材許可證
  - 73: 化粧品許可證
  - 4: 食品標示違規查詢

## Verification before public claims

When Copper asks “does this match our 40M corpus?” or “is it complete?”, check PG first, not files.

Typical schema:

- `tw_health_open.nhi_iode_catalog`
- `tw_health_open.nhi_iode_dataset`
- `tw_health_open.nhi_iode_records`
- `tw_health_open.nhi_drug_formulary`
- `tw_health_open.nhi_facility`
- `tw_health_open.nhi_payment_standard`
- `tw_health_open.tfda_catalog`
- `tw_health_open.tfda_drug_permit`
- `tw_health_open.tfda_drug_ingredient`
- `tw_health_open.tfda_records`

Useful checks:

```sql
select tablename
from pg_tables
where schemaname='tw_health_open'
order by tablename;
```

```sql
select table_name, column_name, data_type
from information_schema.columns
where table_schema='tw_health_open'
order by table_name, ordinal_position;
```

```sql
select coalesce(sum(number_of_data),0)::bigint as expected_rows,
       count(*) filter (where number_of_data is not null) as datasets_with_counts,
       count(*) as datasets
from tw_health_open.nhi_iode_dataset;
```

```sql
select resource_id, count(*)::bigint as rows
from tw_health_open.nhi_iode_records
group by resource_id
order by rows desc
limit 25;
```

Avoid saying “complete” unless expected-vs-ingested checks pass and partial/zero datasets are explained.

## Public repo packaging gate

Do not package or advertise a public `tw-health-open` repo until the live corpus is verified complete or the README clearly says it is partial.

Public repo should include:

- public-safe crawler scripts;
- README with source URLs and legal/public-data scope;
- schema/migration without private DSNs;
- JSONL/Parquet export/import instructions;
- smoke tests or sample fetches;
- validation SQL/report templates.

Do not include:

- private PG DSNs;
- internal scheduler details;
- private logs;
- patient/clinic data;
- credentials or cookies.

## Storage / export advice

- Raw source downloads: `raw/{source}/{dataset_id_or_info_id}/{date}/...`
- Normalized JSONL: one record per line, UTF-8, `ensure_ascii=False`
- Parquet: partition by source/dataset/fetched date for large tables.
- Stream large tables; avoid pandas full-load for tens of millions of rows.
- Add source metadata to every row: source system, dataset/resource id, source URL, fetched timestamp, row hash.
