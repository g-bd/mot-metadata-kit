# Changelog

All notable changes to mot-metadata-kit. Dates are DD/MM/YYYY. The Hebrew guide (`GUIDE-he.html`, section "מה חדש")
carries the same list.

## 0.7.6 — 21/10/2026
- Changelog: this file, and a "מה חדש" section in the Hebrew guide.
- The guide's header shows the full version and the release date; `site/release.py` stamps both.

## 0.7.5 — 20/10/2026
- **`--deep report`** (also in `--deep all`): a sanity check of the survey report PDF against the files. Row counts
  and weight-column sums are looked for in the report (exact or rounded), and every report table row that starts
  with a documented `Values` label is compared with the files — count and share, unweighted and under each weight
  column. A row that disagrees is a warning (`report_figure_mismatch`), never an error: the check asks whether the
  report and the files agree, not whether a number is right. Needs `pypdf`.
- A document (PDF, DOCX…) listed in `Files list` needs no description block under `Files`.
- A document listed in `Files list` that is in the folder is no longer reported as `file_not_found`.

## 0.7.4 — 07/09/2026
- Hebrew-integrity guard: text lost as question marks / mojibake in the data, the metadata and the kit's own outputs.
- A format's accepted tokens (`Null`, `not_recorded`) are ignored by the type check.
- Gershayim round-trip, no absolute paths in the metadata, `declared_files` and `dbf_names` profile mechanisms.

## 0.7.3 — 03/09/2026
- Parquet tables read and aligned like CSV.
- `Size` / `File size` carry the fitting unit and the exact bytes.
- `Spatial coverage` is never written as "occupied territories".

## 0.7.2 — 03/09/2026
- SRS inferred from the bounding box when the `.prj` is missing or empty; an unread layer is named first.

## 0.7.1 — 26/08/2026
- A documented unknown is an answer, not a TODO; the on-board zone codes are documented answers, not join orphans.
- A lookup table is the parent of its join whichever side the format writes it on; DBF without a declared encoding.

## 0.7.0 — 26/08/2026
- `--deep zones`; the `kit_format_exempt` findings bucket; `validate --out-dir`.
- On-board profile: delivery zips, counts-only packages, the summary report as a checked item, CBS field descriptions.

## 0.6.0 – 0.6.2 — 24/08/2026
- Publishing: Cloudflare Pages site, ministry wrapper page, pre-publish leak scan.

## 0.5.0 — 24/08/2026
- First release: mot-metadata, mot-onboard, mot-sensors and mot-fix.
