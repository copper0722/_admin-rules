---
generated: false
type: data
name: zot
description: Deep-read a Zotero item — get fulltext, digest, create vault note. Use when the user provides a citationKey, Zotero item key, or says "讀這篇", "深讀". On-demand, not batch.
argument-hint: [citationKey or item key]
disable-model-invocation: true
---

Deep-read a single Zotero item → digest → create vault knowledge note.

**Principle: knowledge in vault, original in Zotero.**

## Workflow

1. **Locate**: `zotero_get_item_metadata` → title, authors, date, citationKey, itemType
2. **Read**: `zotero_get_item_fulltext` (if unavailable, report and stop)
3. **Digest**: Extract key insights, claims, findings
4. **Classify** by itemType + content:

| Type | Vault destination | Note format |
|---|---|---|
| Journal article / preprint | `醫學文獻筆記/{citationKey}.md` | Human note (zh-TW), teaching style |
| Web article / blog / general | `knowledge/{category}_{YYYYMMDD}_{desc}.md` | Follow `knowledge/_RULES.md` |
| Book / book chapter | `教科書筆記/{citationKey}.md` | Human note (zh-TW) |

5. **Create vault note** with citationKey in frontmatter `source:` field
6. **Tag**: `zotero_batch_update_tags` → add appropriate `_s/` subject tags
7. **Report**: item title → vault path created

## Rules
- Never store full article text in vault — only distilled knowledge
- Medical content → zh-TW, 台灣學術術語
- If item has no citationKey (e.g. webpage), use item key as fallback
- Respect `knowledge/_RULES.md` and `醫學文獻筆記/_RULES.md` for format

Input: $ARGUMENTS
