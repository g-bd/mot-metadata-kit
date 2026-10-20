"""`--deep report` — the survey report PDF against the files it describes (owner's request, 20/10/2026).

A sanity check, opt-in like every deep check: the numbers a reader will quote come from the
report, so the headline figures printed in it should be the ones the delivered files give.
Hard rule 1 still holds — nothing here judges whether a number is RIGHT, only whether the
report and the files AGREE. Never an error: a warning when a report table row disagrees with
the files, info for everything else.

Two checks, both found from the files and the metadata alone (no profile needed):

* headline figures — each data file's row count and the sum of every weight column
  (`weight`, `factor`, `expan…`, `משקל`, `מקדם`) are looked for in the report's numbers,
  exactly or rounded ("כ-91,300");
* coded distributions — for every field documented with `Values`, the count and share of each
  label (unweighted and under each weight column of the same file) against the report's table
  rows that start with that label ("ברגל 64,258 55.6%").

PDF text extraction glues table cells together ("ברגל64,25855.6%"), so a run of digits is
read every way it can be split into a count and a share before it is compared.
"""
from __future__ import annotations

import csv
import gzip
import io
import re
from collections import defaultdict
from pathlib import Path
from typing import Optional

from .io import to_text

WEIGHT_RE = re.compile(r"weight|factor|expan|משקל|מקדם", re.I)
TABLE_ROW_MAX_EXTRA = 40          # a table row is the label plus a few cells, not a sentence
MAX_PAGES = 120
MAX_ROWS = 2_000_000
_RUN_RE = re.compile(r"\d[\d,]*(?:\.\d+)?%?")
_GROUPED_RE = re.compile(r"^\d{1,3}(?:,\d{3})+$")


def _report_pdfs(meta: dict, scan: Optional[dict]) -> list[str]:
    docs = list((scan or {}).get("documents") or [])
    return [d for d in docs if d.lower().endswith(".pdf") and "metadata" not in d.lower()]


def pdf_text(path: Path, pages: int = MAX_PAGES) -> str:
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    out = []
    for page in reader.pages[:pages]:
        try:
            out.append(page.extract_text() or "")
        except Exception:
            out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------- numbers in text
def _count(s: str) -> Optional[float]:
    if not s:
        return None
    if "," in s and not _GROUPED_RE.match(s.split(".")[0]):
        return None
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return None


def split_run(run: str) -> tuple[set[float], set[tuple[float, int]]]:
    """Every (count, share) reading of one glued run. Shares carry their decimal places."""
    counts: set[float] = set()
    shares: set[tuple[float, int]] = set()
    if not run.endswith("%"):
        c = _count(run.rstrip(".,"))
        if c is not None:
            counts.add(c)
        return counts, shares
    body = run[:-1]
    for i in range(len(body)):
        head, tail = body[:i], body[i:]
        if not tail or tail[0] in ",." or "," in tail:
            continue
        try:
            p = float(tail)
        except ValueError:
            continue
        if p > 100 or len(tail.split(".")[0]) > 3 or (len(tail.split(".")[0]) > 1 and tail[0] == "0"):
            continue
        if head:
            c = _count(head)
            if c is None:
                continue
            counts.add(c)
        shares.add((p, len(tail.split(".")[1]) if "." in tail else 0))
    return counts, shares


def numbers_in(text: str) -> tuple[set[float], set[tuple[float, int]]]:
    counts: set[float] = set()
    shares: set[tuple[float, int]] = set()
    for run in _RUN_RE.findall(text):
        c, s = split_run(run)
        counts |= c
        shares |= s
    return counts, shares


def _close_count(report: float, data: float) -> bool:
    return abs(report - data) <= max(1.0, 0.002 * abs(data))


def _rounded_match(report: float, data: float) -> bool:
    """'כ-91,300' for 91,292: the report number is round and within half its rounding step."""
    for step in (1000, 100, 10):
        if report % step == 0 and abs(report) >= step * 10 and abs(report - data) <= step / 2:
            return True
    return False


def _close_share(report: tuple[float, int], data: float) -> bool:
    p, dec = report
    return abs(p - data) <= (0.15 if dec else 0.6)


# --------------------------------------------------------------------------- the files
def _table_rows(folder: Path, entry: dict):
    """(header, row iterator) of a CSV data file, top level or zip member. None when unreadable."""
    from .scan import _zip_member_bytes, detect_encoding
    name = entry["name"].replace("\\", "/")
    p = folder / name
    try:
        if p.exists():
            raw = p.read_bytes()
            if name.lower().endswith(".gz"):
                raw = gzip.decompress(raw)
        elif "/" in name:
            zip_part, _, member = name.partition("/")
            zp = folder / zip_part
            if not zp.exists():
                return None
            raw = _zip_member_bytes(zp.read_bytes(), member)
            if raw is None:
                return None
            if member.lower().endswith(".gz"):
                raw = gzip.decompress(raw)
        else:
            return None
    except Exception:
        return None
    text = raw.decode(entry.get("encoding") or detect_encoding(raw), errors="replace")
    reader = csv.reader(io.StringIO(text), delimiter=entry.get("delimiter") or ",")
    header = [h.strip().lstrip("﻿") for h in next(reader, [])]
    return header, reader


def _num(v: str) -> Optional[float]:
    try:
        return float(v.replace(",", "")) if v and v.strip() else None
    except ValueError:
        return None


def _code_key(v) -> str:
    s = to_text(v).strip()
    try:
        f = float(s)
        return str(int(f)) if f == int(f) else s
    except ValueError:
        return s


def _file_stats(folder: Path, entry: dict, coded: dict[str, dict[str, str]]):
    got = _table_rows(folder, entry)
    if not got:
        return None
    header, rows = got
    weights = [h for h in header if WEIGHT_RE.search(h)]
    wi = {w: header.index(w) for w in weights}
    ci = {c: header.index(c) for c in coded if c in header}
    n = 0
    wsum = defaultdict(float)
    fractional: set[str] = set()
    # dist[field][code][variant] - variant "" = rows, else the weight column
    dist: dict = {c: defaultdict(lambda: defaultdict(float)) for c in ci}
    for row in rows:
        if n >= MAX_ROWS:
            break
        n += 1
        wv = {}
        for w, i in wi.items():
            x = _num(row[i]) if i < len(row) else None
            if x is not None:
                wsum[w] += x
                wv[w] = x
                if x != int(x):
                    fractional.add(w)
        for c, i in ci.items():
            code = _code_key(row[i]) if i < len(row) else ""
            if not code:
                continue
            dist[c][code][""] += 1
            for w, x in wv.items():
                dist[c][code][w] += x
    # a "weight" column of whole numbers is a group id or a count, not an expansion factor
    for c in dist.values():
        for code in c.values():
            for w in [w for w in code if w and w not in fractional]:
                del code[w]
    return {"rows": n, "weights": {w: v for w, v in wsum.items() if w in fractional}, "dist": dist}


# --------------------------------------------------------------------------- report lines
def _label_lines(lines: list[str], label: str) -> list[str]:
    """Report lines that are a table row OF this label: they start with it and carry numbers."""
    out = []
    for ln in lines:
        s = ln.strip().lstrip("•·-–*▪●○ ").strip()
        if not s.startswith(label) or len(s) > len(label) + TABLE_ROW_MAX_EXTRA:
            continue
        nxt = s[len(label):len(label) + 1]
        if nxt and ("֐" <= nxt <= "׿" or nxt.isalpha()):
            continue                        # "ברגל" must not match "ברגלית"
        if _RUN_RE.search(s[len(label):]):
            out.append(s)
    return out


def check_report_vs_data(meta: dict, folder: Optional[Path], scan: Optional[dict], fx) -> None:
    if not folder or not scan:
        return
    pdfs = _report_pdfs(meta, scan)
    if not pdfs:
        return
    texts = []
    for d in pdfs:
        try:
            texts.append(pdf_text(Path(folder) / d))
        except ImportError:
            fx.add("info", "report", d, "report_check_skipped", "pypdf אינו מותקן - הדוח לא הושווה לקבצים", "", "pip install pypdf")
            return
        except Exception as e:  # unreadable PDF: say so, never fail validation over it
            fx.add("info", "report", d, "report_check_skipped", f"לא ניתן לקרוא את הטקסט של '{d}'", str(e)[:200])
    text = "\n".join(texts)
    if not text.strip():
        fx.add("info", "report", ", ".join(pdfs), "report_check_skipped", "לא חולץ טקסט מהדוח (סרוק כתמונה?) - הדוח לא הושווה לקבצים")
        return
    lines = text.splitlines()
    all_counts, _ = numbers_in(text)
    rep = ", ".join(pdfs)

    coded_by_file: dict[str, dict[str, dict[str, str]]] = {}
    for fl in meta.get("Files", []):
        name = to_text(fl.get("File name"))
        for fld in fl.get("File fields") or []:
            vals = fld.get("Values") or []
            m = {_code_key(v.get("value")): to_text(v.get("label")).strip() for v in vals if isinstance(v, dict)}
            m = {k: v for k, v in m.items() if k and len(v) >= 2}
            if m:
                coded_by_file.setdefault(Path(name).name.lower(), {})[to_text(fld.get("Name"))] = m

    n_ok = n_bad = 0
    by_label: dict[str, list[dict]] = defaultdict(list)
    for e in scan.get("files", []):
        if e.get("role") != "data" or e.get("format") not in ("CSV", None) or not e["name"].lower().endswith((".csv", ".csv.gz", ".txt", ".tsv")):
            continue
        coded = coded_by_file.get(Path(e["name"]).name.lower(), {})
        st = _file_stats(Path(folder), e, coded)
        if not st:
            continue
        # headline figures
        heads = [(f"{e['name']}: מספר רשומות", float(st["rows"]))]
        heads += [(f"{e['name']}: סכום {w}", v) for w, v in st["weights"].items()]
        for what, v in heads:
            if abs(v) < 100:
                continue                    # small numbers are everywhere in a report
            exact = any(_close_count(c, v) for c in all_counts)
            rounded = not exact and any(_rounded_match(c, v) for c in all_counts)
            if exact or rounded:
                n_ok += 1
                fx.add("info", "report", what, "report_figure_found",
                       f"{what} = {v:,.0f} - מופיע בדוח{' (מעוגל)' if rounded else ''}")
            else:
                fx.add("info", "report", what, "report_figure_not_found",
                       f"{what} = {v:,.0f} - לא נמצא בדוח", "אם הדוח מציין סה\"כ אחר - כדאי לבדוק מאיפה ההפרש")
        # coded distributions - collected first: one label ("באוטובוס") is often an answer of
        # several fields, and a report row belongs to whichever of them it agrees with
        for field, labels in coded.items():
            d = st["dist"].get(field) or {}
            variants = {""} | set(st["weights"])
            totals = {w: sum(c.get(w, 0.0) for c in d.values()) for w in variants}
            for code, label in labels.items():
                counts = {w: d.get(code, {}).get(w, 0.0) for w in variants}
                shares = {w: 100.0 * counts[w] / totals[w] for w in variants if totals[w]}
                by_label[label].append({"where": f"{e['name']}.{field}={code}", "field": field, "code": code,
                                        "counts": counts, "shares": shares})

    for label, cands in by_label.items():
        for row in _label_lines(lines, label):
            cs, ss = numbers_in(row[len(label):])

            def agrees(c) -> bool:
                # a row that carries a count is judged by it, under the variant(s) it can be;
                # its share alone could match another variant by coincidence (25.7% unweighted)
                sized = [w for w, v in c["counts"].items() if v and any(0.5 * v <= x <= 2 * v for x in cs)]
                if sized:
                    return any(_close_count(x, c["counts"][w]) for x in cs for w in sized)
                return any(_close_share(x, p) for x in ss for p in c["shares"].values())

            if any(agrees(c) for c in cands):
                n_ok += 1
                continue
            # a row is judged only against a field whose count it is plausibly reporting
            near = [c for c in cands if any(v and 0.5 * v <= x <= 2 * v for x in cs for v in c["counts"].values())]
            if not near:
                continue
            n_bad += 1
            parts = []
            for c in near:
                best = max(c["counts"], key=lambda w: (w != "", c["counts"][w]))
                parts.append(f"{c['field']}={c['code']}: {c['counts'][best]:,.0f} ({c['shares'].get(best, 0):.1f}%"
                             f"{', משוקלל ב-' + best if best else ', ללא שקלול'})")
            fx.add("warning", "report", " / ".join(c["where"] for c in near), "report_figure_mismatch",
                   f"'{label}': בדוח '{row}', בקבצים " + "; ".join(parts),
                   "", "בדוק את החישוב בדוח מול הקבצים - אחד מהם אינו מעודכן")
    fx.add("info", "report", rep, "report_check_summary",
           f"השוואת הדוח לקבצים: {n_ok} נתונים תואמים, {n_bad} אינם תואמים",
           "בדיקת שפיות בלבד: נבדקים מספר הרשומות, סכומי המשקלות, ושורות טבלה בדוח שמתחילות בתווית של קוד מתועד (ספירה ואחוז, ללא שקלול ובכל עמודת משקל)")
