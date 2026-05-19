---
type: data
name: method/methodology
description: EBM evidence appraisal methodology — pulled from Straus 6e (2024) + Guyatt Users' Guides 3e (2015) + Hernán Causal Inference: What If. Reference for any agent doing literature critique, debunk articles, or wiki synthesis.
---

# EBM Appraisal Framework

Source authority: Straus SE, Glasziou P, Richardson WS, Haynes RB. **Evidence-Based Medicine: How to Practice and Teach EBM**, 6th ed (2024); Guyatt G, Rennie D, Meade M, Cook DJ. **Users' Guides to the Medical Literature**, 3rd ed (AMA Press, 2015); Hernán MA, Robins JM. **Causal Inference: What If** (2025 online edition, free).

Use this framework whenever an agent must judge whether a citation **supports a causal claim**, **establishes a treatment effect**, or **rebuts a competing claim**. It is the spine of every credible debunk-article rebuttal and every wiki entry that grades evidence.

## 1. Two questions before anything else

For any cited study (Straus 6e Ch3 — order is operator's choice):

1. **Is it valid?** = is it likely to be true? (internal validity, freedom from bias)
2. **Is it important?** = is the magnitude clinically meaningful?

If either answer is unfavorable → study should not anchor a causal claim. **A study being "in a journal" or "high-impact" or "from Harvard" is irrelevant to either question.**

## 2. Glasziou race analogy (high-level lens)

For every study type (therapy, diagnosis, prognosis, harm):

- **Fair start?** Was the population appropriately defined and recruited? Was assignment to intervention/exposure unbiased?
- **Fair race?** Were participants treated identically apart from the intervention? Did they all complete the study?
- **Fair finish?** Were outcomes measured objectively and blindly? Was analysis appropriate?

If any prong fails, **the result is not a credible measure of the truth** — it is a measure of bias.

## 3. PICO format (granular)

For a study claiming therapy or causal effect:

| element | question |
|---|---|
| **P**opulation | Who? Inclusion / exclusion criteria explicit? Representative? |
| **I**ntervention / exposure | What treatment / exposure / risk factor? |
| **C**omparison / control | What was compared? Concurrent control? Placebo? Active comparator? |
| **O**utcome | Hard endpoint (death, MI, stroke) vs surrogate (LDL, CAC)? Blinded? Pre-specified? |

## 4. Therapy validity — RCT 7 questions (Straus 6e Ch4 Table 4.1)

1. **Was assignment randomized?** (RCT > anything else for causal claims)
2. **Was randomization concealed?** (allocation concealment prevents selection bias)
3. **Were groups similar at start?** (baseline characteristics table — Table 1 of paper)
4. **Was follow-up sufficiently long and complete?** ("sufficient" is judged against the disease's natural history; "complete" means <10-20% lost to follow-up)
5. **Were all patients analyzed in the groups to which they were randomized?** (ITT — Intention-To-Treat)
6. **Was blinding maintained?** (patients, clinicians, outcome assessors — triple-blind ideal)
7. **Were groups treated equally apart from the experimental therapy?** (no differential co-interventions)

**Each "no" downgrades the evidence.** A study failing 3+ of these is not credibly causal.

## 5. Therapy importance — effect size (Straus 6e Ch4 Table 4.4)

- **Magnitude:** RR (relative risk), ARR (absolute risk reduction), NNT (number needed to treat); HR for time-to-event
- **Precision:** 95% CI width — wide CI = imprecise estimate even if statistically "significant"
- **Clinical importance ≠ statistical significance** — p<0.05 with NNT=500 means tiny clinical impact

## 6. Harm / etiology validity (Straus 6e Ch7 Table 7.1)

When the question is "does X cause harm" (rather than "does X treat disease"):

1. **Clearly defined groups, similar in all important ways apart from exposure?** (confounding)
2. **Exposures and outcomes measured the same way in both groups?** (information bias)
3. **Sufficiently long and complete follow-up for outcome to occur?**
4. **Do results fulfill causation criteria** (Hill: temporality, dose-response, biologic gradient, consistency across studies, plausibility, coherence)?

## 7. Evidence hierarchy (per study design)

For causal claims, evidence quality drops at each step:

| level | design | key issue |
|---|---|---|
| 1a | systematic review / meta-analysis of RCTs | best, if SR is methodologically sound |
| 1b | individual RCT | gold standard for therapy |
| 2a | SR of cohort studies | better than single cohort |
| 2b | individual cohort study | confounding remains |
| 3a | SR of case-control studies | |
| 3b | individual case-control | recall bias, selection bias |
| 4 | case series, ecological studies | |
| 5 | expert opinion | no empirical grounding |

**n=1 self-experiment** is below level 5 — it does not enter the hierarchy. It is **hypothesis-generating at best, marketing at worst**.

## 8. Three independent streams = causation (Braunwald 13e Ch23)

For modern lipid causality (and any well-established causal pathway):

| stream | source | for LDL |
|---|---|---|
| **Epidemiology** | observational cohorts, hundreds of thousands of patients | higher LDL → more CVD events |
| **Mendelian randomization (genetics)** | natural experiments via loss/gain-of-function variants (PCSK9, LDLR, NPC1L1, etc.) | lifelong low LDL → 70%+ CVD reduction; lifelong high LDL (FH) → high CVD |
| **RCT** | statin, ezetimibe, PCSK9i, bempedoic acid, evinacumab | LDL reduction → CVD reduction, roughly proportional |

When **all three streams converge**, the causal claim is at the strongest level modern medicine offers. A single study, regardless of its conclusion, cannot overturn three independent streams.

## 9. Causal-inference hygiene (Hernán *What If*)

Every causal claim must be checked against:

- **Counterfactual reasoning:** would the outcome have occurred had exposure been absent?
- **Confounding:** is there a common cause of exposure and outcome that wasn't adjusted for?
- **Selection bias:** were the analyzed individuals selected in a way that depends on both exposure and outcome?
- **Measurement bias:** were exposure or outcome measured differently across groups?
- **Time-zero:** is the start of follow-up properly aligned with the start of "exposure"? (Eligibility, assignment, and follow-up must start at the same point)
- **Competing risks:** for time-to-event outcomes, is there a competing event that prevents the index event?
- **Collider:** is there a variable being conditioned on (intentionally or by selection) that is itself a common effect of exposure and outcome? Collider stratification creates spurious associations.

## 10. Specific failure modes to recognize

### n=1 self-experiment

- Subject = author = total potential bias
- No control group
- Single time series, observer expectancy effects guaranteed
- **Cannot establish causation.** Used as marketing-by-publication only.

### Cohort selected for "success" (survivor bias)

- "100 LMHR people who kept keto for 5+ years" excludes anyone who quit because of side effects, LDL anxiety, or events
- Recruitment via self-identifying communities (online keto forums) amplifies self-selection
- Generalizability to "people considering keto" is near zero

### Surrogate endpoint substitution

- Lipid (LDL, ApoB) change is a surrogate
- Plaque imaging (CAC, CCTA total plaque) is a surrogate
- Hard endpoints (MI, stroke, CV death, all-cause death) are what matter
- A 4.7-year study with surrogate endpoints **cannot rule out lifetime hard-endpoint harm**

### Single time-window misread

- "ApoB change at 1 year did not predict plaque change at 1 year" ≠ "ApoB doesn't matter for plaque"
- Baseline ApoB in the population may be uniformly elevated → no contrast → null finding by design
- The 60-year cumulative LDL exposure (Braunwald 13e Ch23) cannot be captured in 1-year contrast

### Game changer rhetoric

- Single paper, especially observational, cannot overturn three converging streams of evidence
- "Game changer" language is a tell — credible new evidence rarely needs that label

### Selective skepticism

- Skepticism applied only to the orthodox view, never to the alternative view
- A new claim should face the same (or higher) evidence bar as the orthodox view it seeks to replace
- "科學的本質是懷疑" — yes, but skepticism must be **uniform**, not weaponized against one side

### Lay-summary distortion

- The original paper says "plaque predicts plaque, ApoB-change doesn't predict plaque-change in 1 year"
- This becomes in lay summary: "ApoB doesn't matter"
- The conditional ("change in 1 year") drops out; the qualifier ("in this self-selected cohort") drops out

## 11. Applying the framework to a debunk-article rebuttal

For each claim in an argument being rebutted:

1. **Quote the full paragraph** containing the claim — never cherry-pick a sentence
2. **Identify the type of claim**: causal, observational, prognostic, mechanistic
3. **Identify the cited evidence** (paper, study type, sample size, follow-up, endpoint)
4. **Apply the relevant framework** (RCT for causal, Harm for etiology, etc.)
5. **State which validity criteria the cited evidence fails**
6. **State what evidence WOULD support the claim** — be specific about the standard not met
7. **Present the convergent counter-evidence** (three streams when available)
8. **Distinguish what the original paper actually shows** from what it is being made to say in the lay version

This is the methodology. Apply it uniformly across the topic — including the counter-claims, not just the orthodox ones.

## 12. What this framework is NOT

- It is not a way to claim "RCTs always win" — observational data is necessary for harms with long latency, rare exposures, or unethical-to-randomize questions
- It is not a way to dismiss novel evidence — novel evidence is welcome but must meet the same evidence bar
- It is not a way to win arguments — it is a way to clarify what is and isn't shown by the evidence

If applied uniformly, the framework usually settles disputes by showing both sides exactly where their evidence is and isn't strong.
