---
type: data
name: wiki-mega
description: |
  Deep medical Q&A skill. Copper asks a clinical / medical / EBM question;
  Opus fans out 5 parallel sub-agents (local wiki_raw + OpenEvidence +
  UpToDate + DynaMed + Gemini CLI grounded web search), then synthesizes
  one concise zh-TW answer with primary-citation table and local-coverage
  gap report. Every invocation produces a saved wiki-human article at
  `personal-website/src/content/notes/public/wiki-human/<slug>/index.md`
  (Copper directive 2026-05-13); chat reply summarises the saved article.
  No `--save` flag — saving is the skill's primary deliverable, not opt-in.

  MANDATORY TRIGGERS: /wiki-mega, /wm, 深查, 大查, mega wiki, /wikimega.
  Trigger requires Q-shape (clinical / medical / EBM question, not source
  ingest). Source-ingest input (PDF / audio / URL / scattered manual paste)
  still goes to /wikify. Single-layer local-only query stays with /wiki.

  Cookie host requirement: invoking session must run on a device whose
  Chrome Beta has live logged-in tabs for UpToDate (CMU proxy), DynaMed,
  and OpenEvidence. Currently hm4 + mbp qualify; cm1 and mba do not.
---

# wiki-mega — 5-source medical Q&A synthesis

Copper directive 2026-05-11: extension of `/wiki` to 5-source fan-out + Opus
synthesis. Per workspace memory `feedback_wiki_search_tri_source.md`:
UpToDate and DynaMed are **peer-reviewed L5 systems**, allowed as navigator
references in tier-honest citation tables but always carrying L5 label.

**OpenEvidence is fundamentally different (Copper directive 2026-05-12).**
OE is a **pure LLM literature aggregator** — no peer review, no editorial
board, no structured editorial pipeline. In the EBM-CC 6S Haynes pyramid OE
is a **blank cell**, not L5. OE in this pipeline serves only as a
**search-side navigator** to discover what primary literature exists; OE's
own summary text is never citable. The honest path when OE returns primary
references the article needs to claim from: **the main Opus does an ad-hoc
WebFetch of the OA full text, reads it, and cites L1 directly with DOI.**
OE-summary numerics are not propagated into article bodies.

**Ad-hoc OA primary fetch rule (Copper directive 2026-05-12).** OA primaries
that support a single specific claim in a single wiki-human article must be
fetched + read + cited L1 in-session. **They are not written into wiki_raw.**
wiki_raw is reserved for cross-article reusable sources (textbook chapters,
guidelines, journal series TOC, regulatory documents). If a primary later
turns out to serve multiple articles, that's when it earns wiki_raw
promotion — parallel to the just-in-time typed-table promote rule in
`tw_health_open.md` runbook.

## Pipeline

```
Question (zh-TW)
  ↓
[Opus restates as precise domain query (refined_q)]
  ↓
5 parallel Agent calls (general-purpose subagent_type, run in single message)
  ├── sub-local      → PG wiki_raw.raw_index + ripgrep wiki_raw + content/wiki
  ├── sub-oe         → scripts/oe.py (OpenEvidence) ← openevidence-skill
  ├── sub-utd        → uptodate-skill (stdlib utd.py + osascript, hm4/mbp Chrome Beta)
  ├── sub-dynamed    → dynamed-skill (stdlib dynamed.py + osascript, hm4/mbp Chrome Beta)
  └── sub-gemini     → gemini -p "<refined_q>" (grounded web search)
  ↓
[Synthesizer: collate, dedupe DOIs, map navigator→primary, gap-check vs
 local wiki_raw, produce concise zh-TW answer]
  ↓
Chat output AND mandatory save to personal-website/src/content/notes/public/wiki-human/<slug>/index.md
```

## Sub-agent prompts

Each sub-agent prompt block below is the literal text the main agent should
pass via `Agent({prompt: ...})`. All five run in one message for parallelism.

### sub-local

```
You are sub-local for /wiki-mega. Query: {refined_q}

Find every local hit in:
  1. PG wiki_raw.raw_index — keyword search on title + body_excerpt
     (psql -h hmj -d vault_main; table wiki_raw.raw_index has columns
     citation_key, title, body_excerpt, raw_md_path)
  2. ripgrep on ~/repos/vault/ (raw .md text)
  3. ripgrep on ~/repos/personal-website/src/content/wiki/ (existing M2M
     wiki synthesis entries)

For each hit return: citation_key | title | path | 1-line relevance to
{refined_q}. Up to 12 hits, prefer textbook chapter > guideline > journal
article > existing wiki entry. Report empty list if nothing relevant.

Output strict markdown table. Under 400 words.
```

### sub-oe

```
You are sub-oe for /wiki-mega. Query: {refined_q}

Invoke the openevidence-skill (its README is at
~/repos/_admin-rules/skills/openevidence-skill/SKILL.md; the worker
script is scripts/oe.py inside that skill). Pass {refined_q} as the
question. Wait for the OE answer.

Return: (1) OE bottom-line in 2-3 sentences (translate to zh-TW), (2)
full citation list with DOI/PMID + first-author + year + journal. Do
NOT add commentary; report exactly what OE said.

**Disclaim openly in your output**: "OE is a pure LLM aggregator (no
peer review, 6S blank); the citations below are search-navigator hits.
The main Opus must ad-hoc fetch + read OA primary full text before
citing any of these as L1 in article body."

**Watch for conflation in the OE summary text**: OE may incorrectly
attribute findings across primary papers (e.g., conflating two
related studies under one sentence). Do not assert specifics from OE
narrative as if verified primary content — surface them as
"OE-claims-this, needs primary verification."

Under 500 words.
```

### sub-utd

```
You are sub-utd for /wiki-mega. Query: {refined_q}, host: {host}.

Use uptodate-skill — stdlib Python CLI that drives the logged-in Chrome
Beta tab via osascript. Each topic snapshot becomes a proper raw entry
under wiki_raw and registers in PG (source_type=clinical_database,
cite_directly=false flag preserved on the snapshot).

Flow:
  1. auth-status:
       python3 ~/repos/_admin-rules/skills/uptodate-skill/scripts/utd.py \
         --host {host} auth-status
     If authenticated=false, report unavailable + the hint string; do
     not attempt search/topic.

  2. search:
       python3 ~/repos/_admin-rules/skills/uptodate-skill/scripts/utd.py \
         --host {host} search "{refined_q}" --max 5
     Get top 5 topic title + URL pairs.

  3. Semantic pick: from the 5 results, pick 1-3 topics that most
     directly address {refined_q}. Drop sibling pages that share the
     disease but cover a different facet (e.g., pathogenesis when the
     query is about treatment). Report your picks + why.

  4. Decide topic_path under wiki_raw for each pick. Use existing PG
     wiki_raw.folder_registry to align with the canonical topic tree:
       psql -h hmj -d vault_main -c \
         "SELECT topic_path FROM wiki_raw.folder_registry \
          WHERE topic_path ILIKE '%<keyword>%' LIMIT 5;"
     Pick the most specific matching folder; if none matches, fall back
     to the closest parent topic_path.

  5. Download each pick:
       python3 ~/repos/_admin-rules/skills/uptodate-skill/scripts/utd.py \
         --host {host} topic "{top-result-url}" \
         --save-to-wiki-raw \
         --target-dir "<topic_path>" \
         --query-origin "{refined_q}"
     The script writes raw.md to wiki_raw/<topic_path>/UpToDate_<slug>_
     <YYYYMMDD>/raw.md and INSERTs a PG row with the publisher's
     constructed recommended_citation in publisher_metadata.

  6. Report:
     - 1-2 sentence zh-TW bottom-line summary of what UTD says on the
       query.
     - Picks list: title + URL + topic_path + citation_key (each picked)
     - Primary citation pointers from each raw.md (PubMed/DOI links in
       the body).

UpToDate is NAVIGATOR by internal policy (cite_directly=false flag).
Final answer synthesis cites the primary refs UTD's body points to, not
UTD itself; but the saved raw.md + PG row carry the publisher's
recommended_citation so a downstream reader-facing piece CAN cite UTD
explicitly when invoked.

Output strict markdown. Under 700 words.
```

### sub-dynamed

```
You are sub-dynamed for /wiki-mega. Query: {refined_q}, host: {host}.

Same flow as sub-utd, using the dynamed-skill CLI:

  python3 ~/repos/_admin-rules/skills/dynamed-skill/scripts/dynamed.py \
    --host {host} auth-status

  python3 ~/repos/_admin-rules/skills/dynamed-skill/scripts/dynamed.py \
    --host {host} search "{refined_q}" --max 5

  python3 ~/repos/_admin-rules/skills/dynamed-skill/scripts/dynamed.py \
    --host {host} topic "{picked-result-url}" \
    --save-to-wiki-raw --target-dir "<topic_path>" \
    --query-origin "{refined_q}"

DynaMed sometimes returns broader-category topics rather than a
named-disease topic (e.g., "IgA nephropathy treatment" → "Glomerular
Disease in Adults - Approach to the Patient"). Pick the topic whose
overview text most directly addresses the query.

Saved raw.md = wiki_raw/<topic_path>/DynaMed_<slug>_<YYYYMMDD>/raw.md
PG row: source_type=clinical_database, journal=DynaMed,
publisher=EBSCO Information Services, recommended_citation constructed
from page metadata (title + Updated date + URL + accessed date).

Cite-by-key downstream. cite_directly=false flag = internal policy
preference for primary refs.

Output strict markdown. Under 700 words.
```

### sub-gemini

```
You are sub-gemini for /wiki-mega. Query: {refined_q}

Run: gemini -p "{refined_q (English-translated if zh-TW source) + 'Cite
DOIs / PMIDs / guideline names. Limit answer to <600 words.'}"

Gemini CLI has built-in google_web_search + web_fetch tools and will
automatically ground the answer. Capture stdout.

Return: (1) Gemini's bottom-line in 2-3 sentences (translate to zh-TW),
(2) primary citation list it surfaced (deduplicate to DOI / PMID /
guideline-name). Flag any source that is a society guideline or position
statement vs an RCT/meta-analysis vs a news/secondary source.

Under 600 words. If gemini binary returns nonzero exit or empty stdout,
report the error and stop; do not retry indefinitely.
```

## Synthesizer (main Opus)

After all 5 sub-agents return, the main Opus does:

1. **Collate**: build a single primary-citation list. Source for each
   citation: which sub-agents cited it.
2. **Dedupe by DOI/PMID/guideline-uid**. Aliases (DOI variants, PubMed
   citation strings) collapse.
3. **Map navigator → primary**: UTD, DynaMed, and OE entries all become
   navigator labels on a primary-ref row, never standalone rows.
   - UTD / DynaMed = peer-reviewed L5 systems (may also stand as L5 cite
     in the wiki-human refs table)
   - OE = LLM aggregator (6S blank); strictly navigator only — never appears
     as a citation row, only in the `Surfaced by` column as a discovery hint
   - If a navigator claim has no primary cite, mark `[no primary ref found]`
     and downgrade to a parenthetical secondary note in the answer.

4. **Ad-hoc OA primary fetch (mandatory before article-body claims)**:
   For each primary DOI/PMID from sub-oe / sub-gemini / UTD or DynaMed
   reference panel that the answer will rely on for numerical or
   trial-specific claims, the main Opus must:
   - WebFetch the DOI URL (follow redirects)
   - Read the OA full text; if paywalled, mark 🟡 and either skip the
     specific numeric or label the claim "via L5 navigator" without
     numerics
   - Cite L1 directly with verified DOI; do not save the fetched paper
     into wiki_raw (ad-hoc rule)
   - Cross-check OE / UTD / DynaMed summary against primary — flag any
     conflation discovered (the canonical example: OE-summary said
     "zebrafish 39% prevalence" but the underlying primary paper
     studied a marine goby, not zebrafish — see CMNV case 2026-05-12).
5. **Local coverage gap check**: for each unique primary DOI/PMID,
   query PG `wiki_raw.raw_index` + `wiki_raw.raw_source_metadata` for
   `doi=` or `citation_key like`. Mark each row ✓ if local raw exists, ✗
   if not. **Note**: ✗ is fine for wiki-human ad-hoc fetch (just means
   the agent read it in-session). The ✗ → wiki_raw migration only
   happens when the same primary serves multiple articles.

6. **Compose final answer** in zh-TW (apply fb-pipeline language style:
   no em-dash sentence-joiners, restrained inline English):

```
# Q: {restated question}

▎結論
{1-3 sentence bottom line, zh-TW}

▎來源比對
- 本地 wiki_raw / textbook: {1-line summary of sub-local result}
- OpenEvidence: {1-line summary of sub-oe result}
- UpToDate (navigator): {1-line summary, references mapped to primary
  table below}
- DynaMed (navigator): {1-line summary, references mapped to primary
  table below}
- Gemini grounded search: {1-line summary, distinguishing guideline /
  RCT / secondary source coverage}

▎Primary citation 表

| 主張 | Primary ref (DOI / PMID / guideline) | Surfaced by | 本地 wiki_raw |
|---|---|---|---|
| ... | 10.xxx/yyy | local + UTD nav + Gemini | ✓ |
| ... | KDIGO 2024 CKD Guideline | DynaMed nav + Gemini | ✓ |
| ... | NEJM 2024;XXX:YYY | OE + Gemini | ✗ → /journal-download |

▎本地覆蓋缺口
- 下列 primary ref 為外源引用但本地 raw 不存在，建議補抓：
  - DOI 10.xxx/yyy ({journal} {year}) → /journal-download or /wikify
  - {guideline name} → /wikify (manual fetch)
- 若 0 缺口：寫「本地覆蓋完整」
```

<<<<<<< Updated upstream
7. **Optional save → `wiki-human` article (Copper directive 2026-05-11)**:
   if invocation included `--save`, write the composed answer as a new
=======
6. **Mandatory wiki-human save (Copper directive 2026-05-13)**: every
   `/wiki-mega` invocation writes the composed answer as a new
>>>>>>> Stashed changes
   `note_type: wiki-human` public article at
   `~/repos/personal-website/src/content/notes/public/wiki-human/{slug}/index.md`.
   This is the skill's primary deliverable; the chat reply is a
   summary that points at the saved article path. There is no flag
   and no opt-in — `/wiki-mega` without a saved article is a failed
   invocation. If the save step is blocked (filesystem error, slug
   collision, sync-guard refusal), report the blocker explicitly and
   do not silently degrade to chat-only.

   Slug convention: `<topic-slug>-<YYYY-MM>` (e.g.
   `dizziness-history-taking-2026-05`), matching the existing
   `wiki-human/` slug pattern. On collision, append `-v2` / `-v3`
   incrementally; do not overwrite an existing article unless the
   user explicitly asks for an update.

   `wiki-human` is a **versatile public article type** (`notes`
   collection, `note_type: wiki-human`); `/wiki-mega` is ONE producer
   pipeline among several. Other wiki-human producers, out of scope for
   this skill: drug-indication articles built from TFDA 藥證 + NHI 給付
   + 仿單 cross-references; policy explainers built from MOHW 公告; etc.
   Each producer pipeline uses different source-tier mixes appropriate
   to its topic.

   Contrast with the other synthesis surface this workspace runs:
   - **`wiki-llm`** (canonical `wiki/` collection at
     `src/content/wiki/{slug}.md`) — M2M compressed English, autonomous,
     aimed at agent retrieval + AEO. `/wiki-mega` does NOT write
     wiki-llm entries.
   - **`wiki-human`** (`notes` collection, `note_type: wiki-human`) —
     reader-facing public article. Citation policy = **EBM-CC 6S
     Haynes pyramid tier-annotated** (Copper directive 2026-05-11).
     Each reference row carries its 6S level; the article freely cites
     synthesis layers (L2–L5) including guidelines and clinical
     databases, but each citation is labeled honestly so readers can
     see whether the claim rests on a primary trial, a meta-analysis,
     a guideline recommendation, or a clinical-database summary.

   **EBM-CC 6S levels used for wiki-human citation tier labels:**

   | 6S level | Type | Examples |
   |---|---|---|
   | L1 Studies | Primary research | RCT / cohort / case-control / lab study |
   | L2 Syntheses | Systematic reviews / meta-analyses | Cochrane review, journal-curated SR/MA |
   | L3 Synopses of syntheses | Pre-appraised summaries of SR/MA | ACP Journal Club, DARE summaries |
   | L4 Summaries | Practice guidelines + textbook chapters | KDIGO / ADA / ESH / AHA guideline, Harrison's / Brenner & Rector's chapter |
   | L5 Systems | **Peer-reviewed** point-of-care integrated CDSS | UpToDate topic, DynaMed topic, BMJ Best Practice topic |
   | (no tier) | LLM aggregator, no peer review | OpenEvidence — never appears in citation rows |

   Notes:
   - L4 + L5 distinction: 6S puts guideline and textbook at L4
     (Summaries) and UTD/DynaMed/BMJ-BP at L5 (Systems), because
     L5 integrates more downstream layers and supports point-of-care
     use. L5 requires peer-reviewed editorial process.
   - **OpenEvidence is NOT L5** (Copper directive 2026-05-12). OE has
     no peer review, no editorial board, no structured editorial
     pipeline; it is a pure LLM literature aggregator. In the 6S
     pyramid OE is a blank cell. Label OE in reference notes as
     `[LLM aggregator — 無 peer review、6S 空白]` only when retaining
     audit-trail; never appear in the main citation list with L? tag.
   - Guideline is NOT pure-tertiary: it has GRADE-style commissioned
     systematic review (L2) under the hood + expert-panel
     evidence-to-recommendation pipeline. The 6S "Summary" label
     captures this hybrid honestly.
   - For wiki-human articles, citation hygiene Law still applies: each
     ref must be one the agent actually read (in-session WebFetch is
     OK; cross-article persistence not required). Tier labels are
     honest; no name-dropping primary RCTs the agent did not read.
   - **Ad-hoc OA primary fetch path**: when OE / UTD / DynaMed
     surfaces a primary DOI that the article needs, the main Opus
     WebFetches the OA full text in-session, reads, cites L1
     directly. Do not persist the paper to wiki_raw (one-off rule).

   wiki-human article shape:
   ```yaml
   ---
   title: {restated question as title}
   published: {today}
   last_reviewed: {today}
   note_type: wiki-human
   visibility: public
   medical_audience: [Physician]   # or [GeneralPublic] when applicable
   topic: [<list>]
   topic_path: <from sub-utd/sub-dynamed pick or from PG folder_registry>
   tags: [<from query domain>]
   references_count: N
   ---

   # {title — zh-TW phrasing of question}

   {1-3 sentence bottom-line zh-TW}

   ## 主題核心

   {3-6 paragraph synthesis, zh-TW, applying fb-pipeline language style
    (no em-dash sentence-joiners, restrained inline English).}

   ## 文獻參考

   | 主張 | 文獻 | 6S level |
   |---|---|---|
   | ... | Brenner & Rector's The Kidney, 12e, Ch. 32 | L4 Summary (textbook) |
   | ... | KDIGO 2024 Glomerular Diseases Guideline | L4 Summary (guideline) |
   | ... | UpToDate, "IgA nephropathy: Treatment and prognosis", Topic 3039 v83.0, accessed 2026-05-11 | L5 System |
   | ... | DynaMed, "Glomerular Disease in Adults — Approach to the Patient", updated 10 Jul 2025 | L5 System |
   | ... | Floege J et al. NEJM 2024;390:1234. doi:10.1056/NEJMra2400000 | L2 Synthesis (journal-curated review) |
   | ... | NefIgArd trial: Lafayette RA et al. Lancet 2023. doi:... | L1 Studies (pivotal RCT) |

   Each row's 6S level is required; this is the citation-tier
   transparency wiki-human exists to deliver. Article may cite any
   mix of L1–L5 appropriate to the topic; per citation hygiene Law,
   every ref must be one the agent actually read.
   ```

   `references_count` counts the citation rows. `topic_path` follows
   existing PG `wiki_raw.folder_registry` topology so the article lands
   in `/topics/{topic_path}/` browsing.

   Citation strings for the clinical-database snapshots (UTD, DynaMed)
   come from `publisher_metadata.recommended_citation` saved by sub-utd /
   sub-dynamed in step 5. Look them up from PG via:
   ```sql
   SELECT publisher_metadata->>'recommended_citation'
   FROM wiki_raw.raw_source_metadata
   WHERE citation_key = '<key>';
   ```

   wiki-human does NOT replace the canonical `wiki/` (wiki-llm). Both
   live; they serve different audiences. `wiki-llm` for AEO / agent
   research depth; `wiki-human` for Copper-facing readership at a
   defined tertiary tier.

## Citation hygiene reminders

- **UpToDate / DynaMed**: peer-reviewed L5 systems. May appear as L5
  citation rows in wiki-human refs table, but only after the agent
  saved the snapshot raw and read it. The article's specific
  numerical / trial-name claims should still trace to L1 primary via
  ad-hoc fetch; UTD/DynaMed prose alone supports only qualitative
  positions.
- **OpenEvidence**: 6S blank — LLM aggregator with no peer review.
  Never appears as a citation row in the article. OE may only appear
  in: (a) the `Surfaced by` column of the synthesizer's primary-cite
  table, (b) optional audit-trail block in the article's 「文獻層級
  說明」 noting how primary refs were discovered. Cite primaries
  directly after ad-hoc OA fetch.
- **Conflation watch**: OE summary text may incorrectly attribute
  findings across multiple primary papers. Always cross-check the
  fetched primary's actual subject/species/methods vs OE's claim. The
  CMNV case (2026-05-12): OE said "zebrafish 39% prevalence" but
  Zhang QL 2018 *Front Microbiol* actually studied marine goby
  *Mugilogobius abei*, not zebrafish; the zebrafish data is in a
  different (paywalled) paper. Such conflation is a recurring risk
  with LLM-aggregator surfaces.
- **Gemini grounded answer**: prefer the underlying source it pulls.
  Gemini text alone is not citable.
- **Local wiki_raw raw .md**: directly citable (citation_key + path).
- **Local synthesized wiki entry**: linkable, but the original
  primary source that wiki entry rests on is the citable atom.
- **Ad-hoc OA primary fetched in-session**: directly citable with
  DOI; no requirement to persist to wiki_raw (one-off rule).

## Cross-refs

- `/wiki` skill: `_admin-rules/skills/wiki/SKILL.md` — local-only 3-layer
  fast query, kept as the default for routine ad-hoc questions.
- `/openevidence-skill`: `_admin-rules/skills/openevidence-skill/SKILL.md`
  — OE worker invoked by sub-oe.
- `/wikify`: `_admin-rules/skills/wikify/SKILL.md` — destination for gap
  closure (PDF/audio/URL ingest into local raw).
- `/journal-download`: `_admin-rules/skills/journal-download/SKILL.md` —
  destination for journal article gap closure.
- `feedback_wiki_search_tri_source.md` memory: governs UTD/DynaMed
  navigator-only rule.
- `feedback_fb_no_em_dash_zhtw_default.md` memory: language style for
  Copper-facing chat output.
- `peak-hours.md`: Gemini CLI is allowed as web-search worker; Cloud
  Gemma 4 remains banned in interactive sessions.

## Notes

- Run sub-agents in parallel: single Agent message with 5 tool-use
  blocks. Do not run sequentially; sequential adds ~5× latency.
- Per sub-agent runtime cap: 90 seconds soft, 180 seconds hard. If a
  sub-agent times out or errors, the synthesizer continues with the
  remaining sources and explicitly marks the failed source as `unavailable`
  in the source-comparison block.
- Refresh frequency: each invocation is one-shot; no caching. UpToDate /
  DynaMed pages change; staleness avoided by re-fetching every call.
- Cookie host fail mode: if chrome-devtools cannot reach Chrome Beta on
  the current device, abort sub-utd / sub-dynamed and tell Copper to
  switch to mbp / hm4 (whichever has live logged-in tabs).
