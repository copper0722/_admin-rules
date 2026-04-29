---
type: data
name: crawler
description: "Browser automation + journal download. Safari AppleScript for web scraping, PDF download, Cloudflare bypass. Maintains website 攻略 wiki. MANDATORY TRIGGERS: /crawler, scrape, crawl, 爬蟲, download from website, extract web data, browser automation, /journal-download, download journal, 下載期刊, download OA."
argument-hint: "[URL | 'describe what to scrape']"
---

# /crawler — Browser Automation Protocol

CC agents drive browsers to interact with websites. Zero LLM token for data access. Two engine paths now coexist (agent-browser is preferred for paywall-heavy + cron use; Safari AppleScript remains for ad-hoc keystroke-driven flows).

## Engine matrix

| method | cost | Cloudflare | auth/subscription | TCC | cron-safe | use when |
|---|---|---|---|---|---|---|
| **curl / wget** | 0 token | ❌ blocked | ❌ no | n/a | ✅ | OA content, APIs, no protection |
| **agent-browser CDP** (real Chrome Beta + persistent profile) | 0 token | ✅ via cf_clearance cookie | ✅ via session cookies | n/a (CDP, no AppleScript) | ✅ | **default for paywall journals + cron**: NEJM, JAMA, JASN, CJASN, KI |
| **Safari + AppleScript** | 0 token | ✅ if pre-passed | ✅ logged in | needs Automation TCC | ⚠️ TCC-fragile | legacy / ad-hoc; Cmd+S keystroke flows |
| **WebFetch** | LLM token | ❌ blocked | ❌ no | n/a | ✅ | quick fetch, no Cloudflare |
| **Computer Use** | high token | ✅ | ✅ | n/a | ❌ | CAPTCHA, login, last resort |

## Why agent-browser became the default for paywall journals (2026-04-29)

Findings while building NEJM auto-download (`medwiki-raw/scripts/NEJM/`):
- Chrome for Testing trips Cloudflare Turnstile loops AND Google OAuth blocks ("瀏覽器可能有安全疑慮"). **Chrome Beta** (real Google channel) does not.
- Chrome 119+ disables `--remote-debugging-port` on the **default user-data-dir** for security; you MUST point `--user-data-dir` at an isolated path (e.g. `~/.chrome-beta-cdp/`).
- agent-browser `--cdp 9222` attaches to that real Chrome Beta → real fingerprint, real cookies → CF + paywall pass once you log in once.
- `agent-browser eval --stdin` returns the JS expression's value (object → JSON object; string → JSON-encoded string). Use a plain expression, not `() => …` (the function itself becomes the return value, serialized as `{}`).
- macOS AppleScript Automation TCC granular permission (Automation → Google Chrome) is brittle across Mac restarts; CDP path bypasses TCC entirely.

**Two pathways:**

```
Pathway A — No Login Required (OA, public, government)
  URL → curl → success? → done
             → 403/Cloudflare? → Safari AppleScript open
               → Cloudflare detected? → Computer Use (screenshot, click checkbox) → then AppleScript
               → Normal page → AppleScript extract/download

Pathway B — Login Required (subscription, paywall)
  URL → Safari AppleScript open
    → Cloudflare? → Computer Use bypass → re-check
    → Login page? → Computer Use login:
        ├── Google Account button visible? → click "Sign in with Google" → Google OAuth flow
        └── No Google? → direct credentials:
              security find-internet-password -s "{domain}" -w → fill email + PW
    → Normal page → AppleScript extract/download
```

**Password policy:** All passwords unique per service. Safe to handle in session. Stored in macOS Keychain. No leak risk.

## Prerequisites (one-time setup)

1. Safari Settings → Developer → Allow JavaScript from Apple Events ✓
2. Safari Settings → Websites → Downloads → Allow ✓
3. System Settings → Privacy → Accessibility → Terminal.app / iTerm2 allowed
4. User logged into subscription sites (NEJM, LWW, etc.) in Safari

## Pattern 1: Read Page Content (zero token)

Extract text or structured data from any URL.

```bash
# Open URL and extract full page text
PAGE_TEXT=$(osascript -e '
tell application "Safari"
    open location "https://example.com/page"
    delay 8
    set pageText to do JavaScript "document.body.innerText" in current tab of front window
    return pageText
end tell')
echo "$PAGE_TEXT" > /tmp/page_content.txt
```

**Tips:**
- `delay 8` = wait for JS-rendered content (adjust per site speed)
- `document.body.innerText` = clean text, no HTML tags
- `document.body.innerHTML` = full HTML if you need structure
- For specific elements: `document.querySelector('.article-body').innerText`

## Pattern 2: Extract Structured Data (links, tables, metadata)

```bash
# Extract all article links + titles from a page
ARTICLES=$(osascript -e '
tell application "Safari"
    set data to do JavaScript "
        Array.from(document.querySelectorAll(\"a[href*='/doi/']\"))
            .map(a => a.href + \" | \" + a.textContent.trim())
            .filter((v,i,arr) => arr.indexOf(v) === i)
            .join(\"\\n\")
    " in current tab of front window
    return data
end tell')
```

```bash
# Extract table data as TSV
TABLE=$(osascript -e '
tell application "Safari"
    set data to do JavaScript "
        var rows = document.querySelectorAll(\"table tr\");
        Array.from(rows).map(r =>
            Array.from(r.querySelectorAll(\"td,th\"))
                .map(c => c.innerText.trim().replace(/\\t/g, \" \"))
                .join(\"\\t\")
        ).join(\"\\n\");
    " in current tab of front window
    return data
end tell')
```

## Pattern 3: Download PDF via Cmd+S (subscription content)

For sites behind paywall — Safari renders PDF inline, Cmd+S saves actual file.

```bash
DOI="NEJMoa2100842"
PDF_URL="https://www.nejm.org/doi/pdf/10.1056/$DOI"
OUTDIR="$HOME/Library/CloudStorage/Dropbox/_inbox"
FNAME="${DOI}.pdf"

osascript -e "
tell application \"Safari\"
    activate
    open location \"$PDF_URL\"
    delay 6
end tell
tell application \"System Events\"
    tell process \"Safari\"
        keystroke \"s\" using {command down}
        delay 2
        -- Select all text in filename field and type new name
        keystroke \"a\" using {command down}
        delay 0.2
        keystroke \"$FNAME\"
        delay 0.3
        -- Navigate to output folder
        keystroke \"g\" using {command down, shift down}
        delay 1
        keystroke \"$OUTDIR\"
        keystroke return
        delay 1
        -- Confirm save
        keystroke return
        delay 3
    end tell
end tell"

# Verify download
if [ -f "$OUTDIR/$FNAME" ]; then
    SIZE=$(stat -f%z "$OUTDIR/$FNAME")
    file "$OUTDIR/$FNAME" | grep -q "PDF" && echo "OK: $FNAME ($SIZE bytes)" || echo "FAIL: not a PDF"
else
    echo "FAIL: file not saved"
fi
```

**⚠️ CRITICAL WARNING:** `System Events` keystroke goes to FRONTMOST window. If user switches away from Safari during download, keystrokes leak to other apps. ALWAYS `activate` Safari before each keystroke sequence.

## Pattern 4: Paginated Scraping

```bash
PAGE=1
ALL_DATA=""
while true; do
    osascript -e "
    tell application \"Safari\"
        open location \"https://example.com/list?page=$PAGE\"
        delay 8
    end tell"

    DATA=$(osascript -e '
    tell application "Safari"
        set data to do JavaScript "
            var items = document.querySelectorAll(\".item\");
            if (items.length === 0) return \"END\";
            Array.from(items).map(i => i.innerText.trim()).join(\"\\n\");
        " in current tab of front window
        return data
    end tell')

    [ "$DATA" = "END" ] && break
    ALL_DATA="$ALL_DATA
$DATA"
    PAGE=$((PAGE + 1))
    sleep 2  # rate limit courtesy
done
echo "$ALL_DATA" > /tmp/all_pages.txt
```

## Pattern 5: Download OA PDF via curl (no browser needed)

```bash
# OA / Free Access — curl first, no Safari needed
curl -L -o "$OUTDIR/$FNAME" \
    -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
    -H "Referer: https://example.com/" \
    "$PDF_URL"

# Verify: real PDF > 50KB, HTML redirect < 20KB
SIZE=$(stat -f%z "$OUTDIR/$FNAME")
if [ "$SIZE" -lt 50000 ]; then
    echo "WARN: file too small ($SIZE bytes), likely HTML redirect — switch to Safari"
    rm "$OUTDIR/$FNAME"
fi
```

## Pattern 6: Page Change Monitor (hash-based)

```bash
# Fetch page, hash content, compare to stored hash
NEW_HASH=$(osascript -e '
tell application "Safari"
    open location "https://www.nhi.gov.tw/ch/some-page"
    delay 10
    set t to do JavaScript "document.body.innerText" in current tab of front window
    return t
end tell' | shasum -a 256 | cut -d' ' -f1)

OLD_HASH=$(cat /tmp/page_hash.txt 2>/dev/null)
if [ "$NEW_HASH" != "$OLD_HASH" ]; then
    echo "PAGE CHANGED"
    echo "$NEW_HASH" > /tmp/page_hash.txt
    osascript -e 'display notification "Page updated!" with title "Monitor"'
fi
```

## Pattern 7: Login (Computer Use, one-time → then AppleScript)

When site requires login. Two sub-paths:

### Path A: Google Account (preferred if available)

Many journal sites support "Sign in with Google". Faster, no password lookup needed.

```
1. Take screenshot → look for "Sign in with Google" / "Continue with Google" button
2. If found:
   - Computer Use: click Google button
   - Google OAuth popup appears
   - If already signed into Google in Safari → auto-selects account → done
   - If Google asks to choose account → screenshot → click Copper's Google account
   - Wait for redirect back to journal site
3. Re-check PAGE_STATE → should be logged in
```

### Path B: Direct Credentials

```
1. Get password from Keychain:
   security find-internet-password -s "{domain}" -w 2>/dev/null
   (or: security find-generic-password -s "{service}" -w)
2. Get username/email: usually copper's Google email — check Keychain or use known email
3. Take screenshot → identify email/username field
4. Computer Use: click field → type email
5. Tab or click → type password
6. Click "Sign in" / press Enter
7. Wait 5s → re-check PAGE_STATE
8. If MFA required → FAIL (report to Copper)
```

**Password policy:** All PW unique per service, safe to handle in session, stored in Keychain. No leak risk.

### After login (both paths):

```
Phase 2 — AppleScript (all subsequent ops, zero token):
  Session cookies persist until expiry (hours to days)
  All scraping, downloading, monitoring = AppleScript only
  No more Computer Use needed for this domain until session expires
```

Computer Use = one-time login cost (~3-5K tokens). All subsequent work = zero token.

## Cleanup

Always close tabs after batch operations:

```bash
osascript -e 'tell application "Safari" to close every tab of every window'
```

## Rate Limiting

| site type | interval | batch size |
|---|---|---|
| Government (NHI, TFDA) | 3s between requests | no limit |
| Publisher (NEJM, Nature) | 3s between requests | 30 PDFs per batch |
| General | 2s between requests | adapt to site |

After each batch of 30 downloads: close all tabs, `sleep 5`, restart Safari if memory high.

## Verification Checklist

After any download:
1. File exists at expected path
2. File size > 50KB (real PDF, not HTML error page)
3. `file {path}` reports correct type (PDF, HTML, etc.)
4. For PDFs: not a "Access Denied" or "Login Required" page

## Anti-patterns

- ❌ `curl` for Cloudflare-protected sites → 403
- ❌ `curl` for subscription PDFs → gets HTML paywall
- ❌ Keystroke without `activate` Safari first → keystrokes go to wrong app
- ❌ >50 tabs open → Safari memory bloat → crash
- ❌ Download while user is using computer → keystroke collision
- ❌ Tesseract/ocrmypdf for OCR → use DT4 ABBYY instead (§2.13)
- ❌ WebFetch for Cloudflare sites → 403

## Website 攻略 Wiki

Each site has unique OA patterns, selectors, login methods, Cloudflare behavior. Agent updates this section after successfully crawling a new site. **This is a living document — grow it bottom-up.**

### Medical Journals

| site | pathway | login | Cloudflare | OA detection | PDF URL pattern | article selector | notes |
|---|---|---|---|---|---|---|---|
| **nejm.org** | B (subscription) | `copper.wang@gmail.com` / Keychain `www.nejm.org` | yes (checkbox) | all paid (subscription = full access) | `/doi/pdf/{DOI}` | `a[href*="/doi/pdf/"]` | weekly Thu issue. `nejm-weekly-download.sh`. Also covers **NEJM Evidence** (same account) |
| **nature.com** | A (OA curl) | Google Account (if needed) | no | `[data-test=open-access]` or OA badge | `articles/{id}.pdf` | `.c-card__title a` | curl works for OA. Subscription articles = Safari |
| **science.org** | A (OA curl) | Google Account (if needed) | sometimes | green lock icon, `[title="FREE ACCESS"]` | `/doi/pdf/{DOI}` | article list links | Free Access ≠ OA, but downloadable |
| **kidney-international.org** | A/B mixed | Google Account (if needed) | no | OA badge on article | `/action/showPdf?pii={id}` | — | Elsevier platform |
| **journals.lww.com** (JASN, CJASN) | B (subscription) | ASN membership: `ivorie3@gmail.com` / Keychain `www.asn-online.org`. Login via ASN portal, NOT journal site directly | no | — | LWW PDF viewer → extract real URL | — | LWW viewer wraps PDF, need JS to get actual URL |
| **jamanetwork.com** | A/B mixed | Google Account (if needed) | no | OA icon | `/doi/pdf/{DOI}` | — | |
| **thelancet.com** | A/B mixed | Google Account (if needed) | no | OA badge | article URL → `/fulltext` → PDF link | — | Elsevier platform |
| **bmj.com** | A (mostly OA) | Google Account (if needed) | no | OA badge | article URL + `.full.pdf` | — | |
| **pubmed.ncbi.nlm.nih.gov** | A (no login) | none | no | N/A (metadata only) | N/A (links to publisher) | `.docsum-content a` | Use for article discovery, not PDF download |

### Credential Lookup

```bash
# NEJM / NEJM Evidence
security find-internet-password -s "www.nejm.org" -w    # → password
security find-internet-password -s "www.nejm.org" -a ""  # → shows account (copper.wang@gmail.com)

# JASN / CJASN (via ASN membership)
security find-internet-password -s "www.asn-online.org" -w
security find-internet-password -s "www.asn-online.org" -a ""  # → ivorie3@gmail.com

# Other journals: almost all bound to Google Account → use Google OAuth flow (Pattern 7 Path A)
```

### Government / Regulatory

| site | pathway | login | Cloudflare | content type | selector | notes |
|---|---|---|---|---|---|---|
| **nhi.gov.tw** | A (no login) | none | yes (JS challenge, auto-resolves 10s) | HTML pages, PDF attachments | page-specific | `nhi-page-monitor.py`, `nhi-*-scraper.py` |
| **fda.gov.tw** (TFDA) | A (no login) | none | no | news, site lists | table rows | `tfda-*-scraper.py` |
| **mohw.gov.tw** | A (no login) | none | sometimes | 公告, 法規 | — | |

### Other

| site | pathway | login | Cloudflare | notes |
|---|---|---|---|---|
| **scholar.google.com** | A | none | sometimes (rate limit) | metadata only, links to publisher |
| **sci-hub** | A | none | no | curl works, DOI → PDF direct |
| **unpaywall.org/api** | A (API) | none | no | `api.unpaywall.org/v2/{DOI}?email=...` → OA PDF URL |

### How to Add a New Site

When agent encounters a new site:
1. Try curl first → note if 403/Cloudflare
2. Try Safari AppleScript → note page load time, selectors
3. Check login: Google Account button? direct PW? institutional?
4. Find OA detection pattern (CSS class, badge, icon)
5. Find PDF URL pattern (DOI-based? pii-based? viewer-wrapped?)
6. Find article list selector (CSS selector for title + link)
7. **Add a row to the table above** — this is the wiki growing

## Existing Scripts

| script | site | engine |
|---|---|---|
| `medwiki-raw/scripts/NEJM/grab-current.sh` | nejm.org | **agent-browser CDP** — grab whatever NEJM article is in the current Chrome Beta tab → `_sidecar/{slug}/` + `_unclassified/{slug}.md`. See `pipelines/NEJM/AGENTS.md`. |
| `medwiki-raw/scripts/NEJM/grab-doi.sh DOI` | nejm.org | **agent-browser CDP** — navigate + grab |
| `medwiki-raw/scripts/NEJM/enqueue-toc.sh` | nejm.org | **agent-browser CDP** — scrape TOC → PG `public.nejm_queue` (manual; triggered via `/nejm-issue` skill) |
| `medwiki-raw/scripts/NEJM/drain-queue.sh` | nejm.org | **agent-browser CDP** — q5min: claim 1, download, mark `downloaded`. Triggered by `quality_audit_tasks.nejm-drain` task-train job (cadence_minutes=5, target_host=hm4). |
| `nejm-weekly-download.sh` | nejm.org | Safari + Cmd+S (legacy; superseded by `nejm/`) |
| `nhi-page-monitor.py` | nhi.gov.tw | Safari Pattern 1 + 6 |
| `nhi-announcement-scraper.py` | nhi.gov.tw | Safari Pattern 1 + 2 |
| `nhi-regulation-scraper.py` | nhi.gov.tw | Safari Pattern 1 + 2 |
| `tfda-news-scraper.py` | fda.gov.tw | Safari Pattern 1 + 2 |
| `tfda-sitelist-scraper.py` | fda.gov.tw | Safari Pattern 1 + 2 |

## Journal Download (merged from /journal-download)

### Selection Filter (Copper's preferences)

| category | action |
|---|---|
| Biomedical Review / Perspective | **ALWAYS download** |
| Medicine (nephrology, cardio, infection, endocrine, neuro, pharmacology) | download |
| AI + medicine / biology | download |
| TLC potential (counterintuitive, story-worthy, general audience appeal) | download |
| Nutrition, exercise physiology, aging | download |
| Pure physics, chemistry, materials, climate, plant, astronomy | **skip** |

### Output Structure

```
_inbox/                             ← downloads land here first
  nejm_{YYYY-MM-DD}/               ← weekly NEJM full issue
  nature_2026_oa/                  ← yearly OA backfill
  {journal}_{date}/                ← per-issue
```

### Cron Integration

| job | schedule | scope | script |
|---|---|---|---|
| `nejm-toc-thursday` | Thu 08:30 TST | scrape current weekly issue → `public.nejm_queue` | `nejm/enqueue-toc.sh --current-issue` |
| `nejm-drain-morning` | 09:30 daily TST | pop 5, sequential download, random 60-180s gap | `nejm/drain-queue.sh --batch 5` |
| `nejm-drain-noon` | 14:30 daily TST | pop 5 (batch 2/3) | `nejm/drain-queue.sh --batch 5` |
| `nejm-drain-evening` | 20:30 daily TST | pop 5 (batch 3/3); 15/day cap | `nejm/drain-queue.sh --batch 5` |
| Nature weekly OA | planned | OA only, filtered | — |
| Science weekly OA | planned | Free Access, filtered | — |

NEJM auto-download is registered in `public.schedule_registry` (4 rows; `job_name` LIKE `nejm-%`) and loaded as launchd user agents on hm4. Each batch does a pre-flight auth probe (navigate to `nejm.org/`, run `auth-check.js`, abort & release claims if CF challenge or sign-in link visible). Day-cap enforced via `nejm_queue.downloaded_at` count. Block events logged to `public.nejm_log`.

## Usage

```
/crawler https://example.com/data            → extract page content
/crawler https://example.com/list --pages    → paginated scraping
/crawler https://example.com/file.pdf        → download file
/crawler monitor https://example.com/page    → set up change detection
/crawler nejm                                → current NEJM issue (= old /journal-download)
/crawler nature --backfill 2026              → Nature 2026 OA backfill
```

Input: $ARGUMENTS
