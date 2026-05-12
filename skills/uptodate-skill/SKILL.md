---
name: uptodate
description: |
  Query UpToDate via a logged-in Chrome Beta session on a Copper-personal
  Mac using the China Medical University library proxy
  (www-uptodate-com.autorpa.cmu.edu.tw:8443). Stdlib-only Python CLI
  shells out to osascript so the existing browser session does the
  heavy lifting; no cookies extraction is needed (Chrome 130+ App-Bound
  encryption blocks that anyway). Mirrors OpenEvidence skill command
  shape so /wiki-mega can call sub-utd through a stable JSON contract.
---

# UpToDate (CMU proxy, AppleScript pipeline)

A stdlib-only Python CLI (`scripts/utd.py`) with three subcommands. All
output is one JSON object on stdout; artifacts land under
`./utd-artifacts/<slug>/` when `--save` is on (default).

| Command | Purpose |
|---|---|
| `python3 scripts/utd.py auth-status` | Confirm a Chrome Beta tab has a live UTD CMU proxy session |
| `python3 scripts/utd.py search "<query>"` | Search UTD, return top topic links |
| `python3 scripts/utd.py topic <topic-url>` | Open topic page, extract title + summary + cited refs |

## Setup (one-time)

1. Open Chrome Beta on a Copper-personal Mac that has CMU library SSO
   working (currently `hm4` and `mbp`; `hmj` / `cm1` / `mba` do not).
2. Log into UpToDate via the CMU proxy at
   `https://www-uptodate-com.autorpa.cmu.edu.tw:8443/contents/search`.
3. Confirm "China Medical University" appears in the page header / chrome.

That's all. There is no `cookies.json` to manage. The CMU SAML session
lives in Chrome Beta's profile and refreshes automatically while the
browser is open and the SSO ticket is still valid (typically 4-8 hours).

## Cross-machine invocation

Pass `--host <hostname>` to run osascript over ssh on another
Copper-personal Mac. Useful when the calling Claude Code session is on
`hm4` but the active UTD tab lives on `mbp`.

```bash
python3 scripts/utd.py --host mbp auth-status
python3 scripts/utd.py --host mbp search "IgA nephropathy treatment"
python3 scripts/utd.py --host mbp topic "https://www-uptodate-com.autorpa.cmu.edu.tw:8443/contents/..."
```

Without `--host`, osascript runs against the local Chrome Beta. The
script expects `ssh <host>` to be passwordless (Tailscale + ssh keys
per Law).

## Auth status

```bash
python3 scripts/utd.py auth-status
```

Returns one of:

- `{"authenticated": true, "library": "China Medical University", "title": "..."}`
- `{"authenticated": false, "hint": "..."}` — no UTD tab open, CMU
  session expired, or page is sign-in screen.

When false, the fix is manual: open Chrome Beta, re-login at
`https://library.cmu.edu.tw/` (or whichever SSO portal Copper uses),
then re-navigate to UpToDate.

## Search

```bash
python3 scripts/utd.py search "medium cut-off membrane dialysis"
python3 scripts/utd.py search "atrial fibrillation NOAC" --max 5
python3 scripts/utd.py search "IgA nephropathy" --no-save
```

Navigates the existing UTD tab to
`/contents/search?search=<urlencoded>&source=USER_INPUT`, polls until
`>5` result links render, then extracts top topic title + URL pairs.

Returns:

```json
{
  "status": "ok",
  "query": "...",
  "url": "https://www-uptodate-com.autorpa.cmu.edu.tw:8443/contents/search?...",
  "result_count": 10,
  "results": [{"t": "Topic title", "h": "https://..."}, ...],
  "artifact_dir": "./utd-artifacts/<slug>/"
}
```

Artifact: `search.json` (the same JSON, indented).

## Topic

```bash
python3 scripts/utd.py topic "https://www-uptodate-com.autorpa.cmu.edu.tw:8443/contents/iga-nephropathy-treatment"
```

Navigates to the topic URL, waits for `<h1>` + 2 KB body text to
render, then extracts:

- `title` (h1 text or document.title fallback)
- `summaryNode` (the section whose heading matches /summary|recommendations|overview/i)
- `body` (first 20 KB of document.body.innerText)
- `refs` (links to pubmed.* or doi.org with text)
- `ref_count`

Artifacts: `topic.json` + `topic.md` (rendered with summary + body excerpt + refs list).

## Reliability mechanisms

- **AppleEvent retry**: each `chrome_eval` retries once on a 逾時 /
  timeout error after a 2-second pause.
- **SPA wait-for-ready**: instead of fixed sleeps, `wait_for_js` polls
  a JS predicate every 500 ms until truthy or 20-second timeout.
- **Tab reuse**: the script reuses any existing tab whose URL contains
  "uptodate"; only opens a new tab if none exists.
- **Per-query slug**: artifacts go to a stable folder based on
  hash(query / URL), so re-runs overwrite cleanly.

## Limitations

- Chrome Beta must be running on the target host. The script does NOT
  start the browser or perform the SAML login flow.
- One Chrome Beta tab serves all UTD operations; concurrent calls from
  different processes will race on the same tab. `/wiki-mega` only
  fires one UTD sub-agent per invocation so this is fine in practice.
- AppleEvent JS execute requires "Allow JavaScript from Apple Events"
  enabled in Chrome Beta's View → Developer menu. Already on for
  Copper's hm4 + mbp profiles.
- If the CMU SAML ticket expires mid-session, the script returns
  `authenticated: false` and Copper must re-login manually. There is
  no auto-refresh.

## Environment overrides

| Variable | Default |
|---|---|
| `UTD_ARTIFACT_DIR` | `./utd-artifacts` |

## Cross-refs

- OpenEvidence skill (`_admin-rules/skills/openevidence-skill/SKILL.md`)
  — the OE-vs-UTD parallel: OE uses cookies.json + curl, UTD uses
  AppleScript because Chrome 130+ App-Bound encryption blocks cookie
  export and UTD does not expose a public API.
- `/wiki-mega` skill — calls `python3 scripts/utd.py` as its sub-utd
  worker, replacing the earlier chrome-devtools MCP fallback.
- `feedback_wiki_search_tri_source.md` memory — UTD is navigator only:
  never cite directly; cite the primary refs UTD points to.
