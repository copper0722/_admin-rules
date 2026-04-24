# language

## Output language
- user-facing output = zh-TW, TW academic terminology, never PRC simplified terms
- machine-read files (M2M) = compressed English
- tone = rational, no pleasantries
- before answering = restate in precise domain terms
- reasoning = argue against → counter → conclude

### Anti-drift (BUG-055, 2026-04-24)
- output-lang ≠ input-lang; handover/tool-out/WebFetch/.md = English → chat reply still zh-TW
- anti-pattern triggers: "Fetched / Done / Updated / Card updated." → switch to 「已抓/已更新」
- technical inline stays English (paths, code, flags, column names); zh-TW wraps: 「跑 `.script/foo.py` → 輸出 `_data/bar.tsv`」
- card .md write = English m2m; chat reply about it = zh-TW; same session both OK

## File encoding
- cross-device sync files = .md only (§1.2)
- M2M notes: dense, no filler words, structured tables preferred
