---
type: data
name: inbox-promote
description: "Promote a sidecar bundle (PDF + raw.md + figures) from any of three inboxes (Dropbox/_Inbox, ~/repos/_inbox, ~/VaultBinary/_inbox) into the canonical sidecar layout at ~/VaultBinary/_sidecar/{citationKey}/, with sha-based diff-merge for duplicates and citation-key block on ambiguity. Manual trigger only. MANDATORY TRIGGERS: /inbox-promote, /promote, promote inbox, ingest dropbox, 處理 inbox, 新 sidecar, inbox 進貨."
argument-hint: "[no args | citationKey override | 'all' | 'dry-run']"
---

# /inbox-promote — Sidecar Bundle Ingestion

Manual-trigger skill. Sweeps all three inboxes for sidecar bundles, diff-merges duplicates, blocks on ambiguous citation keys, then chains into `/wiki`.

## Principle

A "sidecar bundle" = source PDF (or just .md) + (optional) Clipper-extracted .md + (optional) figure/table images, downloaded as a unit. The sidecar layout `~/VaultBinary/_sidecar/{citationKey}/` is canonical (Law §9.3 step 2). This skill normalizes raw inbox bundles into that layout.

Manual-only: agent never auto-promotes without explicit `/inbox-promote` invocation. Reason: citation-key inference is fragile; auto-rename can pollute vault namespace.

## Three inbox sources (cross-device, scan all on every run)

| inbox | path | typical content |
|---|---|---|
| Dropbox cloud | `~/Library/CloudStorage/Dropbox/_Inbox/` | mobile/iPad/desktop downloads, Obsidian Clipper bundles |
| Git tree | `~/repos/_inbox/` | `.md` only (text-side staging; binary banned) |
| OWC binary | `~/VaultBinary/_inbox/` | large PDFs, dynamed batches, dispatch md, Zotero.dmg-style installs |

All three accessible from any Mac (hm4/hmj/cm1/mbp/mba). Cross-device prerequisite: VaultBinary SMB mount must be reachable; Dropbox sync must be current. If either is missing → block with `cannot reach {path}` and exit.

## Bundle detection

1. Sweep all three inboxes (excluding `.DS_Store`, `_archive/`, `chrome-downloads/`, app bundles like `*.app`, `*.dmg`, `*.zip`).
2. Group files by mtime proximity (5-min window) → each group = one bundle.
3. Bundle requirements:
   - At least one `.pdf` OR one `.md` (otherwise skip — likely orphan asset).
   - Other files (`.png/.jpg/.txt`) attached to the closest qualifying bundle by mtime.
4. Dispatch heuristics:
   - PDF >50 MB OR page count >300 (via `pdfinfo`) → suggest `/textbook-ingest` (BrennerRector/Harper33e flow), not promote here. Block with rationale.
   - PDF only, no .md → run MinerU + proofread first (delegate to `pdf-to-raw.py`) to produce source.md, then continue.
   - `.md` only, no PDF → still promote (some sources are text-only, e.g. Gmail digest).

## citationKey derivation (fallback ladder; BLOCK on failure)

1. Clipper frontmatter: `.md` has `source:` URL → known journal pattern (JAMA/NEJM/AJKD/CJASN/PubMed) → first-author-lastname + year + topic-stem-CamelCase (e.g., `Ayoade2026CAMBreastCancer`).
2. PDF metadata: `pdfinfo source.pdf` → Title/Author/Year → derive key.
3. Zotero match: query Zotero API by DOI/URL → use `Better BibTeX Citation Key`.
4. **None of the above succeed → BLOCK** (per Copper directive). Print:
   - bundle file list + sha
   - what each fallback returned
   - prompt: "請命名 citationKey for bundle {N} (or skip)"
   - DO NOT auto-fallback to `Inbox{date}_{slug}`.

## Source fidelity ranking (Copper directive 2026-04-29)

Manual-download raw is highest quality. When choosing which `source.md` to keep on duplicate, prefer:

```
1. Obsidian Clipper       ← highest (publisher HTML → structured md, KaTeX preserved, table HTML intact, image alt-text)
2. Publisher XML/JSON     ← high (when available, e.g., NEJM view-as-XML)
3. MinerU PDF extract     ← good (OCR + layout but loses some structure)
4. plain pdftotext        ← lowest (no structure)
```

Detect provenance from `source.md` frontmatter:
- **Clipper**: `tags: [clippings]` OR `source:` URL in frontmatter
- **MinerU**: `agent: mineru-pipeline` (or `agent: mineru+gemma4-cloud-proofread`) in frontmatter
- **Basic**: no frontmatter or unrecognized agent

## Duplicate handling — diff-merge with LLM judgment

When new bundle's source.pdf SHA matches an existing `_sidecar/{key}/source.pdf`:

```
new bundle → existing sidecar (target)
for each file in new bundle:
  - source.pdf:
      same sha as target → skip (canonical)
  - source.md:
      same sha → skip (no-op)
      different sha → LLM judges by provenance ladder:
        * new=Clipper, target=MinerU/Basic → REPLACE (per Copper directive: manual Clipper has highest quality)
                                              archive target/source.md → target/_archive/source.{ISO}.{prov}.md
        * new=Clipper, target=Clipper      → BLOCK: agent reads both, asks Copper
                                              "newer Clipper found for {key}. diff: +N lines, -M lines.
                                               replace? (replace / keep / save-as-source-v2.md)"
        * new=MinerU,  target=Clipper      → KEEP target (do NOT downgrade); archive new to target/_archive/
        * new=MinerU,  target=MinerU       → newer mtime + larger size wins; archive loser to _archive/
        * new=Basic,   target=*            → KEEP target; archive new
  - figures/*.png or *.jpg:
      compute sha → match any file in target/figures/ → skip (deduplicated)
                  → no match → ADD to target/figures/ as next available figure_N.png OR table_M.png
                              → if filename collision (figure_3.png exists with different sha) → save as figure_3.alt-{sha[:8]}.png + audit_finding
  - other files:
      add to target/_archive/ with date prefix
```

**LLM judgment authority**: agent compares provenance + content diff and decides replace / keep / block. Never pure heuristic — every replace requires either (a) provenance ladder dictates it (Clipper > MinerU > Basic, no ambiguity), or (b) Copper confirms in chat.

Outcome: target sidecar gains any NEW images/text the new bundle has; the canonical `source.md` upgrades to highest fidelity available; replaced files preserved under `_archive/` (Law §1.3, no deletion). After merge, new bundle removed from inbox (mv to inbox/_archive/{date}/).

## Layout (canonical, post-promote)

```
~/VaultBinary/_sidecar/{citationKey}/
├── source.pdf
├── source.md            (Clipper or MinerU-extracted)
├── figures/
│   ├── figure_1.png
│   ├── figure_2.png
│   ├── table_1.png
│   └── ...
├── metadata.json        (sha256 per file, source URL, ingest agent, ingest_at, mineru_status: skip if Clipper bundle, pending if PDF-only)
└── _archive/            (only created when diff-merge surfaces conflicts)
```

## Workflow (numbered steps, agent follows)

1. **Pre-flight**: verify mounts. Run `helper preflight`. If fail → print error + exit.
2. **Sweep**: `helper sweep` lists every bundle across three inboxes with computed sha + size + suggested citationKey + dispatch type (promote / textbook / pdf-to-raw).
3. **For each bundle, in order**:
   a. Show bundle to Copper: file list + sha + suggested key + duplicate match (if any).
   b. If textbook → block, suggest `/textbook-ingest` instead.
   c. If PDF-only and no .md → run `pdf-to-raw` first, then re-evaluate as bundle.
   d. If citationKey derivation succeeded:
      - If duplicate detected → run diff-merge.
      - If no duplicate → mkdir `_sidecar/{key}/{,figures/}`, mv files with canonical names, write `metadata.json`, mv inbox bundle to `inbox/_archive/{date}/`.
   e. If citationKey derivation failed → BLOCK, ask Copper to provide citationKey (or skip this bundle).
4. **Wikify chain**: after each successful promote, invoke `/wiki` on `_sidecar/{key}/source.md` to produce `medwiki-raw/{topic}/{key}.md`.
5. **Final report**: list all promoted, merged, blocked, and skipped bundles + final state of inboxes.

## Helper script

Path: `_admin-private/.script/inbox-promote.py`

Subcommands:
- `preflight` — verify Dropbox sync + VaultBinary mount + PG reachable. Exit 0 if all green.
- `sweep` — emit JSON list of bundles found across all three inboxes.
- `derive-key BUNDLE_ID` — return citationKey derivation result + fallback ladder trace.
- `check-duplicate BUNDLE_ID` — return existing sidecar match + per-file sha diff plan.
- `promote BUNDLE_ID [--key KEY]` — execute mv + metadata.json. `--key` overrides derivation.
- `merge BUNDLE_ID --target KEY` — execute diff-merge into existing sidecar.

All subcommands write to PG `audit_findings` for events that need follow-up (unidentified key, sha collision, mount missing, etc.).

## Block conditions (explicit, do not auto-resolve)

| condition | action |
|---|---|
| VaultBinary not mounted | block, ask Copper to mount + retry |
| Dropbox sync stale (>15min) | block, ask to verify Dropbox is up-to-date |
| citationKey derivation fails | block, ask Copper for key (per directive 2026-04-29) |
| Bundle is textbook (>50MB or >300p) | block, suggest `/textbook-ingest` |
| Same citation key, different source.pdf sha | block, ask: supersede / alternate-version / different-paper |
| PG not reachable | proceed without audit logging, surface warning at end |

## Cross-device behavior

Skill runs on any Mac. All three inbox paths are macOS-standard so no host-specific code. Sidecar destination is always `~/VaultBinary/_sidecar/` (hmj OWC, SMB-mounted everywhere). Output paths use absolute `~` expansion. PG access via Tailscale `hmj:5432` (works from any Mac on the tailnet).

## Cross-references

- `_admin-rules/skills/wiki/SKILL.md` — chained after promote
- `_admin-rules/skills/db/SKILL.md` — `inbox_promote_log` table optional (TODO)
- `medwiki-raw/wiki-classification-sop.md` — citationKey rules
- `medwiki-raw/AGENTS.md` § "Sidecar key schema" — key format authority
- `medwiki-raw/pipelines/textbook/AGENTS.md` — textbook fork
- `_admin-private/.script/pdf-to-raw.py` — fallback for PDF-only bundles
