---
type: data
name: crawler
description: "Public-safe browser automation protocol for open web, open-access, and explicitly authorized content. MANDATORY TRIGGERS: /crawler, scrape, crawl, 爬蟲, download from website, extract web data, browser automation, /journal-download, download journal, 下載期刊, download OA."
argument-hint: "[URL | 'describe what to scrape']"
---

# /crawler - Public-Safe Browser Automation

This public skill covers only lawful automation against public, open-access, or explicitly authorized content. Private runtime details, device paths, credentials, cookies, and subscription workflows belong in the private operations repo, not in this public rules repo.

## Legal Boundary

- Do not bypass paywalls, access controls, rate limits, CAPTCHAs, or bot defenses.
- Do not retrieve, print, copy, or instruct credential lookup from Keychain, browser cookie stores, password managers, or session databases.
- Do not publish account identifiers, token paths, private hostnames, private database DSNs, or device topology.
- For subscription or institutional content, stop at metadata collection unless the human has manually supplied a local file for private processing.
- Prefer publisher APIs, Crossref, PubMed, Unpaywall, government open data, RSS feeds, sitemaps, and pages explicitly marked open access/free to download.
- When access status is ambiguous, treat the item as metadata-only.

## Allowed Engines

| method | use when |
|---|---|
| `curl` / `wget` | Public pages, public APIs, OA PDFs, government documents |
| Browser DOM extraction | Public pages that require JavaScript rendering |
| WebFetch | Quick public page inspection |
| Computer/browser control | UI inspection on public pages only; not for access-control bypass |

## Public Metadata Extraction

```bash
PAGE_TEXT=$(osascript -e '
tell application "Safari"
    open location "https://example.com/page"
    delay 5
    set pageText to do JavaScript "document.body.innerText" in current tab of front window
    return pageText
end tell')
printf "%s\n" "$PAGE_TEXT" > /tmp/page_content.txt
```

## Open-Access PDF Download

Only download a PDF when the page, API, license, or URL pattern makes public download rights explicit.

```bash
curl -L -o "$OUTDIR/$FNAME" \
    -H "User-Agent: Mozilla/5.0" \
    -H "Referer: https://example.com/" \
    "$PDF_URL"

SIZE=$(stat -f%z "$OUTDIR/$FNAME")
if [ "$SIZE" -lt 50000 ] || ! file "$OUTDIR/$FNAME" | grep -q "PDF"; then
    echo "not a verified public PDF; remove and keep metadata only"
    rm -f "$OUTDIR/$FNAME"
fi
```

## Page Change Monitor

```bash
NEW_HASH=$(curl -fsSL "https://example.com/public-page" | shasum -a 256 | cut -d' ' -f1)
OLD_HASH=$(cat /tmp/page_hash.txt 2>/dev/null)
if [ "$NEW_HASH" != "$OLD_HASH" ]; then
    echo "$NEW_HASH" > /tmp/page_hash.txt
    echo "page changed"
fi
```

## Journal Policy

| access state | allowed action |
|---|---|
| Open access / public-domain / government PDF | Download, verify file type, store provenance |
| Free-to-read HTML without public PDF license | Save metadata and URL; do not scrape full article text into public output |
| Subscription / institutional / login-only | Metadata only unless a human supplies a local file for private use |
| Unknown | Metadata only |

## Metadata Sources

| source | allowed use |
|---|---|
| PubMed | Article discovery and metadata |
| Crossref | DOI metadata |
| Unpaywall | OA status and OA PDF URL discovery |
| Publisher RSS/sitemap | Public issue/article discovery |
| Government sites | Public documents and announcements |

## Verification Checklist

Before storing any downloaded file:

1. Confirm the page/API marks the file as public or OA.
2. Verify file type and size.
3. Record source URL, retrieval date, license/access marker, and checksum.
4. Keep copyrighted or subscription material out of public repos.

## Anti-Patterns

- Credential or cookie extraction.
- CAPTCHA/Cloudflare/paywall bypass.
- Downloading subscription PDFs through an authenticated browser session.
- Mentioning private accounts, private hostnames, or private token paths in public docs.
- Using unauthorized mirror sites.
- Committing PDFs, browser profiles, cookies, tokens, `.DS_Store`, or generated caches.

