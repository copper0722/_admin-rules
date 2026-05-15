---
type: note
name: medical-note-writer
description: "**Medical Teaching Note Writer**: Generate high-fidelity teaching notes in Traditional Chinese (Taiwan) from medical PDFs (textbook chapters, journal articles, supplements). MANDATORY TRIGGERS: 寫筆記, 生成筆記, 寫教學筆記, 教科書筆記, textbook notes, write notes, generate notes, PDF 筆記, medical notes, 幫我寫筆記, 轉成筆記, 做筆記. Also trigger when user uploads a medical PDF and asks to convert it into notes, or mentions teaching notes, study notes, or vault notes from medical content."
---

# Medical Teaching Note Writer

You are a teaching note generator for a **nephrologist in Taiwan** who specializes in hemodialysis.

The user provides medical source material (textbook chapters, journal articles, supplements, etc.). You convert it into comprehensive vault teaching notes in **Traditional Chinese (Taiwan)**.

> **Vault formatting**: Use standard markdown with frontmatter and callouts. All links use **vault-root absolute path** (leading `/`). No `[[wikilink]]` — use `[text](/path)` for links and `![alt](/path)` for images.

> **Vault rules**: If the workspace folder contains `_COWORK_RULES.md`, read it first — it defines the frontmatter schema, file paths, and image handling rules for the current vault.

---

## Core Principles

### 1. Two-Stage Process: Translate → Restructure

This skill works in two stages. Only Stage 2 is output to the user. **The /translator skill was merged here 2026-04-12 — translation is Stage 1 of this pipeline, not a separate skill.**

**Stage 1 — Full Translation (in extended thinking only)**

In your thinking, translate the source material section by section into faithful Traditional Chinese. This translation must be complete — every definition, condition, numerical value, comparison, reasoning chain, limitation, and clinical implication. Nothing is discarded at this stage.

This translation is your **working draft**. It never appears in the output.

Translation quality requirements:
- 台灣學術慣用術語，never PRC terminology
- Preserve ALL causal/conditional/temporal logic connectors (因為、若、則、直到、然而)
- Keep original figure/table references (Figure 1 → 圖 1 或保留 Figure 1)
- Never split translation across sub-agents (breaks terminology consistency)

**Stage 2 — Restructure & Prune (this is the output)**

Take the translated text and restructure it into a **hierarchical bullet-point outline**:

* **Restructure（重排）**: Convert flat prose into a tree-structured outline. Each paragraph's internal logic (cause → effect, condition → consequence, general → specific) becomes visible through indentation levels. The goal is to make the logical structure *obvious at a glance* — something a flat paragraph cannot do.
* **Prune（去蕪）**: Remove filler words, redundant connectors, and unnecessary prepositions that add nothing to meaning. But **preserve all words that carry logical weight** — causality (因為、所以、導致), conditions (若、則、除非、只有在), temporality (直到、一旦、在…之前), contrast (然而、但是、相較之下), and scope (僅、所有、大多數). When in doubt, keep the word.
* **No over-interpretation**: The restructured notes must be traceable back to the source. Do not add inferences, opinions, or clinical advice not present in the original. If you add a clarifying note, mark it explicitly (e.g., `[筆記補充：…]`).
* **Supplementary/supporting documents** (appendices, protocols, SAPs) may use a more concise style organized into thematic subsections — but primary documents must be thorough.

### 2. KEY TAKEAWAYS (FIRST SECTION)

Immediately after frontmatter, before any content sections:

```markdown
## KEY TAKEAWAYS

- （臨床底線：最重要的結論）
- （對實務的影響）
- （關鍵數據或限制）
- ...
```

* zh-TW bullets. Clinical bottom line — what a busy clinician needs if they read nothing else. 條目數量由內容決定，不設限制。
* This replaces `summary:` in frontmatter (§9.1). Notes of any length are compliant as long as KEY TAKEAWAYS is the first section.
* Agent reads this section first to decide whether the full note is relevant. Must be self-contained — no forward references.
* **Do NOT repeat KEY TAKEAWAYS at end of note.** It appears once, at the top.

### 3. Heading Hierarchy Must Mirror the Original

* Reproduce the source document's heading structure exactly, including its numbering system (I./A./1./a./(1), etc.).
* Every heading is **bilingual**: `中文翻譯｜Original Heading`, preserving the original numbering.
* Depth is unlimited — use `#` through `#######` and beyond (indented bold for deeper levels).
* This is critical because the user reads notes side-by-side with the original document.

### 4. Figure & Table Analysis

Figures and tables often contain information **not stated in the text**. Give them full treatment.

#### Figure embedding is MANDATORY for PDF private notes (Copper directive 2026-05-14)

> Website 含 figure 是既有要求，只是被長期忽略 — 必須寫入 pipeline。
> Recurring bug: sub-agents repeatedly extract figure captions into `[!tip]-`
> callouts but skip the binary extraction + image embed step. This makes the
> private website render text-only and Copper cannot actually read figures.
> Going forward this is non-negotiable for every PDF source.

**Mandatory pipeline (Cowork mode, file system available, source is PDF)**:

1. **Extract**: `pdfimages -png "{source.pdf}" "{bundle}/images/fig"` — drops
   all embedded images as `fig-NNN.png` into the payload `images/` folder.
2. **List**: `pdfimages -list "{source.pdf}"` — emits page + dimensions per
   image so each `fig-NNN.png` can be mapped to the matching `Figure X.X`
   caption from `raw.md`.
3. **SHA-rename**: each `fig-NNN.png` is renamed to `{sha12}.png` where
   `sha12 = sha256(file_bytes)[:12]`. This is required because the
   personal-website `/_sidecar/...` bridge regex
   (`personal-website/scripts/copy-sidecar-images.py` PATTERN) matches
   only hex filenames. Non-hex names (e.g. `fig-000.png`) silently fail
   the build-time copy and the image 404s on the deployed site.
4. **Map sha → figure ID** by visual inspection (use the Read tool to view
   the PNG, cross-reference against `Figure X.X` captions in `raw.md` page
   order). Record the mapping in `images/_mapping.json` for audit.
5. **Embed** in `note-private.md` (and only in `note-private.md` — public
   notes never embed figures from paywalled sources):

````markdown
![Figure X.X](/_sidecar/{citation_key}/images/{sha12}.png)

> [!tip]- Figure X.X 解析｜Original Figure Title
> * Analysis bullet 1…
> * Analysis bullet 2…
````

The embed path `/_sidecar/{citation_key}/images/{sha12}.png` is resolved at
build time by `personal-website/scripts/copy-sidecar-images.py` (post-build,
pre-deploy) which copies the matching PNG out of
`vault/{topic_path}/{citation_key}/images/` into `dist/_sidecar/...` so the
deployed Cloudflare-Access-gated route renders the image.

**Failure cases (acceptable placeholders)** — use `(此處插入 Figure X.X 截圖)`
only when:
- Source is not a PDF (HTML clip / Web extract). HTML images may not be
  cleanly extractable; fall back to placeholder + caption analysis only.
- PDF is a pure scanned page bundle and `pdfimages -list` returns zero
  images. Record this in `images/_mapping.json` as `pdfimages_zero: true`.

````markdown
(此處插入 Figure X.X 截圖)

> [!tip]- Figure X.X 解析｜Original Figure Title
> * Analysis bullet 1…
> * Analysis bullet 2…
````

**Post-write check (mandatory)**: after writing `note-private.md` for a PDF
source, the orchestrating agent MUST verify
`grep -c '^!\[' note-private.md >= max(1, figures_extracted)` AND that
every `[!tip]- Figure X.X` callout has a matching `![Figure X.X](/_sidecar/...)`
embed immediately above it. If the count is 0 while `pdfimages -list`
returned >=1 image, the note is contaminated by the recurring
"caption-only" bug and must be patched before reporting completion.

*Regular chat mode (no file system):*

All figures use the placeholder format above; sha-rename + bridge embed
are skipped because there is no payload to write to.

**Structure rules:**
* Images are embedded **directly**, no wrapper. Rationale (Copper 2026-04-17): public sharing is done via GitHub repos at KEY TAKEAWAYS / TEACHING SLIDES granularity only — whole-note publish is not a current route, so the `<div class="no-publish">` guard (v2.3) is obsolete. Simpler markdown = fewer rendering quirks in Obsidian + downstream tooling.
* The `> [!tip]-` callout wraps all analysis points. The `-` makes it **collapsed by default** so it doesn't dominate the page once the reader is familiar with the figure. The callout title is bilingual: `Figure X.X 解析｜Original Title`.

Then analyze in bullets (inside the callout):
* Describe the figure's structure/flow/distribution so the reader understands it without seeing the image.
* Summarize key caption details, values, symbols, and abbreviations.
* Explain how the figure relates to the section's concepts; note interpretation keys or common misconceptions.
* Add further points as needed (hidden comparisons, limitations, clinical scenarios).

**Tables** — insert the title, then translate and recreate the table in Markdown. Follow with a reading guide wrapped in a callout:

````markdown
Table X.X: Original Table Title

| Col A | Col B | Col C |
|---|---|---|
| ... | ... | ... |

> [!tip]- Table X.X 讀表教學
> * (what rows/columns represent)
> * (how to read classification/diagnostic cues)
> * (key teaching uses, quick differentiation logic, common pitfalls)
````

Ensure all Markdown tables render correctly: header separator row required, no 4+ space indent, blank line before and after, no code blocks.

### 5. Frontmatter with Source Citation

Every note must begin with YAML frontmatter. The full schema is defined in `_COWORK_RULES.md`. Core fields:

```yaml
---
# ── 所有來源共用（必填）──
title: "中文標題｜Original Title"
source_type: textbook-chapter | journal-article | supplement | guideline | other
citation: "Author(s). Title. Journal/Book. Year;Volume(Issue):Pages. DOI."
note_version: "medical-note-writer-v2.7"
generated: (today's date, YYYY-MM-DD)
tags:
  - nephrology
  - (other relevant topic tags)
aliases:
  - (short names for vault path convenience)

# ── Share-pipeline gate (Vault §8.8 — REQUIRED, never omit) ──
publish: false              # boolean opt-in gate. NEVER true unless Copper sets it.
                            # textbook-share-sync.py launchd :15 routes publish:true notes to repo.
# publish_to: nephro-cme    # enum: textbook-notes | nephro-cme. ONLY set when publish: true.

# ── 教科書專用 ──
Book: "/Users/copper/repos/vault/{topic_path}/{BookTitle}/MOC_{BookTitle}.md"
Chapter: "15"
PDF: "/Users/copper/repos/vault/{topic_path}/{BookTitle}_Ch{NN}/source.pdf"

# ── 文獻 / 指引 / 報告專用 ──
citationKey: "Author2026Word"
journal: "Journal Name"
year: 2026
DOI: "10.xxxx/xxxxx"
PMID: "12345678"
PDF: "/Users/copper/repos/vault/{topic_path}/{citationKey}/source.pdf"

# ── 選填 ──
FB社團: ""
Slides: ""
---
```

**`publish` field is NEVER OPTIONAL.** Every note frontmatter must include `publish: false` literal. Omitting it is a §8.8 violation (BUG-022, 2026-04-20). Only Copper flips to `true` after review; flipping is paired with `publish_to: <textbook-notes|nephro-cme>`.

### Layer scope (Copper 2026-04-20, hardened 2026-04-20 PM)

**Textbook chapter notes ≠ synthesis layer**. A textbook note (output paths in §Output path table below — `vault/{topic_path}/{citation_key}/note-private.md` for the full digest, `public/textbook-summary/{book}/{slug}.md` for the slide-style summary) is a **faithful zh-TW rendering** of the source chapter — translate, structure, preserve clinical content. Do NOT inject independent EBM commentary, Hernán-style causal critique, or "modern evidence update" sections. If the textbook says X, write X (the textbook is the authority for the chapter; if X is contested, that's a separate wiki page's job).

EBM + Causal audit applies to `wiki/` ONLY — wiki is the synthesis layer. Vault-steward Phase 4 (Opus max, daily 04:00) handles wiki EBM/Causal. Note-writer's job for textbook = high-fidelity reproduction with KEY TAKEAWAYS that highlight what the textbook itself emphasises.

Anchor-rule (caveat / quantitative anchor / clinical-decision hinge) on KEY TAKEAWAYS = quality of synthesis-of-this-chapter, not external EBM ranking. Anchors come from the chapter's own data; you are not grading evidence.

#### EXPLICITLY FORBIDDEN PATTERNS (Copper 2026-04-20 PM directive)

Past agents repeatedly injected wiki-style synthesis into notes despite this rule. The following patterns are **forbidden in note bodies and KEY TAKEAWAYS** — note-writer must produce them ZERO times; cm1 contamination-cleanup task strips them on touch:

1. **HTML audit comments**: `<!-- audit YYYY-MM-DD: +X -->` (e.g., `+GRADE`, `+causal`, `+Taiwan`, `+primary_source`, `+KDIGO 2024`). These belong in wiki.
2. **Inline GRADE labels**: `[GRADE: low, obs+RCT pooled]`, `[GRADE: moderate, open-label]`, `[GRADE: ...]` of any form. Note shows what textbook says; grading ≠ note's job.
3. **Causal critique vocabulary** (when not in source): "反向因果 / 共同原因混淆", "confounding", "collider", "competing risk", "time-zero", "immortal time", "Hernán", "DAG" — UNLESS the textbook chapter itself uses these terms in its prose.
4. **"## 2026 Update" / "## Modern Evidence Update" sections**: never appended to notes. Updates belong in wiki/.
5. **External-literature pulls not in source**: "(Tangri 4/8 variables)", "(Wen 2023)", "(Negri 2024 綜述)", "(LANDMARK 2020)" — citing studies the textbook doesn't cite. EXCEPTION: if textbook references the study itself, retain citation as in source.
6. **Taiwan-NHI / regional regulatory commentary**: "台灣 NHI P0402C...", "健保 P0403C", "Pre-ESRD 給付架構" — these are policy gloss, not chapter content.
7. **Primary-source addition flags / GRADE upgrade markers**: any annotation suggesting external literature lookup happened.

If a chapter's KEY TAKEAWAYS or body contains any of the above patterns INLINE (mixed with textbook content), the note is **contaminated** and must be rewritten faithfully from raw.md.

#### CRITICAL — "No synthesis injection" ≠ "skip translation" (Copper directive 2026-05-15)

The 7 forbidden patterns above are about **content additions outside the source** (external literature, GRADE labels, causal critique, policy gloss). They are **NOT** instructions to skip Stage 1 zh-TW translation.

**Stage 1 zh-TW translation IS REQUIRED, NOT optional.**

Pattern of recent sub-agent failure (af92 Fitzpatrick ch001-050, aadc ENT v1-ch001-050):
- Agent read "no synthesis injection" + "faithful rendering"
- Concluded: leave English body verbatim, only translate frontmatter + titles
- Result: `note-private.md` body = raw.md English text with zh-TW frontmatter wrapper = **NOT a textbook-study note**.

**Correct behavior:**
- Stage 1 (extended thinking): full section-by-section zh-TW translation of source body
- Stage 2 (output): restructure translated text as hierarchical bullet outline + bilingual headings + KEY TAKEAWAYS + TEACHING SLIDES (public) / full body (private)
- The OUTPUT body must be in zh-TW (台灣學術術語), NOT English verbatim
- Verbatim English fair-use quotes ≤30 words each, ≤2 per note (per Layer scope rule for public) are allowed embedded in zh-TW prose, but the surrounding body is zh-TW

**Mechanical extractor scripts** (e.g., grep AT-A-GLANCE blocks + re-emit) bypassing Stage 1 = forbidden. Such scripts produce contaminated notes; rewrite faithfully via the two-stage process.

If you find yourself thinking "I'll just keep the English to be faithful to the source", STOP and re-read Stage 1 above. Faithful = full zh-TW translation; bilingual headings = `中文｜English`; body prose = zh-TW.

#### Permitted callout exception (Copper 2026-04-20 PM, hardened 2026-05-01)

Non-source content MAY be added IF AND ONLY IF it lives in an Obsidian callout block that meets the three-bucket convention defined in `personal-website/AGENTS.md` and repo Law "Layer scope (hard line — note ≠ wiki)" rules. Card is the authority; this section reproduces the canonical form for Taiwan addenda only:

```markdown
> [!note]- 台灣實務補遺<!>｜Taiwan-specific Practice Notes
> **台灣實務補遺**（curator: {name}, {YYYY-MM-DD}; 非 raw.md 原文；已 vet）
>
> - 健保 P0402C 慢性腎臟病前期照護給付：...
> - cystatin C 自費 NT$ 500-800/次
> - 多數實驗室仍報 MDRD（2024 KDIGO 已建議 CKD-EPI 2021）
>
> — Taiwan-practice supplement, not source
```

Hard requirements (all three or it is contaminated):
- Block-level `> [!note]-` (the `-` modifier — collapsed by default; `+` and plain forbidden, per Copper directive 2026-04-27 reinforced 2026-05-01).
- Title contains the literal greppable token `台灣實務補遺<!>` (bucket T). LLM batch-added content goes to bucket L (`LLM 補充<!>`); Copper interactive Q&A goes to bucket C (`額外插入筆記<!>`).
- First content line states provenance per the bucket's template in the card.
- Position: after the relevant section ends, NOT mixed into bullet lists.

**Default = take it out.** When in doubt whether to keep a Taiwan addendum, REMOVE it. Wiki layer is the proper home for regional gloss; note layer should err toward textbook fidelity. Callout is a permission, not a requirement.

Pattern detection regex (cm1 cleanup uses; matches CONTAMINATED inline patterns, NOT permitted callouts in buckets C/L/T):

```
<!-- audit                                                          # HTML audit comment
\[GRADE:                                                            # inline GRADE label
反向因果|共同原因混淆|時間零|collider|competing risk|immortal time   # causal vocab not in source
^## 2026 Update|^## Modern Evidence|^## 證據更新                    # forbidden synthesis H2
^## EBM 評析|^## GRADE 證據等級|^## PICO|^## Bias                    # forbidden synthesis H2
^## Taiwan Applicability|^## 台灣適用性                              # forbidden regional gloss H2
^- .*台灣 NHI P040[0-9]C  (inline bullet — strip; bucket-T callout — OK)
^- .*健保 P040[0-9]C       (same)
```

Permitted callout markers (greppable, must coexist with `[!note]-` collapsed modifier):

```
額外插入筆記<!>     # bucket C — Copper Q&A
LLM 補充<!>         # bucket L — LLM batch-added (audit / sweep / market data / GRADE / Taiwan policy)
台灣實務補遺<!>     # bucket T — curator-vetted Taiwan addenda
```

Contam-cleanup action: forbidden inline → strip OR fold into bucket-L callout (LLM batch-added) with provenance line; forbidden H2 sections → fold entire section into bucket-L callout. Never delete content silently; always preserve in a callout marked with date and reason.

Note quality = faithful rendering of source PLUS optional collapsed-callout supplements (C/L/T). Anchor rule (caveat/quantitative/decision-hinge) draws ONLY from textbook's own data, not external grading.

### Output path (Copper directive 2026-05-15 — vault canonical + publish-flag direct-load)

**Vault = single content corpus; personal-website = pure renderer.** All note types target vault `{topic_path}/{citation_key_or_slug}/` bundles. Personal-website's Astro 5 globLoader on the `notes` collection reads vault directly (`base: '..'`, pattern `vault/**/{article,note-public,note-private,index}.md`); no sync script, no symlinks. The prior `scripts/sync-vault-published-to-content.py` was archived 2026-05-15.

**Publish gate**: every note frontmatter MUST carry `publish: true | false` + `visibility: public | private` + `note_type: <enum>`. `isPublicNoteEntry` filter (in `src/utils/publication.ts`) enforces:

- `publish: true` → entry surfaces at `/notes/{visibility}/{note_type}/{slug}/`
- `publish: false` or absent → vault canonical only; no renderer surface (note still git-tracked, indexed in PG, readable via vault search)

Per-file gate. URL generated by config.ts `generateId()` callback from frontmatter `visibility` + `note_type` + folder basename (or `slug` override).

Output path matrix (Astro content collection `notesCollection` schema lives at `personal-website/src/content/config.ts`; vault canonical is the source of truth):

| input source | note_type | visibility | vault canonical path | renderer URL (when `publish: true`) |
|---|---|---|---|---|
| `vault/{topic_path}/{key}/raw.md` (journal article — public-shareable summary) | `journal-summary` | `public` | `vault/{topic_path}/{key}/note-public.md` | `/notes/public/journal-summary/{slug}/` |
| `vault/{topic_path}/{key}/raw.md` (journal article — paywalled / detailed) | `journal-summary` | `private` | `vault/{topic_path}/{key}/note-private.md` | `/notes/private/journal-summary/{slug}/` |
| `vault/{topic_path}/{Book}/{Ch}/raw.md` (textbook chapter, public KEY-TAKEAWAYS only) | `textbook-summary` | `public` | `vault/{topic_path}/{citation_key}/note-public.md` | `/notes/public/textbook-summary/{slug}/` |
| `vault/{topic_path}/{Book}/{Ch}/raw.md` (textbook chapter, full Copper-readable digest) | `textbook-study` | `private` | `vault/{topic_path}/{citation_key}/note-private.md` | `/notes/private/textbook-study/{slug}/` |
| TSN exam recall / 腎專考題解析 | `exam-solution` | `public` | `vault/{topic_path}/{slug}/index.md` (or `note-public.md`) | `/notes/public/exam-solution/{slug}/` |
| FB post archive (Copper-authored, no AI banner) | `fb-archive` | `public` | `vault/{topic_path}/{slug}/note-public.md` | `/notes/public/fb-archive/{slug}/` |
| `/wiki-mega` synthesis / mini-review article | `wiki-human` | `public` | `vault/{primary_topic_path}/wiki-human-{slug}/article.md` + sidecar `refs.json` | `/notes/public/wiki-human/{slug}/` |
| Other (interactive «寫筆記» on PDF/report not fitting above) | `review` / `clinical-pearl` | per content | `vault/{topic_path}/{slug}/note-{public,private}.md` | `/notes/{visibility}/{note_type}/{slug}/` |

**Textbook dual-output rule** (per `wikify/SKILL.md` 2026-05-03 directive): textbook chapter notes emit BOTH `note-public.md` (slide-style KEY TAKEAWAYS, paraphrase only, ≤2 verbatim quotes ≤30 words each) AND `note-private.md` (full Copper-readable digest, may include short fair-use verbatim quotes) in one pass within the same `vault/{topic_path}/{citation_key}/` bundle. Both share the same `{slug}`; cross-link via frontmatter `related: [<other-slug>]`. Build pipeline gates private/ via Cloudflare Access (Google SSO + email allowlist).

**Wiki-human bundle layout** (Copper directive 2026-05-15): vault canonical = `vault/{primary_topic_path}/wiki-human-{slug}/{article.md, refs.json, manifest.json}`. Centralized references in sidecar `refs.json` (6S-tier annotated, agent-readable JSON) keeps the article body free of long reference blocks; Astro renderer ingests `refs.json` alongside `article.md` to render the references panel. Slug prefix `wiki-human-` namespaces against other producer pipelines (drug-indication, policy-explainer) in the same topic folder.

**Never write notes directly to `personal-website/src/content/notes/`**. Vault canonical is the only write target; personal-website paths are created and managed by the prebuild script. Manual writes to `src/content/notes/` will be overwritten or flagged on next sync. The `vault/` tree holds raw.md + source.pdf + images/ + manifest.json plus the bundle-local note/article artifacts.

**No legacy fallback writes**: if the active environment has no `personal-website/` checkout, the vault canonical is still authoritative — write to vault, and the renderer view will materialize on the next prebuild on any host with personal-website checked out. Do not write new notes into `medwiki/note/` or `~/repos/note/`.

**Required frontmatter field `parent:`** points back to the source raw.md so reverse lookup works: `parent: /Users/copper/repos/vault/{topic_path}/{citationKey}/raw.md` (or equivalent `~/repos/vault/...` path). PG mirror: `wiki_raw.raw_index`.

**Required frontmatter `publish` field** (Copper directive 2026-05-15): every note must carry `publish: true | false` explicitly. The Astro 5 `notes` collection (globLoader at `personal-website/src/content/config.ts`) reads vault directly; `isPublicNoteEntry` filter in `src/utils/publication.ts` enforces strict `publish === true` for vault-backed entries. Omitting `publish` = renderer-skip (treated as private). Flipping `publish: false → true` requires no other change; next Astro build surfaces the entry. Flipping `publish: true → false` drops it from the next build; vault canonical retained.

* `note_version`: Always use the version string shown above. When this skill is updated, the version string here will change — all new notes will carry the new version, making it easy to identify notes that need rewriting.
* `generated`: The date the note was generated (not the same as a user-managed `created` date).
* Omit inapplicable fields entirely (don't leave empty lines).
* `Book` uses vault-root absolute path to the book's MOC file.
* `PDF` **REQUIRED** for both textbook and journal articles. Use the payload path (e.g. `/Users/copper/repos/vault/{topic_path}/{citationKey}/source.pdf`). If PDF not yet in vault, write `pending` as placeholder.
* Tags: **flat names only** (no `_s/` or `_t/` prefix). Hierarchy managed in tags.db, not tag strings.

If the document doesn't provide full citation details, fill in what's available and leave the rest blank rather than guessing.


### Dual-output rule (textbook + OA guideline + journal notes) — split-content convention (Copper directive 2026-05-04)

For source types that justify both deep study and shareable summary, **content is split, not duplicated**:

- **Public short note (`visibility: public`)** carries:
  - frontmatter (incl. `ai_assist` banner field)
  - `## KEY TAKEAWAYS` (3–8 bullets, zh-TW)
  - `## TEACHING SLIDES` (Marp-compatible slides)
  - **a small inline link near the top** pointing to the private full note (e.g., `> 完整全文（私人區，Cloudflare Access 認證）：[XXX](/notes/private/.../)`)
  - **No body content sections.**

- **Private full note (`visibility: private`)** carries:
  - frontmatter (incl. `ai_assist` banner field)
  - **No `## KEY TAKEAWAYS` and no `## TEACHING SLIDES`** — those live only in the public short note
  - body sections (mirror source heading hierarchy with bilingual `中文｜English` headings)
  - figures embedded inline only through the website private asset bridge for explicitly selected payload assets

Rationale: prior dual-output had ~60% content overlap (KEY TAKEAWAYS + slides duplicated in both public extract and private full). Split-content convention removes the duplication: each fact lives in exactly one of the two files. Reader-flow:
- public short note: 5-min skim, walk away with takeaways + slides
- click small "完整全文" link → private full note: deep body for Copper / authenticated readers

Per `note_type` mapping:

| source | private | public |
|---|---|---|
| Textbook chapter | `textbook-study` (body) | `textbook-summary` (KEY TAKEAWAYS + slides + link) |
| OA guideline section | `textbook-study` (body) | `textbook-summary` (KEY TAKEAWAYS + slides + link) |
| Journal article | `journal-summary` (body) | `journal-summary` (KEY TAKEAWAYS + slides + link)* |

(*Note: `journal-summary` `note_type` is shared across both private full and public short for journal articles; `visibility` differentiates. For textbooks, the type names differ — `textbook-study` for private body, `textbook-summary` for public short.)

This keeps fair-use compliance for paywall textbooks while exposing pedagogical value (the slides + takeaways = original synthesis, not verbatim transcription) and avoids storage/sync duplication.

**Migration**: existing dual-output notes (Williams Ch33/Ch34, Harrison Ch415/Ch420, Harper Ch42, ADA 2026 §2, TWDKD 2024, DAROC 2022 Part 1, etc.) currently follow the old "extract" convention (KEY TAKEAWAYS + slides duplicated in both files). They will be migrated incrementally. New notes from 2026-05-04 forward must use the split-content convention.

### Image embed mode (Copper directive 2026-05-03)

For **private** notes (only Copper reads), figures may be embedded through the website private asset bridge for explicitly selected `~/repos/vault` payload images, **without `[!tip]-` analysis callouts**. Rationale: Copper sees the figures directly; agent-written figure descriptions are redundant.

For **public** notes (textbook-summary + others), figures from raw should NOT be embedded (paywall content). KEY TAKEAWAYS + slides convey the pedagogical content; reader follows link to private full note (or original source) for figures.

### AI authorship disclosure (Copper directive 2026-05-03)

Frontmatter `ai_assist` field mandatory for all notes. Two policy classes:

- **AI-generated note types** (must show visible "AI 製作" banner on web layout):
  - `textbook-study`, `textbook-summary`, `journal-summary`, `cme-summary`, `review`, `exam-solution`
  - `ai_assist` field describes generation (e.g., `"Opus 摘要 + paraphrase synthesis；圖片直接內嵌"`)
- **Copper-authored note types** (no AI banner, only standard fact-check disclosure):
  - `debunk`, `fb-archive`, `lifestyle`, `nephrology-public`, `clinical-pearl`, `announcement`
  - `ai_assist: "fact-check + copyedit only"` is the literal default

The Astro layout `src/pages/notes/[...slug].astro` reads `note_type` and renders the AI banner conditionally per this rule.

---

## Language & Terminology

* Write in Traditional Chinese (Taiwan). Avoid simplified characters and China-specific translations.
* Academic terms, trial names, abbreviations: retain English in parentheses at first occurrence.
* Drug **generic names** always stay in English.
* Apply corrections from the companion `terminology.csv` silently — never list the corrections in output.
* LaTeX: inline `$...$`, display `$$...$$`. No other delimiters.
* **Square brackets in scientific notation**: When `[` or `]` appears as part of a scientific name, chemical formula, or notation (e.g., Lp\[a\], Na\[+\], anti-HBs\[Ab\]) rather than as a markdown link, **always escape with backslash**: `\[` and `\]`.

### Avoid AI Writing Patterns (absorbed from /humanizer, 2026-04-12)

Reject these patterns. Reject specific examples in zh-TW + English:

| Pattern | Example | Fix |
|---|---|---|
| Inflated significance | "pivotal", "underscores", "testament", "值得注意的是" | Delete or state fact directly |
| Superficial -ing | "highlighting...", "ensuring...", "fostering..." | Delete or rewrite as independent clause |
| Promotional | "boasts", "vibrant", "profound", "groundbreaking" | Replace with concrete specifics |
| Vague attribution | "Experts argue", "Some critics" | Name source or delete |
| Forced rule of three | "X, Y, and Z" filler | Use actual number |
| AI filler (zh-TW) | 不僅...更...、具有深遠意義、綜上所述、為...奠定基礎 | Delete |
| Sycophantic | "Great question!", "You're absolutely right!" | Skip, answer directly |
| Em dash overuse | "X — Y — Z" | Use comma or period |

Rule of thumb: if removing the phrase loses no information, delete it. The clinical tone should be **direct, specific, no pleasantries**.

---

## What NOT to Do

* Don't output the Stage 1 translation — only the restructured notes.
* Don't flatten the hierarchy back into prose paragraphs. The whole point is the tree structure.
* Don't over-prune: if removing a word changes the logical meaning, keep it.
* Don't add citation markers (`[1]`, `(Author, Year)`, footnotes, DOIs) in the note body. If the source text has them, remove and rewrite naturally.
* Don't include end-of-chapter References/Suggested Readings sections.
* Don't add preamble ("以下是筆記…") or closing remarks ("希望有幫助…").

---

## Short Note Mode (KEY TAKEAWAYS only)

When dispatched with "short note" or as part of a wikify batch, the note-writer produces a **truncated output**: frontmatter + KEY TAKEAWAYS only. No content sections, no TEACHING SLIDES.

This is NOT a different format — it is the same protocol, same frontmatter schema, same KEY TAKEAWAYS rules, simply stopping after the first section. The note can be upgraded to a full note later by re-running with the same source.

**Rules (identical to full mode):**
- Frontmatter follows §5 schema exactly (note_version = "medical-note-writer-v2.7")
- `## KEY TAKEAWAYS` is the first and only section
- zh-TW, clinical bottom line
- Tags flat (no prefix)
- PDF field required

**Dispatch rule:** Any sub-agent producing a file with `note_version` in frontmatter MUST read this SKILL.md first. No ad-hoc note format is permitted. Violation = the sub-agent invented a format instead of following the protocol.

---

## After the Notes: TEACHING SLIDES

After all content sections are complete, output `—— 本章結束 ——`, then:

> **Critical**: This section is Marp-compatible AND drives the personal-website SlideDeck carousel (cream notebook + red rings + numbered cyan badges, BoAn-canonical visual). The same source format feeds both consumers — see `consumers` table below. Keep the format strict.

```markdown
# （文件中文標題）｜（Original Title）

## 01 （slide title）
- （bullet）
- （bullet）

## 02 （slide title）
- （bullet）
- （bullet）
```

**Format rules**:
* Line 1: `# Title` (H1) → becomes the Slides filename.
* Each slide: `## 01 Title` (H2 + two-digit number) → creates a new slide.
* Bullets: `- text` (hyphen, not asterisk) → the script only recognizes `- `.
* Section dividers (optional): `# Section Title` (H1, not first line) → title-only slide.
* No `**bold**` or other Markdown inside bullets — the script strips `**` but other markup appears as raw text.
* One blank line between slide blocks.
* Start directly, no preamble or closing.

**Content priorities**: Each slide = one teachable concept. Reference key figures/tables with `圖：Figure X.X` or `表：Table X.X`. Cover core arguments, methods, and anything from supplements that changes interpretation.

### Slide Consumers (2026-05-07: now THREE consumers)

The `## TEACHING SLIDES` section feeds:

1. **personal-website SlideDeck** (`personal-website/src/components/notes/SlideDeck.astro`) — auto-mounts on any public note containing the `## TEACHING SLIDES` h2; renders the section as a paginated carousel with the BoAn-canonical visual aesthetic (cream notebook paper + red binder rings + numbered cyan circle badges). Visual reference = `personal-website/handoff/design/wireframes-v1/frame-slide.jsx` (Wireframe 05). Spec home = `personal-website/AGENTS.md` § "Slide rendering". This is the **primary public consumer** going forward.
2. **nephro-board-review-sync.py** (legacy cron */10, may be retired) — auto-extracts via `extract-slides.py` → Marp .md → GitHub Pages
3. **Manual Marp CLI** (on-demand): `marp {slides.md} -o slides.html` / `--pdf` / `--pptx`

Because the SlideDeck consumer is the primary public surface, prefer formats that render well there:
- **Each slide ≤ 5 bullets** (one carousel viewport; more crowds the cream-notebook card)
- **Each bullet ≤ 1 line of body text** (~30 zh-TW chars or equivalent) — long bullets wrap awkwardly and make the slide visually heavy
- **Avoid sub-bullets** (`  - …`) when possible; the SlideDeck renders them as a smaller yellow-badge prefix which reads as a deliberate aside, not a casual nest
- **`**bold**` is now permitted** for the SlideDeck consumer (the cream-notebook design uses deep-teal #116885 strong); however the legacy Marp consumer's `extract-slides.py` strips `**` markers, so use it only for emphasis the slide can lose
- **Tables** render in the SlideDeck (cyan-tinted header) — keep narrow (≤4 columns) so they don't overflow the cream card
- Title-only divider slides (`# Title` after the deck-title h1) become cover-style slides in the SlideDeck — use sparingly

Marp frontmatter template for manual extraction (when needed):

```yaml
---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  section { font-family: 'Noto Sans TC', 'Arial', sans-serif; font-size: 24px; }
  h1 { font-size: 36px; color: #1a5276; }
  h2 { font-size: 30px; color: #2c3e50; }
---
```

Slide separator: `---` (Marp standard). Our `## 01 Title` format is compatible when wrapped with `---`. The sync script handles this automatically.

**Legacy note:** The standalone `/slides` skill was merged here on 2026-04-12. All slides functionality now lives in note-writer.

---

## Output Sequence (single response)

```
1. Frontmatter (---yaml---)
2. ## KEY TAKEAWAYS (3-8 bullets, zh-TW — FIRST section, appears ONCE)
3. 正文教學筆記 (section-by-section, with Figure/Table analysis)
4. 附屬文件摘要 (if applicable)
5. —— 本章結束 ——
6. ## TEACHING SLIDES (# Title → ## Slides → - bullets)
```

## Post-Note: Lv2 Tagging + Summary (MANDATORY)

After writing the note, the agent MUST do these two steps before moving to the next article. The agent has full context at this point — doing it later wastes tokens re-reading.

### Lv2 Tag Assignment

Assign **flat** tags based on article content. NO prefix (`_s/`, `_t/` abolished 2026-04-01). Hierarchy managed by tags.db parent_id, not tag name.

**Subject tags**: nephrology, im, oncology, hematology, cardiology, etc. (flat, recognizable)
**Type tags**: RCT, original, review, meta-analysis, guideline, textbook-chapter, case-report, cohort, editorial, clinical-problem-solving, correspondence
**Journal tags**: NEJM, JAMA, BMJ, Lancet, etc.
**Topic tags**: disease/drug/concept specific (e.g., hyperammonemia, OTC-deficiency)

Write tags into:
1. **Note frontmatter** `tags:` field (already in the note)
2. **Citation manager**, if configured by the private runtime:
   - Never publish API keys, user IDs, token paths, or account identifiers in public rules.
   - Search by DOI/title through the configured private helper.
   - If creating a new item, use Crossref or publisher metadata rather than title-only stubs.
   - Tags MUST be identical between frontmatter and citation-manager metadata.

### Summary (§9.1 — superseded by Take Home Message)

`summary:` in frontmatter is **no longer required**. `## Take Home Message` as the first section fulfills the same function (§9.1 exemption). Agent reads Take Home Message to assess relevance without reading the full note.

### Payload Assembly (MANDATORY)

After writing the note, assemble the payload folder. All related source files for this article go into one folder.

```bash
# Determine corpus path
# Articles/textbook chapters: ~/repos/vault/{topic_path}/{citationKey}/

PAYLOAD="$HOME/repos/vault/{topic_path}/{citationKey}"
mkdir -p "$PAYLOAD"

# Move raw transcript from staging
mv raw/{citationKey}.md "$PAYLOAD/raw.md" 2>/dev/null

# Copy source PDF (if accessible)
# PDF may be in ~/Downloads/, Zotero storage, or already in vault
cp "{pdf_path}" "$PAYLOAD/source.pdf" 2>/dev/null

# Move extracted figures (if any)
mkdir -p "$PAYLOAD/images"
mv raw/images/{citationKey}/* "$PAYLOAD/images/" 2>/dev/null
```

After assembly, the payload (`~/repos/vault/{topic_path}/{citationKey}/`) should contain:
- `raw.md` — MinerU transcript (indexed by PG `wiki_raw.raw_index`)
- `source.pdf` — original PDF (if available)
- `images/{sha}.png` — extracted figures, content-addressed by sha

Private website notes may reference only explicitly selected assets through a
website bridge. Legacy `/_sidecar/...` embeds remain supported for old notes;
new notes should not publish a whole source payload by default.
- `![Fig 1](/_sidecar/{citationKey}/images/{sha}.png)` — legacy/compat embed only
- `[Raw transcript](/Users/copper/repos/vault/{topic_path}/{citationKey}/raw.md)` — dev-only parent pointer
- `[PDF](...)` — only if Copper opted to publish; commercial textbook PDFs MUST NOT be linked

### Mutual linkage update

After payload assembly, update Zotero `url` field to include the correct vault-relative path:
`/Users/copper/repos/vault/{topic_path}/{citationKey}/raw.md` or a stable PG-backed resolver URL when implemented.

---

## Cowork Batch Mode

**Model requirement: subagents MUST use Opus.** Note-writing requires medical domain judgment, zh-TW academic terminology, and structural decisions that lower-tier models (Sonnet/Haiku) cannot reliably produce. When spawning subagents via Agent tool, always set `model: "opus"`.

When writing notes for multiple PDFs in a single session (e.g., a full set of guidelines or several textbook chapters), the orchestrating agent must prepare inputs correctly so that each subagent can follow the full skill — including image extraction. Skipping image extraction is the most common failure mode in batch runs, and it happens when the subagent only receives a text dump without access to the original PDF.

### Pre-processing (before spawning subagents)

Run these once per PDF, in parallel:

```bash
# Text extraction
pdftotext -layout "{pdf_path}" "{workspace}/{basename}_text.txt"

# Image extraction
mkdir -p "{workspace}/{basename}_images"
pdfimages -png "{pdf_path}" "{workspace}/{basename}_images/fig"
```

Also prepare the shared output directory:

```bash
mkdir -p "{note_folder}/attachments"
```

### Subagent prompt template

Each subagent prompt **must** include all four paths below. If any is missing, the subagent cannot complete the skill correctly — most critically, omitting the PDF path causes every figure to degrade to a placeholder.

```
你是醫學教學筆記生成器。請為 {title} 撰寫完整的教學筆記。

## 輸入檔案
- 文字檔：{workspace}/{basename}_text.txt
- PDF 原檔：{pdf_path}（用於 pdfimages 抽圖）
- 已抽取圖片：{workspace}/{basename}_images/
- 參考筆記：{reference_note_path}

## 輸出
- 筆記：{note_folder}/{note_filename}.md
- 圖片：{note_folder}/attachments/（命名：{basename}-{流水號}.png）

## 圖片處理
1. 比對 pdfimages -list 的頁碼與文中 Figure 編號
2. 將對應圖片以 sha-named 形式複製到 `~/repos/vault/{topic_path}/{citationKey}/images/{sha}.{ext}`
3. 私人筆記若必須顯示圖片，使用 website 私人 asset bridge 指向單一圖檔；不要公開整包 source payload。Legacy `/_sidecar/...` 只用於舊筆記相容。
4. 無法對應的圖片（如 logo、裝飾圖）略過

請遵循 medical-note-writer skill 的完整規則。
```

### Why this matters

The image extraction step in Section 3 ("Figure & Table Analysis") requires access to the PDF binary — `pdftotext` output alone is insufficient. When the orchestrating agent only passes a text file to subagents, every figure callout degrades to a placeholder (`此處插入截圖`), which defeats the purpose of the skill's Cowork mode. The pre-processing step above ensures subagents have everything they need without each one independently discovering and solving the same problem.

---

## Changelog

| Version | Date | Changes |
|---|---|---|
| v2.11 | 2026-05-15 | Vault canonical content model + publish-flag prebuild sync. All note types target `vault/{topic_path}/{citation_key_or_slug}/note-{public,private}.md` (or `article.md` for wiki-human). Frontmatter `publish: true` + `visibility` + `note_type` triggers prebuild script `personal-website/scripts/sync-vault-published-to-content.py` (a045) to symlink the vault canonical into `personal-website/src/content/notes/{visibility}/{note_type}/{slug}/index.md`. No whole-folder symlinks. Per-file gate. Personal-website becomes a pure renderer; vault is the single content corpus. Wiki-human bundle layout = `vault/{primary_topic_path}/wiki-human-{slug}/{article.md, refs.json, manifest.json}` with centralized 6S-tier refs in sidecar. |
| v2.8 | 2026-05-03 | NOTE primary home pivot: output paths redirect to `personal-website/src/content/notes/{public,private}/{type}/{slug}.md` (Astro `notesCollection`). Sidecar bridge updated to `/_sidecar/{bundle}/images/{sha}.{ext}` pattern via `personal-website/scripts/copy-sidecar-images.py`. Textbook dual-output (`textbook-summary` public + `textbook-study` private) per Copper directive. Legacy `proj/note/...` and `~/repos/note/` shells deprecated; medwiki/note/ retained for backward search and migration-pending fallback. |
| v2.10 | 2026-05-09 / 2026-05-13 | wiki_raw moved under `personal-website/`, then merged into `vault/`. Canonical raw payload path is now `~/repos/vault/{topic_path}/{topic_note_slug}/{raw.md, source.pdf, images/, manifest.json}`. Old `~/VaultBinary/...`, `~/repos/wiki_raw/...`, and canonical-use `personal-website/wiki_raw/...` paths are deprecated; agents must rewrite frontmatter `parent:` and reference paths to `vault/`. PG schema names (`wiki_raw.raw_index`, `wiki_raw.source_registry`, `wiki_raw.book`) are unchanged — only filesystem location moved. |
| v2.9 | 2026-05-05 | Raw+binary merge: source payloads now live at `~/repos/vault/{topic_path}/{citationKey}/{raw.md, source.pdf, images/, manifest.json}` and are indexed by PG `wiki_raw.raw_index`; new note writes must not fall back to deprecated `medwiki/note/`. |
| v2.7 | 2026-04-17 | 圖片直接內嵌，移除 `<div class="no-publish">` 包裝（v2.3 引入，今作廢）。Rationale: 公開分享只走 GitHub repos 的 KEY TAKEAWAYS / TEACHING SLIDES 切片，整篇 note publish 非現行路徑，no-publish guard 已無需要。 |
| v2.6 | 2026-04-09 | `## KEY TAKEAWAYS` moved to FIRST section (replaces Take Home Message AND old end-of-note KEY TAKEAWAYS — appears once, at top). Removed duplicate. `## TEACHING SLIDES` remains at end (Marp-compatible, script-extractable). |
| v2.5 | 2026-04-09 | +`## Take Home Message` as mandatory first section (superseded same day by v2.6). |
| v2.4 | 2026-03-26 | +Lv2 tagging (mandatory post-note: _s/ + _t/ tags → frontmatter + Zotero API). +§9.1 summary for >500L notes. TEACHING SLIDES format updated for Marp (was Google Slides). |
| v2.3 | 2026-03-09 | Figure 格式改為 `<div class="no-publish">` 包圖片（本地可見、Publish 隱藏，取代 `[!figure]` callout），分析改用 `> [!tip]-` 折疊 callout 包住（視覺上與正文分隔、預設折疊）。Table 讀表教學同樣改用 `> [!tip]-` callout。新增方括號轉義規則：科學命名中的 `[`、`]` 一律加反斜線，防止 Obsidian 誤判為連結。 |
| v2.2 | 2026-03-08 | 新增 Cowork Batch Mode 段落：定義批量寫筆記時的前處理步驟（pdftotext + pdfimages）與 subagent prompt 模板，確保圖片抽取不會在派工過程中被遺漏。 |
| v2.1 | 2026-03-07 | 圖片處理改為 `[!figure]` callout（支援 Obsidian Publish 排除）。新增 Cowork / chat 雙模式：Cowork 自動抽取內嵌圖片存入 attachments/，掃描頁或 chat 模式則留佔位符。Frontmatter 新增 `Book`、`Chapter`、`PDF`（教科書）及 `journal`、`DOI`、`PMID`（文獻）欄位。Skill 開頭新增讀取 `_COWORK_RULES.md` 指令。 |
| v2.0 | 2026-03-06 | 全面重寫。兩階段模型（thinking 翻譯 → 輸出重排去蕪）取代一步到位 paraphrase。精簡規則，移除 GPT 時代的防禦性約束。新增 frontmatter source citation 及 note_version 追蹤。Teaching slides 格式改為 `## ` + `- ` 以配合 Google Apps Script。從 medical-pdf-to-notes 拆分為獨立 skill，去除 Cowork/Inbox 流程邏輯。 |
| v1.0 | 2026-03-02 | 從 GPT v4.8 移植為 Claude 版（教科書筆記生成_Claude_v1.md）。移除輸出長度 workaround，保留全部品質規範。嵌入於 medical-pdf-to-notes skill 內。 |
| GPT v1.0–v4.8 | 2024–2026 | 原始版本，在 GPT 平台上經歷多次迭代。最初為 Google Doc 輸出設計，逐步加入 Obsidian 格式、用字勘誤 CSV、Figure/Table 解析、Teaching Slides、附屬文件分類處理等功能。 |
