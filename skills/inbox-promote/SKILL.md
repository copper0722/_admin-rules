---
type: data
name: inbox-promote
description: "Public-safe sidecar ingestion contract. Private inbox paths, mounts, scripts, and database writes are intentionally omitted."
argument-hint: "[bundle | dry-run]"
---

# /inbox-promote - Public Contract

Promote a human-supplied source bundle into a private sidecar workspace. This public card describes the data-safety contract only.

## Principles

- Save raw input first.
- Do not discard or overwrite source files without archival.
- Derive a stable citation key from DOI, metadata, or human confirmation.
- Block on ambiguous identity.
- Keep binary PDFs, copyrighted full text, credentials, and private paths out of public repos.

## Bundle Shape

```text
{citationKey}/
  source.pdf        # private when copyrighted
  source.md         # private raw extraction unless license permits sharing
  figures/          # private unless license permits sharing
  metadata.json     # provenance, checksum, source URL, access status
  _archive/         # replaced or superseded files
```

## Public Output

Public repos may receive only:

- Provenance stubs.
- Public-safe summaries.
- Open-license source links.
- Workflow status without private paths.

Private runtime chooses actual inboxes, mount points, scripts, and audit backend.

