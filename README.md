# mot-metadata-kit

**ערכת skills להפצת מידע תחבורתי של משרד התחבורה — לכלי AI.**
**Skills that prepare Israel MoT transport-data metadata — for AI tools.**

---

## עברית

### מה זה

ארבעה skills שמכינים, בודקים, מתקנים ואורזים את **קובץ המטא-דאטה** הנדרש לפי *נוהל הכנה, תיעוד והפצה של קבצי מידע תחבורתי* (גרסה 1.3) של משרד התחבורה, כולל פרופילים ייעודיים לסקרי **און-בורד** (פורמט 1.0) ולחבילות **גלאים** חודשיות (פורמט 1.02).

הפלט: `<שם>-metadata.json / .xlsx / .pdf` בפריסת משרד התחבורה, ולצידו **דוח פערים בעברית** שאומר בדיוק מה חסר או לא תואם.

> הערכה בודקת את **שלמות התיעוד וההתאמה בין המטא-דאטה לקבצים** — היא אינה בודקת את נכונות הנתונים עצמם, בדיוק כמו הנוהל.

| skill | מה הוא עושה |
|---|---|
| `mot-metadata` | הכללי: סורק תיקייה, שואל רק מה שאי-אפשר לגזור מהקבצים, מייצר מטא-דאטה + דוח |
| `mot-onboard` | פרופיל לסקרי און-בורד: קבצי החובה, השדות, המפתחות ובלוק הסקר |
| `mot-sensors` | פרופיל לחבילת `SensorDataSal_*.zip`: שלוש הטבלאות, שמות השדות וכלל ה-NA |
| `mot-fix` | תיקונים מכניים לפי הדוח (שמות, קידוד, ‎.cpg, פגמי מטא-דאטה) — תמיד dry-run קודם, עם גיבוי |

### מה אפשר לבקש — דוגמאות

בכלי AI פשוט כותבים בשפה חופשית. אלה בקשות אמיתיות שעובדות:

**`mot-metadata` — לכל תיקיית נתונים**

- *"הכן מטא-דאטה לפי נוהל ההפצה לתיקייה `G:\data\counts_2026`"* — סורק, שואל מה שחסר, מייצר xlsx/json/pdf + דוח.
- *"בדוק את `metadata.xlsx` בתיקייה הזאת מול הנוהל ותסביר לי בעברית מה לא תקין"*.
- *"המטא-דאטה שקיבלתי לא עומד בנוהל — תכין גרסה מתוקנת בלי לאבד את התיאורים שכתבתי"*.
- *"אילו שדות בקבצים אינם מתועדים במטא-דאטה, ואילו מתועדים אבל לא קיימים?"*
- *"תשלים את התיאורים מתוך ה-README שבתיקייה, ותגיד לי רק מה שנשאר לי למלא"*.
- *"ארוז את סט הנתונים להפצה"* — בונה את ה-ZIP בשם שב-Dataset file + צ׳קליסט.
- *"בדוק גם התאמה בין הערכים בקבצים לרשימות הערכים במטא-דאטה ובין טווח הזמן המוצהר לתאריכים בפועל"*.

**`mot-onboard` — סקרי און-בורד**

- *"הכן מטא-דאטה לסקר האון-בורד שבתיקייה, לפי הפורמט האחוד"* — מזהה את `routes/timetable/trips/obad/obod/zones`, ממלא את מילון השדות ואת בלוק הסקר.
- *"בדוק אם הסקר הזה עומד בפורמט 1.0 — אילו קבצים ושדות חסרים?"*
- *"הסקר בוצע לפני פרסום הפורמט — מה חייבים לתקן ומה אפשר להשאיר ולתעד בהערות?"*
- *"תוודא שרשימת המפתחות בין הקבצים נכונה, ושהמפתחות באמת מתחברים"*.

**`mot-sensors` — חבילות גלאים חודשיות**

- *"הכן מטא-דאטה לחבילת `SensorDataSal_260501_260531.zip`"* — קורא את שלוש הטבלאות מתוך ה-ZIP וממלא את מילון השדות בעברית.
- *"בדוק שהמטא-דאטה של חודש מאי תואם לפורמט 1.02"*.
- *"מה נשאר לי למלא לפני שאני שולח את החבילה?"*

**`mot-fix` — תיקונים על הקבצים עצמם**

- *"תקן את הקבצים לפי הדוח"* — מציג תכנית ממוספרת (שינוי שם / המרת קידוד / תיקון מטא-דאטה) ומחכה לאישור.
- *"תריץ רק את 1 ו-3"* — ‎`--apply --actions "1,3"`.
- *"תמיר את כל ה-CSV מ-Windows-1255 ל-UTF-8 ותוסיף .cpg לשכבה"*.
- *"שמות העמודות בעברית — הנה המיפוי לאנגלית, תחליף בקבצים ובמטא-דאטה"*.

> בכל בקשה: מה שאפשר להסיק מהקבצים (סוגי שדות, גדלים, תאריכים, היטל, תיחום) נלקח אוטומטית; מה שאי-אפשר — נשאלים עליו, וכל מה שנשאר פתוח מסומן `TODO` ומופיע בדוח.

### התקנה

**Claude Code** — שתי פקודות:

```
/plugin marketplace add g-bd/mot-metadata-kit
/plugin install mot-metadata-kit@mot-metadata-kit
```

**Claude.ai / Claude Desktop** — הגדרות ← Capabilities ← Skills ← העלאת skill, ומעלים את
`mot-metadata-skill-<version>.zip` (או את הערכה המלאה) מדף ה-Releases.

**ChatGPT** — פותחים Project, מדביקים ב-Instructions את התוכן של `skills/mot-metadata/SKILL.md`,
ומעלים לקבצי ה-Project את `skills/` מתוך ה-ZIP. עם Code Interpreter פעיל הוא מריץ את הסקריפטים על קבצים שמעלים לצ'אט.

**בלי AI, משורת הפקודה** — מספיק Python 3.10+; החבילות מתקינות את עצמן בהרצה הראשונה.

### שימוש

```bash
python skills/mot-metadata/scripts/mot_metadata.py setup                    # פעם אחת: בדיקה והתקנה
python skills/mot-metadata/scripts/mot_metadata.py build    <תיקייה>        # יצירת מטא-דאטה + דוח
python skills/mot-metadata/scripts/mot_metadata.py validate <תיקייה>        # בדיקת מטא-דאטה קיים
python skills/mot-metadata/scripts/mot_metadata.py package  <תיקייה> --metadata <קובץ>   # אריזת ZIP להפצה
python skills/mot-metadata/scripts/mot_fix.py               <תיקייה> --metadata <קובץ>   # תכנית תיקון (הוסיפו --apply)
```

בכלי AI פשוט מבקשים בשפה חופשית: *"הכן מטא-דאטה לפי נוהל ההפצה לתיקייה הזאת"* / *"בדוק את metadata.xlsx מול הנוהל"*.
ה-skill שואל רק מה שאי-אפשר לגזור מהקבצים (מפרסם, איש קשר, כותרת, תיאורים), וכל מה שנשאר פתוח מסומן `TODO` ומופיע בדוח.

הוסיפו `--profile onboard` או `--profile sensors` לסקרי און-בורד ולחבילות גלאים,
ו-`--deep values,temporal,joins` לבדיקות התאמה מעמיקות בין המטא-דאטה לנתונים.

**מדריך מלא בעברית:** `GUIDE-he.html` (התקנה, שימוש יומיומי, קריאת הדוח, עדכון גרסאות הנוהל).

### שילוב בצנרת (pipeline)

`skills/mot-metadata/scripts/mot_hook.py <תיקייה> --json [--config F]` הוא הצעד שמערכות אחרות קוראות לו בסוף ייצוא:
אף פעם לא זורק חריגה, תמיד מחזיר שורת JSON אחת (`ok | todo | skipped | error`) וכותב את המטא-דאטה והדוח לתוך התיקייה.
הדפוס שעובד בלי AI בלולאה (google-agg-v2, חבילות חודשיות): תבנית `metadata-config.json` אחת עם `{placeholders}`
שהצנרת ממלאת מתוך הריצה עצמה (תקופה, גרסת מפה, שמות שכבות, מספר מקטעים) ומעבירה ב-`--config`. מפתחות `files`
לפי שם קובץ בלבד (ללא נתיב) תופסים גם כשאותם קבצים יושבים בתת-תיקייה בחבילה. **בסביבת הצנרת חייב להיות `pyshp`**,
אחרת כל שכבה מדווחת `layer_unread`.

### מה נסרק

CSV (UTF-8 / Windows-1255 / UTF-16 / gzip), Excel (xlsx וגם xls ישן), Parquet, Shapefile, GeoJSON, GeoPackage,
ZIP (כולל zip בתוך zip) ו-GTFS. גודל כל קובץ נרשם ביחידה המתאימה (KB / MB / GB) ולצידה מספר הבייטים המדויק. תיעוד קיים (README / PDF / DOCX) נקרא אוטומטית ומשמש לתיאורי השדות.
מלל בעברית לעולם אינו נכתב כסימני שאלה: עמודה או ערך מטא-דאטה שהגיעו כ-`????` או כ-mojibake מדווחים כשגיאה, וכל פלט שהערכה כותבת (json / xlsx / csv / html / PDF) נקרא בחזרה כדי לוודא שהעברית שבו שרדה.

---

## English

### What it is

Four skills that create, validate, fix and package the **metadata file** required by the Israel Ministry of
Transport data-distribution guideline (*נוהל הכנה, תיעוד והפצה של קבצי מידע תחבורתי* v1.3), with domain profiles
for **on-board surveys** (format v1.0) and monthly **traffic-sensor** packages (format v1.02).

Output: `<name>-metadata.json / .xlsx / .pdf` in the ministry layout, plus a **Hebrew RTL gap report** listing
exactly what is missing or inconsistent.

> The kit checks **documentation completeness and metadata↔files consistency** — never the correctness of the
> data itself, exactly like the guideline.

| skill | what it does |
|---|---|
| `mot-metadata` | the generic engine: scans a folder, asks only what the files cannot answer, writes metadata + report |
| `mot-onboard` | on-board survey profile: mandatory files, fields, keys and the survey block |
| `mot-sensors` | `SensorDataSal_*.zip` profile: the three tables, field dictionary and the NA rule |
| `mot-fix` | mechanical fixes driven by the report (names, encoding, .cpg, metadata defects) — dry-run first, always backed up |

### Install

**Claude Code** — two commands:

```
/plugin marketplace add g-bd/mot-metadata-kit
/plugin install mot-metadata-kit@mot-metadata-kit
```

**Claude.ai / Claude Desktop** — Settings → Capabilities → Skills → upload skill, using
`mot-metadata-skill-<version>.zip` (or the full kit) from the Releases page.

**ChatGPT** — create a Project, paste `skills/mot-metadata/SKILL.md` into the Instructions, and upload the
`skills/` folder from the ZIP to the Project files. With Code Interpreter enabled it runs the scripts on files
you upload to the chat.

**No AI, plain CLI** — Python 3.10+ is enough; dependencies self-install on first run.

### Use

```bash
python skills/mot-metadata/scripts/mot_metadata.py setup                    # one-time: verify + install deps
python skills/mot-metadata/scripts/mot_metadata.py build    <folder>        # create metadata + report
python skills/mot-metadata/scripts/mot_metadata.py validate <folder>        # check an existing metadata file
python skills/mot-metadata/scripts/mot_metadata.py package  <folder> --metadata <file>   # distribution ZIP + checklist
python skills/mot-metadata/scripts/mot_fix.py               <folder> --metadata <file>   # fix plan (add --apply)
```

In an AI tool just ask in plain language: *"prepare MoT metadata for this folder"* / *"validate metadata.xlsx
against the guideline"*. The skill asks only what the files cannot tell it (publisher, contact, title,
descriptions); anything still open is written as `TODO` and listed in the report.

Add `--profile onboard` / `--profile sensors` for those domains, and `--deep values,temporal,joins` for deeper
metadata↔data consistency checks.

**Full Hebrew guide:** `GUIDE-he.html`.

### Embedding in a pipeline

`skills/mot-metadata/scripts/mot_hook.py <folder> --json [--config F]` is the step other systems call at the end of
an export: it never raises, always prints one JSON line (`ok | todo | skipped | error`) and writes the metadata +
report into the folder. The pattern that runs with no AI in the loop (google-agg-v2 monthly packages): ONE
`metadata-config.json` template with `{placeholders}` the pipeline fills from the run itself (period, map version,
layer file names, link count) and passes with `--config`. `files` keys by basename (no path) match the same files
when the package moves them into a sub-folder. **The host environment needs `pyshp`** or every layer reports
`layer_unread`.

### What it reads

CSV (UTF-8 / Windows-1255 / UTF-16 / gzip), Excel (xlsx and legacy xls), Parquet, Shapefile, GeoJSON, GeoPackage,
ZIP (including nested zips) and GTFS. Every file size is written in the unit that fits (KB / MB / GB) with the exact byte count beside it. Existing documentation (README / PDF / DOCX) is harvested into field
descriptions automatically.
Hebrew is never written as question marks: a column or a metadata value that arrived as `????` or as mojibake is an error, and every output the kit writes (json / xlsx / csv / html / PDF) is read back to prove its Hebrew survived.

### Tests

```bash
python -m pytest tests -q          # 88 unit tests on synthetic fixtures
claude plugin eval .               # skill-behaviour evals (early access)
```

### Bundled specification versions

| spec | version | date |
|---|---|---|
| נוהל הכנה, תיעוד והפצה של קבצי מידע תחבורתי | 1.3 | 15/05/2024 |
| פורמט אחוד לנתוני סקרי און-בורד | 1.0 | 13/11/2024 |
| פורמט נתוני ספירות גלאים | 1.02 | 31/05/2026 |

When the ministry publishes a new version: `python skills/mot-metadata/scripts/spec_update.py <new-spec.pdf>`
produces a diff against the bundled dictionary to review before updating.
