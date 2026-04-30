---
type: data
name: journal-download
description: "Public-safe journal metadata and open-access download protocol. Deprecated implementation detail: operational journal automation lives in private runtime rules. MANDATORY TRIGGERS: /journal-download, download journal, 下載期刊, download OA, download open access, get this week's papers."
---

# Journal Download - Public-Safe Policy

This public skill is policy only. It permits metadata extraction and open-access downloads. Private authenticated workflows, subscription handling, browser profiles, cookies, credentials, and device-specific automation must not be documented in this repo.

## Allowed

- Collect article metadata from PubMed, Crossref, publisher RSS/sitemaps, and public table-of-contents pages.
- Download PDFs only when the article is explicitly open access, public-domain, government-published, or otherwise clearly licensed for public download.
- Export Markdown issue manifests containing title, DOI, authors, abstract where legally visible, source URL, OA status, and access date.

## Not Allowed

- Bypassing paywalls, Cloudflare, CAPTCHA, bot checks, or login walls.
- Reading browser cookie stores or password managers.
- Publishing account identifiers, token paths, internal hostnames, or private paths.
- Downloading subscription PDFs into a public repo.
- Treating "works in my authenticated browser" as public-download permission.

## Minimal OA Flow

1. Discover article metadata from public source.
2. Determine OA status through page markers, license text, Crossref, or Unpaywall.
3. If OA PDF URL is confirmed, download with `curl`.
4. Verify file type and size.
5. Store only metadata/provenance in public repos unless the PDF license allows redistribution.

## Metadata Manifest

```markdown
| date | journal | article_type | title | doi | oa_status | source_url |
|---|---|---|---|---|---|---|
```

When access status is unknown or subscription-only, set `oa_status=metadata_only`.

