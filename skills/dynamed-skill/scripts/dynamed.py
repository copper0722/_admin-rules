#!/usr/bin/env python3
"""DynaMed skill — AppleScript-driven Chrome Beta on a Copper-personal Mac
with an active DynaMed (EBSCO Health) institutional subscription session.

Stdlib only. Same shape as the OpenEvidence + UpToDate skills so
/wiki-mega can call sub-dynamed through a stable JSON contract.

Subcommands:
    auth-status                Verify Chrome Beta has an active DynaMed login.
    search <query>             Navigate DynaMed search URL, return top topic links.
    topic <url>                Open topic URL, extract title + overview +
                               cited refs. With --save-to-wiki-raw, write
                               raw.md into personal-website/wiki_raw/
                               <target-dir>/<citation_key>/raw.md and
                               INSERT a PG row.

Cross-machine: pass --host hmj|cm1|mbp|mba to run osascript over ssh.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

DYNAMED_BASE = "https://www.dynamed.com"
URL_MATCH = "dynamed.com"
SOURCE_NAME = "dynamed"
TOPIC_PATH_HINTS = ("/approach-to/", "/conditions/", "/management/", "/drugs/")
ARTIFACT_ROOT = Path(os.environ.get("DYNAMED_ARTIFACT_DIR", "./dynamed-artifacts"))
WIKI_RAW_ROOT_DEFAULT = Path.home() / "repos" / "personal-website" / "wiki_raw"
WIKI_RAW_ROOT = Path(os.environ.get("WIKI_RAW_ROOT", str(WIKI_RAW_ROOT_DEFAULT)))
OSA_TIMEOUT = 30
NAV_WAIT_DEFAULT = 20
POLL_MS = 500


def osa_eval(applescript: str, host: str | None = None) -> str:
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
    return js.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def chrome_eval(js: str, host: str | None = None, url_match: str = URL_MATCH,
                retries: int = 2) -> str:
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
    for _ in range(retries + 1):
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


def wait_for_js(predicate_js: str, host: str | None = None,
                timeout_s: int = NAV_WAIT_DEFAULT) -> bool:
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
    js = (
        "JSON.stringify({"
        " title: document.title,"
        " bodyHead: (document.body && document.body.innerText || '').slice(0,800),"
        " hasSignInPrompt: !!document.querySelector('a[href*=\"signin\" i],"
        "  button[class*=\"signin\" i], a[href*=\"login\" i],"
        "  button[class*=\"login\" i]'),"
        " hasUserMenu: !!document.querySelector('[class*=\"avatar\" i],"
        "  [class*=\"profile\" i], [aria-label*=\"account\" i],"
        "  [class*=\"initials\" i]')"
        "})"
    )
    try:
        raw = chrome_eval(js, host=host)
    except Exception as e:
        return {"authenticated": False, "error": str(e),
                "hint": "Open Chrome Beta on the target host and load any DynaMed page"}
    if not raw:
        return {"authenticated": False,
                "hint": "No Chrome Beta tab whose URL contains 'dynamed.com'"}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        return {"authenticated": False, "error": f"json: {e}", "raw_head": raw[:200]}
    body = parsed.get("bodyHead", "")
    sign_in = parsed.get("hasSignInPrompt", False)
    user_menu = parsed.get("hasUserMenu", False)
    if user_menu or ("CME" in body and "Specialties" in body) or "Thumbs Up" in body:
        return {"authenticated": True, "title": parsed.get("title", ""),
                "indicator": "user_menu_or_cme_credit_present"}
    if sign_in:
        return {"authenticated": False,
                "hint": "Sign-in prompt visible; institutional session may have expired",
                "title": parsed.get("title", "")}
    return {"authenticated": False, "title": parsed.get("title", ""),
            "raw_body_head": body[:300]}


def cmd_search(host: str | None, query: str, save: bool, max_results: int) -> dict:
    url = (
        f"{DYNAMED_BASE}/results?q="
        f"{urllib.parse.quote(query)}&lang=en"
    )
    chrome_navigate(url, host=host)
    ok = wait_for_js(
        "document.querySelectorAll('a[href*=\"/approach-to/\"],"
        " a[href*=\"/conditions/\"], a[href*=\"/management/\"],"
        " a[href*=\"/drugs/\"]').length > 2",
        host=host, timeout_s=NAV_WAIT_DEFAULT,
    )
    if not ok:
        return {"status": "timeout", "url": url, "query": query,
                "hint": "search results did not render within window"}
    extract_js = (
        "JSON.stringify("
        "[...document.querySelectorAll('a[href*=\"/approach-to/\"],"
        " a[href*=\"/conditions/\"], a[href*=\"/management/\"],"
        " a[href*=\"/drugs/\"]')]"
        ".filter(a => {"
        "  const h = a.href || '';"
        "  if (h.includes('#')) return false;"
        "  const t = (a.textContent || '').trim();"
        "  return t.length > 5 && t.length < 200;"
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
    seen = set()
    deduped = []
    for r in results:
        h = (r.get("h", "") or "").split("#")[0]
        if not h or h in seen:
            continue
        seen.add(h)
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
    ok = wait_for_js(
        "document.querySelector('h1') && document.body.innerText.length > 1500",
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
        "  title: ((document.querySelector('h1')||{}).textContent||document.title||'').trim(),"
        "  body: txt.slice(0, 20000),"
        "  overview: ([...document.querySelectorAll('h2, h3, [class*=\"recommend\" i],"
        "    [class*=\"summary\" i], [class*=\"overview\" i]')]"
        "    .find(h => /overview|recommendations|summary|background/i.test(h.textContent||''))?.parentElement?.innerText||'')"
        "    .slice(0, 4000),"
        "  refs: [...document.querySelectorAll('a[href*=\"pubmed\"],"
        "    a[href*=\"doi.org\"]')]"
        "    .map(a => ({t: (a.textContent||'').trim().slice(0,200), h: a.href}))"
        "    .filter(r => r.t.length > 3)"
        "    .slice(0, 200),"
        "  updated_date: rx(/(?:Updated|Last Updated|Reviewed)\\s+([0-9]{1,2}\\s+[A-Za-z]{3,9}\\s+[0-9]{4})/i)"
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
        citation_key = f"DynaMed_{slug}_{captured_date_compact}"
        target_folder = WIKI_RAW_ROOT / target_dir / citation_key
        target_folder.mkdir(parents=True, exist_ok=True)
        target_file = target_folder / "raw.md"
        target_file.write_text(
            _raw_md_with_frontmatter(out, url, query_origin, citation_key),
            encoding="utf-8")
        rel_raw_path = str(target_file.relative_to(Path.home() / "repos"))
        rel_end_folder = str(target_folder.relative_to(Path.home() / "repos"))
        source_uid = f"clinical_db:dynamed:{slug}"
        title = (out.get("title") or "").strip() or "(no title)"
        publisher_metadata = {
            "topic_title": title,
            "recommended_citation": _construct_dynamed_citation(out, url, captured_iso),
            "updated_date": out.get("updated_date") or "",
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
            journal="DynaMed",
            publisher="EBSCO Information Services",
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
    parsed = urllib.parse.urlparse(url)
    path = (parsed.path or "").strip("/")
    parts = [
        p for p in path.split("/")
        if p and p not in ("approach-to", "conditions", "management", "drugs",
                            "contents")
    ]
    last = parts[-1] if parts else "topic"
    return (re.sub(r"[^a-z0-9-]+", "-", last.lower()).strip("-") or "topic")[:80]


def _construct_dynamed_citation(t: dict, url: str, captured_iso: str) -> str:
    title = (t.get("title") or "").strip() or "(untitled DynaMed topic)"
    updated = (t.get("updated_date") or "").strip()
    parts = [f'"{title}." DynaMed']
    parts.append("EBSCO Information Services")
    if updated:
        parts.append(f"Updated {updated}")
    parts.append(f"Accessed {captured_iso[:10]}")
    parts.append(url)
    return ". ".join(parts) + "."


def _raw_md_with_frontmatter(t: dict, url: str, query_origin: str | None,
                              citation_key: str,
                              source_name: str = SOURCE_NAME) -> str:
    captured = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    title = (t.get("title") or "").strip() or "(no title)"
    body = t.get("body", "") or ""
    overview = (t.get("overview") or "").strip()
    updated = (t.get("updated_date") or "").strip()
    citation_str = _construct_dynamed_citation(t, url, captured)
    fm = [
        "---",
        "type: raw",
        f"citation_key: {citation_key}",
        f"source_type: clinical_database",
        f"source: {source_name}",
        "publisher: EBSCO Information Services",
        "authority_level: navigator",
        "cite_directly: false",
        f"source_url: {url}",
        f"captured_at: {captured}",
    ]
    if query_origin:
        fm.append(f"query_origin: {json.dumps(query_origin, ensure_ascii=False)}")
    fm.append(f"topic_title: {json.dumps(title, ensure_ascii=False)}")
    if updated:
        fm.append(f"updated_date: {json.dumps(updated, ensure_ascii=False)}")
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
    if updated:
        fm.append(f"DynaMed Updated: {updated}")
    fm += [
        f"Ref count: {t.get('ref_count', 0)}",
        "",
        "## Recommended citation (publisher format)",
        "",
        citation_str,
        "",
        "## Overview / Recommendations (extracted)",
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


def _topic_md(t: dict) -> str:
    lines = [
        f"# {t.get('title', '(no title)')}",
        "",
        f"Source URL: {t.get('url', '')}",
        f"Status: {t.get('status', '')}",
        f"Citation refs found: {t.get('ref_count', 0)}",
        "",
        "## Overview / Recommendations (extracted)",
        "",
        t.get("overview", "") or "*(no overview node found)*",
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


def _sql_lit(s: str | None) -> str:
    if s is None:
        return "NULL"
    return "'" + str(s).replace("'", "''") + "'"


def _sql_text_array(items: list[str]) -> str:
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
    p_t.add_argument("--save-to-wiki-raw", action="store_true")
    p_t.add_argument("--target-dir", default=None,
                     help="relative target dir under wiki_raw; required for"
                          " --save-to-wiki-raw")
    p_t.add_argument("--query-origin", default=None)
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
