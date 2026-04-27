# folder-and-tag — wiki classification SOP

Consolidated rule set for vault folder hierarchy + article tagging. Unifies `§8.10`/`§10.2-3`/`§8.6`/`§8.8` (from pre-Phase-9c Vault Rules, lost in 2026-04-25 split) + `medwiki/_system/taxonomy.md` v0.1 (pending review since 2026-03-26) + Copper directives 2026-04-25/26.

This doc is **canonical** for hierarchy + tag SOP. Other refs (`medwiki-raw/CLAUDE.md`, `fuse SKILL.md`, etc.) cite this.

## §1 Universal invariants

1. **dir = topic, file = article** (no `{key}/raw.md` wrapper; flat `{key}.md`)
2. **lowercase including acronyms** (revised 2026-04-22 from old UPPERCASE: `ckd`/`esrd`/`aki`/`nejm`)
3. **`_-prefix` exempt** from topic rules (`_archive/_data/_sidecar/_translations/_system/_index.md` etc.)
4. **3-way mirror invariant**: `medwiki-raw/{path}` ≡ `medwiki/{path}` ≡ Zotero collection (raw/wiki/Zotero hierarchies aligned)
5. **All structured data → PG `vault_main`**; no `.tsv`/`.db` canonical (skill-bundled `.csv` opt-out exception)
6. **Layer purity** (Copper 2026-04-26): `medwiki/` = purely extremely m2m (compressed English, machine retrieval). Any Copper-read content (zh-TW prose, journal club discussion, reading guide, learning summary, weekly tracker) → `~/repos/note/`. `note/` = Copper-readable; `medwiki-raw/` = verbatim source; `medwiki/` = synthesis-for-machine. Cross-layer migration ≠ delete (preserve original layer if reused).
7. **Layer organization style** (Copper 2026-04-26):
   - `medwiki/` flat-friendly (machine doesn't need human nav; agent uses tags + grep)
   - `medwiki-raw/` topic-tree §8.10 strict (3-way mirror, source organization)
   - `note/` **user-friendly Obsidian hierarchy required** (Copper browses via Obsidian; flat = poor UX). DO NOT flatten note/. Build user-friendly folder tree (e.g. `note/{specialty}/{disease}/{key}.md` or by reading-program / journal / textbook source).

## §2 Topic-tree (§8.10 a-h, resurrected)

(a) **3-way mirror** raw/wiki/Zotero — see invariant §1.4.
(b) **同心圓 (concentric circle)**:
- topic = center; siblings = mutually exclusive rings at same depth
- cross-cutting article (fits ≥2 sibling rings) → ascend to parent
- cross-cutting **topic** (whole sub-domain spans ≥2 parents) → **symlink**: canonical in primary parent + symlink in others
- example: `nutrition/sport_nutrition/` canonical + `sport/sport_nutrition` symlink
- siblings MUST be mutually exclusive; if not → ascend
(c) all-lowercase including acronyms.
(d) **Data-driven depth** — top-level skeleton predefined: `basic_medicine/clinical_medicine/medical_statistics/nutrition/research_method/sport/public_health/ai/`. Sub-folder open ONLY when ≥**15-20** entries warrant (§10.2 threshold, revised 2026-04-22 from 30). <15 entries → flat `.md` under parent. Hard depth ceiling **5 levels**.
(e) Each topic folder has `_index.md` (script-regeneratable, agent retrieval landing).
(f) **On-touch migration**: legacy flat files grandfathered, migrate when edited; NEW content goes directly into tree.
(g) Textbooks in topic tree directly: `{topic}/{textbook_key}_Ch{NN}_{slug}.md` (Phase-4 schema, post-flatten 2026-04-26; reaffirmed 2026-04-27 Copper directive). **`_textbooks/` retired** (was source-bin; violated dir=topic). **No per-book subdir.** 2-digit chapter number padding (`Ch00`, `Ch07`, `Ch84`). Existing `_textbooks/{book}/` legacy content = grandfathered, on-touch migrate per §2.f. NEW textbook chapters MUST go to `{topic}/{textbook_key}_Ch{NN}_*.md` directly (no `_textbooks/` wrapper, no per-book subdir). Reasoning (Copper 2026-04-27): raw layer is M2M only ("我 read PDF and note, never read raw"), no human-friendly hierarchy needed; one flat layer per topic; agent retrieval via `rg` + tags. **Agents MUST NOT ask Copper to confirm placement** — this rule is locked. See also: `medwiki-raw/AGENTS.md` § "Textbook chapter placement".
(h) Zotero nested via `parentCollection`; `zotero-vault-sync.py sync-collections` propagates.

## §3 Single-article-dir demolish

Topic dir containing **only 1 article .md** (excl `_index.md`/`CLAUDE.md`) and no subdirs → **demolish**: promote file to parent topic, `rmdir` empty wrapper. No grouping value.

Audit: `single_article_dir` (priority 145, daily). Already in PG.

## §4 Functional sub-folder design (when topic >15 articles)

Per §8.10(d) / §10.2: when topic flat exceeds 15-20 articles → split sub-folders. Splits MUST be:
- **Functional** (semantic clustering: by sub-topic / methodology / population) — NOT alphabetical, NOT chronological
- **5-10 sub-folders** target (each holding 3-15 articles = sweet spot)
- **Mutually exclusive siblings** (per §2.b)
- **`lowercase_snake` names**, content-descriptive (no `misc/`, no `other/`)

LLM-driven: `llm_topic_subfolder_design` (priority 245, weekly opus). Reads article frontmatter+title, clusters, proposes schema. Codex / agent applies via `mv`.

## §5 Tag SOP — content-derived, not source-derived

### §5.1 Tag schema (canonical in `medwiki/_system/taxonomy.md`)

```yaml
tags:
  - _s/{specialty}/{disease}/...   # subject — what article is about (hierarchical)
  - _t/{type}                       # type — RCT / cohort / review / guideline / case-report
  - _w/{status}                     # workflow — wikified / pending / orphan
```

Examples: `_s/im/nephrology/ckd/anemia`, `_t/RCT`, `_w/wikified`

### §5.2 Quality vs lazy

| level | example (Harrison Ch329 — Hypertensive Nephropathy) | judgment |
|---|---|---|
| **Lazy** (NG) | `_t/textbook`, `#harrison`, `_s/im/cardiology` (too broad), `chapter329` | source/format/series only — wiki SOP fail |
| **Quality** (OK) | `_s/im/nephrology/hypertension`, `_s/im/nephrology/secondary_htn`, `_s/im/nephrology/renal_artery_stenosis` | content-derived from chapter actual coverage |

**SOP for agent ingest**:
1. read raw.md content (don't trust filename / source name)
2. extract content topics → map to `_s/...` hierarchical tags
3. add `_t/...` study type from frontmatter or content
4. **tag drives folder placement** (§5.3), not the other way around

### §5.3 Tag → folder placement

Per §2(b) 同心圓:
- article tag `_s/im/nephrology/hypertension/secondary_htn` → folder `medwiki-raw/clinical_medicine/internal_medicine/nephrology/hypertensive_kidney_disease/`
- if tag spans ≥2 rings → place in primary; symlink to others
- audit `llm_folder_vs_tag_consistency` (priority 247, weekly) verifies tag→path consistency

### §5.4 Taxonomy lifecycle (§10.3 data-driven)

```
data → LLM cluster → Copper review → freeze
```

`medwiki/_system/taxonomy.md` is currently v0.1 draft — never completed «freeze». Outstanding TODO: finalize taxonomy → freeze → all subsequent agent writes constrain to frozen tag set; new tags require Copper review.

## §6 Specific case — nephrology/hypertension (Copper 2026-04-26)

Current state: `clinical_medicine/internal_medicine/nephrology/hypertension/` (10+ articles) + `clinical_medicine/internal_medicine/cardiology/hypertension/` (parallel).

Issues:
- "hypertension" too broad; doesn't distinguish general HTN vs CKD HTN
- Articles in nephrology/hypertension/ may be cardio-renal cross-cutting

Spec action:
- rename `nephrology/hypertension` → `nephrology/hypertensive_kidney_disease/` (or `hypertension_and_kidney/`)
- per-article semantic re-classify (LLM-required):
  - article about general HTN (population, BP target unrelated to renal) → mv to `cardiology/hypertension/`
  - article about CKD HTN (BP in dialysis, renal denervation, hypertensive nephropathy) → keep `nephrology/hypertensive_kidney_disease/`
  - cross-cutting (cardio-renal HTN, e.g. ARB in CKD with cardio outcome) → primary based on dominant focus + symlink mirror

This is the §2(b) 同心圓 + §5.3 tag→path workflow in action.

## §7 PG audit catalog supporting this spec

(11 entries total; INSERT'd 2026-04-25/26; cm1 agent runs via `audit/scripts/run-due.py` for script kinds, manual `claude -p` for llm kinds)

| pri | task | driver | covers |
|---|---|---|---|
| 25 | claudemd_size | script | §10.9 / card <150L |
| 35 | oversized_md_2000 | script | §9.2 split candidate |
| 70 | raw_no_frontmatter | script | §5.1 required tag fields |
| 90 | long_md_missing_summary | script | §9.1 summary frontmatter |
| 130 | medwiki_topic_parity | script | §1.4 raw↔wiki mirror |
| 135 | missing_index_md | script | §2(e) `_index.md` per topic |
| 140 | index_md_regen | script | §2(e) auto-generate stale |
| 145 | single_article_dir | script | §3 demolish single-article wrappers |
| 220 | llm_l3_semantic_dup | llm | wiki content overlap |
| 245 | llm_topic_subfolder_design | llm | §4 functional sub-folder |
| 246 | llm_lazy_tags | llm | §5.2 lazy vs quality tags |
| 247 | llm_folder_vs_tag_consistency | llm | §5.3 tag→path verify |
| 250 | llm_misplaced_files | llm | §5.3 article in wrong folder |
| 295 | llm_semantic_dir_synonyms | llm | §2(b) sibling synonym dup |

## §8 Outstanding fixes for cm1 agent

(consolidated from this session's audit + handover #524, #584, #585 to_do/bug)

### High-priority fixes (Bug)

1. **Law (`~/repos/CLAUDE.md`) L32 broken ref**: `note/Hernan_WhatIf/causal_inference_critical_appraisal_checklists.md` does not exist. note repo has no Hernan_WhatIf dir. Source `.txt` only in `medwiki-raw/_archive/_textbooks-pre-wikify-2026-04-26/Hernan_WhatIf/`. Either wikify the .txt → place at expected path, OR fix Law ref to actual location.
2. **medwiki/_wiki-rules-merge-pending.md (162L)**: orphan from medwiki/wiki/ flatten 2026-04-25; merge content into medwiki/CLAUDE.md, then rm.
3. **medwiki-raw/CLAUDE.md L50 stale**: still says "lowercase_snake with UPPERCASE acronyms" — outdated by §8.10(c) revision 2026-04-22 to all-lowercase. Update.
4. **Stale § references throughout**: `§8.10`, `§10.2`, `§9.1`, `§10.9` cited in many .md files but canonical doc was lost in Phase-9c split. After this rule consolidates, update refs to point at `_admin-rules/rules/folder-and-tag.md` (this doc) for hierarchy+tag rules, or other resurrected rule docs.
5. **note/ flat (drift from §1.7)**: note repo currently flat (citationKey-named .md at root, including 12 just-imported `*_zh.md` translations). Per §1.7 needs Obsidian-friendly hierarchy. cm1 agent design + apply (probably `note/{specialty}/{disease}/{key}.md`). Don't flatten further.

### Mid-priority TODO

5. **Wikify _textbooks pending**: 26 `.txt` chapters in `medwiki-raw/_archive/_textbooks-pre-wikify-2026-04-26/` (Hernan_WhatIf 6, Clinical_D_D 8, Guyatt_Users_Guides 2, NEJM_Perspective 1, NEJM_Perspective_ParaMedical 9). MinerU pipeline → `{topic}/{textbook_key}_{ChNN}.md` per §2(g).
6. **Apply llm_topic_subfolder_design** for: nutrition (35), sport (22), clinical_medicine (11). Run audit, get findings, mv articles to designed sub-folders.
7. **Apply llm_misplaced_files** for whole 1252+ raw `.md` corpus (post-flatten). Sample 50/run.
8. **Apply llm_lazy_tags** for whole corpus — re-tag where lazy.
9. **Apply llm_folder_vs_tag_consistency** — verify tag→path post-rebalance.
10. **Apply llm_semantic_dir_synonyms** across all topic dirs.
11. **Finalize `medwiki/_system/taxonomy.md`** v0.1 → v1.0 frozen per §5.4. Use llm_lazy_tags + llm_folder_vs_tag_consistency findings to inform.
12. **Sub-stub script handlers** (`orphan_raw_md` / `schedule_registry_drift` / `note_without_raw_parent` / `git_uncommitted_drift`): migrate to generic `audit_kind` if pattern fits (e.g. `orphan_raw_md` → custom kind `pair_check`); else write actual handler.

### Low-priority / blocked

13. **mba** Tailscale rename (Copper manual UI step).
14. **DB LAW migration** (task #14): inventory remaining `.tsv`/`.db`/`.csv` outside skill assets, migrate to PG.
15. **mbp/mba `~/.zshenv` parity**.

## §9 Cross-references

- Skills using this spec: `wiki/SKILL.md`, `fuse/SKILL.md`, `note-writer/SKILL.md`, `audit/SKILL.md`, `bug/SKILL.md`, `handover/SKILL.md`
- Folder cards citing this spec: `medwiki/CLAUDE.md`, `medwiki-raw/CLAUDE.md`, `note/CLAUDE.md`
- Pre-Phase-9c archived source: `_admin-private/_archive/_pre-split-vault-archive-20260425-151136/CLAUDE.md` §8.10/§10.2/§10.3/§8.6/§8.8

After this doc lands as canonical, scattered §8.10/§10.2 refs in skills/cards should be updated to `_admin-rules/rules/folder-and-tag.md` (no more drift).
