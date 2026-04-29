# language

## Manual session contract
- user = 王介立醫師 (Copper), nephrologist, HD specialist
- chat language = zh-TW, Taiwan academic terminology, never PRC simplified or PRC terms
- tone = rational, no pleasantries
- before answering = restate request in precise domain terms, then answer directly or execute
- do not force an argue-against/counter/conclude template unless Copper explicitly asks for adversarial analysis
- manual chat contract does not override agent-facing file language

## Output language
- user-facing output = zh-TW, TW academic terminology, never PRC simplified terms
- agent-only / machine-read files (M2M) = compressed English
- tone = rational, no pleasantries
- before answering = restate in precise domain terms, then answer directly or execute
- reasoning = direct by default; adversarial structure only when explicitly requested

## Audience routing
- Chat to Copper = zh-TW.
- Copper-reading documents live only under note repos (`note/`, `note/textbook-notes/`, explicit future note repos) plus paired PDFs.
- Other repos, including private repos, are M2M by default.
- Agent-only files = M2M English even during manual zh-TW sessions.
- Agent-only examples: `AGENTS.md`, `CLAUDE.md`, `rules/*.md`, `skills/*/SKILL.md`, `agents/*.md`, prompts, audit cards, task cards, runbooks, handover templates, status docs.
- Public/human deliverables outside note repos must be explicitly marked as deliverables; repo-internal docs remain M2M.
- Ambiguous `.md` outside note repos defaults to M2M English.

### Anti-drift (BUG-055, 2026-04-24)
- output-lang ≠ input-lang; handover/tool-out/WebFetch/.md = English → chat reply still zh-TW
- anti-pattern triggers: "Fetched / Done / Updated / Card updated." → switch to 「已抓/已更新」
- technical inline stays English (paths, code, flags, column names); zh-TW wraps: 「跑 `.script/foo.py` → 輸出 `_data/bar.tsv`」
- `AGENTS.md` card write = English M2M; chat reply about it = zh-TW; same session both OK
- manual session is not a language override for agent-facing files

## File encoding
- cross-device sync files = .md only (§1.2)
- M2M notes: dense, no filler words, structured tables preferred
