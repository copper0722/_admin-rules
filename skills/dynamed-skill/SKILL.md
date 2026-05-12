---
name: dynamed
description: |
  Query DynaMed (EBSCO Health) via a logged-in Chrome Beta session on a
  Copper-personal Mac. Stdlib-only Python CLI shells out to osascript so
  the existing browser session does the heavy lifting; no cookies
  extraction is needed (Chrome 130+ App-Bound encryption blocks that
  anyway, and DynaMed's SPA renders topic content client-side so curl
  + cookies would only return a React shell). Mirrors OpenEvidence /
  UpToDate skill command shape so /wiki-mega can call sub-dynamed
  through a stable JSON contract.
---

# DynaMed (AppleScript pipeline)

A stdlib-only Python CLI (`scripts/dynamed.py`) with three subcommands.
All output is one JSON object on stdout; artifacts land under
`./dynamed-artifacts/<slug>/` when `--save` is on (default).

| Command | Purpose |
|---|---|
| `python3 scripts/dynamed.py auth-status` | Confirm a Chrome Beta tab has an active DynaMed session |
| `python3 scripts/dynamed.py search "<query>"` | Search DynaMed, return top topic links (filters out intra-topic anchor links) |
| `python3 scripts/dynamed.py topic <topic-url>` | Open topic page, extract title + overview + cited refs |

## Setup (one-time)

1. Open Chrome Beta on a Copper-personal Mac with active DynaMed
   institutional subscription auth (currently `hm4` and `mbp`).
2. Log into `https://www.dynamed.com/` via the institutional auth
   flow (EBSCO Health).
3. Confirm the user-initials indicator + CME credit counter render
   (the "CW" + "CME 89.5" elements visible on Copper's account).

No `cookies.json` is needed; the institutional session lives in Chrome
Beta and refreshes automatically while the browser is open.

## Cross-machine invocation

Pass `--host <hostname>` to ssh into another Copper-personal Mac.

```bash
python3 scripts/dynamed.py --host mbp auth-status
python3 scripts/dynamed.py --host mbp search "IgA nephropathy treatment"
python3 scripts/dynamed.py --host mbp topic "https://www.dynamed.com/approach-to/..."
```

Without `--host`, runs against local Chrome Beta.

## Auth status

```bash
python3 scripts/dynamed.py auth-status
```

Returns:
- `{"authenticated": true, "indicator": "user_menu_or_cme_credit_present", "title": "..."}`
- `{"authenticated": false, "hint": "..."}`

Heuristic: DynaMed renders user initials + CME credit counter when
logged in; sign-in / register prompts disappear post-auth.

## Search

```bash
python3 scripts/dynamed.py search "IgA nephropathy treatment"
python3 scripts/dynamed.py search "atrial fibrillation NOAC" --max 5
```

Navigates to `https://www.dynamed.com/results?q=<urlencoded>&lang=en`,
waits for `>2` topic-result links to render
(`/approach-to/`, `/conditions/`, `/management/`, `/drugs/` href
substrings; intra-topic anchor links `#GUID-...` are filtered out).

Returns:

```json
{
  "status": "ok",
  "query": "...",
  "url": "https://www.dynamed.com/results?q=...",
  "result_count": 10,
  "results": [{"t": "Topic title", "h": "https://..."}, ...],
  "artifact_dir": "./dynamed-artifacts/<slug>/"
}
```

## Topic

```bash
python3 scripts/dynamed.py topic "https://www.dynamed.com/approach-to/glomerular-disease-in-adults-approach-to-the-patient"
```

Extracts:

- `title` (h1 text or document.title fallback)
- `overview` (section whose heading matches /overview|recommendations|summary|background/i)
- `body` (first 20 KB of innerText)
- `refs` (pubmed.* + doi.org links with text)
- `ref_count`

Artifacts: `topic.json` + `topic.md`.

## Reliability mechanisms

Same as UpToDate skill: AppleEvent retry on `逾時`, SPA wait-for-ready
JS polling, stdin-piped osascript to avoid remote-shell quoting bugs,
tab reuse to avoid window clutter.

## Limitations

- Chrome Beta must be running on the target host; script does NOT
  start the browser or perform institutional login.
- One Chrome Beta tab serves all DynaMed operations; concurrent
  process calls race on the same tab.
- AppleEvent JS execute requires "Allow JavaScript from Apple Events"
  enabled in Chrome Beta's View → Developer menu.
- DynaMed is a SPA (React + styled-components) so content selectors
  are heuristic; if EBSCO changes DOM structure, search /topic
  extractors may need adjustment.
- Topic results sometimes redirect to broader category pages (e.g.,
  "IgA nephropathy treatment" lands on Glomerular Disease in Adults
  approach rather than an IgAN-specific topic). The skill returns the
  topic URLs as-is; downstream synthesis decides relevance.

## Environment overrides

| Variable | Default |
|---|---|
| `DYNAMED_ARTIFACT_DIR` | `./dynamed-artifacts` |

## Cross-refs

- OpenEvidence skill — the OE pattern adapted for sites without a
  public API; DynaMed and UpToDate both use AppleScript pipeline
  variant.
- UpToDate skill — sibling skill with parallel structure.
- `/wiki-mega` skill — calls `python3 scripts/dynamed.py` as the
  sub-dynamed worker.
- `feedback_wiki_search_tri_source.md` memory — DynaMed is navigator
  only: never cite directly; cite the primary refs DynaMed points to.
