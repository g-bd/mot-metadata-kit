---
name: mot-metadata
description: Create, validate and report on the metadata file required by the Israel Ministry of Transport "נוהל הכנה, תיעוד והפצה של קבצי מידע תחבורתי" (v1.3, 15/05/2024) for ANY dataset folder (CSV incl. UTF-16/Windows-1255/gzip, Excel xlsx+xls, Parquet, shapefile, GeoJSON, GeoPackage, ZIP incl. nested zips and GTFS). Scans the folder, asks the user only what cannot be derived from the files (publisher, contact, title, description, coverage, dataset kind), writes <dataset>-metadata.json + .xlsx + .pdf in the MoT layout, and produces a Hebrew RTL validation report (metadata-report.html) listing every gap against the נוהל. Use when the user says "metadata", "מטא-דאטה", "מטאדאטה", "נוהל הפצת מידע", "data distribution guidelines", "prepare a dataset for the ministry / שולחן עגול / data.gov.il", "check my metadata file", "validate metadata.xlsx", or wants to package transport data for distribution. For on-board surveys use mot-onboard, for monthly traffic-sensor packages use mot-sensors (both build on this skill).
---

# mot-metadata — MoT dataset metadata (create · validate · report)

The נוהל does **not** judge the data. It only defines how a dataset must be *documented and packaged*:
a single metadata file (Excel / JSON / CSV) with a header (Table 1), a survey supplement when the
dataset is a statistical survey (Table 2), one block per data file (Table 3) and one row per field
(Table 4), plus naming rules (§5.7) and a ZIP package (§5.2). This skill therefore checks
**completeness of the metadata and its consistency with the files** — never the correctness of the data.

Full dictionary: `references/guidelines-v1.3.md`. Machine-readable: `references/spec.json`.

## What you can run

`scripts/mot_metadata.py` (Python 3.10+). Dependencies install themselves: the script pip-installs `openpyxl` on
first run if missing; `setup` also installs the optional `pyshp` / `pyproj` and reports whether a Chromium browser
(for PDF) was found. Run `setup` once on a new machine before anything else.

| Command | What it does |
|---|---|
| `setup` | Verify Python ≥ 3.10, install missing packages (pip, falls back to `--user`), check for Chrome/Edge. |
| `scan <folder>` | Inventory: files, real sizes (unit + exact bytes), dates, CSV/XLSX headers + inferred types + low-cardinality values, Parquet schema + row count (pyarrow), shapefile fields/CRS/bbox/geometry, ZIP members (GTFS detected), documents. Writes `scan.json`. |
| `init <folder> [--profile onboard\|sensors]` | Writes `metadata-config.json` — the intake template with every file/field pre-listed and a `_questions` list. |
| `build <folder> [--profile P] [--from old-metadata.xlsx] [--name NAME] [--formats json,xlsx,pdf,csv] [--force]` | Scan + config (+ profile) → `<name>-metadata.json/.xlsx/.pdf` + `metadata-report.html` + `findings.json`. Unanswered required items are written as `TODO` and listed. `--from` seeds the config from an existing (flawed) metadata file so a corrected one is regenerated against the real files. |
| `validate <folder\|metadata-file> [--metadata F] [--profile P] [--kind survey\|monitoring\|...] [--deep values,temporal,joins,zones\|all] [--out-dir D]` | Checks an existing metadata .xlsx/.json against the dictionary, the profile and the folder. Exit code 1 when errors exist. Writes the report + findings; `--out-dir` is created if it does not exist. |
| `render <metadata.json\|xlsx> --pdf out.pdf` | Re-render the metadata document as Hebrew PDF/HTML. |
| `package <folder> [--metadata F] [--out zip]` | Build the הפצה ZIP named by `Dataset file` (Files list + metadata files + Related documents, shapefile sidecars included) and write `package-checklist.json` (zip name = Dataset file, everything listed is present, nothing listed is missing, what in the folder was left out). |
| `scripts/spec_update.py <new spec pdf/docx> [--profile P]` | When MoT publishes a new version: extracts the document's key tables and writes a markdown diff against the bundled dictionary (new keys, keys no longer found, status/kind changes, new expected files/fields) with a JSON snippet to paste. Nothing is changed automatically — you approve, then edit `references/*.json` + `.md` + `spec-sources.json`. |
| `scripts/mot_fix.py` | Mechanical fixes driven by the audit — see the `mot-fix` skill. |

**Embedding in a pipeline**: `scripts/mot_hook.py <folder> --json [--config F] [--formats json,xlsx,pdf]` never
raises and prints one JSON result line (`ok | todo | skipped | error`, plus `todo` / `errors` / `warnings` counts and the
paths written). Config resolution: `--config`, then `<folder>/metadata-config.json`, `$MOT_METADATA_CONFIG`, then a
`metadata-config.json` up to three levels above the folder. A pipeline that makes its own dataset should keep ONE
config template with `{placeholders}`, fill it from the run (period, versions, layer names, counts) and pass it with
`--config` — no interview needed. Key `files` entries by basename so the same config documents the run folder and the
shipped package layout. A layer whose `.prj` is missing or empty gets its SRS inferred from the coordinates
(`crs_inferred` info); a layer the scanner could not read at all is reported as `layer_unread` first (usually `pyshp`
missing in the host environment).

**Doc harvest**: `scan`/`build` also read every README / .md / .txt / .html / .docx / .pdf in the folder. Lines shaped
`field | description` (schema tables) become the field's Description automatically and are flagged in the report
("תיאור נלקח אוטומטית מהתיעוד – יש לאמת"); other mentions are attached as `_hints` in the `init` template so you
can write the description from context instead of asking. Still ask when the documentation is silent.
| `check-spec [--online]` | Shows the bundled spec versions; `--online` tries to detect a newer version on gov.il (gov.il blocks plain HTTP clients — if it fails, open the page in a browser and compare the version/date with `references/spec-sources.json`). |

Severity in the report: **שגיאה** = the נוהל is violated (must fix before distribution), **אזהרה** =
probably wrong/incomplete, **הערה** = suggestion. The report is Hebrew RTL; tables are LTR.

**Deep checks** (`--deep`, opt-in, they read the data files): `values` (documented `Values` vs the
codes present — open key columns are skipped, their join is what means something), `temporal`
(`Temporal coverage` vs the real date range), `joins` (declared keys: orphans), `zones` (a profile
that declares a zones layer: find the layer's key from the profile's candidate names, then resolve
the questionnaire's zone codes against it). `all` runs the four.

**Buckets in `findings.json`**: a finding may carry `"bucket": "kit_format_exempt"` — the FORMAT
itself does not ask for this (a delivery zip's fields, a counts-only package's `obod.csv`/`zones.zip`,
a field the format forbids in the distribution file). Counted in `summary.buckets`, shown in the
report as "הפורמט אינו דורש", never blocking. `summary.todo` carries the build's TODO list, so a
caller does not have to scrape stdout.

**Unanswered is not the same as unknown.** A required TEXT key may be answered
`לא ידוע` / `לא ידוע — לא תועד במקורות` / `unknown — not documented in the sources`
(`references/spec.json → unknown_tokens`): the kit treats it as **answered** — no `todo` — records an
`info` `value_unknown_documented` so it stays visible, and the report prints it under its own
heading rather than in the TODO list. An empty cell, `TODO`, `?`, `N/A` are **not** answers and stay
errors (`value_placeholder`); a key with a shape (date / e-mail / URL) or a closed vocabulary cannot
be answered this way at all. Write the token only when the user says the value is unknowable — it is
their statement, not a way to close a finding.

## Workflow A — create metadata for a folder

1. **Confirm the folder** with the user (absolute path). Ask whether sub-folders belong to the dataset
   (`"recursive": true` in the config) and whether any file should be excluded (working files, old
   versions, a pre-built distribution zip that duplicates the loose files).
2. **Spec freshness**: run `check-spec`. If the user has web access, open
   `references/spec-sources.json → page` and compare the published version/date; if newer, tell the
   user the bundled dictionary may be outdated (still proceed).
3. **Scan**: `scan <folder>`. Read `scan.json` (incl. `doc_hints` harvested from the README / PDFs) and open the
   documentation yourself for anything the harvest missed — it usually contains the field descriptions you need.
   Sub-folders are scanned by default; exclude working folders (old versions, exports, backups) via `exclude`.
4. **Intake — ask only what the files cannot tell you.** Run `init` to get the template, then ask in
   chat (in the user's language; Hebrew answers are expected in the metadata) and write the answers
   into `metadata-config.json`:
   - `dataset_kind`: **survey** (→ Table 2 survey block becomes mandatory) / monitoring /
     administrative / gis / model / other. If the user does not know, explain: "a statistical survey
     = a sample measured and expanded to a population"; otherwise it is not a survey.
   - `header`: Publisher, Contact (+ email), Author (only if different from the publisher), Title,
     Description (2–4 lines: what, why, how collected, completeness), Keywords (≥3; prefer Appendix A
     terms listed in `spec.json → keywords`), Temporal coverage, Spatial coverage, Version, Frequency
     of update, License / Legal constrains / Data quality when relevant.
     **Spatial coverage** is written the way the נוהל asks — ארצי / שם מטרופולין / שם יישוב — or by
     the official administrative name of the area (מחוז, אזור יהודה ושומרון). It never carries the
     wording "the occupied territories" (השטחים הכבושים) in any language, whoever asks for it: the
     build writes `TODO` instead and records the refusal (`_meta.refused_wording`, shown in the
     report), and `validate` reports an existing file that carries it as the error
     `spatial_coverage_wording`. The terms live in `spec.json → spatial_coverage_wording`.
   - `files.<name>.File description` for every data file, and `fields.<field>.Description` for every
     field the README did not explain. Units go in `Comments`; coded fields get `Values`
     (value / label). Date/Time fields get their format in `Comments`.
   - `keys`: `file.field -> file.field` links between files (propose the ones you can see:
     identical id-named columns; confirm with the user).
   Do not ask for anything the scan provides (types, sizes, dates, row counts, CRS, bbox, geometry type).
5. **Build**: `build <folder> [--profile ...] --name <short_latin_name>`. The dataset name becomes the
   ZIP name (`Dataset file`) and the metadata file name `<name>-metadata.*` as the נוהל prescribes.
6. **Review the report** (`metadata-report.html`, summarize it in Hebrew for the user). Then present every
   remaining `TODO` and open question **as a numbered list in chat** (1., 2., 3. …), one line each, grouped
   header → files → fields, so the user can answer inline ("1: משרד התחבורה, 2: ..."). Write the answers into
   `metadata-config.json` and `build --force` again. Iterate until errors = 0. Never leave a TODO silently —
   if the user says "I don't know", record their words in the value or drop the optional key, and say so. Warnings about naming rules (§5.7: Latin names, no spaces/special characters,
   consistent case style) are for the user to decide — renaming files/columns is a data change, not
   a metadata change.
7. **Deliver**: list the produced files and the remaining warnings. Offer `package` to build the הפצה ZIP
   (`Dataset file` name) with its checklist — the נוהל expects data + metadata + documents in one archive.

## Workflow B — validate an existing metadata file

1. Locate the metadata file (`*metadata*.xlsx` / `.json`; ask if several). Decide the dataset kind
   (ask, or infer from the profile: on-board = survey).
2. `validate <folder> --metadata <file> [--profile ...] [--kind ...]`.
3. Explain the findings in Hebrew, grouped like the report (header / survey block / files / fields /
   keys / folder match / naming / profile). Quote the נוהל rule for each error type when useful
   (`references/guidelines-v1.3.md`).
4. If the user wants it fixed: `build <folder> --from <file> [--profile ...]` regenerates a corrected
   document (keeps their descriptions, re-derives everything structural from the files), then
   continue with Workflow A step 6. Never overwrite the user's original file — the new one is
   `<name>-metadata.*`; let them replace it. For defects in the *files* themselves (names with invisible
   characters, cp1255 encoding, missing .cpg) hand over to the `mot-fix` skill (dry-run first).

## Workflow C — a new version of a spec was published

1. Download the new PDF/DOCX. Run `scripts/spec_update.py <file> [--profile onboard|sensors]` → `*-spec-diff.md`.
2. Walk the diff with the user: new keys (usually additions), keys not found (renamed?), status changes.
3. Apply approved changes to `references/spec.json` or the profile's `profile.json` (+ the markdown twin), bump
   version/date in `references/spec-sources.json`, re-run the four regression folders (see project CLAUDE.md).

## Things the validator catches (so you can explain them)

- Missing / `TODO` required header keys; survey block absent for a survey; dates not `dd/mm/yyyy`
  (Excel date cells!); `Dataset file` without `.zip`; key spelled in the wrong case (`version`,
  `File Fields`); unknown keys (typos).
- `Files list` ≠ `Files` blocks ≠ files actually in the folder (including files present only with
  invisible RLM/ZWSP characters in their name); related documents that do not exist.
- Per file: missing format/description/fields; GIS layers without Spatial reference system /
  Geographic bounding / Geographic type; CRS or geometry type contradicting the `.prj`/`.shp`;
  format vs extension.
- Per field: documented but absent in the file (and vice versa), case/space differences, unknown
  type, implausible type (e.g. `Integer` but value `23א`), duplicates, coded fields without
  `Values`, Date/Time fields without a format comment, naming-rule violations, mixed case styles.
- Key list: syntax `a.x -> b.y`, files/fields that do not exist, duplicates, stray spaces/zero-width
  characters.
- Profile: expected files/fields/keys of the domain format (see mot-onboard / mot-sensors).
- **Hebrew written as question marks.** A text column whose values are `????` or U+FFFD, or whose
  Hebrew is cp1252 mojibake, is reported per column with a count and examples
  (`text_lost_as_question_marks` / `hebrew_mojibake`, both errors); the same check runs over the
  metadata's own values (`metadata_value_question_marks`). Those characters are gone - nothing
  downstream can recover them - so the fix is always to re-export from the source in UTF-8. Every
  json/xlsx/csv/html the kit writes is read back and its Hebrew must be there character for
  character (`output_roundtrip_failed` = the kit's own bug, exit 2), and the PDF's first pages must
  yield the title's Hebrew to a text extractor (`pdf_hebrew_not_rendered`; `--allow-unverified-pdf`
  accepts it anyway, still reported).

## Uploaded files instead of a folder (ChatGPT / Claude.ai / Claude Desktop)

When the user uploads files or a ZIP to the chat instead of pointing at a local folder: extract everything into one
working directory in the code sandbox (e.g. `/mnt/data/dataset/`), run the same commands against it, and return the
produced `metadata.xlsx` / `.json` / `metadata-report.html` as downloadable files. Notes for sandboxes without
network access (ChatGPT Code Interpreter): pip auto-install cannot run, but `openpyxl` is preinstalled so the core
works; shapefile/CRS details degrade gracefully when `pyshp`/`pyproj` are absent (the report says so); PDF is skipped
(no browser) — deliver the HTML instead. The intake conversation is identical.

## No code execution available? (claude.ai / ChatGPT chat)

Do the same by hand: ask the user for the folder listing and the header row of each file (or let
them paste `scan.json` produced elsewhere), then write the metadata following
`references/guidelines-v1.3.md` tables 1–4 in the Excel layout of `references/examples/`
(column A = key, column B = value, blocks continue on the next rows with an empty A; the `Files`
section starts with a `Files` row; every file starts with `File name` and its fields follow a
`File fields` header row: name | type | description | comments | value | label | comment). Produce
the report as a Hebrew RTL document with the same sections and severities.

## Boundaries

- Never invent publisher/contact/coverage/descriptions — ask, or leave `TODO` and say so.
- Never write "the occupied territories" (השטחים הכבושים / occupied territories) as a Spatial
  coverage, even when told to — name the area by its official designation (see Intake). The kit
  refuses it in `build` and flags it in `validate`; do not work around either.
- Sizes are real: `Size` / `File size` carry the unit that fits (B / KB / MB / GB) **and** the
  exact byte count, e.g. `16.5 MB (17,268,557 bytes)`. Never round a small file down to `0.0`.
  If the user says a required text value cannot be known, write the documented-unknown token
  (see above) at their word; never choose it for them to make a finding go away.
- Never change the user's data files or their original metadata file.
- Traffic counts (ספירות תנועה) are exempt from the נוהל (§6) and use the uniform counts format
  (v3.0 online); this skill does not cover them.
