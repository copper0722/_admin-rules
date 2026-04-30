# _admin-rules Agent Card

Scope: public rules, skills, commands, and reusable agent behavior.

## Canonical Role

- This repo contains reusable public agent governance.
- Keep rules generic enough for public sharing; no secrets, patient data, private device tokens, or private family/clinic details.
- Private operational topology belongs in the private operations repo, not here.

## Edit Rules

- Rules live in `rules/`.
- Agent prompt templates live in `agents/`.
- Claude/Codex commands live in `commands/`.
- Skill packages live in `skills/`.
- Terminology: card = `AGENTS.md`; Law = workspace root `AGENTS.md`.
- `CLAUDE.md` is a Claude auto-injection shim/symlink, not the editable card.
- Do not duplicate root Law; reference the workspace root `AGENTS.md` for global policy.

## Quality Bar

- Agent-only / machine-facing files = M2M English, always.
- Manual zh-TW chat does not change file language.
- Copper-reading documents live only under note repos; other private repos remain M2M.
- Public/human deliverables outside note repos must be explicitly marked as deliverables.
- Prefer deterministic, testable rules over prose-only norms.
- If a rule can be enforced mechanically, create or update an audit script in the private operations repo and keep this repo as the public policy surface.
