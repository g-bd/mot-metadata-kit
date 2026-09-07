---
name: mot-fix
description: Apply the mechanical fixes that a MoT metadata audit (mot-metadata validate → findings.json) points at, safely - file names with invisible characters/spaces/special chars, Windows-1255 CSVs → UTF-8, missing .cpg next to shapefiles, metadata xlsx defects (key casing, zero-width characters, Excel date cells, Dataset file without .zip, duplicate key rows, field names not matching the files), and optional column renames (snake_case / explicit mapping). Dry-run by default, backup of every touched file, change log, never deletes, never touches data values. Use when the user says "fix the files", "תקן את הקבצים", "rename to Latin", "convert to UTF-8", "fix the metadata file", "apply the audit", or after a validation report lists naming/encoding/casing errors. Content gaps (descriptions, survey block, missing files) are NOT fixed here - they go back to mot-metadata intake.
---

# mot-fix — audit-driven mechanical fixes (opt-in)

Companion of `mot-metadata`. Script: `../mot-metadata/scripts/mot_fix.py`.

```
python ../mot-metadata/scripts/mot_fix.py <folder> --metadata <metadata.xlsx> [--profile onboard|sensors]        # dry run → fix-plan.json
python ../mot-metadata/scripts/mot_fix.py <folder> --metadata <metadata.xlsx> --apply                             # execute → _mot_backup_<stamp>/, fix-log.json
python ../mot-metadata/scripts/mot_fix.py <folder> --only columns --snake-case --column-map map.json --apply       # column renames
```

## Fix families (`--only`, default `names,encoding,cpg,metadata`)

| family | what changes | what never changes |
|---|---|---|
| `names` | file names: strip RLM/ZWSP, spaces → `_`, drop `* # % $ & ( ) ,` …; shapefile sidecars renamed together; Files list / Key list in the fixed metadata follow | file contents |
| `encoding` | CSV/TXT detected as Windows-1255 rewritten as UTF-8; `Data encoding` = UTF-8 in the fixed metadata | values, delimiters, line endings |
| `cpg` | writes `<layer>.cpg` (`UTF-8` or `1255`, sniffed from the .dbf) when absent | .dbf itself |
| `metadata` | `version`→`Version`, `File Fields`→`File fields`; zero-width chars removed from every value; ISO/Excel dates → `dd/mm/yyyy`; `Dataset file` gets `.zip`; `Metadata version 1.1` added; duplicate Key list rows dropped; written as `<name>-fixed.xlsx` + `.json` | the original metadata file |
| `columns` (opt-in) | header row renames: invisible chars stripped; `--snake-case` for Latin names; `--column-map {"old":"new"}` for anything else (the only way to replace Hebrew headers); metadata field names follow | cell values, row order |

## Procedure

1. Run `mot-metadata validate` first and read the report with the user. Point at the findings this skill can close:
   `file_name`, `file_name_invisible_chars`, `encoding_note`, `dbf_encoding`, `key_case`, `invisible_chars`,
   `field_name_invisible`, `date_format`, `dataset_zip`, `key_duplicate`, `field_case`, `style_profile`.
2. **Dry run**, then present the plan in chat as a **numbered list** — one action per line, exactly what changes:
   `1. שינוי שם: ‏‏obod.csv → obod.csv` / `2. המרת קידוד: trips.csv Windows-1255 → UTF-8` / `3. מטא-דאטה: version → Version` …
   Ask the user to approve by numbers ("הכל", "1-3", "בלי 4"). Renaming columns or files is a data change that may
   break their own pipelines — an explicit yes is required before `--apply`. Partial approval is real:
   `--apply --actions "1,3-5"` executes only those plan numbers; `--only <families>` narrows by family
   (default: `names,encoding,cpg,metadata,zipnames`).
3. After a **partial** apply the remaining plan numbers are stale (files may have been renamed) — run the dry run
   again before approving more. `--apply`. Confirm the backup folder and `fix-log.json`; then re-run `validate` on `<name>-fixed.xlsx` and show the
   before/after error counts.
4. Hebrew column names: do not invent translations. Ask the user for the Latin names (or derive them from the domain
   format's dictionary — e.g. the OB profile's `expected_files[*].fields`) and pass them with `--column-map`.

## Question marks are not a fixable defect

`mot_fix` re-encodes a file whose bytes are still there (cp1255 -> UTF-8, a missing `.cpg`). It
does NOT touch a value that already reads `????` or U+FFFD: those characters were destroyed by
whatever wrote the file, and inventing replacements would be inventing data. When `validate`
reports `text_lost_as_question_marks`, say so plainly and ask for a re-export from the source.

## Boundaries

- Never deletes; never edits data values; never overwrites the original metadata (writes `-fixed`).
- Leaves content decisions (descriptions, survey block, which files belong to the dataset) to `mot-metadata`.
- Renames inside ZIP archives are out of scope — unpack, fix, repack with `mot_metadata.py package`.
