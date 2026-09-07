---
name: mot-onboard
description: Create or validate the metadata of an on-board (OB) bus passenger survey dataset according to the Israel MoT "פורמט אחוד לנתוני סקרי און-בורד" v1.0 (13/11/2024) on top of the data-distribution נוהל v1.3. Knows the mandatory file set (routes.csv, shapes.zip/GTFS, timetable.csv, plan.csv, trips.csv, obad.csv, obod.csv, zones.zip, survey report PDF, metadata xlsx), every expected field with type/status/description, the trip_id / route_id conventions, the key-list links, the extra header keys (Contractor, Daily periods, Survey days, Vehicle types, Survey completeness) and the survey block (Statistical population, Sample frame, Sampling method, Survey method...). Use when the user mentions "on-board", "און-בורד", "OB survey", "סקר נוסעים באוטובוסים", "obad/obod/trips", "פעימה", "סקר עולים יורדים", or wants to prepare/validate an OB survey for distribution. Generic datasets → mot-metadata; sensors → mot-sensors.
---

# mot-onboard — on-board survey metadata (format v1.0)

This skill is the **onboard profile** of `mot-metadata`: same engine, same commands, with
`--profile onboard`. Read `../mot-metadata/SKILL.md` for the workflow; this file adds what is
specific to on-board surveys. Reference text: `references/onboard-format-v1.0.md`;
machine-readable expectations: `references/profile.json`.

```
python ../mot-metadata/scripts/mot_metadata.py init     <folder> --profile onboard
python ../mot-metadata/scripts/mot_metadata.py build    <folder> --profile onboard --name <survey>_<year>
python ../mot-metadata/scripts/mot_metadata.py validate <folder> --profile onboard [--metadata F] [--deep all]
python ../mot-metadata/scripts/mot_metadata.py build    <folder> --profile onboard --from <old metadata.xlsx>
```

`--deep zones` is the on-board one: it finds the zones layer's key (`zone_id`, `YISHUV_STA`,
`YISHUV_STAT_2022`, `YISHUV_STAT11`, `STAT11`, `TAZ`), names the field that matched, and resolves
`obod.zone_id_orig/dest` against it. It answers "does the layer this package ships index the codes
this package uses", and nothing about whether a code is right. The codes Table 11 defines for a trip
end that is **not** a zone — −1 חוץ לארץ, −2 יישובים פלסטיניים, −3 מחנות צה"ל ושב"ס, −4 לא ידוע — index
nothing on purpose: they are left out of `zone_code_unresolved` and of `join_orphans`, count and
percentage alike, and reported as an `info` `zone_special_codes` with how many rows carry each. The
kit reads them from `profile.json`, so a format that adds or renumbers one changes the dictionary
only. And because `zones.zip` is the join's **lookup** side (`key_role: lookup`), the relation is
judged in the direction it is used — the codes the layer does not index, never the zones nobody
travelled to — whichever way round the format writes the key line.

## What the profile adds automatically

- **Dataset kind = survey** → the survey block is mandatory (נוהל Table 2 as adapted by the OB
  format: Statistical population, Survey completeness*, Reference area, Collection period, Sample
  frame (one `month_year` row per licensing period), Sampling method, Survey method; optional:
  Sample size/proportion trips & passengers*, Response rate*, Estimation method, Data validation).
- **Extra header keys** (marked * in the format): Contractor (block), Daily periods (block,
  `hh:mm-hh:mm` ascending), Survey days, Vehicle types (block), Survey completeness (מלא / חלקי).
- **Expected files** (Table 5) with their descriptions pre-filled and their field dictionaries
  (Tables 6–12) used to pre-fill `Type`, `Description`, `Comments` and the `Values` of coded fields
  (`day_type` 1/2/3/11–15, `zone_id_*` negative codes −1..−4). Files are matched by name:
  `routes.csv`, `shapes*.zip` / `gtfs*.zip` (GTFS → no field documentation needed, format noted),
  `timetable.csv`, `plan.csv` (same structure as timetable), `trips.csv`, `obad.csv`, `obod.csv`,
  `zones*.zip` / `statistical_areas*.shp` (GIS → CRS/bbox/geometry + `Zones type`), survey report
  `.pdf` (→ Related documents), `*metadata*.xlsx`.
- **Expected key list**: routes→timetable (route_id), timetable→trips (route_id, trip_id),
  trips→obad / obod (**`trip_index` or `trip_id` — either satisfies it**; §3.8 prints one, §3.6 and
  Tables 10–11 name the other, and the kit does not pick a winner), obod zone_id_orig/dest →
  zones.zone_id.
- **What the format does NOT ask for, and so neither do we** — recorded in the `kit_format_exempt`
  bucket, never blocking: the fields of a **delivery zip** (`shapes.zip`, a GTFS/licensing container
  carried through unchanged — Table 5); `obod.csv` and `zones.zip` of a **counts-only** package
  (`Survey completeness = חלקי` **and** no `obod.csv` — both conditions, or one metadata cell would
  excuse two files); and the identifying fields the format **forbids** in a distribution file
  (`orig_address`, `orig_lat_lon`, `dest_address`, `dest_lat_lon`).
- **The documents**: a summary report / methodology document is a checked item (warning when
  **neither** is there — the summary report IS the methodology, and it may be `.pdf` or `.docx`); a
  separate methodology document and a questionnaire are recorded at `info`. Never an error.
- **Field names are matched after the typography is removed** (zero-width characters, a stray `?`,
  `last _bus_stop`, NBSP, case) and the canonical name is reported (`field_alias`) — so a field that
  IS in the file is never called missing. A *synonym* is not matched: the kit does not decide that
  one contractor's `boarding` "is" `boardings`.
- **A header-less CSV** is detected and reported; its first data row is never promoted to a field list.
- **An unknown contractor is an answer.** `Contractor` (also `Author`, `Contact`) may carry
  `לא ידוע` / `לא ידוע — לא תועד במקורות` / `unknown — not documented in the sources`. A survey
  older than its own paperwork is answered, not unfinished: no `todo`, an `info`
  `value_unknown_documented` keeps it visible, the row is not split into a name and a role, and the
  report prints it under ערכים שתועדו כלא ידועים rather than in the TODO list. An empty cell,
  `TODO`, `?` and `N/A` are still errors — only the spelled-out tokens count.
- **A zones layer that declares no encoding is still read.** A `.dbf` written in Windows-1255 with no
  `.cpg` and a code-page byte that says only "ANSI" used to leave the layer with zero documented
  fields, which no answer in `metadata-config.json` could reach. The kit tries the `.cpg`, then
  UTF-8, then the DBF's own code page, then Windows-1255, and reports which it used
  (`dbf_encoding_assumed`). Shipping a `.cpg` is still the real fix.
- **Hebrew is never written as question marks.** A column of `????`, a value with U+FFFD, or Hebrew
  that arrived as cp1252 mojibake is an error (`text_lost_as_question_marks` / `hebrew_mojibake`),
  and so is the same damage in the metadata document (`metadata_value_question_marks`). An OB
  delivery written through a cp1255 export is where this bites: the value is unrecoverable, so the
  answer is a re-export, never a hand-typed guess.
- **CBS statistical-areas field descriptions ship with the profile** (`references/cbs-fields.json`,
  the CBS's own wording) so a package that carries the standard layer can reach 0 errors.
- **`Survey completeness` is proposed, never written** — `חלקי` when `obod.csv` is absent, `מלא`
  when every Table-5 file is there. The author confirms it.
- **Naming**: field names must be lowercase `snake_case` English (format §3.4); `trip_id` =
  `line_id_direction_alternative_departure_time[_day_type]_month_year`; `trip_index` is the unique
  per-trip key linking trips/obad/obod.
- Distribution files must not contain identifying data (names, addresses, coordinates of
  origin/destination — `orig_address`, `orig_lat_lon`, `dest_address`, `dest_lat_lon`); no empty
  cells — missing data is `Null`.

## Intake questions specific to OB (ask, then write to metadata-config.json)

> `Spatial coverage` follows the base rule (mot-metadata): מטרופולין X / שם יישוב / official
> administrative names only — never "השטחים הכבושים" / "occupied territories", whoever asks.

1. Contractor(s) that executed the survey — or, if no source records them,
   `לא ידוע — לא תועד במקורות`. Never guess a company name.
2. Daily periods used for expansion (e.g. 06:00-09:00, 09:00-15:00 ...).
3. Survey days represented (ימי חול א'-ה' / ו' / ש').
4. Vehicle types sampled (רגיל / מפרקי / מיניבוס).
5. Survey completeness: מלא (all files of Figure 1) or חלקי (boardings/alightings only).
6. Statistical population, Reference area, Collection period, Sample frame (`month_year` rows),
   Sampling method, Survey method; optional sample sizes/proportions, response rate, expansion
   (estimation) method, validation done.
7. Which zones layer was used (statistical areas 2022 / model traffic zones) → `Zones type`, and
   whether the zone key field was renamed to `zone_id` as the format requires.

## Validating older surveys (pre-format, e.g. TLV-metro pulse 1 ver0.8)

Expect many "expected file/field missing" findings (routes.csv / timetable.csv naming, `trip_index`,
`*_factored` fields, `zone_id_*`, `day_period`). Report them as **format gaps** distinct from
**נוהל gaps** (survey block, GIS keys, Files list ≠ Files, key-list syntax, Excel date cells, key
casing). The user decides whether to restructure the data to v1.0 or to document it as-is with a
note in `Comments` that the dataset predates the format. Either way the נוהל gaps must be fixed.

## No code execution available?

Follow `../mot-metadata/SKILL.md` (manual section) and use `references/onboard-format-v1.0.md`
Tables 3–12 as the checklist; `references/profile.json` lists every expected field with its status
(required / required* / optional).
