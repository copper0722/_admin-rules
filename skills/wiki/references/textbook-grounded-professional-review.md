# Textbook-grounded professional review of external drafts

Use when Copper forwards an external article/interview/patient-education draft and asks for professional proofreading/calibration against the local corpus (e.g. `去查 Daugirdas textbook modality choice 做專業校稿`).

## Pattern

1. Treat this as retrieval + editorial calibration, not wikify and not a new published wiki article.
2. Read the external draft already saved under secretary or extract it from attachments if needed.
3. Search local `~/我的雲端硬碟/agent-share/textbook/` (gdrive canonical) / `vault/` for the precise clinical frame. For completed textbook chapters, search `proofread.md` / `article.md`; do not decompress or search `raw.md.gz` unless auditing provenance.
4. Read specific line ranges from the relevant chapter(s), not whole books.
5. Produce two artifacts when useful:
   - internal professional review with source/line grounding for Copper
   - concise reply draft that Copper can paste to the sender, without internal file paths or line citations
6. For patient-facing media drafts, prefer cautious wording:
   - avoid implying one modality is universally best
   - distinguish evidence from policy preference
   - flag observational evidence and selection bias when claims sound causal
   - include treatment burden, feasibility, caregiver support, life goals, and shared decision-making
7. Save the review under the existing secretary project folder and copy the paste-ready reply to clipboard when appropriate.

## Example: Kidney Life Plan / dialysis modality choice

Grounding from Daugirdas Handbook of Dialysis 6e:
- Ch15: modality selection should educate patients about all available options; choices depend on patient preference, accessibility, feasibility, and medical factors. Home modalities can be prioritized when medically appropriate and feasible, but not as a one-size-fits-all rule.
- Ch15: home HD outcome advantages are largely observational and subject to selection bias / unmeasured confounding; avoid writing `HHD improves survival/treatment effect` as a certainty.
- Ch23: PD prescription has moved from narrow adequacy/clearance framing toward High-Quality Goal-Directed PD, including volume status, residual kidney function, symptoms, treatment burden, and quality of life.

## Output style

- Chat/report to Copper: zh-TW, concise, with cited local line ranges if making professional claims.
- Sender-facing draft: polite, no internal infra/file paths, no mention of agents/tools, and no over-technical citation dump unless Copper asks.