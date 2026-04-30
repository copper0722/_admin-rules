---
type: data
name: nejm-issue
description: "Public-safe NEJM issue metadata triage. Downloads are limited to public/open-access material; subscription workflows are private and not documented here."
argument-hint: "[--url URL]"
---

# /nejm-issue - Metadata Triage

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

