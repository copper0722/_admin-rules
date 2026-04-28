---
type: data
name: fb-pipeline
description: "FB page operations: post → quality article + TLC slide pipeline, Graph API token diagnostics, and Page messaging capability checks. MANDATORY TRIGGERS: /fb-pipeline, fb pipeline, process fb post, 寫文章, fb article, FB token, Facebook Graph API, 粉專私訊, Page inbox."
---

# FB Content Pipeline

Use this skill for Facebook Page work around Copper's TLC/王介立醫師 page: content pipeline, Graph API operations, token/permission diagnostics, comments/engagement, and Page inbox capability checks.

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

## Facebook Graph API diagnostics

Use this section when Copper asks about FB tokens, Graph API access, Page comments/engagement, Page inbox, or fan-page private messages.

1. First search the `secretary/fb` card/docs for the current canonical token path. As of 2026-04, the Page token is documented at `~/.local/share/deck/fb_page_token.json`.
2. Never print token values. It is safe to print non-secret metadata: JSON keys, `page_id`, `page_name`, `fan_count`, `expires`, and permission names.
3. Validate basic Page access before diagnosing a specific feature:
   ```bash
   python3 - <<'PY'
   import json, urllib.parse, urllib.request
   from pathlib import Path
   p = Path('~/.local/share/deck/fb_page_token.json').expanduser()
   data = json.loads(p.read_text())
   token = data['page_token']
   page = data['page_id']
   url = 'https://graph.facebook.com/v19.0/' + page + '?' + urllib.parse.urlencode({
       'fields': 'name,fan_count',
       'access_token': token,
   })
   print(urllib.request.urlopen(url, timeout=20).read().decode())
   PY
   ```
4. For Page inbox/private-message management, test `/{page_id}/conversations` with fields like `id,updated_time,snippet,unread_count,message_count,participants`. If Graph API returns `(#200) Requires permission: pages_messaging or User associated with the Page access token does not have an appropriate role on the Page`, the existing token can manage posts/engagement but cannot manage inbox. Copper needs a Page token with `pages_messaging` and appropriate Page role/app review before Hermes can triage or reply to Page private messages.
5. Medical fan-page private messages should default to triage, digest, and reply drafts. Do not auto-send individualized medical advice; if replies are enabled, keep low-risk canned routing replies or ask Copper to approve drafts.

## Meta Business domain verification / Page messaging blockers

Use this section when `pages_messaging` is blocked by Meta Developer setup, Business Manager domain verification, or a vendor-managed clinic website/domain.

Class of task: diagnosing whether Copper can satisfy Meta Business domain verification and `pages_messaging` prerequisites using existing local website repos, DNS access, or vendor CMS automation.

1. Record the Meta app + business context without secrets:
   - app name / app ID
   - Business Manager ID/name
   - Page ID/name
   - domain verification URL
   - exact Graph API error text
2. Check the current Page token metadata only, never the token value:
   - `~/.local/share/deck/fb_page_token.json`
   - keys present, `page_id`, `page_name`, `expires`, permission names
3. Check DNS before assuming CMS access is enough:
   ```bash
   DOMAIN='example.com'
   for q in NS A CNAME TXT; do dig +short $q "$DOMAIN"; done
   for q in A CNAME TXT; do dig +short $q "www.$DOMAIN"; done
   ```
   Existing third-party verification TXT records (Google, Meta, etc.) imply someone previously had DNS control; identify whether that is the user, registrar, or vendor.
4. Inspect the website repo/class of CMS before attempting changes:
   - Read the website repo's `AGENTS.md` or equivalent project card first.
   - CMS article/body publishing, static-page body editing, or image upload does NOT imply domain verification capability.
5. Evaluate Meta's three verification routes explicitly:
   - DNS TXT: preferred; requires registrar/DNS access or vendor action.
   - HTML file at domain root: only works if a file can be served exactly at `https://domain/<verification-file>.html`; uploads to vendor asset paths or image-only file managers usually do not qualify.
   - Meta tag in homepage `<head>`: only works if the CMS/vendor exposes global template/head editing; injecting meta tags into article/about body is unlikely to pass.
6. For vendor/white-label CMS sites, do not assume repo publishing can solve verification. Document the likely blocker and ask the domain controller/vendor for the DNS TXT record:
   ```text
   Please add a Meta Business domain verification TXT record.
   Host/Name: @
   Type: TXT
   Value: <Meta verification value>
   TTL: default / 1 hour
   ```
7. Persist the audit in the relevant project repo/note rather than relying on chat memory. Include: DNS observations, CMS capabilities, rejected verification paths, and exact next action.

## DB Path
`~/Vault/proj/fb/data/fb.db`
