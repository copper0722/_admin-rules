# PubMed ESRD/HD OA recurring lane

Use this reference when Copper asks to restore or audit the PubMed ESRD/HD open-access article crawler.

## Decision captured

Copper wants the ESRD/HD OA article crawler to be a formal recurring lane, not a one-shot/manual run.

The lane must obey the central scheduler law in the private repo:

- PG registration first.
- Run through the existing task-train/q5/q30 style portal as appropriate.
- No ad-hoc launchd or crontab entry.
- Host-gated, bounded runtime, durable logs, and PG run state/result logging.

## Do not use PubMed page offset as a durable cursor

Do **not** persist `retstart` / page number as the cross-run continuation point. PubMed result sets can reorder or change as records are added/updated, OA/PMC status changes, and metadata is corrected. Persisting “last page processed” can miss articles or duplicate work.

Preferred pattern:

1. Maintain PG run state per source pipeline, e.g.:
   - `source_pipeline = pubmed_oa_hd_reviews`
   - `last_success_at`
   - `last_query_start_date`
   - `last_query_end_date`
   - `last_successful_pub_or_entrez_date`
   - `last_run_status`
   - `rows_seen`, `rows_inserted`, `rows_updated`, `rows_skipped`, `errors`
2. Each run queries a sliding recent window with overlap:
   - `last_successful_date - 7..30 days` through `now`, plus
   - optional periodic 2-year backfill audit.
3. Let PubMed results repeat across runs; make writes idempotent.

## Deduplication and upsert

Repeated articles may be fetched; they must not create duplicate registry rows or duplicate wiki work.

Stable identity priority:

1. DOI → `source_uid = doi:{doi}`
2. PMID → `source_uid = pmid:{pmid}`
3. PMCID or citation key only if DOI/PMID absent

Existing PG protections observed in `wiki_raw.raw_source_metadata`:

- primary key: `source_uid`
- unique: `doi`
- unique: `citation_key`

Crawler writes should use `INSERT ... ON CONFLICT DO UPDATE`, not append-only inserts.

Store PMID/PMCID/DOI in `publisher_metadata` or equivalent provenance columns so future reconciliation can verify identity drift.

## Raw Markdown writes

- Target canonical raw-KB route from Law/cards, not stale archived paths. For Copper this is hm4 `~/repos/vault/` unless the task is explicitly about legacy staging migration.
- Use deterministic paths per article.
- Write to a temp file and atomic-rename to `raw.md`.
- If `raw.md` exists:
  - same hash → skip;
  - changed hash → update only with version/provenance or explicit policy.
- Record `source_sha256` / normalized text hash where schema supports it.

## Stage separation

Stage 1 deterministic crawler:

- PubMed search / metadata / PMC OA fulltext detection.
- Download/write raw text where OA/publicly reusable.
- PG upsert.
- No LLM topical judgment.

Stage 2 LLM relevance gate:

- Read PG metadata + `raw.md`.
- Classify:
  - `ACCEPT_ESRD_HD` — true ESRD / HD / dialysis / CKD G5D relevance;
  - `REJECT_NOT_ESRD_HD` — off-topic or false-positive use of “dialysis”;
  - `NEEDS_REVIEW` — ask Copper in zh-TW with source_uid/path.
- Do not treat keyword hits or deterministic download success as topic acceptance.

Stage 3 Opus wikify:

- Only accepted rows enter source-derived wiki synthesis.
- Non-Opus workers may do mechanical inventory/checks only.

## Reverse / reject convention

If an article is not ESRD/HD relevant, remove it from the active ESRD pending queue rather than leaving it as `pending_llm`.

Before updating status, inspect the live schema constraints. Historical sessions found `wiki_raw.raw_source_metadata.reading_status` without a reject value, but a 2026-05-12 hmj `vault_main` check showed the constraint already allows:

- `pending_llm`
- `assigned`
- `needs_fulltext`
- `needs_table_ocr`
- `needs_human_review`
- `note_drafted`
- `wikified`
- `rejected_not_esrd_hd`

If a target DB clone still lacks `rejected_not_esrd_hd`, either add the allowed status via reviewed migration or use a reversible marker in `publisher_metadata` / `payload_flags` plus an active-query exclusion until migration. Do not perform destructive deletion just to “reverse” a rejected article unless Copper explicitly authorizes that destructive operation.

## Backlog example

A previous 2-year staging corpus lived under a PubMed staging path and had pending LLM review. The correct handling was to create:

- a mechanical checker/inventory task; and
- batch LLM relevance-gate tasks split by date range.

The checker should cover rows with `oa_status` or `license_status` still `unknown`; deterministic import may not finalize those fields even when `raw.md` exists.
