---
name: todo
description: "TODO format and management. Use when writing, reading, or scanning TODOs in any AGENTS.md card. Also use when agent needs to understand type/mode system. MANDATORY TRIGGERS: /todo, write TODO, add task, vault-todo, scan todos, TODO format."
---

# TODO Format

Standard format for all `AGENTS.md` TODO items. Scanned by `vault-todo.py` and dashboard `/api/todos`.

## Format

```
- [ ] {description} — {type}:{mode} ({YYYY-MM-DD}), {source}
- [x] {description} — {type}:{mode} ({YYYY-MM-DD}), {source} ✅ {completion-date}
```

## Types

| type | meaning | example |
|---|---|---|
| `dispatch` | assigned from another agent/card | from tsn agent, from Aiko |
| `plan` | self-planned task | admin roadmap item |
| `bug` | needs fixing | auth broken, script crash |
| `blocked` | waiting on external | needs Copper decision |
| `manual` | requires Copper's hands | physical setup, UI config |
| `dd` | deep dive research | new topic to learn |
| `review` | revisit existing research | old topic with new data |

## Modes

| mode | meaning | behavior |
|---|---|---|
| `auto` | scheduled agents can execute directly | /burn, trigger sees → does |
| `manual` | needs Copper confirmation | interactive session asks first |

Default mode = `manual` (if omitted). Examples: `dd:auto`, `plan:manual`, `bug` (= bug:manual).

## Rules

1. `{type}` required. `{date}` required (creation date). `{source}` optional.
2. Agent writing TODOs MUST use this format. Old format encountered → convert on touch.
3. `vault-todo.py` = sole scanner. Path: `.script/vault-todo.py`.
4. Completed items: keep 30 days, then may be cleared.
5. TODOs live in `## TODO` section of `AGENTS.md` (§10.9 card structure).

## /burn Behavior

Burn run (gated on token budget, never on clock hour): `vault-todo.py` scans all cards → filters `mode=auto`:
1. `dd:auto` → Opus agent per topic → deep dive → write to project KB
2. `review:auto` → Sonnet agent → read past + new → update note
3. `bug:auto` → fix
4. `plan:auto` → execute
5. `manual` → skip (wait for interactive session)

## Project KB Pipeline (§10.10)

Every proj/ encountering a related topic → extract keywords → dd:auto TODO.
External input (email, 公告, meeting) → save to `policy/` subfolder + update `_index.md`.
New topic = dd. Existing topic = review.
