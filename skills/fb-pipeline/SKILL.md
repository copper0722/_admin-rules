---
generated: false
type: data
name: fb-pipeline
description: "FB post → quality article + TLC slide pipeline. Picks 1 unprocessed post from fb.db, writes polished article + appends Marp slide. MANDATORY TRIGGERS: /fb-pipeline, fb pipeline, process fb post, 寫文章, fb article."
---

# FB Content Pipeline

Process ONE Facebook post from fb.db → polished article + TLC slide.

## Two-Stage Architecture

**Stage 1 (`/fb-pipeline`)**: Production. Every 1 min. Pick 1 post → write article + slide. Fast, no organization overhead.
**Stage 2 (`/fb-organize`)**: Editorial. Separate agent, periodic. Review all articles → group. Review slides → organize.

---

## Stage 1: Produce (this skill)

1. **Pick 1 post** (random, no category filter):
```sql
SELECT id, datetime, title, content, topic FROM posts
WHERE pipeline_done IS NULL AND length(content) > 100
ORDER BY RANDOM() LIMIT 1
```

2. **Write article** → `proj/fb/articles/{topic}/{slug}.md`
   - zh-TW, target: 一般民眾 (general population, non-medical folks)
   - Structure: title, lead paragraph, body (2-4 sections), takeaway
   - Apply fb-style-feedback.md rules: no 破折號, add numbers, systemic closure
   - Frontmatter: title, date, topic, source_post_ids: [list], status: draft
   - Length: per vault rule (§9.1: >500L needs summary; §9.2: >2000L needs split; natural length, no forced constraint)
   - Tone: 親切易懂, like explaining to a friend. Not dumbing down — making accessible.
   - Multiple citations OK: one article can synthesize several related FB posts

4. **Append slide** → `proj/fb/slides/tlc-mega-slides.html` (single HTML file, hundreds of slides OK)
   - If file doesn't exist → create with HTML boilerplate (keyboard nav ←→, slide counter, TOC)
   - Append new `<section>` slide block per article
   - **Style = Copper's FB voice**: valuable content, concise, no bullshit, no 陳腔爛調
   - Every slide must make the reader think "wow, I didn't know that" or "this is actually useful"
   - Numbers > vague claims. Specific > generic. Surprising > obvious.
   - zh-TW, large readable font (min 28px body, 42px headers)
   - Single file grows to hundreds of slides — organized by topic sections
   - Topic separator slide when topic changes (acts as chapter divider)
   - Open in browser = instant presentation. Goal: "這麼多內容，收藏！考慮邀請演講"

5. **Tag post** in db:
```sql
-- Mark as processed
UPDATE posts SET pipeline_done = 1 WHERE id = {post_id};

-- Add granular tags (bottom-up, from reading content)
-- Tags = topics, keywords, diseases, drugs, concepts discovered in content
INSERT OR IGNORE INTO post_tags (tag) VALUES (?);
INSERT OR IGNORE INTO post_tag_map (post_id, tag_id, tagged_by)
  SELECT {post_id}, id, 'pipeline' FROM post_tags WHERE tag = ?;
```
   - Tags are granular (e.g. '血液透析', '低血壓', 'EPO', '營養', 'marathon')
   - Multiple tags per post OK
   - Agent reads content → decides tags from what it learned
   - post_tags table grows organically (bottom-up taxonomy)

6. **Citation**: every article + slide must cite source posts
   - Format: `來源：FB #{{id}} ({{date}})` — multiple OK per article
   - After graph_id backfill: upgrade to clickable FB URL
   - Article frontmatter: `source_post_ids: [{{id1}}, {{id2}}, ...]`
   - Slide: `<p class="source">` block with all cited post IDs

7. **Tag post done**: `UPDATE posts SET pipeline_done=1 WHERE id={id}`

8. **Report**: post ID, topic, article path, slide appended. Exit.

---

## Stage 2: Organize (`/fb-organize`) — separate agent, after batch

Run after Stage 1 batch (e.g. after 1 hour / 60 articles). Triggered manually or by admin.

1. **Article grouping**: scan `proj/fb/articles/` → cluster by topic → merge related articles → condense overlapping content → ensure each article is standalone + valuable
2. **Article quality**: remove fluff, strengthen weak articles, ensure citations present
3. **Slide organization**: read `proj/fb/slides/tlc-mega-slides.html` → reorder by topic → insert section dividers → remove weak/redundant slides → ensure flow
4. **Report**: articles merged, slides reordered, quality stats

## Article Style Guide

- Target audience: 一般民眾 (non-medical)
- Copper's voice: 專業但親切, 用數據說話
- No jargon without explanation
- Each article = standalone (no assumed prior knowledge)
- End with: 為什麼這很重要 (clinical relevance to everyday life)

## Slide Format (HTML)

All vault slides = HTML. Single growing file, open in browser = instant presentation.

```html
<!-- append this block per slide -->
<section class="slide">
  <h2>{Topic Title}</h2>
  <ul>
    <li>Point 1</li>
    <li>Point 2</li>
    <li>Point 3</li>
  </ul>
  <p class="source">來源：FB 粉專 {date}</p>
</section>
```

Keyboard nav: ← → arrows. Slide counter in corner.

## DB Path
`~/Vault/proj/fb/data/fb.db`
