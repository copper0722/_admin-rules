---
name: wiki
description: "Wikify any source into vault .md. PDF/URL/text/email → structured .md in vault. Core principle: if not .md, it's forgotten. MANDATORY TRIGGERS: /wiki, wikify, 維基化, 'convert to md', 'save to vault', or drops a PDF/URL."
argument-hint: "[path to PDF | URL | 'text:...' | 'inbox']"
---

# /wiki — Wikify Pipeline

Any source → structured .md → vault. The vault is a private Wikipedia operated by LLM.

## Principle

Wiki section (`wiki/`) = M2M knowledge cache maintained entirely by machine. Auto-iterating. Agents have **FULL AUTHORITY** over all wiki .md — create, update, merge, split, restructure, delete without Copper approval. No human in the loop. Wiki quality is the agent's responsibility. This is the one section of the vault where agents are autonomous owners, not assistants.

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

Every source (OA or not) must be in `article_registry.db` (local) AND cited in at least one wiki .md `## Sources` section.

```
Source enters system → article_registry.db (local DB, doi/pmid/is_oa/status)
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

# Step 2: extract all PMIDs/DOIs from registry
# Local: sqlite3 article_registry.db "SELECT doi FROM articles"
# Cloud: read cloud/data/source_registry.tsv

# Step 3: diff → orphans
comm -23 /tmp/all_sources.txt /tmp/cited_sources.txt > /tmp/orphan_sources.txt

# Step 4: orphans → flag for deletion or wikify
# If source has raw.md → wikify it (fix the gap)
# If source has no raw.md and not OA → archive (not worth processing)
# If source is OA → try to wikify from internet before deleting
```

**Cloud agent support:** Local cron exports DB to `cloud/data/source_registry.tsv` (text, in repo) so cloud can also run orphan scan.

**Bidirectional check:**
- Orphan source (in DB, not cited) → wikify or delete
- Phantom citation (cited in wiki, not in DB) → add to DB

## Entity Hierarchy

| source | output | placement |
|---|---|---|
| PDF (academic, has DOI) | note.md (via /note-writer) | ref/articles/{citationKey}/ |
| PDF (project, no DOI) | raw.md → note.md | proj/{project}/data/ sidecar |
| URL / webpage | .md extract | proj/ or kb/ by topic |
| Email / text | .md capture | proj/ or kb/ by topic |
| Transcript | .md structured | proj/ or copper/ |

PDF is NEVER the primary entity. .md = first-class citizen. PDF = sidecar attachment.

## Workflow

### Mode A: Single file (`/wiki /path/to/file.pdf`)

1. Validate input exists (not 0 bytes, not iCloud placeholder)
2. Detect source type:
   - PDF → Mode A-PDF
   - URL → Mode A-URL
   - Text block → Mode A-Text
3. Determine destination: has DOI? → ref/articles/. Has project? → proj/. Else → kb/

### Mode A-PDF — MANDATORY PIPELINE: PDF → raw.md → note/wiki

**Never skip raw.md.** Every PDF must go through MinerU first. No direct PDF→note.

```
PDF → DEDUP CHECK → MinerU → raw.md (sidecar, type: raw)
                                ↓
                         CC cleanup (簡→繁, LaTeX, tables)
                                ↓
                        ┌───────┴───────┐
                   note.md (if Copper    wiki.md (auto,
                    requests /note-writer)  M2M cache)
```

**STEP 0 — DEDUP CHECKPOINT (before ANY processing):**
1. Extract DOI from PDF filename, first page text, or metadata
2. Query ALL of these (stop at first match):
   - `_data/article_registry.db` → `SELECT uid, status, vault_raw_path FROM articles WHERE doi = ?` (2174 entries, primary dedup source)
   - `_data/textbooks.db` → `SELECT * FROM editions WHERE series_id = ? AND edition = ?` (for textbook chapters, check chapters_raw)
   - `proj/journal/data/journal.db` → `SELECT doi FROM articles WHERE doi = ?`
   - `_data/agent_lookup.db` → search by DOI key
   - `ls ref/articles/` → folder names contain citationKey
3. DOI/uid already exists → **SKIP entirely** (don't re-MinerU, don't re-wikify)
4. No DOI (gov docs, textbook chapters) → check title similarity in existing wiki .md
5. **After processing**: UPDATE `article_registry.db` (set status, vault_raw_path, vault_wiki_path). For textbooks: UPDATE `textbooks.db` chapters_raw count.
6. Log every dedup decision

**STEP 0B — EDITION CHECK (textbooks only):**
1. Check `ref/books/` for all editions of same textbook
2. If newer edition exists in vault → do NOT process older edition
3. Processing order = **year DESC** (newest first, always)

Steps:
1. Copy to /tmp/ if on virtual FS (GDrive, iCloud)
2. **Run MinerU**: `mineru -p {pdf} -o /tmp/mineru_out/ -m auto -b pipeline`
3. **Copy ALL output to sidecar** (raw.md + images/):
   ```bash
   # MinerU outputs to /tmp/mineru_out/{filename}/auto/
   MINERU_OUT="/tmp/mineru_out/{filename}/auto"
   SIDECAR="{citationKey}/"
   cp "$MINERU_OUT"/*.md "$SIDECAR/raw.md"
   # CRITICAL: also copy images folder — without this, image refs in raw.md break
   if [ -d "$MINERU_OUT/images" ]; then
       cp -r "$MINERU_OUT/images" "$SIDECAR/images/"
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
   - Has DOI → citationKey → `ref/articles/{citationKey}/raw.md`
   - No DOI, has project → `proj/{project}/data/{name}/raw.md`
   - No DOI, no project → `kb/{topic}/raw.md`
7. Move PDF to sidecar as `source.pdf`
8. **Simultaneous wiki evaluation** (not a separate step):
   - CC reads the cleaned raw.md
   - Scans existing `wiki/` for related topic
   - Match found → UPDATE existing wiki .md (append new findings, revise if contradicted)
   - No match → CREATE new wiki .md in `wiki/`
   - This is ONE step with raw.md creation, not a batch job later
9. If Copper requests → also generate note.md via /note-writer (on demand)
10. Report: raw.md path, wiki.md path, line count, fixes applied

### Mode A-URL

1. Fetch content via web fetch
2. Extract main content (strip nav/ads)
3. Structure as .md with source URL in frontmatter
4. Write to proj/ or kb/ by topic

### Mode A-Text

1. Parse input text
2. Structure as .md
3. Write to appropriate folder

### Mode B: Inbox triage (`/wiki inbox`)

1. `ls _inbox/` — list all unprocessed files
2. For each file:
   - PDF → queue for Mode A-PDF
   - .md already → review, move to destination
   - Other → convert to .md
3. Process queue sequentially
4. Report: N files wikified, destinations

### Mode C: Batch (`/wiki batch /path/to/folder/`)

1. List all PDFs in folder without .md sidecar
2. Queue all for Mode A-PDF
3. Process sequentially (MinerU is slow, ~5min per large PDF)
4. Report progress

## Hard Rules (card-level, all agents)

**HR-3 TEXTBOOK = LATEST EDITION ONLY.** If newer edition of same textbook exists in vault (`ref/books/`), do NOT wikify older. Archive superseded editions (§1.3).

**HR-4 PROCESSING ORDER = YEAR DESC.** Newest content first. Textbooks: 2026 before 2024. Articles: 2026 before 2021. Newer supersedes older.

**HR-6 UID CHAIN.** Every PDF → raw.md (uid in frontmatter) → Zotero entry (same uid). UID types: `doi:` (CrossRef→Zotero), `isbn:` (Google Books API), `pmid:` (PubMed), `gov:{文號}` (公文 header). Script: `raw-uid-zotero-sync.py` (weekly cron). Orphan = PDF without raw.md or raw.md without UID.

## Rules

- MinerU output is NEVER final — always Claude cleanup
- Known MinerU issues: 簡→繁, LaTeX artifacts, name errors, table misalignment
- If MinerU fails → try pdfminer fallback → if both fail → report, don't retry
- Raw first (§1.8): save MinerU output as raw.md in sidecar, then clean
- Every PDF without .md sidecar = not wikified = invisible to system
- /note-writer handles academic PDF→teaching note (higher quality, more token). /wiki handles bulk conversion.

## AppleScript — Safari PDF Download

```bash
# Navigate to PDF URL and save via Cmd+S (subscription required)
osascript -e "
tell application \"Safari\"
  activate
  open location \"https://www.nejm.org/doi/pdf/10.1056/NEJMoa2100842\"
  delay 6
end tell
tell application \"System Events\"
  tell process \"Safari\"
    keystroke \"s\" using {command down}
    delay 2
    keystroke \"a\" using {command down}
    delay 0.2
    keystroke \"NEJMoa2100842.pdf\"
    delay 0.3
    keystroke \"g\" using {command down, shift down}
    delay 1
    keystroke \"$HOME/Library/CloudStorage/Dropbox/Vault/_inbox/\"
    keystroke return
    delay 1
    keystroke return
    delay 2
  end tell
end tell"
```

## Mode D: EBM Appraisal (absorbed from /med-read, 2026-04-12)

For journal articles + guidelines, wiki evaluation includes full EBM + causal inference appraisal. Source-type routing + Guyatt 3-gate (validity/importance/applicability) + Hernán target trial + DAG.

**Deep methodology reference (when appraising complex studies):**
- `wiki/methodology/wiki_causal_inference.md` — full Hernán digest
- `wiki/methodology/wiki_research_methods_ebm.md` — full Guyatt digest
- `ref/books/Hernan_WhatIf/causal_inference_critical_appraisal_checklists.md` — 70+ checklist items

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

## Supersedes

This skill replaces `/pdf2md`, `/med-read`, `/appraise`, `/condense` (all absorbed 2026-04-12). Old triggers route here.

Input: $ARGUMENTS
