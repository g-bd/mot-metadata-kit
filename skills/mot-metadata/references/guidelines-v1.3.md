# נוהל הכנה, תיעוד והפצה של קבצי מידע תחבורתי — גרסה 1.3 (15/05/2024)

Source: משרד התחבורה, שולחן עגול איסוף מידע תחבורתי · page https://www.gov.il/he/pages/data_distribution ·
PDF `MoT data distribution guidelines v.1.3.pdf` (21 pages). In force since 21/02/2021. Based partly on
"עקרונות וסטנדרטים לביצוע הנגשת מאגרי מידע לציבור" (רשות התקשוב, v1.0, 2018) §7 and on Eurostat SIMS
for statistical surveys. Binding for MoT units and corporations; recommended for everyone else.

The נוהל covers **how a dataset is prepared, documented (metadata) and packaged**. It does **not** deal with
how the data was collected, its accuracy or usage limits — those are *described* in the metadata, not judged.

## Changes in v1.3 (§1.1)
- Keys between linked files (`Key list`) added to the metadata (Table 1).
- For Time fields, put the time format in the field `Comments` (e.g. `hh:mm:ss`); same for Date (`dd/mm/yyyy`).
- New field type `DateTime` (Date + Time).
- GIS datasets must state the geometry type: Point / Polyline / Polygon (Table 3).

## Definitions (§4, abridged)
- **קובץ נתונים**: a file of data; identified by name + extension. **פורמט פתוח**: non-proprietary (CSV, text, XML, Excel…).
- **פורמט מורכב**: a dataset that needs several files (shapefile = 3+ files sharing a name; main file = `.shp`).
- **סט נתונים**: one or more files forming the (partial or full) product of a data-collection or planning activity.
  **פשוט** = one file; **מורכב** = several files (often linked by id keys).
- **קובץ מטא-דאטה**: structured file accompanying a dataset describing its properties per this נוהל.
- **סקר סטטיסטי**: measurement on a sample generalised to a population.

## Preparing a dataset (§5.2)
1. list of files in the dataset; 2. description of each file's structure; 3. the metadata file; 4. **dataset + metadata
saved into one ZIP archive**. Prefer open formats (mandatory when published to the public; a proprietary twin such as
SAS may be added). Versions must be distinguishable (public vs licensed versions too).

## Metadata file structure (§5.4)
Header (general information) + one structure block per file. Parameters are English keys (`Parameter = value`);
three kinds: **value** (one line), **array** (`value1, value2` on one line), **block** (several lines, each a value
or free text). Status: `required`, `optional`, `required*` (required under a condition). Optional keys without a
value are simply omitted. Dates are `dd/mm/yyyy`. Some keys have enumerated values (use them as written).

## Table 1 — header dictionary
| Key | He | Kind | Status | Notes |
|---|---|---|---|---|
| Publisher | מפרסם | value | required | body publishing the data |
| Contact | איש קשר | value | required | contact person at author or publisher |
| Contact Email | דואר אלקטרוני | value | optional | |
| Author | מחבר | value | required* | ministry / authority / unit responsible — fill when different from Publisher |
| Author Email | | value | optional | |
| Title | שם סט הנתונים | value | required | meaningful name |
| Description | תיאור כללי | block | required | content, purpose, completeness… several lines |
| Keywords | תגיות | value (comma list) | required | see §5.6 / Appendix A |
| Created | תאריך יצירה | value | required | dd/mm/yyyy |
| Frequency of update | תדירות עדכון | value | optional | שנתי / רבעוני / חודשי / שבועי / יומי / המאגר אינו מתעדכן / מתעדכן בתדירות לא קבועה (default: אינו מתעדכן) |
| Version | גרסה | value | required* | mandatory for versioned datasets; if it replaces earlier versions say so in Comments |
| Last updated | עדכון אחרון | value | required | dd/mm/yyyy |
| Temporal coverage | טווח זמן | value | required | free text, e.g. 2000-2005 |
| Spatial coverage | כיסוי מרחבי | value | required | ארצי / מטרופולין X / עירוני / שם יישוב — official administrative names only; never "השטחים הכבושים" / "occupied territories" (kit rule, see below) |
| Language | שפה | value | optional | |
| Related documents | מסמכים נלווים | block | optional | pdf/text files shipped with the dataset |
| References | הפניות | block | optional | URLs |
| Legal constrains | מגבלות שימוש | block | optional | confidentiality, copyright, privacy |
| License | רישיון שימוש | value | optional | |
| Data quality | איכות המידע | value | optional | source, accuracy… |
| Dataset file | קובץ סט הנתונים | value | required | name of the **.zip** archive |
| Files list | רשימת קבצים | block | required* | complex datasets: one row per file (a complex-format file = one row) |
| Size | גודל | value | optional | MB |
| Metadata creator | | value | optional | |
| Metadata creation date | | value | required | dd/mm/yyyy |
| Metadata version | גרסת מטא-דאטה | value | optional | write **1.1** for this נוהל version |
| Comments | הערות | block | optional | |
| URL | כתובת מקוונת | value | optional | |
| Files | קבצים | block | required* | complex datasets: one Table-3 block per file |
| Key list | רשימת מפתחות | block | required* | complex datasets with links: `file.field -> file.field` per row |

## Table 2 — survey supplement (only when the dataset is a statistical survey)
| Key | He | Kind | Status |
|---|---|---|---|
| Statistical population | אוכלוסייה סטטיסטית | block | required |
| Statistical unit | יחידה סטטיסטית | value | required |
| Reference area | אזור הסקר | value | required |
| Collection period | תקופת הסקר | value | required |
| Sample frame | מסגרת הדגימה | value | required |
| Sampling method | שיטת הדגימה | value | required |
| Sample size | גודל המדגם | value | required |
| Sample proportion | אחוז המדגם | value | optional |
| Survey method | שיטת הסקר | block | required |
| Estimation method | שיטת האמידה | block | required |
| Estimation period | תקופת האמידה | value | required |
| Data processing | עיבוד הנתונים | block | optional |
| Overall accuracy | מרווח הטעות | block | optional |
| Data validation | תיקוף הנתונים | block | optional |
| Statistical definitions | מושגים סטטיסטיים | value | optional |

## Table 3 — per-file dictionary
| Key | He | Status | Notes |
|---|---|---|---|
| File name | שם קובץ | required | |
| File format | פורמט | required | extension; complex format → main file extension only |
| File description | תיאור קובץ | required | not needed for a single-file dataset |
| File fields | שדות | required (block) | Table 4 rows |
| File size | גודל | optional | MB; complex format → all sidecar files. The kit writes the fitting unit + exact bytes, e.g. `16.5 MB (17,268,557 bytes)` |
| File date | תאריך יצירה | optional | dd/mm/yyyy |
| Spatial coverage | כיסוי מרחבי | optional | if different from the dataset; same wording rule as the header |
| Spatial reference system | היטל | required* (GIS) | ITM / EPSG:2039 (רשת חדשה) / GRS_1980 (רשת ישנה) / WGS_1984 |
| Geographic bounding | תיחום גאוגרפי | required* (GIS) | four bounding coordinates |
| Geographic type | סוג ישות | required* (GIS) | Point / Polyline / Polygon |
| File Comments | הערות | optional | |

## Table 4 — per-field dictionary
| Key | Status | Notes |
|---|---|---|
| Name | required | exactly as in the file |
| Type | required | Text, Number, String, Integer, Real, Date, Time, DateTime; key field → `Text(key)` (also `Integer(key)` in practice); put time/date format in Comments |
| Description | required | |
| Comments | optional | units (km, kg…), formats |
| Values | required* (coded fields) | list of value / label / comment |

## §5.6 Keywords
Add several standard keywords from Appendix A (English, comma separated) so the dataset can be found in a library.
Appendix A groups (abridged): context (existing/planning/project/future data), scope (urban, inter-urban, national,
district, local), modes (roads, traffic, public transport, bus, train/rail, urban mass transit, taxi, bicycle,
micro-mobility, pedestrians, private vehicles, motorcycles, commercial vehicles, trucks, aviation/maritime data),
performance (travel times, speed, delays, waiting/walking times, transfers, accessibility, density, occupancy,
turnover, fares, park and ride), safety (accidents, injured data, traffic violations/citations, events, weather data,
work zone data), measurements (traffic counts, traffic volumes, trajectories, kilometrage, passenger counts/volumes,
boarding/alighting counts, origin-destination data, travel behavior, customer satisfaction), projects (project
inventory, five-year/investment plans, yearly budget, master/outline/building plan, land use), infrastructure
(freeways, intersections, interchanges, railroads, terminals, priority lanes, bicycle lanes, sidewalks, parking
on/off-street), control (signs, traffic signals, cameras, detectors, signing authority, tolls), PT (route description,
stations information, timetable, frequency, fare zones, boundaries).

## §5.7 Naming rules
**Files**: short but descriptive; Latin letters; no spaces or special characters (`* # % $`…); accepted extensions.
**Versions**: consistent scheme; at dataset (zip) level for complex datasets; dates or version numbers.
**Fields**: consistent across files; short, readable, unique within a file; not generic (`VAR1` → `weight`); Latin,
English preferred over transliteration (`weight` not `mishkal`); one compound style (CamelCase / camelCase /
snake_case); no spaces/special characters; identifiers end with `ID` (`objectID`); respect format length limits
(e.g. DBF 10 characters).

## §5.8 Metadata file format
Excel, or text (json / csv). Name: `<dataset>-metadata.<ext>` e.g. `priority2019-metadata.json`. Excel example
(Figure 3): column A = key, column B = value(s); blocks continue on the next rows; the Files section repeats
`File name / File format / File description / File Fields (name, type, description, comment, value, label)`.
Key example (Figure 4): `trips.csv.trip_id_unique -> obad.csv.trip_id_unique`.

## §6 Exceptions
Traffic counts (ספירות תנועה) have their own metadata: "פורמט אחוד לספירות תנועה" (נוהל cites v2.01; gov.il now
hosts v3.0) — https://www.gov.il/he/pages/uniform_format_traffic_counts.

## How the kit reads the נוהל — unanswered vs unknown (0.7.1, owner rule 26/08/2026)

The נוהל says a required key must carry a value; it does not say what to write when the value
cannot be known — the contractor of a survey older than its own paperwork, a contact who left the
ministry years ago. Until 0.7.1 the only honest thing to write was `TODO`, which reads as "somebody
still has to answer this" and never stops reading that way.

A required **text** key may now carry an explicit token instead:

| written | read as |
|---|---|
| `לא ידוע` · `לא ידוע — לא תועד במקורות` · `unknown — not documented in the sources` | **an answer.** No `todo`; an `info` finding `value_unknown_documented` keeps it visible, and the report prints it under "ערכים שתועדו כלא ידועים" — never in the TODO list. |
| an empty cell · `TODO` · `?` · `N/A` · `-` · `...` | **not an answer.** Still an error (`missing_required` / `todo` / `value_placeholder`). |

Only the spelled-out tokens count, and only on a key the נוהל leaves as prose: a key with a shape
(`Created`, `Contact Email`, a URL) or a closed vocabulary (`Survey completeness`) is not answered by
"unknown", because the answer would neither parse nor be in the list. The tokens live in
`references/spec.json → unknown_tokens`; a profile may add one, and may not take one away or promote
a rejected placeholder.

## How the kit reads the נוהל — Spatial coverage wording, real sizes, Parquet (0.7.3, owner rule 03/09/2026)

**Spatial coverage.** The נוהל asks for a verbal description — ארצי / שם מטרופולין / שם יישוב. The kit
writes it that way, or by the official administrative name of the area (מחוז, אזור יהודה ושומרון),
and **never as "the occupied territories"** (השטחים הכבושים, occupied territories, or any spelling of
either), whoever asks for it. A `metadata-config.json` value carrying that wording is written as
`TODO` and recorded in `_meta.refused_wording` (the report prints it under "נוסח שנדחה בכיסוי המרחבי");
a metadata file that already carries it — at the dataset level or per file — gets the error
`spatial_coverage_wording`. The terms are data (`spec.json → spatial_coverage_wording`, substring
match, case- and invisible-character-insensitive); a profile may add one, never remove one.

**Encoding integrity (KP-R3, the owner 06/09/2026).** Hebrew text is never written as question
marks. This is a completeness-of-documentation rule, not a rule about data content: a cell holding
`????` or U+FFFD carries no information at all, and no reader and no later correction can bring it
back. A text column whose values are a run of `?` (or where `?` is at least half the characters),
or which holds U+FFFD, is reported once per column as `text_lost_as_question_marks` (error) with a
count and examples; a column whose Hebrew is cp1252 mojibake is `hebrew_mojibake` (error); the same
damage in the metadata document's own values is `metadata_value_question_marks` (error). Every
output the kit writes is read back before it is offered: json / xlsx / csv / html must return every
Hebrew string character for character (`output_roundtrip_failed`, exit 2 - the kit's bug, never the
user's), and a PDF's first pages must yield the title's Hebrew to a text extractor
(`pdf_hebrew_not_rendered`, warning; `build --allow-unverified-pdf` accepts it, still reported).
The thresholds, the mojibake markers and the wording are data (`spec.json → encoding_integrity`);
a profile may tighten a threshold or add a marker, never remove one, and it may not change a
severity.

**Sizes.** `Size` and `File size` are "MB" in the נוהל's wording. The kit writes the unit that keeps the
number readable **and** the exact byte count — `612 B (612 bytes)`, `6.3 KB (6,451 bytes)`,
`16.5 MB (17,268,557 bytes)`, `2.04 GB (…)` — so a small lookup table is no longer `0.0` and the size
is the real one. For a shapefile the total of the layer's sidecar files; for a member of a zip, its
own uncompressed size.

**Parquet.** A `.parquet` table is a data file like a CSV: its schema is the field list (types from the
Arrow schema — Integer / Real / Date / DateTime / Time / Text), its footer the exact row count, and it
is aligned with the metadata exactly as a CSV is — fields in file vs. in metadata, documented `Values`
vs. the codes in the column, key joins — on disk and inside a zip. Read with `pyarrow` (installed by
`setup`); without it the file is listed with its size and the cause named.
