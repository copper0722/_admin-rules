---
type: data
name: nejm-issue
description: "Manual NEJM issue/TOC enqueue + agent-driven preference filter. Trigger when Copper says /nejm-issue, NEJM 本期, NEJM weekly, NEJM 抓本期, scrape NEJM TOC, or after a Thursday issue drops. Spawns an agent that runs enqueue-toc.sh, then re-prioritises pending rows in public.nejm_queue per Copper's preference filter (review/perspective/nephrology/cardio/AI bias; pure physics/chemistry/materials/astronomy → skipped)."
argument-hint: "[--url URL]   default: navigate to https://www.nejm.org/toc/nejm/current"
---

# /nejm-issue — NEJM weekly issue manual trigger

Replaces the (removed) `nejm-toc-thursday` cron. Copper invokes this on
Thursdays after the new issue drops, or any time he wants to refresh the queue
from a TOC URL.

The skill does two things sequentially:

1. **Scrape TOC into PG queue** (`enqueue-toc.sh`)
2. **Spawn an agent** that re-prioritises the freshly-enqueued rows per
   Copper's preference filter, marks out-of-scope DOIs `skipped`, and reports.

The q30m drain (`quality_audit_tasks.nejm-drain` on hm4) then absorbs the
prioritised pending rows naturally; no separate launch needed.

## When to use

- Thursday after the weekly NEJM issue drops (new TOC at `nejm.org/toc/nejm/current`)
- Any time Copper wants to refresh from a different TOC URL (e.g. a specialty
  collection, archive page, search result)
- After clearing a CF block — re-prime the queue from the latest issue

## Workflow

### Step 1 — Scrape (deterministic, no LLM token)

Call `enqueue-toc.sh` with the navigation flag of choice:

```bash
~/repos/medwiki-raw/scripts/NEJM/enqueue-toc.sh --current-issue
# or:
~/repos/medwiki-raw/scripts/NEJM/enqueue-toc.sh --url <SOMETHING>
# or (TOC already loaded in Chrome Beta tab):
~/repos/medwiki-raw/scripts/NEJM/enqueue-toc.sh
```

Script ON CONFLICT DO NOTHING → safe to call multiple times.

### Step 2 — Preference filter (agent-driven; Sonnet OK)

Spawn a sub-agent with the prompt below. The agent reads the new pending
rows, applies Copper's preference filter, UPDATEs priority/status, and
returns a one-paragraph summary.

```
Agent({
  description: "NEJM TOC preference filter",
  subagent_type: "general-purpose",
  prompt: <<<the prompt below>>>
})
```

#### Agent prompt

> You are processing NEJM articles freshly enqueued in `public.nejm_queue`
> on hmj (DSN `postgresql://copper@hmj/vault_main`). Your job: re-prioritise
> the **status='pending' AND enqueued_at >= now() - interval '6 hours'**
> rows per Copper's preference filter, and skip out-of-scope ones.
>
> Filter (from `_admin-rules/skills/crawler/SKILL.md` + Copper's stated
> preferences):
>
> | content | action |
> |---|---|
> | Biomedical Review / Perspective / Editorial | **priority +50** (always download) |
> | Original Article in nephrology / cardio / infection / endocrine / neuro / pharmacology | priority +30 |
> | AI + medicine / biology | priority +30 |
> | TLC potential (counterintuitive, story-worthy, general appeal) | priority +20 |
> | Nutrition / exercise physiology / aging | priority +20 |
> | Original Article in oncology / surgery / OB-Gyn / psychiatry | priority 100 (default) |
> | Pure physics / chemistry / materials / climate / plant / astronomy | **status='skipped'** |
> | Letters to the editor / corrections (NEJMc*) | priority -30 |
>
> Use article_type, title, and the source URL to judge. NEJMoa = Original
> Article; NEJMra = Review; NEJMp = Perspective; NEJMcps / NEJMcpc =
> case-records; NEJMicm = Images in CM; NEJMc = Correspondence; NEJMe =
> Editorial; NEJMms / NEJMcibr = misc.
>
> For each row, fetch the article landing page if title alone is ambiguous
> (use grab-doi.sh in --force? NO — read the title only; do NOT trigger
> downloads). If unclear, leave priority alone.
>
> Apply via SQL UPDATE. Return a markdown table summarising:
> | DOI | title | article_type | new_priority | new_status | reason |
>
> Limit your sweep to rows enqueued by the last 6 hours; do not re-sort
> the entire queue.

The drain task picks up the highest-priority pending row first, so the
filter alone is enough; no separate trigger needed.

## Anti-patterns

- ❌ Setting up a cron for /nejm-issue. By design, Copper triggers manually
  when a new issue is worth attention; Thursday auto-cron causes
  weekend-burst when Copper isn't reading.
- ❌ Letting the agent download articles during filter. Filter step is
  metadata-only; downloads are q30m drain job.
- ❌ Bulk re-prioritising the entire queue. Agent should only touch rows
  enqueued in this session window.
