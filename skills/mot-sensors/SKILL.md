---
name: mot-sensors
description: Create or validate the metadata of a monthly traffic-sensor (גלאים) package delivered to the national traffic-count basket (סל הספירות הלאומי) according to the MoT "פורמט נתוני ספירות גלאים" v1.02 (31/05/2026, page uniform_format_traffic_sensors pending publication) on top of the data-distribution נוהל v1.3. Knows the package naming SensorDataSal_<from>_<to>.zip with table1 (count period), table2 (sensor list with arms/directions) and table3 (hourly volumes by 5 vehicle classes and 2 directions, NA for partial hours), the Hebrew field names and their meaning. Use when the user mentions "sensors", "גלאים", "נתוני גלאים", "SensorDataSal", "סל הספירות", "נת"י detectors", "ספירות גלאים", or wants to document a monthly sensor zip for distribution. Generic datasets → mot-metadata; on-board surveys → mot-onboard.
---

# mot-sensors — monthly sensor package metadata (format v1.02)

The **sensors profile** of `mot-metadata` (`--profile sensors`). Workflow and commands are in
`../mot-metadata/SKILL.md`; reference text in `references/sensor-format-v1.02.md`; expectations in
`references/profile.json`.

```
python ../mot-metadata/scripts/mot_metadata.py build    <folder with SensorDataSal_*.zip> --profile sensors
python ../mot-metadata/scripts/mot_metadata.py validate <folder> --profile sensors [--metadata F]
```

## What the profile adds automatically

- Recognises `SensorDataSal_<yymmdd>_<yymmdd>.zip` and its members
  `..._table1.csv` (count period, one row), `..._table2.csv` (sensor catalogue), `..._table3.csv`
  (hourly counts). The members are scanned inside the zip (Windows-1255 encoding detected) and each
  gets its own file block with the v1.02 field dictionary (Hebrew names, types, descriptions,
  vehicle-class labels 1 = דו גלגלי, 2 = פרטי, 3 = מסחרי, 4 = משאית/אוטובוס, 5 = משאית כבדה, NA rule).
- Derives `Temporal coverage`, `Title` and `Dataset file` from the package name; sets
  `Frequency of update = חודשי`, `Spatial coverage` = inter-urban network, default keywords
  (traffic detectors, traffic counts, traffic volumes, inter-urban, ...).
- Key list: `table2.קוד גלאי -> table3.קוד גלאי`.
- Field names are Hebrew **by the format's own definition**; the נוהל (§5.7) prefers Latin names —
  reported as a single warning per table, not as errors. If the MoT later publishes Latin headers,
  update `references/profile.json` (`expected_files[*].fields[*].Name`).
- Dataset kind = monitoring (not a survey → no survey block).

- **Hebrew is never written as question marks.** A `????` or mojibake column in a monthly package
  is an error (`text_lost_as_question_marks` / `hebrew_mojibake`), as is the same damage in the
  metadata (`metadata_value_question_marks`); the kit also reads back every output it writes to
  prove the Hebrew survived.

## Intake questions (only these are usually needed)

> `Spatial coverage` follows the base rule (mot-metadata): ארצי / official administrative names
> only — never "השטחים הכבושים" / "occupied territories", whoever asks.

1. Publisher (משרד התחבורה / נתיבי ישראל) and Author (אגף ניהול תנועה, נתיבי ישראל) — Author only
   if different from Publisher.
2. Contact person + email.
3. A 2–3 line Description (sensor technology — radar; lane → direction conversion key; hourly
   aggregation; NA for partial hours; month covered). A ready default is in
   `references/sensor-format-v1.02.md` → "Description template".
4. Version / Comments if this month's package replaces an earlier delivery.

## Format checks you can offer beyond metadata (optional, ask first)

The profile only documents the package. If the user wants the *format* itself checked (column set of
each table, one row in table1, table2 sensors all present in table3, NA vs 0 in partial hours,
24 × days rows per sensor) point them to the sensor-sal system (`sensor-sal-v1`, audit stage) — this
skill deliberately does not judge the data.

## Spec freshness

The gov.il page `uniform_format_traffic_sensors` was not yet published when this skill was built
(08/2026); the bundled text comes from the v1.02 docx circulated by e-mail. When the page goes live,
run `check-spec --online` (or open the page), compare the version, and update
`references/sensor-format-v1.02.md` + `profile.json` + `../mot-metadata/references/spec-sources.json`.
A future revision is expected to add junction-level (צומת) data in addition to the section (חתך) level.
