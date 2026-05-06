---
type: data
name: nejm-issue
description: "Public-safe NEJM issue metadata triage. Superseded 2026-05-06 by the unified journal-download skill which now covers AIM, NEJM, JAMA, BMJ via per-journal policy. Retained as a thin alias so existing /nejm-issue invocations still resolve. Downloads are limited to public/open-access material; subscription workflows are private and not documented here."
argument-hint: "[--url URL]"
---

# /nejm-issue - Metadata Triage (superseded)

Superseded 2026-05-06 by the unified `journal-download` skill, which carries the same public-safe policy boundary across every tracked publisher (AIM weekly, NEJM weekly, JAMA weekly, BMJ weekly) via per-journal config. Prefer `/journal-download` (or any of its trigger phrases like 「抓 NEJM」/「bundle journal issue」) for new work; `/nejm-issue` remains as a thin alias.

Use this skill to inspect a public NEJM table of contents, collect metadata, and prioritize reading candidates. This public version must not describe private queues, database endpoints, authenticated downloaders, cookies, or subscription automation.

## Allowed

- Read public TOC metadata.
- Classify articles by type and clinical relevance.
- Save title, DOI, URL, article type, abstract when publicly visible, and access status.
- Download only if a public/OA download right is explicit.

## Not Allowed

- Subscription PDF/video download instructions.
- Authenticated browser or cookie workflows.
- Private queue or scheduler details.
- Private database DSNs.

When in doubt, metadata-only.

