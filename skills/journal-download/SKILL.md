---
name: journal-download
description: "DEPRECATED — merged into /crawler skill (ref/skills/crawler/SKILL.md). All triggers now route to /crawler. MANDATORY TRIGGERS: /journal-download, download journal, 下載期刊, download OA, download open access, get this week's papers."
---

> **⚠️ DEPRECATED: This skill is merged into `/crawler` (`ref/skills/crawler/SKILL.md`).** Use `/crawler` for all browser automation including journal downloads. This file kept for reference only.

# Journal PDF Download Skill

Download journal article PDFs using Safari (logged-in session) + AppleScript. Bypasses Cloudflare. Zero token cost for operations.

## Execution Flow

```
Step 0: AppleScript open journal URL
  ↓
Step 0.1: Check page state (JS: document.title + document.body.innerText.substring(0,200))
  ↓
  ├── Normal page (title contains journal name) → proceed to Step 2 (extract articles)
  ├── Cloudflare challenge ("Just a moment", "Verify you are human") → Step 0.2
  └── Login page / session expired → Step 0.3
  
Step 0.2: Cloudflare bypass via Computer Use (one-time, high token)
  → CC takes screenshot of Safari window
  → CC identifies Cloudflare challenge type (checkbox, turnstile, waiting)
  → If checkbox: CC clicks the checkbox via Computer Use
  → If waiting ("Just a moment..."): wait 10s, re-check (often auto-resolves)
  → After bypass: re-run Step 0.1 to confirm normal page
  → Then ALL subsequent work = AppleScript (zero token)

Step 0.3: Login via Computer Use (one-time, high token)
  → CC takes screenshot → identifies login form
  → CC fills credentials (from Keychain: `security find-internet-password -s {domain} -w`)
  → CC submits form, waits for redirect
  → After login: re-run Step 0.1 to confirm
  → Then ALL subsequent work = AppleScript (zero token)
```

### Step 0: Open Journal URL + Auto-Detect Page State

```bash
# Open URL
osascript -e '
tell application "Safari"
    activate
    open location "{toc_url}"
    delay 10
end tell'

# Check page state (zero token)
PAGE_STATE=$(osascript -e '
tell application "Safari"
    set t to do JavaScript "
        JSON.stringify({
            title: document.title,
            text: document.body.innerText.substring(0, 500),
            url: window.location.href
        })
    " in current tab of front window
    return t
end tell')

echo "$PAGE_STATE"
# Parse: if title contains "Just a moment" or "Attention Required" → Cloudflare
# Parse: if text contains "Sign in" or "Log in" → login needed
# Parse: if title contains journal name → normal, proceed
```

### Step 0.2: Cloudflare Bypass (Computer Use)

Only triggered when Step 0 detects Cloudflare. CC uses multimodal screenshot reading:

```
1. Take screenshot: osascript -e 'tell application "Safari" to activate' && screencapture -x /tmp/safari_cf.png
2. CC reads screenshot (multimodal) → identifies challenge type
3. If checkbox visible:
   - Get checkbox position from screenshot
   - osascript: click at coordinates via System Events
   - Wait 5s, re-screenshot to verify
4. If "Just a moment..." waiting page:
   - sleep 10, then re-check PAGE_STATE
   - Usually auto-resolves (Cloudflare JS challenge)
5. If Turnstile CAPTCHA:
   - CC reads and solves visually via Computer Use
   - This is the expensive path — minimize usage
6. After any bypass: re-run PAGE_STATE check
   - If still Cloudflare → retry once, then FAIL (report to Copper)
   - If normal page → proceed to Step 2
```

**Token budget:** Cloudflare bypass costs ~2-5K tokens (screenshots). Once passed, session cookies persist — all subsequent pages on same domain = AppleScript only (zero token). Worth the one-time cost.

### Step 0.3: Login (Computer Use)

```
1. Get credentials: security find-internet-password -s "{domain}" -g 2>&1
   (or: security find-generic-password -s "{service}" -w)
2. Take screenshot → identify email/username field
3. Click field → type username
4. Tab → type password
5. Click "Sign in" / press Enter
6. Wait 5s → re-check PAGE_STATE
7. If MFA required → FAIL (report to Copper, needs manual intervention)
```

## Journal Registry

| journal | access | TOC URL pattern | OA marker | PDF URL pattern |
|---|---|---|---|---|
| **NEJM** | subscription | `nejm.org/toc/nejm/current` | all (paid) | `/doi/pdf/{DOI}` |
| **Nature** | OA only | `nature.com/nature/volumes/{vol}/issues/{issue}` | `[data-test=open-access]` or OA badge on article element | `articles/{id}.pdf` |
| **Science** | Free Access | `science.org/toc/science/{vol}/{issue}` | green lock icon, tooltip "FREE ACCESS", `[title="FREE ACCESS"]` | `/doi/pdf/{DOI}` |
| **JASN** | subscription | `journals.lww.com/jasn/pages/currenttoc.aspx` | — | via LWW viewer |
| **CJASN** | subscription | `journals.lww.com/cjasn/pages/currenttoc.aspx` | — | via LWW viewer |
| **KI** | OA some | `kidney-international.org/current` | OA badge | `/action/showPdf?pii={id}` |
| **Lancet** | OA some | `thelancet.com/journals/lancet/issue/current` | OA badge | article URL + `/fulltext` → PDF link |
| **JAMA** | OA some | `jamanetwork.com/journals/jama/currentissue` | OA icon | `/doi/pdf/{DOI}` |
| **BMJ** | OA some | `bmj.com/content/current` | OA badge | article URL + `.full.pdf` |

## Download Protocol

### Step 1: Open TOC in Safari (uses Step 0 flow above)

Run Step 0 → Step 0.1 (auto-detect page state). If Cloudflare or login → handle automatically. Once on normal page → proceed:

### Step 2: Extract article list via JavaScript

```applescript
tell application "Safari"
    set articles to do JavaScript "
        var results = [];
        document.querySelectorAll('article, [data-test=article]').forEach(el => {
            var isOA = /* journal-specific OA detection */;
            var titleEl = el.querySelector('h3 a, h2 a, .c-card__title a');
            var title = titleEl ? titleEl.textContent.trim() : '';
            var href = titleEl ? titleEl.href : '';
            var type = el.querySelector('.c-meta__type')?.textContent.trim() || '';
            if (title && isOA) results.push(type + '\\t' + title + '\\t' + href);
        });
        results.join('\\n');
    " in current tab of front window
    return articles
end tell
```

### Step 3: Filter by Copper's preferences

| category | action |
|---|---|
| Biomedical Review / Perspective | **ALWAYS download** |
| Medicine (nephrology, cardio, infection, endocrine, neuro, pharmacology) | download |
| AI + medicine / biology | download |
| TLC potential (counterintuitive, story-worthy, general audience appeal) | download |
| Nutrition, exercise physiology, aging | download |
| Pure physics, chemistry, materials, climate, plant, astronomy | **skip** |

### Step 4: Download PDF via Safari Cmd+S

```bash
osascript -e '
tell application "Safari"
    activate
    open location "{pdf_url}"
    delay 6
end tell
tell application "System Events"
    tell process "Safari"
        keystroke "s" using {command down}
        delay 2
        keystroke "a" using {command down}
        delay 0.2
        keystroke "{filename}.pdf"
        delay 0.3
        keystroke "g" using {command down, shift down}
        delay 1
        keystroke "{output_dir}"
        keystroke return
        delay 1
        keystroke return
        delay 3
    end tell
end tell'
```

### Download method priority

**OA / Free Access articles → curl first (no auth needed, no UI interference):**

```bash
curl -L -o "{output_path}" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)" \
  -H "Referer: {journal_toc_url}" \
  "{pdf_url}"
```

**Subscription articles → Safari Cmd+S (needs auth session):**

⚠️ WARNING: System Events keystroke goes to FRONTMOST window. If user switches away from Safari during download, keystrokes leak to other apps. ALWAYS `activate` Safari before each keystroke sequence. Warn user not to switch windows during batch download.

curl for OA = preferred. Safari Cmd+S = subscription only.

### Step 5: Verify downloads

```bash
# Check file size — real PDF > 50KB, HTML redirect < 20KB
file "{output_path}"  # must say "PDF document"
stat -f%z "{output_path}"  # must be > 50000
```

### Step 6: Close Safari tabs + write index

```applescript
tell application "Safari" to close every tab of every window
```

Write `_index.md`:
```markdown
| date | journal | type | title | filename | size |
```

## Output Structure

```
proj/journal/
├── nejm_{YYYY-MM-DD}/          ← weekly NEJM full issue
│   ├── NEJMoa2511674.pdf
│   └── ...
├── nature_2026_oa/             ← yearly OA backfill
│   ├── _index.md
│   └── {slug}.pdf
├── science_2026_oa/            ← yearly OA backfill
│   └── ...
└── {journal}_{vol}_{issue}/    ← per-issue if needed
```

## Cron Integration

| job | schedule | scope |
|---|---|---|
| NEJM weekly | Thu 7AM | full issue (subscription) |
| Nature weekly OA | Fri 7AM (planned) | OA only, filtered |
| Science weekly OA | Fri 8AM (planned) | Free Access, filtered |

## Usage

```
/journal-download nejm              → current issue, all articles
/journal-download nature            → current issue, OA + preference filter
/journal-download science           → current issue, Free Access + filter
/journal-download nature --backfill 2026  → all 2026 issues
/journal-download nejm --date 2026-04-02  → specific issue
```

## Anti-patterns

- ❌ curl for subscription content → gets HTML paywall
- ❌ curl for Cloudflare-protected sites → 403
- ❌ Download without checking file type (PDF vs HTML redirect)
- ❌ Leave Safari tabs open after batch download
- ❌ >50 PDFs without sleep intervals (rate limit risk)
- ❌ Computer Use for every page → only for Cloudflare/login (one-time)
- ❌ Skip PAGE_STATE check → may download Cloudflare challenge HTML as "PDF"
- ❌ Hardcode credentials in scripts → use macOS Keychain (`security` command)

## Reference

Full browser automation protocol: `/crawler` skill (`ref/skills/crawler/SKILL.md`)
