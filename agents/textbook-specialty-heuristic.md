---
type: agent-routing-heuristic
purpose: per-textbook specialty lookup so corpus-search agents (note-writer, wikify, exam-solution content-fill) consult the right source for each question type
audience: agents
maintained_by: Copper directive 2026-05-07
---

# Textbook Specialty Routing Heuristic

Each authoritative source in `wiki_raw` has a SPECIFIC niche where it adds value beyond what other sources cover. Agent corpus-search MUST consult the table below first when picking which `citationKey` to read for a given question type. Avoid reading the wrong source for a question (e.g. quoting Washington Manual for pathophysiology, or quoting Williams for bedside drug doses).

## How to use

1. Identify the question's primary CATEGORY (mechanism / drug-dosing / guideline-recommendation / education-method / acute-management / Taiwan-local).
2. Look up the matching ROW in the routing table.
3. Read FIRST source listed; fall through subsequent sources only when the first does not cover the specific claim.
4. Chinese-language books (TADE) are CME 第二線 — only cite when no foreign Tier 1/2/3 source covers the claim, OR when content is uniquely Taiwan-local (per `personal-website/cme/AGENTS.md` § Reference tier hierarchy).

## Routing table (DM endocrinology corpus)

| Question category | Primary source | Why this niche | NOT recommended for |
|---|---|---|---|
| **Mechanism / pathophysiology** (insulin signaling, β-cell physiology, IRS-1/PI3K/AKT, ectopic fat, lipotoxicity) | Williams Textbook of Endocrinology 15e (Ch33 T2DM patho, Ch35 T1DM, Ch40 obesity neuroendocrine) | Authoritative mechanism text; cellular + molecular depth; integrates clinical correlate | Bedside dosing; Taiwan local context |
| **Biochemistry of insulin signaling** (kinase cascade, FOXO/SREBP/GLUT4 branches, second-messenger cross-talk) | Harper's Illustrated Biochemistry 33e (Ch42 hormone action) + Lehninger 8e (Ch12 PIP2/IRS1, Ch23 adipocyte AMPK) | Deeper biochemistry than clinical textbooks; signal-cascade level | Clinical management; drug recommendations |
| **Guideline recommendation** (target A1C, BP, LDL, screening interval, drug class first-line) | ADA Standards of Care in Diabetes — current edition (e.g. 2026 §1–§17) | Annual consensus; recommendation-grading (A/B/C/E); covers all DM care domains | Detailed pathophysiology; bedside protocol mechanics |
| **Bedside protocol / drug dosing** (insulin titration, K replacement during DKA, sliding scale, perioperative SGLT2i hold, transition IV→SC insulin) | Washington Manual of Medical Therapeutics 38e (Ch23 DM and Related Disorders) | Hospitalist-oriented; concrete dose tables; "what to write in the order set" | Population-level recommendations; education methodology |
| **Acute hyperglycemic crisis** (DKA / HHS dx criteria, fluid + insulin + K protocol, mortality data) | ADA 2026 §6 (Hyperglycemic Crises) + ADA 2026 §16 (Hospital Care) + Williams 15e Ch35 (T1DM/DKA patho + Tx) + Washington Manual 38e Ch23 (treatment table) | Multi-source converging — ADA = guideline frame; Williams = patho + pediatric DKA detail; Washington Manual = literal IV order | Outpatient prevention; education methodology |
| **DKD natural history + management** | ADA 2026 §11 (CKD and Risk Mgmt) + TWDKD 2024 (Taiwan-specific clinical guideline) + Williams 15e Ch33 (DM-related complications section) | ADA = staging + drug class; TWDKD = Taiwan-specific NHI / 共照網 routing; Williams = mechanism overlay | Drug-only questions (use Washington Manual); pure mechanism (use Williams + Harper) |
| **CV risk in DM / lipid / BP** (statin, ACE/ARB, finerenone, SGLT2i CV outcomes) | ADA 2026 §10 (CV Disease and Risk Management) + landmark trials (LEADER / SUSTAIN-6 / SELECT / EMPA-REG / DAPA-CKD / CREDENCE / FIDELIO) | ADA = recommendation + trial integration; trials themselves for primary data | Mechanism; education |
| **Pregnancy + GDM** (preconception, GDM dx, glycemic targets, insulin in pregnancy, metformin/glyburide debate, postpartum) | ADA 2026 §15 (Diabetes in Pregnancy) + Williams 15e Ch44 (when ingested) | ADA = current consensus including HAPO/TOBOGM/CONCEPTT/CHAP; Williams = endocrine physiology of pregnancy | Acute crisis; drug class drug-by-drug overview |
| **Obesity + weight management for DM** (semaglutide/tirzepatide, bariatric surgery, post-bariatric hypoglycemia) | ADA 2026 §8 (Obesity & Weight Mgmt) + Harrison 22e Ch413-414 (obesity) + Williams 15e Ch40 (obesity neuroendocrine) | ADA = recommendation + 2026 GLP-1/GIP-GLP-1 + bariatric; Harrison = general internal med framing; Williams = neuroendocrine mechanism | Pure surgery technique; pure dietitian-level meal planning |
| **Microvascular complications** (retinopathy / neuropathy / foot care) | ADA 2026 §12 (Retinopathy/Neuropathy/Foot Care) + IWGDF + foreign retina specialty refs as needed | ADA = recommendation + screening + IWGDF risk strat + DPN drug tier | Acute crisis; outpatient lifestyle |
| **Diabetes education methodology** (how to teach DM patient — SMBG operation, insulin injection step-by-step, behavior change technique, motivational interviewing for DM, self-management training, 衛教師 certification standards) | **TADE 2026 糖尿病衛教核心教材**（中華民國糖尿病衛教學會） | **Specific niche** (Copper 2026-05-07): 衛教方法學 + 自我管理訓練 + Taiwan-context 衛教 protocol design + 衛教師認證體系；其他英文教科書不會深入這層 | Clinical mechanism (use Williams); drug recommendation (use ADA); Taiwan-local clinical guideline (use TWDKD/DAROC) |
| **Taiwan-specific clinical guideline** (NHI 給付, 共照網 routing, 國健署 program, Taiwan epidemiology, DKD subgroup) | DAROC 2022/2024 + TWDKD 2024 | Foreign-source synthesis WITH local adaptation; not pure translation | Generic DM mechanism / management — go ADA first |
| **Patient nutrition for DM** (Mediterranean / 低碳 / DASH / plant-based + Taiwan diet patterns + portion exchange) | Krause 16e (Medical Nutrition Therapy for DM, when ingested) + ADA 2026 §5 (Lifestyle Behaviors) + TADE 2026 (份量代換 Taiwan-specific) | Krause = dietitian-grade depth; ADA = recommendation; TADE = Taiwan portion-exchange + 衛福部 衛教給付項目 | Pathophysiology; pharmacology |

## Adding a new entry

When a new textbook is ingested into `wiki_raw`:
1. Read its preface / table of contents to identify its specific value-add over already-indexed sources.
2. Add a row to the routing table with: question category → primary source → niche statement → "NOT recommended for" boundary.
3. Update note-writer SKILL.md cross-reference if the new source becomes the primary for any question category.
4. Commit to `_admin-rules/agents/textbook-specialty-heuristic.md`.

## Boundary principle

**No textbook is "the universal source" for DM**. Each source has a niche; selecting the right one materially improves citation accuracy. Generic citation choices (e.g. always citing ADA + Williams for everything) lead to misalignment when the question is actually about education methodology, biochemistry, or local Taiwan policy. Use this routing heuristic FIRST, fall through SECOND.

## Cross-refs

- `personal-website/cme/AGENTS.md` § "Reference tier hierarchy for CME content-fill" — formal Tier 1/2/3 + Chinese-book second-line rule
- `_admin-rules/skills/note-writer/SKILL.md` — primary corpus-search agent that consumes this heuristic
- `wiki_raw/AGENTS.md` — raw corpus inventory + tag protocol
- `personal-website/src/data/tag-registry.yml` — tag canonical names (avoid drift in citation tags)
