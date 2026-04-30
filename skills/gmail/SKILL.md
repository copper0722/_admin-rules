---
type: data
name: gmail-secretary
description: "Public-safe email triage policy. Private mailbox automation, token paths, cloud routine state, and account-specific workflows are intentionally omitted."
---

# Gmail Secretary - Public Policy

This public card defines email-triage behavior without exposing private accounts, tokens, paths, scripts, or runtime details.

## Allowed

- Summarize message purpose, deadlines, requested actions, and reply requirements.
- Classify threads as urgent, needs-reply, waiting, FYI, calendar-related, or archive candidate.
- Draft replies for human review.

## Not Allowed In Public Rules

- Account identifiers.
- OAuth/token file paths.
- Browser cookies or session data.
- Private cloud routine paths.
- Mailbox-specific labels or filters that reveal private operations.

Private implementation details must live in the private operations repo.

