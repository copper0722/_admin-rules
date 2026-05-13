# Topic-specific OA relevance gate

Use this when an open-access article downloader has already completed deterministic stages (metadata discovery, OA/license check, raw.md/PDF promotion) for a narrow topic queue, but content still needs LLM judgment before wikify.

## Core rule

Deterministic download success means “source available,” not “source belongs in this topic wiki.” For narrow queues such as ESRD/HD/dialysis, an Opus/LLM pass must read both metadata and article content before wiki synthesis.

## Inputs

- PG/source registry rows with OA/license evidence and raw path.
- `raw.md` content under the canonical raw layer.
- Optional publisher metadata/abstract/DOI/PMID.

Example PG filters in Copper-style systems:

- `ingest_status = promoted`
- `reading_status = pending_llm`
- `mineru_status in (done, not_applicable)`
- `oa_status = positive`
- `license_status in (public_reusable, free_to_read_only, manual_review)`
- `raw_md_path is not null`

## Classification

For each source, read metadata + raw.md, then classify:

- `ACCEPT_TOPIC`: article is substantively about the topic.
- `REJECT_NOT_TOPIC`: article was downloaded but is not substantively about the topic.
- `NEEDS_REVIEW`: topic relevance or license state is ambiguous.

For ESRD/HD, positive signals include end-stage renal disease, kidney failure requiring replacement therapy, maintenance hemodialysis/haemodialysis, peritoneal dialysis, CKD G5D, dialysis access, dialysis-specific CKD-MBD/PTH/anemia/vascular access/infection issues. General CKD, AKI, diabetes, obesity, or kidney biology alone is not enough unless the article specifically studies ESRD/HD/dialysis patients or operations.

## Actions

- `ACCEPT_TOPIC`: Opus-only wikify/update the relevant wiki entry; cite DOI/PMID/source_uid; update PG reading status and wiki path using local convention.
- `REJECT_NOT_TOPIC`: reverse topic registration safely. Prefer reversible PG status/soft-delete (`reading_status = rejected_not_<topic>`, `ingest_status = rejected`, `sync_deleted_at/sync_updated_at`, or local convention). Do not leave it as active `pending_llm` for the topic queue.
- `NEEDS_REVIEW`: create a zh-TW human block with exact source_uid/path and the decision required.

## Pitfalls

- Do not classify from title alone.
- Do not let OA/license positivity imply topical relevance.
- Do not hard-delete PG/source rows without an export or rollback plan.
- Non-Opus workers may build candidate lists and verification SQL, but source-derived wiki prose and relevance judgment should go to Opus/clauderunner.
