#!/usr/bin/env python3
"""Portable 1:1 port of openevidence-mcp tools.

Subcommands mirror the MCP tool surface:
  auth-status         -> oe_auth_status
  history             -> oe_history_list
  article <id>        -> oe_article_get
  ask "<question>"    -> oe_ask

Stdlib only. Cookies are loaded from a JSON file (browser export array OR
playwright storage-state). Default lookup order:
  $OE_COOKIES, ./cookies.json, <skill>/cookies.json, ~/.openevidence/cookies.json

Artifacts are written to $OE_ARTIFACT_DIR or ./oe-artifacts/<article_id>/.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

BASE_URL = os.environ.get("OE_BASE_URL", "https://www.openevidence.com")
DEFAULT_ARTICLE_TYPE = "Ask OpenEvidence Light with citations"
PENDING_STATUSES = {"queued", "pending", "processing", "running", "in_progress"}
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120 Safari/537.36"
)
PUBLICATION_FIGURE_RE = re.compile(
    r"REACTCOMPONENT!:!PublicationFigure!:!(\{[\s\S]*?\})\n*"
)
VISUAL_TAG_RE = re.compile(r"<visual>([^[<]+?)(?:\[\d+\])?</visual>")
DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)]\((https?://[^)\s]+)\)")


# ---------- cookies ----------

class CookieJar:
    def __init__(self, cookies: list[dict]) -> None:
        self._cookies = cookies

    @classmethod
    def load(cls, path: Path) -> "CookieJar":
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            inputs = raw
        elif isinstance(raw, dict) and isinstance(raw.get("cookies"), list):
            inputs = raw["cookies"]
        else:
            raise SystemExit(f"Unsupported cookie file shape: {path}")

        now = time.time()
        normalized: list[dict] = []
        for c in inputs:
            name = c.get("name")
            if not isinstance(name, str) or not name:
                continue
            expires = c.get("expirationDate") or c.get("expires")
            if isinstance(expires, (int, float)) and expires > 0 and expires <= now:
                continue
            domain = (c.get("domain") or "").lstrip(".").lower()
            normalized.append({
                "name": name,
                "value": "" if c.get("value") is None else str(c.get("value")),
                "domain": domain,
                "hostOnly": c.get("hostOnly") is True,
                "path": c.get("path") or "/",
                "secure": c.get("secure") is True,
            })
        if not normalized:
            raise SystemExit(f"No usable cookies in {path}")
        return cls(normalized)

    def header_for(self, url: str) -> str:
        u = urllib.parse.urlparse(url)
        host = (u.hostname or "").lower()
        path = u.path or "/"
        scheme = u.scheme
        matches = []
        for c in self._cookies:
            if c["secure"] and scheme != "https":
                continue
            d = c["domain"]
            if d:
                if c["hostOnly"]:
                    if host != d:
                        continue
                else:
                    if host != d and not host.endswith("." + d):
                        continue
            cp = c["path"]
            if not (path == cp or (path.startswith(cp) and (cp.endswith("/") or path[len(cp):len(cp)+1] == "/"))):
                continue
            matches.append(c)
        matches.sort(key=lambda x: -len(x["path"]))
        return "; ".join(f"{c['name']}={c['value']}" for c in matches)


def resolve_cookies_path() -> Path:
    candidates: list[Path] = []
    env = os.environ.get("OE_COOKIES")
    if env:
        candidates.append(Path(env).expanduser())
    candidates.append(Path.cwd() / "cookies.json")
    candidates.append(Path(__file__).resolve().parent.parent / "cookies.json")
    candidates.append(Path.home() / ".openevidence" / "cookies.json")
    for p in candidates:
        if p.is_file():
            return p
    raise SystemExit(
        "cookies.json not found. Set $OE_COOKIES or place cookies.json next to the skill."
    )


# ---------- HTTP ----------

def _request(jar: CookieJar, method: str, path: str, body: dict | None = None) -> tuple[int, bytes]:
    url = urllib.parse.urljoin(BASE_URL + "/", path.lstrip("/"))
    cookie = jar.header_for(url)
    if not cookie:
        raise SystemExit(f"No cookies match {url}")
    headers = {
        "cookie": cookie,
        "origin": BASE_URL,
        "referer": BASE_URL + "/",
        "accept": "application/json, text/plain, */*",
        "user-agent": USER_AGENT,
    }
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["content-type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def get_json(jar: CookieJar, path: str) -> Any:
    last_status, last_body = 0, b""
    for attempt in range(3):
        last_status, last_body = _request(jar, "GET", path)
        if last_status < 500:
            break
        time.sleep((attempt + 1) * 0.4)
    if last_status < 200 or last_status >= 300:
        raise SystemExit(f"GET {path} failed: {last_status} {last_body[:400]!r}")
    return json.loads(last_body.decode("utf-8"))


def post_json(jar: CookieJar, path: str, body: dict) -> Any:
    last_status, last_body = 0, b""
    for attempt in range(2):
        last_status, last_body = _request(jar, "POST", path, body=body)
        if last_status < 500:
            break
        time.sleep((attempt + 1) * 0.4)
    if last_status not in (200, 201):
        raise SystemExit(f"POST {path} failed: {last_status} {last_body[:400]!r}")
    return json.loads(last_body.decode("utf-8"))


# ---------- text/figure extraction ----------

def strip_react_component_blocks(text: str) -> str:
    text = re.sub(r"^REACTCOMPONENT!:![\s\S]*?\n\n\n", "", text)
    text = re.sub(r"REACTCOMPONENT!:![A-Za-z]+!:!\{[\s\S]*?\}\n*", "", text)
    return text.strip()


def extract_answer_text(article: dict) -> str | None:
    output = article.get("output") or {}
    sa = output.get("structured_article") or {}
    raw_text = sa.get("raw_text")
    if isinstance(raw_text, str) and raw_text:
        return raw_text
    text = output.get("text")
    if isinstance(text, str) and text:
        return strip_react_component_blocks(text)
    history = (article.get("inputs") or {}).get("history")
    if isinstance(history, list) and history:
        last = history[-1]
        if isinstance(last, dict):
            ot = last.get("outputText")
            if isinstance(ot, str):
                return ot
    return None


def extract_figures_from_text(text: str) -> list[dict]:
    out: list[dict] = []
    for m in PUBLICATION_FIGURE_RE.finditer(text):
        try:
            payload = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        url = payload.get("url")
        if isinstance(url, str) and url:
            fig = {"name": payload.get("name") or "", "url": url}
            cap = payload.get("caption")
            if isinstance(cap, str) and cap:
                fig["caption"] = cap
            out.append(fig)
    return out


def _walk_citation_figures(root: Any, into: list[dict]) -> None:
    if isinstance(root, list):
        for x in root:
            _walk_citation_figures(x, into)
        return
    if not isinstance(root, dict):
        return
    citations = root.get("citations")
    if isinstance(citations, list):
        for c in citations:
            md = (c or {}).get("metadata") or {}
            cm = md.get("content_metadata") or {}
            for fig in cm.get("figures") or []:
                url = fig.get("url")
                if isinstance(url, str) and url:
                    item = {"name": fig.get("name") or "", "url": url}
                    cap = fig.get("caption")
                    if isinstance(cap, str) and cap:
                        item["caption"] = cap
                    into.append(item)
    for v in root.values():
        _walk_citation_figures(v, into)


def extract_figures(article: dict) -> list[dict]:
    output = article.get("output") or {}
    sa = output.get("structured_article")
    citation_figs: list[dict] = []
    _walk_citation_figures(sa, citation_figs)
    text_figs: list[dict] = []
    if isinstance(output.get("text"), str):
        text_figs = extract_figures_from_text(output["text"])
    seen, result = set(), []
    for fig in citation_figs + text_figs:
        key = (fig.get("name", ""), fig["url"])
        if key in seen:
            continue
        seen.add(key)
        result.append(fig)
    return result


def resolve_visual_tags(text: str, figures: list[dict]) -> str:
    if not figures:
        return text
    lookup = {}
    for f in figures:
        n = f.get("name")
        if n and n not in lookup:
            lookup[n] = f

    def repl(m: re.Match) -> str:
        name = m.group(1)
        f = lookup.get(name)
        if not f:
            return m.group(0)
        alt = f"{f['name']}: {f['caption']}" if f.get("caption") else f["name"]
        return f"![{alt}]({f['url']})"

    return VISUAL_TAG_RE.sub(repl, text)


# ---------- citations / bibtex ----------

def _strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", text)).strip()


def _normalize_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    return re.sub(r"[.);,\s]+$", "", re.sub(r"^doi:", "", doi, flags=re.I)).lower()


def _doi_from_text(text: str) -> str | None:
    m = DOI_RE.search(text or "")
    return m.group(0) if m else None


def _title_from_citation(c: str) -> str | None:
    m = re.search(r"\. ([^.]+)\. [A-Z][A-Za-z ]+\.", c)
    return m.group(1) if m else None


def _normalize_structured_citation(c: dict) -> dict | None:
    md = c.get("metadata") or {}
    detail = md.get("citation_detail") or {}
    raw = c.get("citation")
    raw_citation = _strip_html(raw) if isinstance(raw, str) else ""
    title = detail.get("title") or (_title_from_citation(raw_citation) if raw_citation else None)
    href = detail.get("href")
    doi = _normalize_doi(detail.get("doi") or _doi_from_text(raw_citation))
    if not raw_citation and not title and not href and not doi:
        return None
    figs_raw = (md.get("content_metadata") or {}).get("figures") or []
    figures = []
    for f in figs_raw:
        if isinstance(f.get("url"), str) and f["url"]:
            item = {"name": f.get("name") or "", "url": f["url"]}
            if isinstance(f.get("caption"), str) and f["caption"]:
                item["caption"] = f["caption"]
            figures.append(item)
    rec = {
        "key": "",
        "citation": raw_citation,
        "title": title,
        "href": href,
        "doi": doi,
        "pmid": detail.get("pmid") if isinstance(detail.get("pmid"), int) else None,
        "repository": detail.get("repository"),
        "published": detail.get("dt_published"),
        "authors": detail.get("authors_string"),
        "journal": detail.get("journal_name"),
        "publicationInfo": detail.get("publication_info_string"),
        "pageImage": (figures[0]["url"] if figures else None),
    }
    if figures:
        rec["figures"] = figures
    return {k: v for k, v in rec.items() if v not in (None, "")}


def _walk_structured_citations(root: Any, into: list[dict]) -> None:
    if isinstance(root, list):
        for x in root:
            _walk_structured_citations(x, into)
        return
    if not isinstance(root, dict):
        return
    citations = root.get("citations")
    if isinstance(citations, list):
        for c in citations:
            if isinstance(c, dict):
                norm = _normalize_structured_citation(c)
                if norm:
                    into.append(norm)
    for v in root.values():
        _walk_structured_citations(v, into)


def _markdown_citations(text: str) -> list[dict]:
    out: list[dict] = []
    for m in MARKDOWN_LINK_RE.finditer(text or ""):
        title = _strip_html(m.group(1))
        href = m.group(2)
        out.append({
            "key": "",
            "citation": title,
            "title": title,
            "href": href,
            "doi": _normalize_doi(_doi_from_text(href) or _doi_from_text(title)),
        })
    for m in DOI_RE.finditer(text or ""):
        doi = _normalize_doi(m.group(0))
        if not doi:
            continue
        out.append({
            "key": "",
            "citation": f"doi:{doi}",
            "doi": doi,
            "href": f"https://doi.org/{doi}",
        })
    return [{k: v for k, v in c.items() if v not in (None, "")} for c in out]


def _dedupe_key(c: dict) -> str:
    parts = [
        (c.get("doi") or "").lower(),
        str(c.get("pmid") or ""),
        re.sub(r"#page=\d+$", "", (c.get("href") or "")).lower(),
        (c.get("title") or "").lower(),
        (c.get("citation") or "").lower(),
    ]
    return "|".join(p for p in parts if p)


def _sanitize_key(v: str) -> str:
    return re.sub(r"[^A-Za-z0-9:_-]+", "", v)


def _year_from_date(d: str | None) -> str | None:
    if not d:
        return None
    m = re.search(r"\d{4}", d)
    return m.group(0) if m else None


def _assign_keys(citations: list[dict]) -> list[dict]:
    used: dict[str, int] = {}
    out = []
    for i, c in enumerate(citations):
        author = (c.get("authors") or "").split(",")[0].split(".")[0] if c.get("authors") else (c.get("repository") or "oe")
        year = _year_from_date(c.get("published")) or ""
        title_word = ""
        if c.get("title"):
            tw = re.search(r"[A-Za-z0-9]+", c["title"])
            title_word = tw.group(0) if tw else ""
        base = _sanitize_key(f"{author}{year}{title_word}") or f"oe{i + 1}"
        n = used.get(base, 0)
        used[base] = n + 1
        c2 = dict(c)
        c2["key"] = base if n == 0 else f"{base}{n + 1}"
        out.append(c2)
    return out


def extract_citations(article: dict, answer_text: str = "") -> list[dict]:
    output = article.get("output") or {}
    sa = output.get("structured_article")
    structured: list[dict] = []
    _walk_structured_citations(sa, structured)
    candidates = structured + _markdown_citations(answer_text)
    seen, unique = set(), []
    for c in candidates:
        k = _dedupe_key(c)
        if k in seen:
            continue
        seen.add(k)
        unique.append(c)
    return _assign_keys(unique)


# crossref

def _fetch_crossref(url: str) -> dict | None:
    headers = {
        "accept": "application/json",
        "user-agent": "openevidence-skill/1.0 (https://github.com/htlin222/openevidence-mcp)",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {}
        return None
    except (urllib.error.URLError, TimeoutError):
        return None


def _crossref_by_doi(doi: str, mailto: str | None) -> dict | None:
    q = {"mailto": mailto} if mailto else {}
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='')}"
    if q:
        url += "?" + urllib.parse.urlencode(q)
    j = _fetch_crossref(url)
    return (j or {}).get("message")


def _crossref_by_biblio(query: str, mailto: str | None) -> dict | None:
    params = {"rows": "1", "query.bibliographic": query}
    if mailto:
        params["mailto"] = mailto
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    j = _fetch_crossref(url)
    items = ((j or {}).get("message") or {}).get("items") or []
    return items[0] if items else None


def _title_similarity(a: str, b: str) -> float:
    norm = lambda s: re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
    la = set(norm(a).split())
    lb = set(norm(b).split())
    if not la or not lb:
        return 0.0
    return len(la & lb) / max(len(la), len(lb))


def validate_with_crossref(citations: list[dict], mailto: str | None) -> list[dict]:
    out = []
    for c in citations:
        rec = dict(c)
        try:
            if c.get("doi"):
                work = _crossref_by_doi(c["doi"], mailto)
                if work is None:
                    rec["crossref"] = {"status": "error", "method": "doi"}
                elif not work:
                    rec["crossref"] = {"status": "not_found", "method": "doi", "doi": c["doi"]}
                else:
                    title = (work.get("title") or [None])[0]
                    sim = _title_similarity(c["title"], title) if (title and c.get("title")) else None
                    rec["crossref"] = {
                        "status": "validated", "method": "doi",
                        "doi": work.get("DOI"), "title": title,
                        "similarity": sim, "work": work,
                    }
            elif c.get("title"):
                work = _crossref_by_biblio(c["title"], mailto)
                if not work:
                    rec["crossref"] = {"status": "not_found", "method": "bibliographic"}
                else:
                    title = (work.get("title") or [None])[0]
                    sim = _title_similarity(c["title"], title) if title else 0.0
                    rec["crossref"] = {
                        "status": "candidate" if sim >= 0.7 else "not_found",
                        "method": "bibliographic",
                        "doi": work.get("DOI"), "title": title,
                        "score": work.get("score"), "similarity": sim, "work": work,
                    }
            else:
                rec["crossref"] = {"status": "skipped", "method": "none",
                                   "message": "No DOI or title to validate."}
        except Exception as e:
            rec["crossref"] = {"status": "error", "method": "doi" if c.get("doi") else "bibliographic", "message": str(e)}
        out.append(rec)
    return out


def _bib_escape(v: str) -> str:
    return v.replace("\\", "\\\\").replace("{", "").replace("}", "")


def _first_value(values: list[str] | None) -> str | None:
    if not values:
        return None
    for v in values:
        if v and v.strip():
            return v
    return None


def _crossref_year(work: dict | None) -> str | None:
    if not work:
        return None
    for k in ("issued", "published", "published-print", "published-online"):
        parts = (work.get(k) or {}).get("date-parts") or []
        if parts and parts[0] and isinstance(parts[0][0], int):
            return str(parts[0][0])
    return None


def _crossref_authors(work: dict | None) -> str | None:
    if not work:
        return None
    authors = work.get("author") or []
    out = []
    for a in authors:
        if a.get("family") and a.get("given"):
            out.append(f"{a['family']}, {a['given']}")
        elif a.get("name"):
            out.append(a["name"])
        elif a.get("family"):
            out.append(a["family"])
        elif a.get("given"):
            out.append(a["given"])
    return " and ".join(out) if out else None


def citations_to_bibtex(citations: list[dict]) -> str:
    out = []
    for c in citations:
        cr = c.get("crossref") or {}
        work = cr.get("work") if cr.get("status") in ("validated", "candidate") else None
        ctype = "article" if (work and work.get("type") == "journal-article") or c.get("journal") or c.get("doi") else (
            "inproceedings" if work and work.get("type") == "proceedings-article" else "misc")
        fields = []
        def add(name: str, value: str | None) -> None:
            if value and str(value).strip():
                fields.append(f"  {name} = {{{_bib_escape(str(value).strip())}}},")
        add("title", _first_value((work or {}).get("title")) if work else c.get("title"))
        add("author", _crossref_authors(work) or c.get("authors"))
        add("journal", _first_value((work or {}).get("container-title")) if work else c.get("journal"))
        add("year", _crossref_year(work) or _year_from_date(c.get("published")))
        add("volume", (work or {}).get("volume"))
        add("number", (work or {}).get("issue"))
        add("pages", (work or {}).get("page"))
        add("doi", (work or {}).get("DOI") or c.get("doi"))
        add("url", (work or {}).get("URL") or c.get("href"))
        add("publisher", (work or {}).get("publisher") or c.get("repository"))
        add("note", c.get("publicationInfo"))
        body = "\n".join(fields)
        out.append(f"@{ctype}{{{c['key']},\n{body}\n}}")
    return "\n\n".join(out)


# ---------- artifacts ----------

def _sanitize_path_segment(v: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", v)


def _ext_from_url(url: str) -> str:
    try:
        path = urllib.parse.urlparse(url).path
        dot = path.rfind(".")
        if dot != -1:
            ext = path[dot:].lower().split("?")[0].split("#")[0]
            if re.match(r"^\.[a-z0-9]{2,5}$", ext):
                return ext
    except Exception:
        pass
    return ".jpg"


def _download_figures(figures: list[dict], figures_dir: Path) -> None:
    if not figures:
        return
    figures_dir.mkdir(parents=True, exist_ok=True)
    used: dict[str, int] = {}
    for fig in figures:
        try:
            base = _sanitize_path_segment(fig.get("name") or "figure")
            n = used.get(base, 0)
            used[base] = n + 1
            ext = _ext_from_url(fig["url"])
            filename = f"{base}{ext}" if n == 0 else f"{base}_{n + 1}{ext}"
            dest = figures_dir / filename
            req = urllib.request.Request(fig["url"], headers={"user-agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as resp:
                dest.write_bytes(resp.read())
            fig["localPath"] = str(dest)
        except Exception:
            continue


def artifact_root() -> Path:
    return Path(os.environ.get("OE_ARTIFACT_DIR") or (Path.cwd() / "oe-artifacts")).expanduser()


def save_artifacts(article: dict, *, validate_crossref: bool, mailto: str | None) -> dict:
    article_id = str(article.get("id") or "unknown-article")
    out_dir = artifact_root() / _sanitize_path_segment(article_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    answer = extract_answer_text(article) or ""
    figures = extract_figures(article)
    resolved_answer = resolve_visual_tags(answer, figures)
    citations = extract_citations(article, answer)

    if validate_crossref:
        citations = validate_with_crossref(citations, mailto)
    else:
        citations = [{**c, "crossref": {"status": "skipped", "method": "none"}} for c in citations]

    bibtex = citations_to_bibtex(citations)

    article_path = out_dir / "article.json"
    answer_path = out_dir / "answer.md"
    citations_json = out_dir / "citations.json"
    bib_path = out_dir / "citations.bib"
    crossref_path = out_dir / "crossref-validation.json"
    figures_json = out_dir / "figures.json"
    figures_dir = out_dir / "figures"

    article_path.write_text(json.dumps(article, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    answer_path.write_text(resolved_answer, encoding="utf-8")
    citations_json.write_text(json.dumps(citations, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    bib_path.write_text(bibtex + "\n", encoding="utf-8")
    crossref_path.write_text(json.dumps(
        [{"key": c["key"], "title": c.get("title"), "doi": c.get("doi"),
          "href": c.get("href"), "crossref": c.get("crossref")} for c in citations],
        indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    _download_figures(figures, figures_dir)
    figures_json.write_text(json.dumps(figures, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return {
        "artifactDir": str(out_dir),
        "articlePath": str(article_path),
        "answerPath": str(answer_path),
        "citationsJsonPath": str(citations_json),
        "bibPath": str(bib_path),
        "crossrefValidationPath": str(crossref_path),
        "figuresJsonPath": str(figures_json),
        "bibtex": bibtex,
        "citationCount": len(citations),
        "crossrefValidatedCount": sum(1 for c in citations if (c.get("crossref") or {}).get("status") == "validated"),
        "figureCount": len(figures),
    }


def format_artifacts(artifacts: dict | None, include_bibtex: bool) -> dict | None:
    if artifacts is None:
        return None
    if include_bibtex:
        return artifacts
    return {k: v for k, v in artifacts.items() if k != "bibtex"}


# ---------- API actions ----------

def cmd_auth_status(jar: CookieJar) -> dict:
    status, body = _request(jar, "GET", "/api/auth/me")
    if status != 200:
        return {
            "authenticated": False,
            "statusCode": status,
            "message": f"OpenEvidence auth is not active (status {status}). Refresh cookies.json.",
        }
    return {"authenticated": True, "statusCode": status, "user": json.loads(body.decode("utf-8"))}


def cmd_history(jar: CookieJar, limit: int, offset: int, search: str | None) -> Any:
    q = {"limit": str(limit), "offset": str(offset)}
    if search:
        q["search"] = search
    return get_json(jar, f"/api/article/list?{urllib.parse.urlencode(q)}")


def cmd_article(jar: CookieJar, article_id: str, *, save: bool, crossref: bool,
                include_bibtex: bool, mailto: str | None) -> dict:
    article = get_json(jar, f"/api/article/{article_id}")
    figures = extract_figures(article)
    answer_raw = extract_answer_text(article)
    artifacts = save_artifacts(article, validate_crossref=crossref, mailto=mailto) if save else None
    return {
        "article_id": article_id,
        "extracted_answer_raw": resolve_visual_tags(answer_raw, figures) if answer_raw else None,
        "figures": figures,
        "artifacts": format_artifacts(artifacts, include_bibtex),
    }


def wait_for_article(jar: CookieJar, article_id: str, timeout_ms: int, interval_ms: int) -> dict:
    started = time.time()
    while True:
        article = get_json(jar, f"/api/article/{article_id}")
        status = str(article.get("status") or "").lower()
        if status and status not in PENDING_STATUSES:
            return article
        if (time.time() - started) * 1000 > timeout_ms:
            return article
        time.sleep(interval_ms / 1000)


def cmd_ask(jar: CookieJar, *, question: str, original_article_id: str | None,
            wait_for_completion: bool, timeout_sec: int, poll_interval_ms: int,
            disable_caching: bool, personalization_enabled: bool, article_type: str,
            variant_configuration_file: str, save: bool, crossref: bool,
            include_bibtex: bool, mailto: str | None) -> dict:
    body: dict = {
        "article_type": article_type,
        "inputs": {
            "variant_configuration_file": variant_configuration_file,
            "attachments": [],
            "question": question,
            "use_gatekeeper": True,
        },
        "personalization_enabled": personalization_enabled,
        "disable_caching": disable_caching,
    }
    if original_article_id:
        body["original_article"] = original_article_id

    created = post_json(jar, "/api/article", body)
    article_id = str(created.get("id") or "")
    if not article_id:
        raise SystemExit("OpenEvidence returned no article id.")
    if not wait_for_completion:
        return {"created": created, "article_id": article_id,
                "note": "Article created. Poll with `oe.py article <id>`."}

    article = wait_for_article(jar, article_id, timeout_sec * 1000, poll_interval_ms)
    figures = extract_figures(article)
    answer_raw = extract_answer_text(article)
    artifacts = save_artifacts(article, validate_crossref=crossref, mailto=mailto) if save else None
    return {
        "article_id": article_id,
        "status": str(article.get("status") or ""),
        "extracted_answer_raw": resolve_visual_tags(answer_raw, figures) if answer_raw else None,
        "figures": figures,
        "artifacts": format_artifacts(artifacts, include_bibtex),
    }


# ---------- CLI ----------

def _emit(obj: Any) -> None:
    json.dump(obj, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(prog="oe", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("auth-status", help="Check session validity (oe_auth_status)")

    p_hist = sub.add_parser("history", help="List question history (oe_history_list)")
    p_hist.add_argument("--limit", type=int, default=20)
    p_hist.add_argument("--offset", type=int, default=0)
    p_hist.add_argument("--search", default=None)

    p_art = sub.add_parser("article", help="Fetch article + save artifacts (oe_article_get)")
    p_art.add_argument("article_id")
    p_art.add_argument("--no-save", action="store_true", help="Do not write artifacts")
    p_art.add_argument("--no-crossref", action="store_true", help="Skip Crossref validation")
    p_art.add_argument("--no-bibtex", action="store_true", help="Omit bibtex from response")
    p_art.add_argument("--mailto", default=os.environ.get("OE_CROSSREF_MAILTO"))

    p_ask = sub.add_parser("ask", help="Submit a new question (oe_ask)")
    p_ask.add_argument("question")
    p_ask.add_argument("--follow-up", dest="original_article_id", default=None,
                       help="UUID to extend an existing thread")
    p_ask.add_argument("--no-wait", action="store_true")
    p_ask.add_argument("--timeout", type=int, default=120, help="Seconds to wait for completion")
    p_ask.add_argument("--poll-interval-ms", type=int, default=1200)
    p_ask.add_argument("--disable-caching", action="store_true")
    p_ask.add_argument("--personalization", action="store_true")
    p_ask.add_argument("--article-type", default=DEFAULT_ARTICLE_TYPE)
    p_ask.add_argument("--variant", default="prod")
    p_ask.add_argument("--no-save", action="store_true")
    p_ask.add_argument("--no-crossref", action="store_true")
    p_ask.add_argument("--no-bibtex", action="store_true")
    p_ask.add_argument("--mailto", default=os.environ.get("OE_CROSSREF_MAILTO"))

    args = parser.parse_args()

    cookies_path = resolve_cookies_path()
    jar = CookieJar.load(cookies_path)
    auth = cmd_auth_status(jar)
    if not auth["authenticated"]:
        _emit({"error": auth["message"], "statusCode": auth["statusCode"], "cookies_path": str(cookies_path)})
        sys.exit(2)

    if args.cmd == "auth-status":
        _emit(auth)
        return
    if args.cmd == "history":
        _emit(cmd_history(jar, args.limit, args.offset, args.search))
        return
    if args.cmd == "article":
        _emit(cmd_article(
            jar, args.article_id,
            save=not args.no_save,
            crossref=not args.no_crossref,
            include_bibtex=not args.no_bibtex,
            mailto=args.mailto,
        ))
        return
    if args.cmd == "ask":
        _emit(cmd_ask(
            jar,
            question=args.question,
            original_article_id=args.original_article_id,
            wait_for_completion=not args.no_wait,
            timeout_sec=args.timeout,
            poll_interval_ms=args.poll_interval_ms,
            disable_caching=args.disable_caching,
            personalization_enabled=args.personalization,
            article_type=args.article_type,
            variant_configuration_file=args.variant,
            save=not args.no_save,
            crossref=not args.no_crossref,
            include_bibtex=not args.no_bibtex,
            mailto=args.mailto,
        ))
        return


if __name__ == "__main__":
    main()
