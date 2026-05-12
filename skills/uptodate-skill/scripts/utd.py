#!/usr/bin/env python3
"""UpToDate skill — AppleScript-driven Chrome Beta on a Copper-personal Mac
with an active China Medical University library proxy session
(www-uptodate-com.autorpa.cmu.edu.tw:8443).

Stdlib only. Mirrors OpenEvidence skill command shape so /wiki-mega can
swap sub-utd from chrome-devtools + ad-hoc AppleScript to a stable
contract.

Subcommands:
    auth-status                Verify Chrome Beta has a live UTD CMU
                               session (looks for "China Medical
                               University" header on any UTD tab).
    search <query>             Navigate UTD search URL, wait for results
                               to render, extract top topic links.
    topic <url>                Open topic URL, wait for content, extract
                               title + Summary & Recommendations + cited
                               references. Save artifacts when --save.

Output of every command is a single JSON object on stdout (mirrors OE
output shape).

Cross-machine: pass --host hmj|cm1|mbp|mba to run osascript over ssh.
Default = local host. Only mbp + hm4 have Chrome Beta UTD CMU sessions
established as of 2026-05-11.

Browser dependency: Chrome Beta must be running on the target host with
at least one UTD tab logged in via CMU autorpa proxy. The script will
not perform the SAML / CMU SSO login flow.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

WIKI_RAW_ROOT_DEFAULT = Path.home() / "repos" / "personal-website" / "wiki_raw"
WIKI_RAW_ROOT = Path(os.environ.get("WIKI_RAW_ROOT", str(WIKI_RAW_ROOT_DEFAULT)))
SOURCE_NAME = "uptodate"

UTD_BASE = "https://www-uptodate-com.autorpa.cmu.edu.tw:8443"
URL_MATCH = "uptodate"  # substring used to find existing UTD tab
LIB_MARKER = "China Medical University"
ARTIFACT_ROOT = Path(os.environ.get("UTD_ARTIFACT_DIR", "./utd-artifacts"))
OSA_TIMEOUT = 30  # seconds for a single osascript invocation
NAV_WAIT_DEFAULT = 20  # seconds for SPA load
POLL_MS = 500


def osa_eval(applescript: str, host: str | None = None) -> str:
    """Run an AppleScript snippet locally or via ssh; return stdout.

    Pipes the AppleScript through stdin so the remote shell does not
    mangle quoting / newlines. osascript with `-` reads from stdin.
    """
    if host:
        cmd = ["ssh", "-o", "ConnectTimeout=5", host, "osascript", "-"]
    else:
        cmd = ["osascript", "-"]
    r = subprocess.run(cmd, input=applescript, capture_output=True,
                       text=True, timeout=OSA_TIMEOUT)
    if r.returncode != 0:
        raise RuntimeError(
            f"osascript failed (host={host or 'local'}): "
            f"{r.stderr.strip() or r.stdout.strip()}"
        )
    return r.stdout.rstrip("\n")


def js_for_applescript(js: str) -> str:
    """Escape a JS source string for inclusion as an AppleScript
    double-quoted string literal."""
    return js.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def chrome_eval(js: str, host: str | None = None, url_match: str = URL_MATCH,
                retries: int = 2) -> str:
    """Find a Chrome Beta tab whose URL matches url_match, run js inside,
    return the result. Retries on AppleEvent timeout."""
    js_esc = js_for_applescript(js)
    applescript = (
        'tell application "Google Chrome Beta"\n'
        '  repeat with w in windows\n'
        '    repeat with t in tabs of w\n'
        f'      if (URL of t as string) contains "{url_match}" then\n'
        f'        return execute t javascript "{js_esc}"\n'
        '      end if\n'
        '    end repeat\n'
        '  end repeat\n'
        '  return ""\n'
        'end tell\n'
    )
    last = ""
    for attempt in range(retries + 1):
        try:
            return osa_eval(applescript, host=host)
        except RuntimeError as e:
            last = str(e)
            if "逾時" in last or "timeout" in last.lower():
                time.sleep(2.0)
                continue
            raise
    raise RuntimeError(f"chrome_eval retries exhausted: {last}")


def chrome_navigate(url: str, host: str | None = None,
                    url_match: str = URL_MATCH) -> str:
    """Navigate an existing matching tab to url; if none, open a new tab
    in the front window."""
    applescript = (
        'tell application "Google Chrome Beta"\n'
        '  repeat with w in windows\n'
        '    repeat with t in tabs of w\n'
        f'      if (URL of t as string) contains "{url_match}" then\n'
        f'        set URL of t to "{url}"\n'
        '        return "navigated"\n'
        '      end if\n'
        '    end repeat\n'
        '  end repeat\n'
        f'  tell front window to make new tab with properties {{URL:"{url}"}}\n'
        '  return "new_tab"\n'
        'end tell\n'
    )
    return osa_eval(applescript, host=host)


def chrome_close_tabs_for(url_substr: str, host: str | None = None,
                          keep_first: bool = True) -> int:
    """Close all Chrome Beta tabs whose URL contains url_substr. If
    keep_first, retain the first match. Returns count closed."""
    applescript = (
        'tell application "Google Chrome Beta"\n'
        '  set killed to 0\n'
        '  set seenOne to false\n'
        '  repeat with w in windows\n'
        '    set tabsToClose to {}\n'
        '    repeat with t in tabs of w\n'
        f'      if (URL of t as string) contains "{url_substr}" then\n'
        f'        if {"not seenOne and " if keep_first else ""}true then\n'
        '          set end of tabsToClose to t\n'
        '          set killed to killed + 1\n'
        '        end if\n'
        '        set seenOne to true\n'
        '      end if\n'
        '    end repeat\n'
        '    repeat with t in tabsToClose\n'
        '      close t\n'
        '    end repeat\n'
        '  end repeat\n'
        '  return killed\n'
        'end tell\n'
    )
    try:
        return int(osa_eval(applescript, host=host) or 0)
    except Exception:
        return 0


def wait_for_js(predicate_js: str, host: str | None = None,
                timeout_s: int = NAV_WAIT_DEFAULT) -> bool:
    """Poll a JS predicate (returning truthy/falsy) until truthy or
    timeout. predicate_js must be a single expression, no statements."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            r = chrome_eval(f"!!({predicate_js})", host=host).strip().lower()
            if r == "true":
                return True
        except Exception:
            pass
        time.sleep(POLL_MS / 1000.0)
    return False


def cmd_auth_status(host: str | None) -> dict:
    """Look for a UTD tab; if present, check page content for CMU
    library marker."""
    js = (
        "JSON.stringify({title: document.title,"
        " bodyHead: (document.body && document.body.innerText || '').slice(0,800)})"
    )
    try:
        raw = chrome_eval(js, host=host)
    except Exception as e:
        return {"authenticated": False, "error": str(e),
                "hint": "Open Chrome Beta on the target host and load any UTD CMU page"}
    if not raw:
        return {"authenticated": False,
                "hint": "No Chrome Beta tab whose URL contains 'uptodate'"}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        return {"authenticated": False, "error": f"json: {e}", "raw_head": raw[:200]}
    body = parsed.get("bodyHead", "")
    title = parsed.get("title", "")
    if LIB_MARKER in body or "CMU" in body or "autorpa.cmu.edu.tw" in title:
        return {"authenticated": True, "library": "China Medical University",
                "title": title}
    if "Sign in" in body and LIB_MARKER not in body:
        return {"authenticated": False,
                "hint": "UTD page visible but no CMU marker; CMU SSO may have expired",
                "title": title}
    return {"authenticated": False, "title": title, "raw_body_head": body[:300]}


def cmd_search(host: str | None, query: str, save: bool, max_results: int) -> dict:
    url = (
        f"{UTD_BASE}/contents/search?search="
        f"{urllib.parse.quote(query)}&source=USER_INPUT"
    )
    chrome_navigate(url, host=host)
    # UTD search results render top-of-page within ~3-6s. Wait for at
    # least one canonical topic-title link (carries source=search_result
    # + selectedTitle= query params) to appear.
    ok = wait_for_js(
        "document.querySelectorAll('a[href*=\"selectedTitle=\"]').length > 0",
        host=host, timeout_s=NAV_WAIT_DEFAULT,
    )
    if not ok:
        return {"status": "timeout", "url": url, "query": query,
                "hint": "search results did not render within window"}
    # Real result topics are anchor tags whose href has
    # source=search_result + selectedTitle= ; sub-section + image links
    # share a topicKey but should be filtered out (we collapse to
    # parent topic).
    extract_js = (
        "JSON.stringify("
        "[...document.querySelectorAll('a[href*=\"selectedTitle=\"]')]"
        ".filter(a => {"
        "  const h = a.href || '';"
        "  return h.includes('source=search_result')"
        "    && !h.includes('sectionRank=')"
        "    && !h.includes('/image?')"
        "    && !h.includes('authors-and-editors')"
        "    && (a.textContent||'').trim().length > 5;"
        "})"
        ".slice(0, " + str(max(max_results, 1) * 2) + ")"
        ".map(a => ({t: (a.textContent||'').trim().slice(0,180),"
        " h: a.href}))"
        ")"
    )
    raw = chrome_eval(extract_js, host=host)
    try:
        results = json.loads(raw)
    except json.JSONDecodeError:
        results = []
    # dedupe by URL, keep first, cap to max_results
    seen = set()
    deduped = []
    for r in results:
        h = r.get("h", "")
        # Strip fragment
        canon = h.split("#")[0]
        if canon in seen:
            continue
        seen.add(canon)
        deduped.append(r)
        if len(deduped) >= max_results:
            break
    out = {"status": "ok", "query": query, "url": url,
           "results": deduped, "result_count": len(deduped)}
    if save:
        slug = _slug_for(query)
        adir = ARTIFACT_ROOT / slug
        adir.mkdir(parents=True, exist_ok=True)
        (adir / "search.json").write_text(
            json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        out["artifact_dir"] = str(adir)
    return out


def cmd_topic(host: str | None, url: str, save: bool,
              save_to_wiki_raw: bool = False,
              target_dir: str | None = None,
              query_origin: str | None = None) -> dict:
    chrome_navigate(url, host=host)
    # UTD topic pages do not use <h1>; wait on body length + topic-id
    # footer marker, which only appears once the topic content is loaded.
    ok = wait_for_js(
        "document.body.innerText.length > 4000 &&"
        " /Topic\\s+\\d+\\s+Version\\s+[\\d.]+/.test(document.body.innerText)",
        host=host, timeout_s=NAV_WAIT_DEFAULT,
    )
    if not ok:
        return {"status": "timeout", "url": url,
                "hint": "topic content did not render within window"}
    extract_js = (
        "(() => {"
        " const txt = document.body.innerText;"
        " const rx = re => { const m = txt.match(re); return m ? (m[1] || m[0]) : ''; };"
        " return JSON.stringify({"
        "  title: ((document.querySelector('h1, h2.heading, .article-title')||{}).textContent||document.title||'').trim(),"
        "  body: txt.slice(0, 20000),"
        "  summaryNode: ([...document.querySelectorAll('h2, h3, [class*=\"summary\" i]')]"
        "    .find(h=>/summary|recommendations|overview/i.test(h.textContent||''))?.parentElement?.innerText||'').slice(0,4000),"
        "  refs: [...document.querySelectorAll('a[href*=\"pubmed\"], a[href*=\"doi.org\"]')]"
        "    .map(a=>({t: (a.textContent||'').trim().slice(0,200), h: a.href}))"
        "    .filter(r=>r.t.length>3)"
        "    .slice(0, 200),"
        "  topic_id: rx(/Topic\\s+(\\d+)\\s+Version\\s+[\\d.]+/),"
        "  version: rx(/Topic\\s+\\d+\\s+Version\\s+([\\d.]+)/),"
        "  topic_last_updated: rx(/(?:This topic last updated|Topic last updated)[:\\s]+([^\\n.]+)/i),"
        "  literature_review_through: rx(/Literature review current through[:\\s]+([^\\n.]+)/i)"
        " });"
        "})()"
    )
    raw = chrome_eval(extract_js, host=host)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        return {"status": "parse_error", "error": str(e), "raw_head": raw[:300]}
    out = {"status": "ok", "url": url, **parsed,
           "ref_count": len(parsed.get("refs", []))}
    if save_to_wiki_raw:
        if not target_dir:
            out["save_mode"] = "wiki_raw_skipped"
            out["save_error"] = ("--save-to-wiki-raw requires --target-dir"
                                  " (agent must decide topic_path)")
            return out
        slug = _slug_for_url(url)
        captured_dt = datetime.datetime.now(datetime.timezone.utc)
        captured_date_compact = captured_dt.strftime("%Y%m%d")
        captured_iso = captured_dt.isoformat(timespec="seconds")
        citation_key = f"UpToDate_{slug}_{captured_date_compact}"
        target_folder = WIKI_RAW_ROOT / target_dir / citation_key
        target_folder.mkdir(parents=True, exist_ok=True)
        target_file = target_folder / "raw.md"
        target_file.write_text(
            _raw_md_with_frontmatter(out, url, query_origin, citation_key, SOURCE_NAME),
            encoding="utf-8")
        rel_raw_path = str(target_file.relative_to(Path.home() / "repos"))
        rel_end_folder = str(target_folder.relative_to(Path.home() / "repos"))
        source_uid = f"clinical_db:uptodate:{slug}"
        title = (out.get("title") or "").strip() or "(no title)"
        publisher_metadata = {
            "topic_id": out.get("topic_id") or "",
            "version": out.get("version") or "",
            "topic_title": title,
            "recommended_citation": _construct_utd_citation(out, url, captured_iso),
            "topic_last_updated": out.get("topic_last_updated") or "",
            "literature_review_through": out.get("literature_review_through") or "",
            "captured_at": captured_iso,
            "source_url": url,
            "ref_count": out.get("ref_count", 0),
        }
        if query_origin:
            publisher_metadata["query_origin"] = query_origin
        payload_flags = [
            "clinical_database", "cite_directly:false",
            "authority:navigator", f"snapshot:{captured_date_compact}"
        ]
        pg_result = _pg_insert_snapshot(
            citation_key=citation_key,
            source_uid=source_uid,
            source_type="clinical_database",
            title=title,
            year=captured_dt.year,
            journal="UpToDate",
            publisher="Wolters Kluwer Health",
            publication_date=captured_dt.date().isoformat(),
            raw_md_path=rel_raw_path,
            sidecar_key=f"wiki_raw/{citation_key}",
            end_folder_path=rel_end_folder,
            payload_flags=payload_flags,
            publisher_metadata=publisher_metadata,
        )
        out["save_mode"] = "wiki_raw_snapshot"
        out["citation_key"] = citation_key
        out["wiki_raw_path"] = str(target_file)
        out["target_dir"] = str(target_folder)
        out["pg"] = pg_result
    elif save:
        slug = _slug_for(url)
        adir = ARTIFACT_ROOT / slug
        adir.mkdir(parents=True, exist_ok=True)
        (adir / "topic.json").write_text(
            json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        (adir / "topic.md").write_text(_topic_md(out), encoding="utf-8")
        out["save_mode"] = "artifact_dir"
        out["artifact_dir"] = str(adir)
    return out


def _slug_for(s: str) -> str:
    h = hashlib.sha1(s.encode("utf-8")).hexdigest()[:10]
    base = "".join(c if c.isalnum() or c in "-_" else "-" for c in s.lower())
    base = "-".join(filter(None, base.split("-")))[:60]
    return f"{base or 'query'}-{h}"


def _slug_for_url(url: str) -> str:
    """URL-derived stable slug for wiki_raw snapshot folder. Strips
    section names like /contents/, /approach-to/, /conditions/ so the
    folder name carries the topic identifier itself."""
    parsed = urllib.parse.urlparse(url)
    path = (parsed.path or "").strip("/")
    parts = [
        p for p in path.split("/")
        if p and p not in ("contents", "approach-to", "conditions",
                            "management", "drugs")
    ]
    last = parts[-1] if parts else "topic"
    return (re.sub(r"[^a-z0-9-]+", "-", last.lower()).strip("-") or "topic")[:80]


def _construct_utd_citation(t: dict, url: str, captured_iso: str) -> str:
    """Construct UpToDate-style recommended citation from page metadata."""
    title = (t.get("title") or "").strip() or "(untitled UTD topic)"
    topic_id = (t.get("topic_id") or "").strip()
    version = (t.get("version") or "").strip()
    updated = (t.get("topic_last_updated") or "").strip()
    parts = [f'"{title}." UpToDate']
    if topic_id and version:
        parts.append(f"Topic {topic_id} Version {version}")
    if updated:
        parts.append(f"Updated {updated}")
    parts.append("Wolters Kluwer Health")
    parts.append(f"Accessed {captured_iso[:10]}")
    parts.append(url)
    return ". ".join(parts) + "."


def _raw_md_with_frontmatter(t: dict, url: str, query_origin: str | None,
                              citation_key: str, source_name: str = SOURCE_NAME) -> str:
    """Render the topic dict as a wiki_raw raw.md for a clinical-database
    snapshot. Frontmatter marks it as `cite_directly: false` (internal
    policy: prefer primary refs) but is otherwise a normal raw entry that
    registers in PG and carries the publisher's recommended citation."""
    captured = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    title = (t.get("title") or "").strip() or "(no title)"
    body = t.get("body", "") or ""
    overview = (t.get("summaryNode") or t.get("overview") or "").strip()
    topic_id = t.get("topic_id") or ""
    version = t.get("version") or ""
    topic_updated = t.get("topic_last_updated") or ""
    lit_review = t.get("literature_review_through") or ""
    citation_str = _construct_utd_citation(t, url, captured)
    fm = [
        "---",
        "type: raw",
        f"citation_key: {citation_key}",
        f"source_type: clinical_database",
        f"source: {source_name}",
        "publisher: Wolters Kluwer Health",
        "authority_level: navigator",
        "cite_directly: false",
        f"source_url: {url}",
        f"captured_at: {captured}",
    ]
    if query_origin:
        fm.append(f"query_origin: {json.dumps(query_origin, ensure_ascii=False)}")
    fm.append(f"topic_title: {json.dumps(title, ensure_ascii=False)}")
    if topic_id:
        fm.append(f"topic_id: {topic_id}")
    if version:
        fm.append(f"version: {version}")
    if topic_updated:
        fm.append(f"topic_last_updated: {json.dumps(topic_updated, ensure_ascii=False)}")
    if lit_review:
        fm.append(f"literature_review_through: {json.dumps(lit_review, ensure_ascii=False)}")
    fm.append(f"ref_count: {t.get('ref_count', 0)}")
    fm.append(f"recommended_citation: {json.dumps(citation_str, ensure_ascii=False)}")
    fm += [
        "fidelity_notes: |",
        f"  Snapshot of {source_name} clinical-database topic page,",
        "  registered in PG wiki_raw.raw_source_metadata as",
        "  source_type=clinical_database. Internal policy prefers citing",
        "  primary literature listed below over this snapshot itself",
        "  (cite_directly=false) per workspace memory",
        "  feedback_wiki_search_tri_source.md, but the publisher's",
        "  recommended citation is preserved in publisher_metadata for",
        "  cases that explicitly need to reference the tertiary source.",
        "---",
        "",
        f"# {title}",
        "",
        f"Source URL: {url}",
        f"Captured: {captured}",
    ]
    if topic_id:
        fm.append(f"UpToDate Topic ID: {topic_id} (Version {version})")
    if topic_updated:
        fm.append(f"Topic last updated: {topic_updated}")
    if lit_review:
        fm.append(f"Literature review current through: {lit_review}")
    fm += [
        f"Ref count: {t.get('ref_count', 0)}",
        "",
        "## Recommended citation (publisher format)",
        "",
        citation_str,
        "",
        "## Overview / Summary (extracted)",
        "",
        overview or "*(no overview node found)*",
        "",
        "## Body excerpt (first 20k chars)",
        "",
        body,
        "",
        "## Cited references (primary literature pointers)",
        "",
    ]
    for r in t.get("refs", []):
        fm.append(f"- [{r.get('t', '')}]({r.get('h', '')})")
    return "\n".join(fm)


def _sql_lit(s: str | None) -> str:
    """Escape a string for use as SQL literal. NULL on None."""
    if s is None:
        return "NULL"
    return "'" + str(s).replace("'", "''") + "'"


def _sql_text_array(items: list[str]) -> str:
    """Build a Postgres text[] literal from a list of strings."""
    quoted = []
    for s in items:
        esc = s.replace("\\", "\\\\").replace('"', '\\"')
        quoted.append(f'"{esc}"')
    return "'{" + ",".join(quoted) + "}'"


def _pg_insert_snapshot(citation_key: str, source_uid: str, source_type: str,
                         title: str, year: int | None, journal: str,
                         publisher: str, publication_date: str | None,
                         raw_md_path: str, sidecar_key: str,
                         end_folder_path: str, payload_flags: list[str],
                         publisher_metadata: dict) -> dict:
    """Shell out to psql; INSERT or UPDATE on (citation_key)."""
    pg_host = os.environ.get("VAULT_PG_HOST", "hmj")
    sql = (
        "INSERT INTO wiki_raw.raw_source_metadata ("
        " source_uid, citation_key, source_type, reading_status,"
        " mineru_status, title, year, journal, publisher,"
        " publication_date, raw_md_path, sidecar_key, source_pdf_path,"
        " payload_flags, publisher_metadata,"
        " folder_name, note_md_path, end_folder_path"
        ") VALUES ("
        f" {_sql_lit(source_uid)},"
        f" {_sql_lit(citation_key)},"
        f" {_sql_lit(source_type)},"
        " 'pending_llm',"
        " 'not_applicable',"
        f" {_sql_lit(title)},"
        f" {year if year else 'NULL'},"
        f" {_sql_lit(journal)},"
        f" {_sql_lit(publisher)},"
        f" {_sql_lit(publication_date)},"
        f" {_sql_lit(raw_md_path)},"
        f" {_sql_lit(sidecar_key)},"
        " NULL,"
        f" {_sql_text_array(payload_flags)},"
        f" {_sql_lit(json.dumps(publisher_metadata, ensure_ascii=False))}::jsonb,"
        " NULL, NULL,"
        f" {_sql_lit(end_folder_path)}"
        ") ON CONFLICT (citation_key) DO UPDATE SET"
        " raw_md_path = EXCLUDED.raw_md_path,"
        " publisher_metadata = EXCLUDED.publisher_metadata,"
        " payload_flags = EXCLUDED.payload_flags,"
        " end_folder_path = EXCLUDED.end_folder_path,"
        " updated_at = now()"
        " RETURNING citation_key;"
    )
    r = subprocess.run(
        ["psql", "-h", pg_host, "-d", "vault_main", "-tA", "-c", sql],
        capture_output=True, text=True, timeout=30,
    )
    if r.returncode != 0:
        return {"pg_status": "error", "stderr": r.stderr.strip()[:500],
                "stdout": r.stdout.strip()[:200]}
    return {"pg_status": "ok", "citation_key_returned": r.stdout.strip()}


def _topic_md(t: dict) -> str:
    lines = [
        f"# {t.get('title', '(no title)')}",
        "",
        f"Source URL: {t.get('url', '')}",
        f"Status: {t.get('status', '')}",
        f"Citation refs found: {t.get('ref_count', 0)}",
        "",
        "## Summary / Recommendations (extracted)",
        "",
        t.get("summaryNode", "") or "*(no summary node found)*",
        "",
        "## Body excerpt (first 20k chars)",
        "",
        t.get("body", ""),
        "",
        "## Cited references",
        "",
    ]
    for r in t.get("refs", []):
        lines.append(f"- [{r.get('t', '')}]({r.get('h', '')})")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default=None,
                    help="ssh into this host for osascript (default: local)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth-status")
    p_s = sub.add_parser("search")
    p_s.add_argument("query")
    p_s.add_argument("--max", dest="max_results", type=int, default=10)
    p_s.add_argument("--no-save", action="store_true")
    p_t = sub.add_parser("topic")
    p_t.add_argument("url")
    p_t.add_argument("--no-save", action="store_true")
    p_t.add_argument("--save-to-wiki-raw", action="store_true",
                     help="save raw.md into personal-website/wiki_raw/"
                          "<target-dir>/<url-slug>/raw.md as a reference"
                          " snapshot; flips off the artifact-dir branch")
    p_t.add_argument("--target-dir", default=None,
                     help="relative target dir under wiki_raw; default ="
                          " _external_reference/uptodate")
    p_t.add_argument("--query-origin", default=None,
                     help="query string for frontmatter traceability")
    args = ap.parse_args(argv)

    if args.cmd == "auth-status":
        out = cmd_auth_status(host=args.host)
    elif args.cmd == "search":
        out = cmd_search(
            host=args.host, query=args.query, save=not args.no_save,
            max_results=args.max_results)
    elif args.cmd == "topic":
        out = cmd_topic(
            host=args.host, url=args.url, save=not args.no_save,
            save_to_wiki_raw=args.save_to_wiki_raw,
            target_dir=args.target_dir,
            query_origin=args.query_origin)
    else:
        ap.error(f"unknown command: {args.cmd}")
        return 2

    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
