---
type: data
name: fuse
description: "Fuse multiple LLM reports on the same topic into a single consensus wiki entry. MANDATORY TRIGGERS: /fuse, 融合, merge reports, 合併報告, synthesize, combine DR outputs, fuse reports, wiki 品質升級."
---

# Multi-LLM Report Fusion (v2, 2026-04-20)

Fuse N independent LLM reports (Deep Research outputs) on the same question into one unified, high-quality consensus document. Final destination = a canonical wiki entry at §8.10 topic-tree path.

**Council vs Fuse**: Council = adversarial debate → judge picks winner. Fuse = collaborative synthesis → merge best of all into one with provenance preserved. `/fuse` ≠ `/council`.

**Scope change (v3, 2026-04-27 — Copper directive)**: **Canonical fuse session path = `note/fuse/{topic}_{YYYYMMDD}/`** (NOT `proj/wiki/fuse/...` per old v2; NOT colocated with consumer scope). Reasoning: fuse session contains zh-TW WIP reasoning + sourced LLM outputs that match note/ Obsidian-readable layer privacy contract. Consumer scopes (e.g., `secretary/tsn/.../{topic}/`) get **symlinks** pointing back to canonical, never copies — to prevent drift between consumer-side workspace and master.

**Symlink convention**: `{consumer_scope}/_fuse_session_{YYYYMMDD}` → `~/repos/note/fuse/{topic}_{YYYYMMDD}/`. Use absolute symlink path so it survives consumer-scope rename.

(Earlier v2 path `proj/wiki/fuse/...` retired with proj/ wrapper retire 2026-04-25. v1 root `_fuse/` retired 2026-04-20.)

## Standard Workflow (5 steps)

### Step 0: Gap scan + prompt synthesis (preparation)

Copper asks a question that warrants multi-LLM DR. Before dispatching, CC:

1. **Vault gap scan** — Explore agent scans `wiki/`, `raw/`, `proj/note/`, `proj/fb/` (exclude `copper/`, `BoAn/`, `_archive/`, `.git/`) for existing coverage. Output → `proj/wiki/fuse/{topic}_{YYYYMMDD}/gap_analysis.md`:
   - Tier-1 (direct topic hits), Tier-2 (adjacent), Tier-3 (passing mentions clustered)
   - FB public-facing audience baseline (what has Copper already communicated to ~100K FB?)
   - Systematic absences (what the prompt MUST fill)
   - Proposed §8.10 canonical destination for the fused wiki entry
2. **Prompt synthesis** — write the DR prompt to `proj/wiki/fuse/{topic}_{YYYYMMDD}/prompt.md`:
   - **"Known vault coverage" block at top** — name existing wiki/ref files; instruct LLMs to *cite / build-on / challenge*, not restate
   - Research question precisely defined (zh-TW academic terms + English for international LLMs)
   - Output format (PARTs, required tables, minimum row counts, required columns)
   - **Epistemic rules (non-negotiable)** cascading from `wiki/CLAUDE.md ## Methodology` 16 Source Verification rules: primary-source-only with DOI/PMID; observed vs derived separation; study-design hierarchy (RCT > cohort > cross-sectional > animal); surrogate flag; Taiwan/Asian applicability; no fabrication
3. **Session _index.md** — write per schema in `proj/wiki/fuse/CLAUDE.md`. Status = `prompt-ready`. Record topic, created-date, sources roster (4 LLM placeholders), wiki_target path (proposed).
4. **Pasteboard** — `cat proj/wiki/fuse/{topic}_{YYYYMMDD}/prompt.md | pbcopy`. Hand off to Copper.

### Step 1: Dispatch prompt

Copper pastes into each LLM (Claude / GPT / Gemini / Grok / Perplexity / Kimi — pick 4 per account availability + peak-hour quota). Each LLM runs Deep Research (20-40 min wall-clock per LLM).

On Copper's "all dispatched" confirmation → update `_index.md` status = `dispatched`, record which LLM roster was used.

### Step 2: Receive results

Copper saves each LLM's output as `.md` and drops into `_inbox/` (or specifies paths). CC moves:

```bash
mv _inbox/{file}.md proj/wiki/fuse/{topic}_{YYYYMMDD}/source_{llm}.md
```

Naming: `source_claude.md`, `source_gpt.md`, `source_gemini.md`, `source_grok.md` (or `source_perplexity.md` / `source_kimi.md` per actual roster).

On first file arrival → `_index.md` status = `received`; update `sources[].received_at` and `sources[].path`. When all N arrive → proceed to Step 3.

### Step 3: Generate fused document

Run the 5-phase protocol below → produces:
- `proj/wiki/fuse/{topic}_{YYYYMMDD}/fused_draft.md` — main consensus document (NOT yet in wiki/)
- `proj/wiki/fuse/{topic}_{YYYYMMDD}/_inventory.md` — Phase 1 output
- `proj/wiki/fuse/{topic}_{YYYYMMDD}/_alignment.md` — Phase 2 output

Update `_index.md` status = `fused`, `fused_draft` path set.

### Step 4: Wiki commit (canonical output)

1. **Resolve §8.10 canonical path** — use `wiki_target` from `_index.md` (set in Step 0) OR re-derive from topic keywords per Vault §8.10 topic-tree rules. Path format: `wiki/{top_domain}/{specialty}/{disease}/{stage}/{modality}/{topic}.md`.
2. **Frontmatter harmonization**:
   - `type: wiki`
   - `sources:` array referencing `proj/wiki/fuse/{topic}_{YYYYMMDD}/source_*.md`
   - `parent: /proj/wiki/fuse/{topic}_{YYYYMMDD}/fused_draft.md` (reverse pointer)
   - `publish: false` (Copper-only gate for share pipeline; §8.8)
   - `summary:` (required if >500L per §9.1)
3. **Cross-link sweep** — grep for `(/wiki/{sibling_topic}` patterns; add back-references from sibling wiki entries + MOC / _index.md files. Update `wiki/.../…_index.md` if topic folder has one.
4. **Provenance tags preserved** — consensus tags `[all]/[C+G]/[split]/[only:X]` stay in-line (they are the methodology's value; don't strip for "cleanliness").
5. **Commit** — auto-commit cron will sweep; OR explicit `git add {wiki_path} proj/wiki/fuse/{topic}_{YYYYMMDD}/_index.md && git commit -m "wiki-commit: {topic} (/fuse session {YYYYMMDD})"`.
6. **_index.md update** — status = `wikified`, `wiki_committed_at` = timestamp, `wiki_target` confirmed.
7. **Archive cue** — after 30d with status=wikified, vault-steward cron zips `proj/wiki/fuse/{topic}_{YYYYMMDD}/` → `_archive/_fuse_{topic}_{YYYYMMDD}.zip` (§1.3). `_index.md` status = `archived` (only the _index.md stays visible as breadcrumb; sources + draft in zip).

## Input (Step 0 entry)

Copper provides either:
- **Topic-only** — "研究 X" → CC runs Step 0 from scratch (gap scan + prompt synthesis)
- **Partial prompt** — Copper has a draft prompt → CC runs gap scan only, enriches prompt with "Known vault coverage" block + epistemic rules
- **Prompt + gap already done** — CC jumps to Step 1 (pasteboard)

## Input (Step 2 entry — late join)

Copper has DR outputs already in hand (from a previous non-`/fuse` workflow):
- File paths OR `_inbox/` drop OR pasted content inline
- CC retroactively creates `proj/wiki/fuse/{topic}_{YYYYMMDD}/` folder, materializes prompt.md (extract from Copper's memory if possible; else flag as "retro-import"), moves source files, proceeds to Step 3

## Protocol (Step 3 5-phase detail)

### Phase 1: Inventory

Read all N reports. For each:

```markdown
### Source: {LLM name}
- **Length**: {word count}
- **Structure**: {section headings list}
- **Core thesis**: {1-2 sentences}
- **Unique contributions**: {points not found in other reports}
- **Quality assessment**: {depth, evidence quality, actionability} /10
```

Output: `proj/wiki/fuse/{topic}_{YYYYMMDD}/_inventory.md`. Show to Copper before proceeding.

### Phase 2: Alignment Matrix

Extract all distinct 論點 (claims/recommendations) across reports. For each pair, classify:

| 關係 | 定義 | 處理 |
|---|---|---|
| **一致** | 同一論點，結論相同 | 合併一條，標 `[all]`，用最完整版本 |
| **互補** | 不同面向，不矛盾 | 全部納入，邏輯排列 |
| **相斥** | 同一論點，結論衝突 | 並列，標 `[split]`，列各自論據，**不替 Copper 決定** |
| **無關** | 完全不同事 | 各自保留在相關 section |
| **包含** | A 是 B 子集 | 用完整版，標來源 |

Build alignment table:

| 論點 | LLM-A | LLM-B | LLM-C | LLM-D | 關係 | 處理 |
|---|---|---|---|---|---|---|
| {claim} | {pos} | {pos} | {pos} | {pos} | 一致/相斥/... | {action} |

Output: `proj/wiki/fuse/{topic}_{YYYYMMDD}/_alignment.md`. Show to Copper. Copper may resolve `[split]` items before Phase 3.

### Phase 3: Synthesis

Write `proj/wiki/fuse/{topic}_{YYYYMMDD}/fused_draft.md`. Rules:

1. **Structure**: rebuild from alignment-matrix topics. Organize by subject matter, NOT any single LLM's structure.
2. **Content selection**: for each 論點, use the most detailed/accurate version. Never average — pick best, supplement with others.
3. **Provenance tags**: `[C]` Claude, `[G]` GPT, `[Ge]` Gemini, `[Gr]` Grok, `[P]` Perplexity, `[K]` Kimi, `[all]` consensus, `[C+G]` partial consensus, `[only:X]` unique insight, `[split]` unresolved.
4. **Conflict resolution**: where reports disagree, state strongest position first, then dissent: "However, [G] argues...".
5. **Unique insights**: include substantive unique points with `[only:X]` tag — these are often the most valuable.
6. **No dilution**: fused doc is MORE actionable than any single input, not a watered-down average.
7. **Language**: match inputs (zh-TW if inputs zh-TW, English if English; bilingual if mixed).
8. **Epistemic grading cascade**: every numeric claim retains DOI/PMID from the source LLM's output. Cross-verify at least the 3-5 highest-stakes numbers against primary source (CrossRef/PubMed) — flag any mismatch as `[verify-failed]`.

### Phase 4: Quality Check

Self-audit the fused draft:

| Check | Pass? |
|---|---|
| Every alignment-matrix section represented | |
| No claim without provenance tag | |
| All `[split]` items have both sides presented | |
| Unique insights preserved (not dropped) | |
| Actionable recommendations have concrete steps | |
| Length ≥ longest single input (fusion adds, not cuts) | |
| No internal contradictions | |
| Top-5 numeric claims cross-verified against primary source | |

### Phase 5: Session record

Write session metadata to `proj/wiki/fuse/{topic}_{YYYYMMDD}/_index.md` status trail. DO NOT move `fused_draft.md` to wiki yet — Step 4 handles that.

## Folder layout (reminder)

```
proj/wiki/fuse/
  CLAUDE.md                                ← workspace protocol
  {topic}_{YYYYMMDD}/
    _index.md                              ← status + sources roster + wiki_target
    prompt.md                              ← Step 0d
    gap_analysis.md                        ← Step 0c
    source_claude.md                       ← Step 2
    source_gpt.md
    source_gemini.md
    source_grok.md                         ← or perplexity / kimi
    _inventory.md                          ← Phase 1
    _alignment.md                          ← Phase 2
    fused_draft.md                         ← Phase 3 (Step 3 complete)
```

Final canonical output → `wiki/{topic_path}/{topic}.md` (Step 4, §8.10). Session folder retained 30d as audit trail → `_archive/` zip.

## Provenance Tag Reference

| Tag | Meaning |
|---|---|
| `[all]` | all sources agree |
| `[C]` `[G]` `[Ge]` `[Gr]` `[P]` `[K]` | single-source |
| `[C+G]` etc. | partial consensus |
| `[only:C]` | unique insight from Claude |
| `[split]` | no consensus, both sides presented |
| `[verify-failed]` | numeric claim didn't match primary source cross-check |

## Usage Examples

```bash
# Full flow (Step 0 onward)
/fuse "GLP-1 RA body composition methodology beyond DXA"

# Late-join (source files already in hand; skip Step 0, retro-create folder)
/fuse --retro --topic "EMR publication infrastructure" \
  _inbox/dr_output_claude.md _inbox/dr_output_gpt.md _inbox/dr_output_gemini.md

# Step 0 only (prompt + gap scan, don't dispatch yet)
/fuse --prep "causal inference in observational CKD studies"
```

## Anti-patterns

- DO NOT average or "balance" positions — pick the strongest, note alternatives
- DO NOT drop unique insights because other LLMs didn't mention them
- DO NOT create a shorter document than the longest input
- DO NOT remove provenance tags to "clean up" — they are the methodology's value
- DO NOT commit `fused_draft.md` directly to `wiki/`; always go through Step 4 (canonical-path resolution + cross-link sweep + frontmatter harmonization)
- DO NOT skip Step 0 gap scan even when Copper's urgency is high — the "Known vault coverage" block is half the value of /fuse (LLMs otherwise waste DR budget re-deriving what Copper already has)

## Relation to other skills

- `/council` = adversarial debate mode (different semantic; LLMs argue, one wins). Separate skill, separate workspace.
- `/note-writer` = single-source zh-TW teaching note. `/fuse` output may become a `/note-writer` input for Copper-facing polished version.
- `/med-read` = single-source medical literature appraisal. `/fuse` invokes `/med-read` epistemic rules cascade via the "Known vault coverage" block.
- Vault §8.10 topic-tree is authoritative for Step 4 canonical path resolution.
