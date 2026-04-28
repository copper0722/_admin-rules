---
type: data
name: new-folder
description: "Create new vault folder with §10.9 standard AGENTS.md card + _archive/. Use when user says /new-folder, 'create folder', '建資料夾', 'new project', or needs a new vault directory."
---

# New Folder

Create a vault folder with proper card and archive structure.

## Usage

`/new-folder {path}` — path relative to vault root (e.g. `proj/myproject`, `kb/topic`)

## Steps

1. Validate path: must be under vault root (`~/Vault/`). Reject absolute paths or paths outside vault.

2. Create folder:
```bash
mkdir -p ~/Vault/{path}
mkdir -p ~/Vault/{path}/_archive
```

3. Write `~/Vault/{path}/AGENTS.md` using §10.9 template:

```markdown
# {path}/ — {ask user for one-line description}

{Leave empty — agent fills on first entry}

## TODO

## Notes

- {today}: folder created.
```

4. Write `~/Vault/{path}/_archive/AGENTS.md`:

```markdown
# {path}/_archive/ — Archive

Completed, superseded, or historical files from `{path}/`.

## Rules

1. **Entry criteria:** file is completed, superseded, or no longer active.
2. **Unzipped .md = pending review.** Agent reads → extracts useful info → zips.
3. **Zipped = confirmed archived.** Do not unzip unless asked.
4. **No new content here.**

## TODO

## Notes

- {today}: archive card created.
```

5. If path starts with `proj/` → also update `proj/AGENTS.md` table (add new row).

6. Report: folder created, card written, archive ready.

## §10.9 Card Structure Rules

All folder `AGENTS.md` cards MUST have these 2 sections at bottom (fixed order):

1. **## TODO** — uses `/todo` skill format (`{type}:{mode}`). auto = scheduled agents execute, manual = ask Copper.
2. **## Notes** — agent scratchpad: observations, decisions, cross-session memo. Free format.

**Agent behavior:**
- Enter folder → read card → if missing 2 sections → add them (migration on touch)
- TODO: auto items executed by /burn and triggers. Manual items require Copper confirmation.
- Notes: persistent across sessions. No cleanup unless stale.

## Archive Rules (every _archive/)

1. Entry: file completed, superseded, or no longer active.
2. Unzipped .md in _archive/ = pending review. Agent MUST: read → extract useful info → zip.
3. Zipped = confirmed archived. Unsearchable, resource-saving (Law §1.3).
4. No new content created in _archive/.
