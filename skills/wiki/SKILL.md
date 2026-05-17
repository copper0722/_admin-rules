---
type: data
name: wiki
description: "LLM-wiki Q&A skill. Copper asks ad-hoc clinical / medical / policy / literature questions; agent retrieves from local LLM-wiki three layers (PG wiki_raw.raw_index + wiki_raw raw md + personal-website wiki & notes), integrates a chat answer with chapter+line citations, and reports local coverage gaps. MANDATORY TRIGGERS: /wiki, wiki?, 查 wiki, 問 wiki, 查 raw, 查 LLM-wiki, 查 LLM 的 wiki, /q, /ask, /wq. Trigger requires Q-shape (clinical/medical question, not source ingest). Source-ingest input (PDF/audio/URL/scattered manual paste) goes to /wikify."
argument-hint: "[clinical / medical / policy question]"
summary: "LLM-wiki Q&A skill: retrieve from three local LLM-wiki layers (PG wiki_raw.raw_index + raw md + personal-website wiki/notes) and answer clinical/medical questions with chapter+line citations; reports local coverage gaps. Q-shape questions only — source ingest routes to /wikify."
---

# /wiki — LLM-wiki Q&A Skill

Retrieve from the local LLM-wiki three layers and integrate a chat answer.

This is the **retrieval direction** counterpart to `/wikify` (ingest direction). 2026-05-07 trigger split: `/wiki` was reassigned from the wikify ingest skill to this Q&A skill (Copper directive).

## Principle

- LLM-wiki retrieval reads **raw md (git-tracked) and wiki/notes synthesis only**. NEVER load binary (PDF / images / tables / source media) into context for retrieval — binary is local-only audit asset (gitignored under `vault/`), retrieval-irrelevant. Memory rule: `feedback_llm_wiki_retrieval_no_binary.md`.
- Output = chat answer to Copper, NOT a published artifact. Reader-only zone rules (no internal infrastructure, device names, AGENTS.md citations, AI process disclosures) do not apply because chat ≠ publish; but if Copper later says "this is for FB / publish", switch to Copper-authored note format with reference tier and inline `[N]` numbered citations (memory: `feedback_reference_tier_copper_authored_notes.md`, `feedback_inline_citation_numbered.md`).
- Voice: zh-TW Taiwan medical terminology, calm academic tone, no debunk drama, inline English for technical tokens (paths, drug INN, classifier names, gene symbols).
- Ad-hoc retrieval, **single round-trip**: do not invoke task tracking, do not write memory unless the question itself asks for it.

## Workflow

1. **Restate** Copper's question in precise zh-TW domain terms (one line). This both clarifies the scope and gives Copper a chance to redirect before retrieval cost is paid.

2. **Parallel retrieval** across four layers:
   - **PG metadata layer** — `psql -h hmj -U copper -d vault_main` against `wiki_raw.raw_index`; multi-column `ILIKE` over `file_path` / `title` / `citation_key` plus `'<lower_kw>' = ANY(tags)`. Use lowercase tag form. Sample query:
     ```sql
     SELECT DISTINCT citation_key, file_path, title, line_count
     FROM wiki_raw.raw_index
     WHERE file_path  ILIKE '%<kw>%'
        OR title       ILIKE '%<kw>%'
        OR citation_key ILIKE '%<kw>%'
        OR '<kw_lower>' = ANY(tags)
     ORDER BY citation_key LIMIT 50;
     ```
   - **vault raw md layer** — `rg -l --type md -i '<kw_en>|<kw_zh>' ~/repos/vault/`. `personal-website/wiki_raw` is only a symlink/backcompat route; new retrieval docs should name `vault/`.
   - **personal-website layer** — `rg -l --type md -i '<kw>' ~/repos/personal-website/src/content/{wiki,notes}/`. Wiki entries are M2M synthesis with `tags` + `slug`; notes are Copper-authored zh-TW digests + AI-authored textbook-summary / journal-summary etc.
   - **agent-share/textbook sidecar layer (retrieval only, not wikify)** — search completed `~/我的雲端硬碟/agent-share/textbook/<book>/<ed>/chapters/<slug>/` bundles (gdrive canonical, hm4/mbp-mounted; legacy `~/repos/textbook-share/` retired 2026-05-17). Copper explicitly distinguishes **wiki search** from **wikify**; do not answer a search-efficiency question by describing wiki synthesis. Per-chapter priority is `article.md > proofread.md > raw.md`; after 2026-05-13 completed chapters should normally be `proofread.md + raw.md.gz` with no searchable `raw.md`. Generic `rg --type md` should therefore hit `proofread.md`/`article.md`, not compressed raw. If multiple layers match one chapter, keep the highest layer and do **not** load `raw.md` and `proofread.md` together unless verifying OCR/proofread quality.
   - **External synthesis NAVIGATOR layer (Copper directive 2026-05-10)** — UpToDate + DynaMed are tertiary synthesis used to **discover primary references**, NEVER cited directly in the answer (commercial source + unstable versioning + academic primary-cite standard). Auth cookies for both live ONLY in **hm4 Chrome Beta** (same place as journal-toc bundler subscriber sessions); WebFetch from any host cannot reuse those cookies → must drive via `chrome-devtools` MCP:
     - **UpToDate** (CMU proxy, logged-in UpToDate Anywhere): navigate to `https://www-uptodate-com.autorpa.cmu.edu.tw:8443/contents/search?search=<kw_en>`, take snapshot of hits, click top relevant topic, take snapshot to extract its references list.
     - **DynaMed**: same pattern via `https://www.dynamed.com/search?q=<kw_en>` (or `www-dynamed-com.autorpa.cmu.edu.tw` proxy variant).
     - Workflow: read the topic's bibliography → identify which primary refs (RCT / guideline / meta-analysis / textbook chapter) ground each clinical recommendation → pull those primary refs from local wiki_raw / PG; if missing, log them as fetch candidates (PMID / DOI + topic_path).
     - Fallback: if `chrome-devtools` MCP not available this session, try WebFetch as best-effort (will likely return logged-out splash) and report the gap honestly.
     - Coverage rationale: UpToDate + DynaMed catch evolving recommendations that 1-2 year old textbook chapters may have superseded; their reference lists are the actionable artifact. Memory: `feedback_wiki_search_tri_source.md`.
   - Run all four in **one batched message of parallel Bash + chrome-devtools MCP calls** — no sequential.

3. **Read** the relevant hits' specific paragraphs (chapter + line range). Do not load whole files unless small. Prefer `Read` with offset+limit over full read.

4. **Integrate** — source-grounding discipline before writing the answer:
   - If Copper asks to review,校稿, or draft a reply to someone else's article/email/初稿, read the target draft first and anchor every critique to an actual sentence or phrase in that draft. Do not argue against an implication the draft does not make.
   - When the draft already states the correct principle, explicitly acknowledge that and frame changes as precision/wording improvements, not as corrections of a strawman. Example pitfall from FMC Kidney Life Plan review: the draft already said居家透析並非適合每一位病人/沒有最好只有最適合; the reply should not say "avoid making readers think home dialysis is always better" as if the author claimed that. Instead: "整體方向正確；建議把 HHD『提升治療效果』改成較精準的排程/頻率/時間描述，並把 PD『清潔』改成無菌操作與感染預防。"
   - Before finalizing an outbound reply, do a quick traceability check: each requested change should map to (a) a quoted/located source-draft phrase and (b) the retrieved medical/textbook basis.

5. **Integrate** — fixed answer skeleton:

   ```
   ## {結論一句話 zh-TW}

   ### 直接證據（本機 LLM-wiki）
   | 來源 (章節 + 行號) | 引用片段或重點 |
   |---|---|
   | Harrison 22e Ch{NN} (L{n}) | "..." |
   | Washington Manual 38e Ch{NN} §{name} (L{n}) | "..." |

   ### 外部 synthesis 對照（UpToDate / DynaMed → 其引用之原始文獻）
   - UpToDate "Topic title" → 引用 [PMID/DOI A, B, C] → 本機已有 [A, C] / 缺 [B → 建議 fetch]
   - DynaMed "Topic title" → 引用 [PMID/DOI D, E] → 全部本機已有 ✓
   *（NEVER cite UpToDate / DynaMed itself — they are navigators to primary refs only）*

   ### 機轉 / 補充
   - bullet, with inline (chapter+line) citation when claim is non-trivial

   ### 本機覆蓋盤點 (≤3 條)
   - ✅ 已有: ...
   - ❌ 缺: ... → 建議 fetch (citation_key + DOI/PMID + topic_path)
   - ⚠️ 不一致: 若 UpToDate / DynaMed 引用之最新 primary ref 與本機 synthesis 牴觸 → 註明並建議 fetch + update local wiki
   ```

5. **Boundaries**:
   - Question too broad ("CKD") → list top 5 hits with one-line each, ask Copper which angle to dive.
   - Question is "write a note about X" not "tell me about X" → redirect to `/note-writer` (Opus-only teaching note pipeline).
   - Question depends on figure / table / image content → respond "binary not in retrieval contract" + suggest spawning an image-description sub-agent if Copper has the source binary mounted.
   - Question is "for FB / publish / 衛教" → switch output mode: zh-TW publish-ready, calm objective voice (memory: `feedback_debunk_cool_objective_voice.md`), inline `[N]` citations + numbered `## References` list, reference tier = Tier 1 textbook + Tier 2 guideline + Tier 3 top-journal review only (memory: `feedback_reference_tier_copper_authored_notes.md`). NO internal infrastructure leak (memory: `feedback_no_ai_methodology_in_article_body.md`).

- **Textbook-grounded professional review of external drafts** — when Copper forwards an article/interview/patient-education draft and asks to check it against local textbooks (e.g. `去查 Daugirdas textbook modality choice 做專業校稿`), use the editorial calibration pattern in `references/textbook-grounded-professional-review.md`: retrieve precise textbook line ranges, write an internal grounded review, and provide a clean sender-facing reply draft without internal paths.

## Reference tier ordering (priority)

1. Tier 1 textbook chapter raw / synthesized wiki entry — strongest backing.
2. Tier 2 guideline raw / synthesized wiki entry — for clinical recommendations.
3. Tier 3 top-journal review (NEJM Review, Lancet Seminar, JAMA Review, Cochrane SR, Annual Review, Ann Intern Med In the Clinic) — for evolving topics.
4. Historical-anchor primary RCT — only when textbook / guideline endorses the cited RCT and the body labels it as historical reference.
5. Coverage gap → report fetch list (citation_key + DOI/PMID + topic_path); do NOT self-initiate WebSearch (No-Self-Initiated-Web-Search principle from /wikify skill).

## Output language convention

- Manual session = zh-TW Taiwan terminology (no PRC simplified, no PRC terms).
- Inline technical tokens stay English: drug names (e.g. `dapagliflozin`), file paths, code, column names, gene/protein symbols, classifier abbreviations (BISAP, APACHE-II, etc.).
- Tables in Markdown, never ASCII-art.
- No emoji unless Copper explicitly asks.
- No bullet "結論先行" preamble for short answers; jump straight into structure.

## Retrieval recipes (reusable Bash blocks)

### PG raw_index multi-key

```bash
psql -h hmj -U copper -d vault_main <<'SQL'
\pset pager off
SELECT DISTINCT citation_key, file_path, title, line_count
FROM wiki_raw.raw_index
WHERE file_path   ILIKE '%KW%'
   OR title        ILIKE '%KW%'
   OR citation_key ILIKE '%KW%'
   OR 'kw_lower'   = ANY(tags)
ORDER BY citation_key LIMIT 50;
SQL
```

### Personal-website wiki + notes

```bash
rg -l --type md -i 'KW_en|KW_zh' \
   ~/repos/personal-website/src/content/wiki/ \
   ~/repos/personal-website/src/content/notes/
```

### vault raw md

```bash
rg -l --type md -i 'KW' ~/repos/vault/
```

### Reading specific hit paragraph

```bash
# Use Read tool with offset+limit to avoid full-file loads on large textbooks
```

## What this skill does NOT do

- Does NOT write or modify any wiki / note / raw / personal-website / wiki_raw file. Pure read/answer cycle.
- Does NOT fetch external sources (no WebSearch, no curl to journal sites). Coverage gaps are reported, not closed in this skill.
- Does NOT generate teaching notes (use `/note-writer`).
- Does NOT ingest sources (use `/wikify`).
- Does NOT reach into binary (PDF / image / table / audio / video).
- Does NOT spawn task tracking, sub-agents, or background work for one-off Q&A.

## Cross-refs

- `_admin-rules/skills/wikify/SKILL.md` — ingest direction (source → raw → wiki); `/wiki` and `/wikify` are sibling triggers split 2026-05-07.
- `_admin-rules/skills/note-writer/SKILL.md` — Opus-only teaching note from medical PDFs.
- `_admin-rules/skills/fuse/SKILL.md` — multi-LLM report consensus → wiki entry.

## Memory dependencies

This skill assumes the following memory rules are loaded:

- `feedback_llm_wiki_retrieval_no_binary.md` (binary out of retrieval scope)
- `feedback_reference_tier_copper_authored_notes.md` (Tier 1/2/3 ordering)
- `feedback_inline_citation_numbered.md` (publish-bound citation format)
- `feedback_no_ai_methodology_in_article_body.md` (reader-only zone firewall)
- `feedback_debunk_cool_objective_voice.md` (calm objective voice)
- `feedback_pull_before_search.md` (don't declare missing without cross-device check)

Input: $ARGUMENTS
