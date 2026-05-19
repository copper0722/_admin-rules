---
type: data
name: method
description: "EBM methodology reference + reflection skill. Reference doc = `methodology.md` (EBM appraisal framework from Straus 6e + Guyatt Users' Guides + Hernán Causal Inference: What If). MANDATORY TRIGGERS: /method, 反省文獻, method reflect, 方法論反省, EBM appraisal, debunk methodology."
---

# /method — Methodology Reference + Reflection

This skill has two modes:

## Mode A — Methodology reference (use when writing debunk articles, wiki critiques, evidence grading)

**Read [`methodology.md`](./methodology.md)** for the full EBM appraisal framework. Apply uniformly:

- Two questions: Is it valid? Is it important?
- Glasziou race analogy (fair start / race / finish)
- PICO format
- Therapy validity (Straus 6e Ch4 Table 4.1, 7 RCT questions)
- Harm validity (Straus 6e Ch7 Table 7.1, 4 questions + Hill criteria)
- Evidence hierarchy (1a SR-of-RCT → 5 expert opinion; n=1 self-experiment below 5)
- Three independent streams (epi + Mendelian randomization + RCT)
- Hernán causal hygiene (counterfactual, confounding, selection, measurement, time-zero, collider, competing risks)
- Failure modes (n=1, survivor cohort, surrogate endpoint, time-window misread, "game changer" rhetoric, selective skepticism, lay distortion)
- Application: full-paragraph quote → claim type → cited evidence → framework applied → criteria failed → convergent counter-evidence

Use this reference whenever writing a rebuttal or wiki-human article that grades evidence.

## Mode B — Methodology reflection (post-session lessons capture)

Reflect on this conversation for literature/data errors corrected by Copper. Extract actionable rules. Update wiki.

## STEPS

1. **Scan** conversation history for Copper corrections on:
   - Citation/source errors (LLM synthesis cited as fact, unverified claims)
   - Data presentation errors (wrong denominator, stale data, observed vs derived)
   - Cross-country comparison errors (false equivalence, missing structural context)
   - Academic presentation errors (subjective interpretation where objectivity needed)
   - Draft-review errors: responding to a strawman or inferred claim rather than the actual draft text; failing to anchor feedback in what the counterparty actually wrote

2. **Extract** per error:
   - **Failure mode**: what was wrong (specific example from this session)
   - **Check**: how to avoid in future (actionable rule)

3. **Read** `wiki/methodology/wiki_research_methods_ebm.md` §19 — check for duplicates

4. **Append** new lessons to §19 (numbered §19.N). Skip if already covered.

5. **Update** `wiki/CLAUDE.md` Methodology → Source Verification section (condensed version of new rules)

6. **Report** to Copper: list of new lessons added (or "no new lessons found")

## RULES

- Only extract from ACTUAL corrections in THIS session. Don't invent hypothetical errors.
- For professional/draft review, first restate what the source draft actually says and identify exact phrases being changed. Do not frame feedback as preventing a claim unless the draft actually makes or strongly implies that claim.
- Each lesson must have a concrete failure mode from the conversation, not a generic principle.
- If no corrections happened → report "本次 session 無文獻評讀糾正" and exit.
- M2M English for wiki files, zh-TW for report to Copper.
