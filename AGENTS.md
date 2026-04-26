# _admin-rules Agent Card

Scope: public rules, skills, commands, and reusable agent behavior under `/Users/copper/repos/_admin-rules`.

## Canonical Role

- This repo contains reusable public agent governance.
- Keep rules generic enough for public sharing; no secrets, patient data, private device tokens, or private family/clinic details.
- Private operational topology belongs in `_admin-private/`, not here.

## Edit Rules

- Rules live in `rules/`.
- Agent prompt templates live in `agents/`.
- Claude/Codex commands live in `commands/`.
- Skill packages live in `skills/`.
- Do not duplicate root Law; reference `/Users/copper/repos/AGENTS.md` for global policy.

## Quality Bar

- M2M English by default.
- Prefer deterministic, testable rules over prose-only norms.
- If a rule can be enforced mechanically, create or update an audit script in `_admin-private` and keep this repo as the public policy surface.
