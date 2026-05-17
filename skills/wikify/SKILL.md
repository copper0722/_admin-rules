---
type: data
name: wikify
description: "Wikify any source into vault .md. PDF/mp3/URL/text/email/social-media → verbatim raw.md → wiki. Core principle: if not .md, it's forgotten. Same fidelity pipeline (Law §9.3) for every source type. MANDATORY TRIGGERS: /wikify, wikify, 維基化, 'convert to md', 'save to vault', drops a PDF/mp3/audio/URL, or pastes social-media post / screenshot / 零散文字. NOTE 2026-05-07: /wiki trigger reassigned to LLM-wiki Q&A skill (separate folder skills/wiki/); this skill is ingest direction only."
argument-hint: "[path to PDF | mp3/m4a/wav | URL | 'text:...' | 'inbox']"
---

# /wikify — Wikify Pipeline

Any source → structured .md → vault. The vault is a private Wikipedia operated by LLM.

## Principle

Wiki section (`wiki/`) = M2M knowledge cache maintained entirely by machine. Auto-iterating. Agents have **FULL AUTHORITY** over all wiki .md — create, update, merge, split, restructure, delete without Copper approval. No human in the loop. Wiki quality is the agent's responsibility. This is the one section of the vault where agents are autonomous owners, not assistants.

## Model Routing

Wiki synthesis/wikify/content mutation is Claude Opus-only. Use Opus for any
source-derived wiki prose, summary, key points, clinical interpretation,
evidence grading, causal appraisal, merge/split judgment, or contradiction
resolution.

Non-Opus scripts/agents may fetch sources, run MinerU/whisper, materialize
raw.md, update manifests/indexes, and perform mechanical link/path repairs.
They must leave `pending_opus_wiki` state instead of writing source-derived
wiki text.

## Textbook note dual-output pipeline (Copper directive 2026-05-03)

When `/note-writer` (or any agent) produces a textbook chapter note, **emit both versions in one pass**, never one + manual derivation:

- **Public version** → `vault/{topic_path}/{citation_key}/note-public.md`
  - Slide-style KEY TAKEAWAYS (5–10 bullets)
  - No verbatim quotes from copyrighted textbook (paraphrase only)
  - Last page: clickable link to private full version (build pipeline gates via CF Access)
  - Frontmatter: `note_type: "textbook-summary"`, `visibility: "public"`
- **Private version** → `vault/{topic_path}/{citation_key}/note-private.md`
  - Full chapter digest, zh-TW, Copper-readable
  - May include short verbatim quotes from textbook (within fair-use bounds; ≤2 quotes ≤30 words from commercial textbook per `synthesis-not-transcription rule` above)
  - Detailed mechanism, clinical implications, Taiwan-specific layer (NHI / TFDA / 健保給付規定)
  - Frontmatter: `note_type: "textbook-study"`, `visibility: "private"`

Both are publish-ready (per Copper directive: "讓 note 輸出即可在網站上分享"). Build pipeline does not need extra step — output of /note-writer is final-ready.

The two variants share the same `{slug}`; cross-link via frontmatter `related: [<other-slug>]`.

## Wiki primary home (Copper directive 2026-05-03; vault canonical 2026-05-15)

**Vault = single content corpus; personal-website = pure renderer (Copper directive 2026-05-15).**

- New wiki entries → `personal-website/src/content/wiki/{slug}.md` (flat slug, hyphenated, lower-case; wiki-llm collection stays renderer-side as M2M agent retrieval surface). Astro collection schema lives at `personal-website/src/content/config.ts` `wikiCollection`. Web URL: `/wiki/{slug}/`.
- New NOTE entries → **vault canonical** `vault/{topic_path}/{citation_key_or_slug}/note-{public,private}.md` (or `article.md` for wiki-human synthesis bundles). Frontmatter `publish: true` + `visibility` + `note_type` triggers prebuild script `personal-website/scripts/sync-vault-published-to-content.py` (a045) to symlink the vault canonical into `personal-website/src/content/notes/{visibility}/{note_type}/{slug}/index.md`. No whole-folder symlinks; per-file gate. Web URL: `/notes/{visibility}/{note_type}/{slug}/`.
- `wiki_raw/` moved under `personal-website/` 2026-05-09, then was merged into `vault/` 2026-05-13. Canonical raw text + source binaries are co-located at `~/repos/vault/{topic_path}/{topic_note_slug}/{raw.md, source.pdf, images/, manifest.json}`; raw `.md` is git-tracked, binary is gitignored. PG mirror: `wiki_raw.raw_index`. Deprecated `medwiki/wiki`, `medwiki/note`, `wiki_raw/raw`, and standalone `~/repos/wiki_raw/...` entries may remain for backward search only.
- **Whole-book PDF location (Copper directive 2026-05-09)**: when the source binary represents the *entire textbook*, place it at `~/repos/vault/_data/book/{book_citation_key}/{book_citation_key}.pdf` (one folder per book; co-locate per-book metadata + cover image if available). Per-chapter folders under `{topic_path}/{citationKey_Ch{NN}}/source.pdf` may still hold a chapter-only PDF cut, but the authoritative whole-book PDF lives under `_data/book/`. Zotero `book` itemType is the source of truth for which whole-book PDFs must exist (Zotero entry was created only after Copper confirmed the PDF exists).
- Wiki entry titles must NOT contain textbook names (Copper directive: 「標題移除教科書名」). Body must be paraphrase synthesis, never transcription. Citations live in `## Sources` section.
- Cross-reference between wiki entries via `[[slug]]` wikilinks; build pipeline (remark plugin, see Astro integration TODO) resolves to `<a href="/wiki/{slug}/">` on web. Cross-references from wiki body to raw payloads resolve to plaintext citations on web; binary/source sidecars stay private.

## Mindset (Copper directive 2026-05-03): wiki = "順便兼做"

Wiki synthesis is **incremental side-effect of reading the source**, not a
heavy separate pass. Once Opus has read the source to land raw, the wiki
entry update costs only marginal effort — do it. Append-and-cross-link rather
than waiting for a "perfect" first pass. The wiki accumulates value over many
small updates; do not gate on completeness.

- A rough but accurate append to an existing wiki entry > deferring "until I
  have time to write it well"
- New topic with no existing entry → create a stub with key facts + sources;
  next reading session refines it
- "Skip wiki synthesis, will do later" is a process bug — by the time later
  comes, the source content is no longer fresh in context

## Autonomous Wiki Workflow (Copper directive 2026-05-07)

Wiki layer = **100% autonomous + self-improving + convergent**. The 2026-05-03 "順便兼做" mindset (above) is the *trigger* — when an Opus session touches a source, it updates the wiki. The directives below are the *governance* of that touch — what counts as "well-maintained wiki".

### Authority

- **No Copper review gate**: agent creates / updates / merges / splits / deletes wiki entries without asking. `draft:true` is not a "wait for Copper" signal; it is a stub-marker for genuinely incomplete entries (and even those should publish promptly).
- **Always-publish**: default `draft: false`. Every entry is live at `/wiki/{slug}/` the moment it is written. Wiki is **not** promoted to homepage (homepage is curated articles + 一般民眾 / 專業人員 split landing; wiki is a library reference layer reached by search, AEO, or `[[slug]]` wikilinks).
- **Pure LLM-run**: Opus only for source-derived prose. Non-Opus mechanical work (link repair, schema validation, audit-script flagging, manifest sync) OK. No human review gate at any step.
- **No copper-readable summary**: wiki is M2M; neither Copper nor general humans read it by default. A separate human-readable wiki layer may be added later (Copper directive 2026-05-07: 「未來可能會新增 wiki for human，再說」). Until then, wiki entries omit `## Clinical Bottom Line`, `## Topic Overview` prose intros, `## Why X Cannot Y` rhetorical headers, `## Davenport Proposed Informed-Consent` style narrative scaffolding, and any other section that exists primarily to summarize the entry for a human reader.

### Self-improvement cycle

Triggered every time wiki touches an entry (whether for new source ingest, audit fix, or routine pass):

1. **New source on existing topic** → revise existing entry; do **not** append blindly.
2. **Reconcile contradictions**: when new source disagrees with existing claim, surface both with citations + judge which is currently best-supported.
3. **Compress redundancy**: merge duplicate facts, remove stale claims, retire superseded sources.
4. **Update changelog one line per session**: `- YYYY-MM-DD: integrated PMID:xxx (compressed §A, added §B, split §C → wiki_<sibling-slug>)`.
5. **Update sources count + paywall_sources / oa_sources / trial_sources / synthesis_lens / contradictions_resolved** to match actual content (not stale frontmatter).

### Convergence over append

Default mode = **revise + tighten**, not append + grow. Each session leaves entry **equal-or-shorter** unless genuinely new ground covered.

- If two facts say the same thing → keep one.
- If a paragraph can become a 3-row table → make it a table.
- If a 5-cell table has 4 redundant cells → use a one-line statement with the embedded number.
- If a section's only content is one fact → fold into adjacent section.
- If a `## Sources` line is to a paper that no body line references → review whether the citation is still earning its keep; if yes, add a body reference; if no, retire to changelog as `dropped: PMID:xxx (unused)`.

### Length triggers

| line count | action |
|---|---|
| <100 | OK |
| 100-300 | OK; M2M-density spot check |
| 300-500 | review for compress (likely some redundancy or narrative residue accumulated over multiple passes) |
| **>500** | **must compress or split** before next session ends — agent does NOT publish entries >500 lines as steady state |

### Split criteria

Split a single entry into multiple when ALL three hold:

1. ≥2 distinct subtopics each have ≥3 distinct facts.
2. Each subtopic is independently citable (i.e. is itself a concept other entries / external articles would link to via `[[slug]]`).
3. Resulting children entries are each ≥50 lines after split (otherwise the split was premature; merge back).

Cross-link split entries via frontmatter `related: [<sibling-slug>]` and inline `[[sibling-slug]]` wikilinks. Update changelog of all involved entries with the split decision + sibling slugs.

### Compress criteria (alternative path when length triggers fire but split criteria don't)

1. Convert narrative paragraphs → tables.
2. Eliminate `## Topic Overview` / `## Clinical Bottom Line` / `## Why X Cannot Y` / `## Davenport Proposed...` style sections (M2M directive 2026-05-07).
3. Move verbose source quotes → cite source path (raw.md or PMID/DOI); wiki keeps synthesis only.
4. Drop low-information bridge sentences ("Importantly", "It is worth noting that", "In contrast", etc. when they don't add a fact).
5. Collapse repeated `(95% CI, …; *p*=…)` formatting into a per-table column once the same statistic family is reported for multiple rows.

### Anti-patterns (audit-script-detectable, must fail audit)

These are mechanically detectable (grep / wc / regex). Per Law §design-principle, encode as audit, not Law prose. PG `quality_audit_tasks` rows:

| task name | detection rule |
|---|---|
| `wiki_human_ux_residue` | `^## (Clinical Bottom Line|Topic Overview|Conclusions / Clinical Bottom Line|Why .+ Cannot|Davenport.+Proposed)\b` matched in any `personal-website/src/content/wiki/*.md` |
| `wiki_oversize` | line count > 500 in any `personal-website/src/content/wiki/*.md` (excluding frontmatter + sources + changelog) |
| `wiki_draft_legacy` | `^draft: true` in any `personal-website/src/content/wiki/*.md` (legacy from before always-publish directive — should be 0 after 2026-05-07 bulk flip) |
| `wiki_orphan_source` | `## Sources` entry not referenced anywhere in body |
| `wiki_stale_count` | frontmatter `sources:` value mismatches actual count of `## Sources` entries |

Findings → `audit_findings`; agent reads + fixes + UPDATE `resolved_at`. Fix is part of the same autonomous loop above; no Copper escalation needed for any of these.

### Relation to "順便兼做" mindset

The 2026-05-03 mindset said "rough but accurate append > deferring". The 2026-05-07 directives sharpen that: rough first pass IS still better than deferring, BUT the next pass MUST tighten and converge — a wiki entry is not done when first written; it is done when each subsequent touch makes it shorter, denser, or more correct. Append-only mode is acceptable only for the literal first pass on a brand-new topic.

## Synthesis-not-transcription rule (Copper directive 2026-05-03)

**Wiki = paraphrase synthesis, not verbatim quote stack.** The reason wiki
synthesis is Opus-only is precisely that synthesis requires judgment — if the
output is just `> "verbatim from textbook"` blocks, the work could have been
done by `grep`. That defeats the model-tier choice and exposes the vault to
unnecessary copyright risk.

**Hard rules for source-quote density inside `wiki/*.md`:**

1. **Commercial textbooks** (Williams, Harrison, Harper, Lehninger, Brenner,
   Daugirdas, Nissenson, Scott-Brown, etc.) — **paraphrase + cite**. Use
   verbatim quote only when the *wording itself* is the point being made
   (e.g., a guideline's recommendation level statement, a paradigm-shift
   sentence whose hedging matters). Even then: ≤30 words, ≤2 such quotes per
   entry. Default mode = synthesis sentence + `(Williams 15e Ch33,
   §Hyperinsulinemia and IR)` citation.
2. **Open-access guidelines** (ADA SoC, KDIGO, Taiwan medical association
   guidelines, AHA/ACC, NIH, etc.) — verbatim quotes acceptable in moderation
   (≤150 words per quote, no aggregation cap). These are intended for
   citation; quoting recommendations verbatim is the conventional and legal
   norm.
3. **Open-access journal articles** — abstract-level paraphrase preferred;
   verbatim only for distinctive sentences (a specific HR + CI report,
   an authors' explicit conclusion line). ≤150 words per quote.
4. **Raw layer is the verbatim mirror.** If you find yourself wanting to
   quote a long textbook passage, that passage already lives in
   `~/repos/vault/{topic_path}/{citationKey}/raw.md`. Cite the payload path or
   PG `wiki_raw.raw_index` row; do not duplicate verbatim into wiki.
5. **Note layer is also synthesis** (Copper-readable zh-TW digest), not raw
   echo; same rule applies, see `personal-website/AGENTS.md` and the
   `/note-writer` skill.

The line between fair-use synthesis and copyright-exposure transcription is
not always sharp; when in doubt, paraphrase. The Opus model tier was chosen
precisely so this judgment happens at write-time.

## Wiki Article Standard Format

Every `wiki/wiki_*.md` file MUST follow this structure:

```markdown
---
summary: one-line description of topic scope
sources: 12
updated: 2026-04-06
tags: [nephrology, CKD, SGLT2]
---

# Topic Title

{M2M content — key facts, structured tables, clinical data, comparisons}

{Organized by subtopic sections as needed}

## Sources
- PMID:12345678 Author2024 — key finding from this paper
- PMID:23456789 Author2025 — contradicts above on X point
- DOI:10.1056/NEJMoa... — RCT: primary endpoint result
- fb:post_id — Copper's commentary on topic

## Changelog
- 2026-04-06: +3 Taiwan studies (PMID:xxx, xxx, xxx). Updated prevalence data.
- 2026-04-05: Created from 25 GDrive journal notes.
```

### Field rules

| field | required | rule |
|---|---|---|
| `summary` | if >500L (§9.1) | one-line, for agent scan before full read |
| `sources` | yes | count of source papers/documents |
| `updated` | yes | last modification date |
| `tags` | yes | flat tag names (§tag architecture) |

### Content rules (EBM protocol — NEJM review / textbook standard)

**Role model: NEJM review articles + Harrison's Principles of Internal Medicine.**
Wiki .md should read like a professional medical reference, not a blog or summary.

| principle | rule |
|---|---|
| **Evidence grading** | every clinical claim → cite evidence level. RCT > prospective cohort > retrospective > case series > expert opinion. Use GRADE when available (1A/1B/2C etc.) |
| **Quantitative** | numbers, not words. Write `HR 0.77 (95% CI 0.65-0.93, p=0.005)` not "significantly lower". Include NNT, ARR, effect size when reported. |
| **Structured like textbook** | organize by: Epidemiology → Pathophysiology → Diagnosis → Management → Prognosis. Not free-form prose. |
| **Guideline alignment** | cite guideline + recommendation grade: `KDIGO 2024 recommends SGLT2i for CKD G2-G4 with albuminuria (1B)` |
| **Conflicting evidence** | if studies disagree → present both: `DAPA-CKD showed benefit (PMID:xxx), but CREDENCE subgroup showed no benefit in non-DM (PMID:yyy)` |
| **Limitations** | note study limitations: sample size, population, follow-up, industry funding |
| **Clinical relevance** | not just "statistically significant" — state the clinical meaning: "NNT=21 over 3 years, meaning 1 in 21 patients avoids dialysis" |
| **Verifiability** | every claim → cite source (PMID/DOI). No unsourced assertions. |
| **No original research** | wiki = synthesis of existing sources, not CC's invention. CC organizes, does not opine. |
| **Neutral** | M2M factual. If sources disagree → present both sides with citations |
| **Citation needed** | if a claim lacks source → add `[citation needed]` marker. Fill on next pass. |
| **Cross-link** | link related wiki pages: `[topic](/wiki/wiki_*.md)` |
| **Bold edit** | CC edits freely (full authority). Copper audits periodically. |
| **No self-initiated web search** | Agent does NOT WebSearch on its own. If info is missing → give Copper a ready-to-use search prompt. Copper runs mini LLM council (multi-model web search) and feeds result back. Agent's job = formulate the right question, not search. |

### Sources section rules

- Every source = one line: `PMID/DOI — Author Year — key finding`
- New sources appended, never remove old ones (unless retracted)
- Sources that contradict each other → note explicitly
- OA sources preferred (always retrievable)

### Changelog rules

- Bottom of file, newest first
- One line per edit session: `- YYYY-MM-DD: what changed (source PMIDs)`
- Changelog = human-readable revision history (supplements git log)
- Keep last 20 entries. Older → archive to `## Changelog Archive` if needed.

### Source lifecycle

Every source (OA or not) must be in the configured source registry AND cited in at least one wiki .md `## Sources` section.

```
Source enters system -> source registry (doi/pmid/is_oa/status)
  → wiki .md cites it in ## Sources (PMID:xxx Author2024 — finding)
  → source is "alive" = cited by wiki

Orphan source = in DB but NOT cited by any wiki .md
  → candidate for deletion (not worthy of a single wiki article)
```

**Orphan scan protocol (audit duty):**

```bash
# Step 1: extract all cited PMIDs/DOIs from wiki files
grep -hoE 'PMID:[0-9]+' wiki/wiki_*.md | sort -u > /tmp/cited_pmids.txt
grep -hoE 'DOI:[^ ]+' wiki/wiki_*.md | sort -u > /tmp/cited_dois.txt

# Step 2: extract all PMIDs/DOIs from the configured source registry

# Step 3: diff → orphans
comm -23 /tmp/all_sources.txt /tmp/cited_sources.txt > /tmp/orphan_sources.txt

# Step 4: orphans → flag for deletion or wikify
# If source has raw.md → wikify it (fix the gap)
# If source has no raw.md and not OA → archive (not worth processing)
# If source is OA → try to wikify from internet before deleting
```

**Cloud agent support:** if a cloud agent lacks PG access, use a read-only export snapshot as fallback context only. PostgreSQL remains canonical.

**Bidirectional check:**
- Orphan source (in DB, not cited) → wikify or delete
- Phantom citation (cited in wiki, not in DB) → add to DB

## Entity Hierarchy

Post 2026-05-05 raw+binary merge + 2026-05-09 personal-website pivot: canonical layout is `~/repos/vault/{topic}/{citationKey}/{raw.md, source.pdf, ...}` (atomic per-task folder; raw + binary co-located; raw `.md` git-tracked, binary gitignored). Whole-book PDFs (entire textbook bundle) go to `~/repos/vault/_data/book/{book_citation_key}/{book_citation_key}.pdf` instead of being scattered across chapter folders.

| source | transcription tool | verbatim output | placement |
|---|---|---|---|
| PDF (academic, has DOI) | **MinerU on configured runtime** | raw.md + images/ -> note via `/note-writer` | `~/repos/vault/{topic}/{citationKey}/{raw.md, source.pdf, images/, source/}` |
| PDF (textbook chapter) | **MinerU on configured runtime** | raw.md + images/ | `~/repos/vault/{topic}/{BookEdition}_Ch{NN}/{raw.md, source.pdf, images/}` |
| PDF (project, no DOI) | MinerU | raw.md | `proj/{project}/data/{name}/raw.md` |
| **mp3 / m4a / wav** (podcast, lecture, meeting) | **whisper-cpp on configured runtime** | raw.md verbatim transcript | `~/repos/vault/{topic}/{citationKey}/{raw.md, source.mp3}` |
| URL / webpage | WebFetch + DOM clean | .md extract | `~/repos/vault/{topic}/{slug}/raw.md` (no binary) |
| Email / text | direct parse | .md capture | `~/repos/vault/{topic}/{slug}/raw.md` |
| Transcript (existing .txt) | direct ingest | .md structured | `~/repos/vault/{topic}/{slug}/raw.md` |

Binary source (PDF/mp3/wav) is NEVER the primary entity. `.md` = first-class citizen. Binary co-locates with raw inside the same task folder. **Same principle, different tool**: PDF -> MinerU; audio -> whisper-cpp; runtime selection belongs in the private project card. Law §9.3 Principle of Fidelity applies equally - no wiki/note synthesis until verbatim raw.md exists.

Ingestion staging: incoming PDFs land at `~/Library/Mobile Documents/com~apple~CloudDocs/Downloads/` (canonical iCloud-Downloads inbox since 2026-05-06 afternoon; system Downloads `~/Downloads` periodically `mv`'d here by `com.copper.downloads-to-icloud` LaunchAgent). Per-source workdir `<inbox>/{citationKey}/source.pdf` is optional. Run MinerU, then promote into `~/repos/vault/{topic_path}/{topic_note_slug}/` for chapter-level payloads, or `~/repos/vault/_data/book/{book_citation_key}/` for whole-book PDFs (see `_admin-private/.script/promote-mineru-output.py`). Retired inbox paths: `~/Dropbox/_Inbox/` (deprecated 2026-05-06 afternoon, archive remains for forensic trail), `~/repos/_inbox/` (non-canonical).

## Workflow

### Mode A: Single file (`/wiki /path/to/file.{pdf,mp3,m4a,wav,...}`)

1. Validate input exists (not 0 bytes, not iCloud placeholder)
2. Detect source type by extension + MIME:
   - `.pdf` -> Mode A-PDF (MinerU on configured runtime)
   - `.mp3` / `.m4a` / `.wav` / `.ogg` / `.flac` -> **Mode A-Audio (whisper-cpp on configured runtime)**
   - URL → Mode A-URL
   - Text block → Mode A-Text
3. Determine destination: has DOI? → `~/repos/vault/{topic_path}/{citationKey}/`. Has project-only scope? → project-local data path declared by that repo card. Else → ask for routing or create a pending audit card.

### Mode A-PDF — MANDATORY PIPELINE: PDF → raw.md → note/wiki

**Never skip raw.md.** Every PDF must go through MinerU first. No direct PDF→note.

```
PDF → DEDUP CHECK → MinerU → raw.md (payload, type: raw)
                                ↓
                         CC cleanup (簡→繁, LaTeX, tables)
                                ↓
                        ┌───────┴───────┐
                   note.md (if Copper    wiki.md (auto,
                    requests /note-writer)  M2M cache)
```

**STEP 0 — DEDUP CHECKPOINT (before ANY processing):**
1. Extract DOI from PDF filename, first page text, or metadata
2. Query canonical PostgreSQL first (stop at first match):
   - `wiki_raw.raw_index` by DOI / citationKey / payload path
   - domain textbook / article tables in `vault_main` when available
   - bounded filesystem check under `~/repos/vault/{topic_path}/` only when PG has no row
3. DOI/uid already exists → **SKIP entirely** (don't re-MinerU, don't re-wikify)
4. No DOI (gov docs, textbook chapters) → check title similarity in existing wiki .md
5. **After processing**: update PG `wiki_raw.raw_index` (and domain tables when available) with `raw_path`, `source_path`, status, and wiki/note links.
6. Log every dedup decision

**STEP 0B — EDITION CHECK (textbooks only):**
1. Check PG textbook inventory or bounded `~/repos/vault` textbook paths for all editions of same textbook
2. If newer edition exists in vault → do NOT process older edition
3. Processing order = **year DESC** (newest first, always)

Steps:
1. Copy to /tmp/ if on virtual FS (GDrive, iCloud)
2. **Run MinerU**: `mineru -p {pdf} -o /tmp/mineru_out/ -m auto -b pipeline`
3. **Promote ALL output to the payload folder** (raw.md + images/):
   ```bash
   # MinerU outputs to /tmp/mineru_out/{filename}/auto/
   MINERU_OUT="/tmp/mineru_out/{filename}/auto"
   PAYLOAD="$HOME/repos/vault/{topic_path}/{citationKey}"
   mkdir -p "$PAYLOAD"
   mv "$MINERU_OUT"/*.md "$PAYLOAD/raw.md"
   # CRITICAL: also copy images folder — without this, image refs in raw.md break
   if [ -d "$MINERU_OUT/images" ]; then
       mkdir -p "$PAYLOAD/images"
       mv "$MINERU_OUT/images"/* "$PAYLOAD/images/"
   fi
   ```
   Add `type: raw` frontmatter to raw.md.
4. **Image descriptions** (CRITICAL — incomplete raw.md = REDO): MinerU outputs `![](images/xxx.png)` refs. CC MUST replace each with a text description:
   - Read the image file (CC is multimodal)
   - Write a standardized description: `**[Figure N]** {what the figure shows, key data points, axis labels, trends}`
   - For tables in images: extract as markdown table
   - For charts/graphs: describe data, axes, key values, trends
   - Goal: raw.md = complete text substitute for PDF. CC never needs to open images.
   - **If raw.md has `![](...)` without text description → it is INCOMPLETE. Fix before proceeding.**
5. Claude cleanup on raw.md:
   - 簡體→繁體
   - LaTeX artifacts, HTML table formatting
   - OCR errors
   - **Remove page numbers** (headers/footers: "Chapter 5 / Harrison's Principles..." or standalone numbers)
   - **Remove references/bibliography** section at end of chapter (numbered reference list `[1]`, `[2]`... or `References` heading). These are not useful in raw.md — the source PDF has them if needed. raw.md = content only.
   - **Truncate at next chapter heading** if boundary page included: if raw.md has two chapter-level headings (`# 35 ...` followed by `# 36 ...`), delete everything from second heading onwards.
6. Determine identity:
   - Has DOI → citationKey → `~/repos/vault/{topic_path}/{citationKey}/raw.md`
   - No DOI, has project → project-local data path declared by that repo card
   - No DOI, no project → `~/repos/vault/{topic_path}/{slug}/raw.md` after explicit topic routing
7. **Move (NOT copy) PDF to payload folder — HR-7 invariant** (see Hard Rules below):
   ```bash
   mv "$INBOX_PDF" "$PAYLOAD/source.pdf"
   # Per-file cleanup verification — must run before step 8:
   ls "$INBOX" 2>/dev/null | grep -F "$(basename "$INBOX_PDF")" \
       && echo CLEANUP_FAIL || echo cleanup_ok
   ```
   Use `mv`, **never** `cp`. A `cp` leaves a stale duplicate that pollutes the inbox: Copper cannot tell processed-stale apart from unprocessed-new, and the next agent (cron / interactive) cannot either. If the verify step prints `CLEANUP_FAIL`, fix it immediately (re-run `mv`) before moving to step 8 — never proceed with stale inbox state.
8. **Wiki synthesis (Opus-only, MANDATORY — definition of done for inbox routine)**:
   - Claude Opus reads the cleaned raw.md
   - Scans existing `wiki/` for related topic
   - Match found → UPDATE existing wiki .md (append new findings, revise if contradicted)
   - No match → CREATE new wiki .md in `wiki/`
   - Non-Opus automation must stop at raw.md + manifest/index + queue state and explicitly mark `pending_opus_wiki` so the next Opus session resumes
   - **HARD RULE (Copper directive 2026-05-03)**: any source entering `_inbox/` is NOT considered processed until its wiki synthesis is complete. raw.md alone is incomplete state. Inbox-triage and Mode-B batch reports MUST list wiki .md path per file (or explicit `pending_opus_wiki` for non-Opus runs); a batch that produced raw.md but no wiki synthesis is reported as incomplete, not done.
   - Personal-website / nephro-cme / boan-website articles MUST cite the wiki .md (via wikilink), not the raw .md. Articles that cite raw without an existing wiki entry indicate the wiki step was skipped — fix by synthesizing the wiki entry first.
9. **Note layer (Opus-only, on-demand ONLY — explicitly NOT routine)** (Copper directive 2026-05-03):
   - note.md is **never** generated by routine inbox processing or Mode B batch
   - Generated only when Copper explicitly triggers (e.g., "寫筆記", "note it!", `/note-writer` invocation)
   - Per `~/repos/personal-website/AGENTS.md`, note layer is Copper-readable zh-TW; it is not a side-effect of inbox flow
10. Report: raw.md path, wiki.md path (or explicit `pending_opus_wiki`), line count, fixes applied

### Mode A-Audio — MANDATORY PIPELINE: mp3/wav → raw.md (same as PDF)

**Never skip raw.md.** Every audio file must go through the configured transcription runtime first. No direct audio->note. Same Principle of Fidelity as PDF (Law §9.3).

```
mp3/wav -> DEDUP CHECK -> stage in payload `{topic_path}/{key}/source.mp3`
                              ↓
                      ffmpeg -ar 16000 -ac 1 -c:a pcm_s16le → source.wav
                              ↓
                      whisper-cli --model ggml-medium.en.bin --file source.wav
                              ↓
                      verbatim transcript → raw.md (Pattern B frontmatter)
                              ↓
                      ┌───────┴───────┐
                note.md (/note-writer)  wiki.md update/create (M2M)
```

**Canonical implementation**: use the private runtime helper declared by the active repo card; public rules must not publish private helper paths, hostnames, or mount topology.

```bash
audio-to-raw \
    --mp3 /path/to/source.mp3 \
    --key {citationKey} \
    --topic {topic_path} \
    --title "{title}" \
    [--journal ... --doi ... --speakers ... --tags ... --source-type podcast|lecture|meeting]
```

**STEP 0 — DEDUP CHECK** (before transcribing):
1. Compute sha256 of source.mp3 -> check PG `wiki_raw.raw_index` / configured source registry for an existing payload folder
2. If DOI known (e.g., Annals On Call podcast has DOI 10.7326/ANNALS-*) → same dedup as Mode A-PDF
3. If same `citationKey` already has `~/repos/vault/.../{citationKey}/raw.md` → SKIP (don't re-transcribe)

**STEP 1 — Stage source audio**: place the file in the payload path declared by the active private repo card. Public rules must not hardcode private hostnames, mounts, or transport workarounds.

**STEP 2 — Convert to WAV**: `ffmpeg -y -i source.mp3 -ar 16000 -ac 1 -c:a pcm_s16le source.wav`. whisper-cli requires 16kHz mono PCM.

**STEP 3 — Transcribe with the configured local engine**:
- Model and device selection belong in the private runtime card.
- Command shape: `whisper-cli --model {model} --file source.wav --output-txt --language en --threads {n}`
- Run bounded background jobs with durable logs and poll until exit.
- Output: `source.wav.txt` (plain text) + optional `source.wav.srt` (timestamp-aligned).

**STEP 4 — Write raw.md** with Pattern B frontmatter:
```yaml
---
citationKey: {key}
uid: "doi:{DOI if available}"
payload: "~/repos/vault/{topic_path}/{key}"
type: raw
title: "..."
source_type: podcast            # or: lecture / meeting / interview / conference_talk
journal: "..."                   # for Annals On Call / NEJM podcast / JAMA Audio etc
year: YYYY
speakers: "Name1, Name2"
generated: YYYY-MM-DD
agent: whisper-cpp/ggml-medium.en
tags: [...]
summary: "..."
---

# {Title}

**Source**: `~/repos/vault/{topic_path}/{key}/source.mp3`
**Transcript**: whisper-cpp + {model}.

---

## Verbatim Transcript

{whisper output, leading spaces stripped}
```

**STEP 5 — Cleanup + dispatch** (same as PDF):
- Remove intermediate `source.wav` when it can be regenerated from mp3
- Rename `source.wav.txt` -> `transcript.txt` in the payload folder
- Simultaneous wiki evaluation (same as Mode A-PDF step 8): scan existing wiki/ for topic match; update or create
- Optional note.md via `/note-writer` short mode on Copper request

**Hardware pinning**: device/model selection is deployment-specific and belongs in the private runtime card.

**Tool choice note**: pipeline layer should remain CLI-first for reproducibility. GUI tools are manual fallback only.

### Mode A-URL

1. Fetch content via web fetch
2. Extract main content (strip nav/ads)
3. Structure as .md with source URL in frontmatter
4. Write to proj/ or kb/ by topic

### Mode A-Manual — `/wikify` (zero-binary scattered manual input)

> **2026-05-17 amendment — social-media pearl pipeline (Copper directive evening
> session):**
>
> When Copper pastes a **social-media post by a physician / 衛教 KOL**
> (FB / Threads / IG / X / Line / 醫聯網 / blog), the default action is no
> longer just "save to vault". The protocol is:
>
> 1. **Save pearl bundle** at
>    `~/我的雲端硬碟/agent-share/pearls/<YYYY>/<YYYY-MM-DD>_<handle>_<phrase>/`
>    (year bucket, no author subfolder). Bundle layout per
>    `agent-share/pearls/AGENTS.md` §«Per-pearl bundle layout»:
>    `raw.md` (frontmatter + verbatim body + optional `## Comments` block) +
>    `manifest.json` + (if image attached) `images/img_N.{jpg,png}` saved as
>    **binary** (post 2026-05-17 supersedes the older "OCR-only no binary"
>    rule for pearls — images are part of the pearl) + (if comments)
>    `comments.jsonl`. Set
>    `verification_status: unverified` initially.
> 2. **Fact-check** the post's substantive clinical claims against
>    textbook / guideline / primary literature. Default sources, in
>    priority order:
>    a. `wiki_raw.raw_index` PG search for the primary citation named in
>       the post (DOI / PMID / journal+year). If hit, read full text.
>    b. If primary not local, retrieve via Copper-provided URL (e.g. ACPjournals
>       full text via logged-in browser), save to
>       `agent-share/journal/<journal>/<column>/<slug>/raw.md` +
>       `manifest.json` with extracted key findings.
>    c. Cross-reference with vault-resident textbook chapter (Harrison /
>       Mandell / specialty textbook) per the existing Mode A-Manual
>       step 5.
>    d. OpenEvidence / UpToDate / DynaMed as L5 navigators (not direct
>       citation per memory `feedback_wiki_search_tri_source`).
> 3. **Build claim-by-claim table** in vault topic note: every substantive
>    claim → corroborated / partial / contradicted vs primary, with the
>    specific quote / table / value.
> 4. **Write note + wiki** at
>    `vault/<topic_path>/<topic_slug>/{note.md, article.md, refs.json}`:
>    - `note.md` = reader-facing zh-TW (single file, H2 sections incl.
>      Take home / Slides / Body / Clinical scenarios / References;
>      `public_sections: [take_home, slides, body]` whitelist).
>    - `article.md` = M2M compressed English (≤ 200 lines per
>      `feedback_wiki_human_length_cap`; auto-publish `draft: false`).
>    - Reference both the pearl bundle path and the primary citation in
>      `references` and `sources`.
> 5. **Flip pearl bundle `manifest.verification_status`** from
>    `unverified` → `corroborated` / `partial` / `refuted` based on
>    fact-check; add `verification_note` with summary; add
>    `derivative_note_path` + `derivative_wiki_path` pointing to vault
>    topic folder.
> 6. **Append chain-log** at
>    `agent-share/pearls/_agent-status/_chain-log.tsv` (7 col;
>    `bundled_manual` status).
> 7. **Do not** create an author subfolder under `pearls/` for new
>    sources (Copper directive 2026-05-17:「不設專區」). Only the
>    grandfathered `mysportscience/` retains a subfolder.
>
> If the social-media post is **non-medical / non-professional** (channel
> announcement, poll teaser, personal life, political / advocacy,
> off-topic news), reject in chat — do NOT save to pearls/. The agent is
> the gating layer for noise (`feedback_fb_pearls_cancelled_manual_only`).
>
> The original Mode A-Manual workflow below remains the reference for the
> raw mirror + textbook cross-reference mechanics; the new protocol above
> wraps it with the pearls/ + fact-check + note + wiki cycle.

**Trigger**: Copper pastes scattered manual input directly into chat — most commonly a social-media post (Facebook / Line / Instagram / Threads / X), a screenshot of a chat / lab report / 公告, a transcribed quote, or a free-form note. There is no PDF, no audio, no URL the agent must fetch — the source text and any embedded image content arrive inline in the conversation. `/wikify` (or bare paste of recognizable scattered manual input) routes here. NOTE 2026-05-07: pre-split alias `/wiki text:...` no longer routes here; `/wiki` is now the LLM-wiki Q&A skill (retrieval direction).

**Why a separate mode**: Mode A-PDF and Mode A-Audio assume a binary source artefact and a transcription tool (MinerU / whisper-cpp). Manual social-media input has no binary worth keeping by default — the screenshot is a vehicle for text, not a primary source. The fidelity contract therefore shifts: **embedded image content must be OCR / multimodal-extracted into raw.md verbatim text**, not stored as a binary payload, unless Copper explicitly asks to keep the original screenshot. (Copper directive 2026-05-02: "影像直接文字化進 raw".)

**Step 0 — Triage input shape (Copper directive 2026-05-02: "wikify 不一定包含 raw")**

`/wikify` 的核心工作是**查證 + 整理 wiki**。raw 鏡像是 conditional — 只有當 input 含「外部第三方來源文本」時才需要 verbatim 鏡像；如果 input 是 Copper 自己的問題或案例查證請求，就不寫 raw，直接跑 cross-reference + wiki synthesis。

| input shape | example | raw.md? | run which steps |
|---|---|---|---|
| **Source-shaped** | 外部第三方來源（FB/Line/IG/Threads 貼文、他人 screenshot、引述他人 quote、廣告稿、公告片段、新聞剪貼） | yes | run steps 1–8 in order |
| **Question-shaped** | Copper 自己丟一個問題、案例、查證請求（"X 是真的嗎"、"幫我整理 Y"、"我的患者 Z 怎麼處理"、"來源就是一個問題"） | **no** | skip steps 1–4. Run step 5 (textbook cross-ref) → step 7 (wiki synth, citing Copper's question as `manual:copper:{topic_slug}` in `## Provenance`) → step 8 (report). The question itself is the prompt; truth-grounding comes from textbook + vault literature. |
| **Hybrid** | Copper 貼一段來源並附自己的問題或評論（最常見："這篇 FB 對嗎？"、"這份報告怎麼解讀？"） | yes (source portion only) | run steps 1–4 on the source portion only; Copper's framing/question goes into wiki synthesis as the angle, not into raw |

The principle: raw layer is a mirror of *external* source text. Copper's own questions, comments, and case prompts are not external sources — they are framing for the wiki query, and should not be mirrored into raw. Real work shared across all shapes = step 5 (textbook cross-reference) + step 7 (wiki synthesis); raw mirroring (steps 1–4) is conditional on shape.

**Steps:** (run conditionally per Step 0 above)

1. **Verbatim capture** (Source-shaped + Hybrid only). Preserve the source text exactly: zh-TW characters, emoji, hashtags, line breaks, ASCII-art, the author's spacing. Do **not** rewrite, condense, or "clean up" — the raw layer's job is to be a faithful mirror. If the platform conventions are part of the message (e.g. FB-style short-line layout), preserve them inside a fenced block.

2. **Inline image text-extraction** (Source-shaped + Hybrid only). For each screenshot or pasted image:
   - Read the image with the multimodal Read tool.
   - Transcribe every legible token into a section of raw.md, structured by what the image is (e.g. `## Screenshot N — patient FB private message`, `## Screenshot N — lab report block`).
   - Tabular data (lab reports, prescription tables) → reproduce as markdown table. Preserve H/L flags, units, reference ranges when visible.
   - Note explicitly which fields are illegible / partly redacted; do not guess values.
   - Do **not** create a binary payload by default. If Copper asks to keep the original, move it to `~/repos/vault/{topic_path}/{citationKey}/source.{png,jpg}` with sha256 in the filename and add `payload: ~/repos/vault/{topic_path}/{citationKey}` to frontmatter.

3. **Source identity (uid scheme)** (Source-shaped + Hybrid only; Question-shaped uses `manual:copper:{topic_slug}` directly in wiki ## Provenance, no raw frontmatter required). Manual sources do not have DOI / ISBN / PMID. Use platform-prefixed uids:
   - `fb:{author_handle}:{topic_slug}` — Facebook post (e.g. `fb:SuYining2026:thalassemia_carrier`)
   - `line:{thread_id_or_author}:{topic_slug}` — Line message
   - `ig:{author_handle}:{topic_slug}` — Instagram
   - `threads:{author_handle}:{topic_slug}` — Threads / X
   - `manual:copper:{topic_slug}` — Copper's own question / case prompt (Question-shaped); cited in wiki only, no raw mirror
   - `manual:{topic_slug}` — generic free-form text with no platform anchor

4. **Frontmatter scheme** (Pattern C — manual / social-media; Source-shaped + Hybrid only):
   ```yaml
   ---
   type: raw
   citationKey: {AuthorYear}_{platform}_{topic_slug}
   uid: {fb|line|ig|threads|manual}:{handle}:{topic_slug}
   source_type: fb_expert_opinion | fb_post_quote | line_message | ig_post | threads_post | manual_text
   platform: facebook | line | instagram | threads | manual
   author: {name}
   author_role: {credentials / institution if known}
   title: {post title or first line}
   post_date: YYYY-MM-DDTHH:MM±HH:MM   # if known; else YYYY-MM only
   post_url: https://...                # if available
   captured_date: YYYY-MM-DD
   captured_by: copper-manual-input
   fidelity_notes: |
     Embedded image content was OCR-transcribed verbatim into raw.md
     (per Copper directive 2026-05-02). No binary payload kept by default.
   specialty: [<one or more domain tags>]
   topic: {topic_slug}
   tags: [<flat tag list>]
   cross_ref:
     textbook:
       - {BookKey}: {raw path to chapter}
     cited_in_post:
       - "{citation as printed in source}"
   agent: claude-opus-4-7-manual-wikify
   generated: YYYY-MM-DD
   ---
   ```

5. **MANDATORY textbook cross-reference** (all input shapes — this is the core work of `/wikify`). The agent picks the most relevant vault-resident textbook chapter from the Vault Textbook Reference Index (below), reads it, and either confirms or contradicts the clinical claim or answers the question with a citable line range. The cross-reference goes into a `## Cross-reference — {Book} {Edition} Ch{NN}` section of raw.md (Source-shaped / Hybrid) or directly into the wiki body (Question-shaped) with quoted lines. If no vault textbook covers the topic, fall back to vault-resident review articles, then report a citation gap (no self-initiated WebSearch).

6. **Topic placement** per repo Law routing fallback (raw/wiki/note share a `{topic_path}` skeleton where practical):
   - Folder = topic collection (a disease, organ system, methodology), not article shape.
   - For social-media expert opinions about a clinical topic, place under the same topic folder as the corresponding textbook chapter, e.g. a thalassemia-screening FB post goes to `~/repos/vault/clinical_medicine/internal_medicine/hematology/anemia(hematology)/{citationKey}/raw.md` next to `Harrison22e_Ch103/raw.md`.
   - When the topic is genuinely cross-cutting (policy, reimbursement, screening program), use the cross-cutting top-level peer per `protocol/wiki_classification_sop.md`.

7. **Wiki synthesis** (all input shapes). Per `wiki_raw/AGENTS.md` "Wikify Content Boundary":
   - Default = source-faithful synthesis. Do **not** auto-add EBM A1-A11 / PICO / GRADE / Hernán-causal-check sections just because the source is clinical.
   - If multiple sources on the same topic exist (textbook chapter + manual source + cited papers), produce one consolidated wiki .md combining them.
   - Cite the manual source in `## Sources`:
     - Source-shaped / Hybrid → `fb:{handle}:{topic_slug} — {author} {date} — {one-line of what it added}`
     - Question-shaped → in `## Provenance` (not `## Sources`): `manual:copper:{topic_slug} — Copper question {YYYY-MM-DD} — {one-line of the question}`. The wiki body's authority comes from the textbook + literature citations, not the question.
   - The wiki entry must surface the textbook cross-reference inline; do not bury it.

8. **Report**. Print: input shape decided (Source-shaped / Question-shaped / Hybrid), raw.md path (if written), wiki.md path (if created or updated), the textbook chapter consulted for cross-reference, any citation gap (PMIDs to fill later), and any binary kept on Copper's request.

### Mode A-URL → Mode A-Text shim

The thin "parse → structure → write" workflow above remains for plain text snippets that do not warrant the Mode A-Manual scaffolding (e.g. a 3-line gloss, an internal memo). Anything that is recognisably a social-media post, contains screenshots, or makes externally-citable clinical claims should escalate to Mode A-Manual.

### Mode B: Inbox triage (`/wiki inbox`)

Canonical inbox path is declared by the project-local private card.

1. List all unprocessed files at the configured inbox with bounded commands.
2. For each file:
   - `.pdf` → queue for **Mode A-PDF** (MinerU)
   - `.mp3` / `.m4a` / `.wav` → queue for **Mode A-Audio** (whisper-cpp)
   - `.md` already → review frontmatter, route to proper vault path
   - `.docx` / `.html` → convert to .md first, then route as text source
   - Other binary → investigate or move to `proj/{p}/data/` with metadata
3. Process queue sequentially with the configured runtime.
4. **HR-7 mandatory cleanup — `mv`, not `cp`** (see Hard Rules below). After **each** file's payload folder + raw.md + (optional) note land successfully:
   ```bash
   mv "$INBOX_FILE" "$PAYLOAD/source.{pdf,mp3,m4a,wav,...}"
   ls "$INBOX" 2>/dev/null | grep -F "$(basename "$INBOX_FILE")" \
       && echo CLEANUP_FAIL || echo cleanup_ok
   ```
   Per-file: must print `cleanup_ok` before moving to the next file in the queue. Per-failed-file: even when MinerU/whisper fails, **still** `mv` the binary to `~/repos/vault/{topic_path}/{citationKey}/source.{ext}` and write a `raw.md` stub with `status: mineru_failed` (or equivalent). Inbox **never** retains the failed binary either — failure path is payload-with-stub, not "leave it for next time".
5. **HR-7 final batch invariant** — before reporting completion, verify the inbox is clean of all source binaries the batch was responsible for:
   ```bash
   find "$INBOX" -maxdepth 1 -type f \
       \( -iname '*.pdf' -o -iname '*.mp3' -o -iname '*.m4a' -o -iname '*.wav' \
          -o -iname '*.docx' -o -iname '*.epub' \) | wc -l
   ```
   Must be 0 (or equal to the count of files the batch explicitly skipped — those must be enumerated in the report). Anything > 0 is a recurrent-bug regression; do not declare batch complete; loop back and `mv` the residuals.
6. Report: N files wikified by type, per-file cleanup_ok log line, batch final inbox-residual count, any explicitly-skipped files (with reason).

### Mode C: Batch (`/wiki batch /path/to/folder/`)

1. List all PDFs in folder without payload `raw.md`
2. Queue all for Mode A-PDF
3. Process sequentially (MinerU is slow, ~5min per large PDF)
4. Report progress

## Hard Rules (card-level, all agents)

**HR-3 TEXTBOOK = LATEST EDITION ONLY.** If newer edition of same textbook exists in `~/repos/vault` or PG inventory, do NOT wikify older. Archive superseded editions (§1.3).

**HR-4 PROCESSING ORDER = YEAR DESC.** Newest content first. Textbooks: 2026 before 2024. Articles: 2026 before 2021. Newer supersedes older.

**HR-6 UID CHAIN.** Every PDF → raw.md (uid in frontmatter) → Zotero entry (same uid). UID types:

| scheme | when to use | example |
|---|---|---|
| `doi:<doi>` | DOI registered (CrossRef → Zotero) | `doi:10.1056/NEJMoa2400000` |
| `pmid:<pmid>` | PubMed-indexed (no DOI fallback) | `pmid:38123456` |
| `isbn:<13>` | book with ISBN-13 (Google Books / publisher / WorldCat) | `isbn:9781975160340` |
| `book:<citation_key>` | **book without ISBN** — society textbook, internal compilation, society guideline bundled as book | `book:TADE_DM_Edu_Core_2026` |
| `gov:<文號>` | government document (公文 header) | `gov:衛部醫字第...號` |
| `local:<key>` | vault-internal, pre-publication, unpublished | `local:Copper_DM_Personal_Notes_2026` |

**Books are special** — the canonical source-of-truth table is `personal_website.book` (3NF domain table; CHECK constraints encode the UID convention). Do **not** INSERT new `kind='book'` rows in `personal_website.source_registry`; new books go to `personal_website.book` only. The whole-book PDF goes under `~/repos/vault/_data/book/{book_citation_key}/` (Copper directive 2026-05-09). Full convention + migration recipe in `vault/_config/protocol_book_registry.md`.

Script: `raw-uid-zotero-sync.py` (weekly cron). Orphan = PDF without raw.md or raw.md without UID.

**HR-7 INBOX STATE INVARIANT — `mv`, never `cp`** (Copper 2026-04-24, re-flagged 2026-05-02 as **recurrent malignant bug**). After every successfully-processed source binary (PDF / audio / image), the inbox copy MUST be `mv`'d into its payload folder (`~/repos/vault/{topic_path}/{citationKey}/source.{ext}` for chapters/articles, `~/repos/vault/_data/book/{book_citation_key}/{book_citation_key}.pdf` for whole books), never `cp`'d. Reasoning: Copper inspects the inbox to know what is unprocessed; a stale duplicate makes processed-vs-unprocessed indistinguishable, and the next agent — interactive or cron — inherits the same ambiguity. Failure mode is "next session re-processes / mis-skips, inbox accumulates stale binaries, a real new arrival is eventually missed in the noise".

- **Per-file post-condition** (run after every individual `mv`): `ls "$INBOX" | grep -F "$(basename "$file")"` returns nothing.
- **Per-batch post-condition** (run before declaring batch complete): `find "$INBOX" -maxdepth 1 -type f \( -iname '*.pdf' -o -iname '*.mp3' -o -iname '*.m4a' -o -iname '*.wav' -o -iname '*.docx' -o -iname '*.epub' \) | wc -l` = 0 (or equal to the count of explicitly-skipped files enumerated in the report).
- **Failed-MinerU / failed-whisper path**: the binary is still `mv`'d to the payload folder (`~/repos/vault/{topic_path}/{citationKey}/source.{ext}`); the failure is recorded as a `raw.md` stub with `status: mineru_failed` / `status: whisper_failed`. The inbox NEVER retains a failed binary "for retry" — retry happens against the payload folder, not the inbox.
- **`dropbox-inbox-audit.sh` is a safety-net, not a substitute** (q1h cron, archives `cp`-duplicates by sha256 match against payload folders — does not catch agents that skipped the move entirely). Agent self-enforcement is the primary control.

Applies to all Modes (A-PDF, A-Audio, A-Manual when binary payload kept, B inbox triage, C batch). Re-flagged as a Hard Rule rather than a Mode B sub-step so the invariant survives Mode boundary.

## Rules

- MinerU output is NEVER final — always Claude cleanup
- Known MinerU issues: 簡→繁, LaTeX artifacts, name errors, table misalignment
- If MinerU fails → try pdfminer fallback → if both fail → report, don't retry
- Raw first (§1.8): save MinerU output as raw.md in the payload folder, then clean
- Every PDF without payload `raw.md` = not wikified = invisible to system
- /note-writer handles academic PDF→teaching note (higher quality, more token). /wiki handles bulk conversion.

## Public Download Boundary

For public rules, PDF download examples are limited to open-access or otherwise clearly licensed files. Subscription or authenticated source acquisition is a private workflow and must not be documented in this public repo.

## Topic-specific OA article gate before wikify

When an OA downloader was run for a narrow topic queue (for example ESRD/HD articles), deterministic download/promotion is not enough to mark the source as wikified. Add an LLM relevance gate before wiki synthesis:

1. Query PG/source registry for OA + raw-present + `pending_llm` rows in the topic queue.
2. Read both metadata and `raw.md` content; do not classify from title alone.
3. Classify each source as `ACCEPT_TOPIC`, `REJECT_NOT_TOPIC`, or `NEEDS_REVIEW`.
4. `ACCEPT_TOPIC` → Opus-only wikify/update the relevant wiki entry and then mark PG reading status as wikified using the repo's convention.
5. `REJECT_NOT_TOPIC` → reverse the topic registration safely: prefer reversible PG status/soft-delete (`rejected_not_<topic>`, `sync_deleted_at`, or the project convention). Hard delete only with an explicit rollback plan.
6. `NEEDS_REVIEW` → block with a zh-TW visible reason containing source_uid/path and the exact decision needed.

See `references/topic-specific-oa-relevance-gate.md` for the ESRD/HD pattern.

## Mode D: EBM Appraisal (absorbed from /med-read, 2026-04-12)

For journal articles + guidelines, wiki evaluation includes full EBM + causal inference appraisal. Source-type routing + Guyatt 3-gate (validity/importance/applicability) + Hernán target trial + DAG.

**Deep methodology reference (when appraising complex studies):**
- `wiki/methodology/wiki_causal_inference.md` — full Hernán digest
- `wiki/methodology/wiki_research_methods_ebm.md` — full Guyatt digest
- `~/repos/vault/research_method/causal_inference/Hernan_WhatIf/causal_inference_critical_appraisal_checklists.md` — 70+ checklist items, if present

### Source Type Detection (auto)

| signal | → type | output section |
|---|---|---|
| DOI + Methods/Results/Discussion | journal-article | Full EBM (A1-A11) |
| "guideline" + graded recommendations | guideline | Recommendation table + Taiwan context |
| Chapter numbering + textbook publisher | textbook | Faithful digest (numbers/thresholds preserved) |
| 公告/法規/NHI/衛福部 | policy | Regulatory digest |
| "case report" ≤3 patients | case-report | Clinical reasoning (no GRADE) |
| "review" synthesis only | review | Structured summary |

### Journal Article Full Appraisal (A1-A11)

A1. Paper identification (title, authors, journal, DOI, trial name, NCT)
A2. Study design classification + reporting guideline (CONSORT/STROBE/PRISMA/STARD/TRIPOD)
A3. PICO (flag surrogate vs hard endpoints)
A4. Methods critique
  - RCT: randomization, allocation concealment, follow-up, blinding, baseline balance, ITT, sample size + fragility
  - Observational: Guyatt harm guides + Hernán causal check (target trial, DAG, backdoor paths, collider)
  - SR: PRISMA (≥2 databases, ROB2/ROBINS-I, I², Egger's)
A5. Results (ARR + RRR, NNT/NNH, KM separation, Asian/renal subgroup)
A6. Causal inference (Hernán)
  - Causal claim despite observational? Treatment intervenable? 7-component target trial?
  - DAG: backdoor blocked? collider/mediator?
  - **Nephrology bias scan**: immortal time, prevalent user, competing risk, confounding-by-indication, time-varying, HR frailty, measurement (eGFR ≠ true GFR)
A7. GRADE (RCT→HIGH, observational→LOW; downgrade/upgrade rules)
A8. External validity (Taiwan HD: demographics, NHI coverage, 3×/wk 4h HD fit)
A9. Clinical bottom line (1 sentence)
A10. Subgroup credibility (Guyatt 6-item, if applicable)
A11. Teaching points (3-5 bullets, TLC Medicine audience)

### Nephrology Red Flags (auto-apply)

1. Dialysis exclusion bias (eGFR <30 or dialysis excluded)
2. Surrogate trap (phosphate/PTH/Kt/V/Hb targets; see EVOLVE, TREAT, CHOIR, 4D)
3. Competing risk (death competes with almost all non-mortality endpoints)
4. Immortal time (early vs late dialysis initiation)
5. Confounding by indication + time-varying (ESA-Hb loop, nutrition-dose loop → g-methods)
6. Prevalent user bias (90-day survivor) → new-user active-comparator preferred
7. Collider/reverse epidemiology (restriction to dialysis = conditioning → obesity paradox)
8. HR frailty selection (report survival differences, not just HR)
9. Taiwan NHI relevance (drug availability, reimbursement, 健保碼)

## Mode E: Quick Triage (absorbed from /appraise, 2026-04-12)

For batch processing (RSS digest, PubMed alerts, /burn), output compact 10-15 line assessment per paper. No full A1-A11.

**Triage format (zh-TW):**

```
## {Author Year} — {abbreviated title}

**Study type**: {RCT / cohort / SR+MA / etc.}
**PICO**: P={...} | I={...} | C={...} | O={primary}
**Key result**: {effect size, CI, p}
**Evidence quality**: {GRADE} — {one-line rationale}
**Relevance**: {HIGH/MEDIUM/LOW} — {why, per Copper's nephrology/HD/Taiwan context}
**Verdict**: {READ/SKIM/SKIP} — {one-line}
Flag: {red flag} (omit if none)
```

**Decision logic:**
- READ: HIGH relevance + MODERATE-or-better evidence. Practice-changing.
- SKIM: MEDIUM relevance OR HIGH relevance but LOW evidence.
- SKIP: LOW relevance OR VERY LOW evidence OR duplicate.

**Batch mode:** Separate papers with `---`. End with summary: `Triage: {N} papers — {n} READ, {n} SKIM, {n} SKIP`.

## Mode F: Condensation (absorbed from /condense, 2026-04-12)

Reduce file count by merging similar files into consolidated articles.

**Trigger:** folder >15 files OR user says "condense", "整理", "清理", "丟進去".

**Workflow:**
1. Target folder = $ARGUMENTS (default: scan for folders >15 files)
2. Triage by keyword prefix: `ls *.md | sed 's/_20[0-9][0-9].*$//' | sort | uniq -c | sort -rn`
3. For each keyword group:
   - Read ALL files in group
   - Cluster by topic similarity (3-5 files per cluster)
   - Write ONE consolidated .md per cluster (tree-structured bullet outline, M2M English for system, zh-TW for user-facing; preserve all facts/dates/decisions)
   - Archive originals: `zip _archive/{group}_originals.zip {files}` → delete originals
4. Skip primary source materials (check folder CLAUDE.md for protected files)
5. **proj/ folders:** agent can condense freely. **kb/ folders:** requires Copper review (§9.1).
6. Report: group name, files before → after

**Rules:**
- Archive only after condensation verified complete
- Only .zip in `_archive/` (never loose .md)
- Never merge files across different keyword prefixes into same article

**"丟進去" upgrade (route + tag):**
When user pastes content + says "丟進去/整理/file this/歸檔":
1. Condense first (去蕪存菁)
2. Route: user-specified target > proj/ > kb/
3. Dedup: scan target folder for ≥50% overlap → merge into existing, else create new
4. Tag: if kb/ → extract tag cloud → frontmatter `tags: [...]`

## Mode G: Specialty Clinical Medicine LLM-wiki Bootstrapping

**Trigger:** The user asks to build a high-quality specialty CME/LLM-wiki for an external team, to ingest a textbook corpus as payload, or to open a new `clinical_medicine/{specialty}` folder (e.g. ENT, cardiology, endocrinology).

### Taxonomy routing for cross-cutting clinical concepts

Before creating a disease/specialty-local folder, decide whether the concept is truly owned by that specialty or is a cross-cutting method/policy domain:

- Clinical tools or measurements used beyond one specialty (e.g. body composition monitoring, frailty scales, exercise testing) → prefer `clinical_medicine/assessment_methods/{concept}/` in `~/repos/vault`, `wiki_raw` indexes, and personal-website publisher paths, then link from specialty pages as needed.
- Reimbursement, regulation, health insurance, device payment, national policy, or payer-system topics → prefer a top-level peer domain such as `health_insurance_reimbursement/{topic}/` rather than burying it under `clinical_medicine/`.
- Disease/specialty paths may contain symlinks or index links back to the canonical cross-cutting folder, e.g. `clinical_medicine/internal_medicine/nephrology/ckd/esrd/dialysis_reimbursement -> ../../../../../health_insurance_reimbursement/dialysis_reimbursement`.
- If the source material is pending from a human/vendor and facts are incomplete, create a small `_index.md` plus a pending-source page with explicit source gaps; do not invent reimbursement details via unsourced synthesis.
- Mirror the same routing in `~/repos/vault` and PG `wiki_raw.raw_index`; verify case-sensitive paths (`ckd` vs `CKD`) before committing path metadata.

This is a corpus/bootstrap workflow, not a single-PDF `/note-writer` task.

1. **Orient to existing repo structure first**:
   - Check the project `AGENTS.md` files if present.
   - Search both repos for the target specialty before creating folders.
   - If the task originates from an invitation/project, record strategic purpose in the owning private project note.
2. **Sidecar corpus ingest**:
   - Put large source PDFs under the active payload path declared by the project card. Legacy `_sidecar/` paths are compatibility only and should be git-ignored.
   - Before downloading, resolve and record the real binary target using the project resolver. Do not assume the displayed repo path is local disk.
   - For Google Drive folders, install/use `gdown` when appropriate: `python3 -m pip install --user gdown`; then `python3 -m gdown --folder '{url}' -O {payload_dir} --remaining-ok`.
   - Verify downloaded files with `ls -lh`, page counts, SHA256, and `stat` mtimes before proceeding. For multi-device payload folders, verify both the declared path and the resolved binary path when reachable.
3. **Manifest first**:
   - Use PyMuPDF (`fitz`) to write `manifest.json` in the payload folder with file name, bytes, page count, SHA256, PDF metadata, and TOC sample.
   - Create a committed markdown manifest summarizing the corpus and pointing to the payload path.
4. **Open canonical folders**:
   - Create the project-local synthesized wiki index for the specialty/topic.
   - Create the project-local raw/source staging index for the specialty/topic.
   - Include purpose, tags, source corpus, pipeline state, and next-step checklist.
5. **Extraction pipeline**:
   - For large textbooks (>500 pages or multi-volume corpora), **split chapters first, then run MinerU per chapter**. Do not OCR an entire 1000+ page volume into one raw.md.
   - Use PDF TOC/bookmarks or contents-page parsing to create `chapter_manifest.json` with chapter id, title, page range, chapter PDF path, SHA256, and `raw_target` before OCR.
   - Create a lightweight repo-tracked status mirror (`..._extraction_status.json` or equivalent) from the git-ignored payload manifest so a future/cloud agent can still see `chapters_total`, `raw_exists`, `pending_mineru`, and `chapter_pdfs_missing_or_remote` even when the binary payload is absent.
   - Add a small repo-tracked status script (for example `scripts/{corpus}_status.py`) that first reads the live payload manifest when present, then falls back to the committed status mirror. It should print pending counts and optionally list pending chapter IDs.
   - Put a `NEXT_AGENT_README.md` or equivalent sentinel inside the git-ignored payload folder itself, pointing back to the committed workflow/status files. This helps local agents landing in the payload understand that PDFs may be intentionally un-MinerU'd.
   - Start with one representative/high-priority chapter using MinerU when available: `mineru -p '{chapter_pdf}' -o {raw_workdir} -m auto -b pipeline`.
   - Run long MinerU jobs in background with completion notification; do not block the user for an entire textbook corpus.
   - Add local extraction workdirs such as `**/_mineru_runs/` to `.gitignore`; never commit large intermediate OCR outputs unless deliberately promoted to raw `.md`.
   - For mechanical raw proofreading after MinerU, Gemma-class cheap/cloud/local models are acceptable if constrained to OCR cleanup only; synthesis remains a separate higher-reasoning pass.
6. **Commit small metadata, not binaries**:
   - Commit/push `_index.md`, markdown manifest, committed extraction status mirror, status script, `.gitignore` changes, and the originating project note.
   - Verify `git status` does not include payload PDFs or MinerU run directories.
   - Pull/sync to other reachable machines when this is infrastructure for future agents; note unreachable hosts explicitly.
7. **Report state clearly**:
   - Sidecar path and files downloaded.
   - Created vault article/raw path and PG metadata.
   - Git commits pushed.
   - Background pipeline session id and current state.
   - Any unreachable machine or blocked next step.

## Vault Textbook Reference Index

When wikifying any source (especially Mode A-Manual), the agent must pick a
vault-resident textbook chapter to cross-reference clinical claims. This index
is the LLM's mental map of "what books are in the vault". It is a snapshot;
authoritative inventory will live in the textbooks PG table once that lands.
Verify presence with `find ~/repos/vault -path '*<Prefix>*' -name raw.md | head`
before citing a specific chapter.

| Specialty / scope | Textbook | Latest edition in vault | Year | Payload locator | Legacy note |
|---|---|---|---|---|---|
| Internal medicine (definitive) | Harrison's Principles of Internal Medicine | 22e | 2025 | `~/repos/vault/clinical_medicine/internal_medicine/**/Harrison22e_Ch*/raw.md` | topic-distributed |
| Internal medicine (pocket) | Pocket Medicine | 9e | 2026 | search PG / `~/repos/vault` for `PocketMedicine9e` | inbound |
| Therapeutics quick-ref | Washington Manual of Medical Therapeutics | 38e | recent | search PG / `~/repos/vault` for `WashingtonManual38e` | per-chapter |
| Nephrology (definitive) | Brenner & Rector's The Kidney | 12e | recent | `~/repos/vault/clinical_medicine/internal_medicine/nephrology/**/BrennerRector12e_Ch*/raw.md` | per-chapter |
| Dialysis | Daugirdas, Handbook of Dialysis | 6e | 2026 | search PG / `~/repos/vault` for `Daugirdas2026` | figures may exist |
| Dialysis (alt) | Dialysis Therapy | 6e | 2023 | search PG / `~/repos/vault` for `DialysisTherapy_6e` | inbound |
| Dialysis (intro) | Core Concepts in Dialysis | 2021 | 2021 | search PG / `~/repos/vault` for `CoreConceptsDialysis` | inbound |
| Pediatric nephrology | Pediatric Nephrology | 6e | recent | `~/repos/vault/clinical_medicine/**/nephrology*/*Pediatric*/raw.md` | per-chapter |
| ENT | Scott-Brown's Otorhinolaryngology, Head and Neck Surgery | 8e | recent | `~/repos/vault/clinical_medicine/ENT/**/ScottBrown8e*/raw.md` | V1/V2/V3 |
| Biochemistry | Harper's Illustrated Biochemistry | **34e (latest); 33e archived 2026-04-24** | 2026 | search PG / `~/repos/vault` for `Harper34e` | 33e archived |
| Biochemistry (alt) | Lehninger Principles of Biochemistry | 8e | recent | search PG / `~/repos/vault` for `Lehninger8e` | per-chapter |
| Physiology | Ganong's Review of Medical Physiology | 26e | 2019 | search PG / `~/repos/vault` for `Ganong_26e` | inbound |
| Biology (preclinical) | Campbell Biology | 13e | 2026 | search PG / `~/repos/vault` for `Campbell_13e` | inbound |
| Causal inference / epidemiology | Hernán & Robins, Causal Inference: What If | latest open-edition | open-access | `~/repos/vault/research_method/causal_inference/**/Hernan_WhatIf*/raw.md` | checklist may be note-linked |
| EBM / critical appraisal | Guyatt Users' Guides to the Medical Literature | latest in vault | recent | search PG / `~/repos/vault` for `Guyatt_Users_Guides` | per-chapter |
| Health research methods | Health Research Methods | 3e | 2021 | search PG / `~/repos/vault` for `HealthResMethods_3e` | inbound |
| Renal guideline | KDIGO 2024 CKD | 2024 | 2024 | search PG / `~/repos/vault` for `KDIGO_CKD` | wiki/note distributed |

### How to pick the right book

- **Hematology / oncology / general internal medicine claim** → Harrison 22e first (definitive, 2025).
- **Nephrology mechanism / disease** → Brenner & Rector 12e (definitive). For HD/PD operations → Daugirdas Handbook of Dialysis 6e.
- **Pediatric nephrology** → Pediatric Nephrology 6e (definitive).
- **ENT** → Scott-Brown 8e (V1 = general / head-neck surgery basics, V2 = otology / paediatric ENT, V3 = rhinology / laryngology / facial plastics).
- **Biochemistry mechanism** → Lehninger 8e or Harper 34e (incoming). Harper 33e archived; do not cite older edition (HR-3 latest-edition-only).
- **Physiology** → Ganong 26e.
- **Causal inference / observational study critique** → Hernán *What If* (free open-access; canonical for target-trial framing, DAG, time-zero).
- **EBM / critical appraisal of trials** → Guyatt Users' Guides.
- **Renal guideline alignment** → KDIGO 2024 CKD (current); cite recommendation grade.
- **Quick clinical reference at point-of-care** → Washington Manual 38e or Pocket Medicine 9e.

If the picked book lacks the specific topic, fall back order: (1) primary literature already indexed by PG `wiki_raw.raw_index` or present under `~/repos/vault/{topic_path}/`, (2) recent NEJM / Lancet / JAMA / specialty-flagship review located via PG / bounded `~/repos/vault` search, (3) report citation gap and let Copper run mini LLM council (no self-initiated WebSearch per the No-Self-Initiated-Web-Search rule above).

## Supersedes

This skill replaces `/pdf2md`, `/med-read`, `/appraise`, `/condense` (all absorbed 2026-04-12). Old triggers route here.

**2026-05-07 trigger split (Copper directive)**: `/wikify` is the canonical trigger for this ingest skill; `/wiki` was retired as an alias and reassigned to the new LLM-wiki Q&A skill at `_admin-rules/skills/wiki/`. Routing rule:

- Ingest-shape input (PDF / audio / URL / scattered manual paste) → `/wikify` (this skill)
- Question-shape input (clinical / medical / policy Q&A from local LLM-wiki) → `/wiki` (Q&A skill)

Cross-refs:
- `_admin-rules/skills/wiki/SKILL.md` — LLM-wiki Q&A
- `_admin-rules/skills/note-writer/SKILL.md` — Opus-only teaching note
- `_admin-rules/skills/fuse/SKILL.md` — multi-LLM report consensus

Input: $ARGUMENTS
