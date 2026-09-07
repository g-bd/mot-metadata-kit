"""Render findings as a self-contained Hebrew (RTL) HTML report with LTR tables."""
from __future__ import annotations

import datetime as _dt
import html
import json
from pathlib import Path
from typing import Any, Optional

SEV_HE = {"error": "שגיאה", "warning": "אזהרה", "info": "הערה"}
SEC_HE = {"header": "כותרת (טבלה 1)", "survey": "בלוק הסקר (טבלה 2)", "files": "תיאור הקבצים (טבלה 3)", "fields": "תיאור השדות (טבלה 4)",
          "keys": "רשימת מפתחות", "naming": "כללי שמות (5.7)", "folder": "התאמה לתיקייה", "profile": "פורמט ייעודי", "spec": "גרסת הנוהל",
          "outputs": "פלטי הערכה (שלמות הקידוד)"}
SEC_ORDER = ["header", "survey", "files", "fields", "keys", "folder", "naming", "profile", "outputs", "spec"]


def _e(v: Any) -> str:
    return html.escape("" if v is None else str(v))


def _ltr(v: Any) -> str:
    return f"<span dir='ltr'>{_e(v)}</span>"


def render_report(findings: list[dict], summary: dict, meta: Optional[dict] = None, scan: Optional[dict] = None, spec_info: Optional[dict] = None, title: Optional[str] = None) -> str:
    counts = summary.get("counts", {})
    ok = counts.get("error", 0) == 0
    t = title or (meta or {}).get("Title") or "דוח בדיקת מטא-דאטה"
    gl = (spec_info or {}).get("guideline", {})
    ps = (spec_info or {}).get("profile_spec") or {}
    now = _dt.datetime.now().strftime("%d/%m/%Y %H:%M")
    # sections
    sections = []
    for sec in SEC_ORDER:
        rows = [f for f in findings if f["section"] == sec]
        if not rows:
            continue
        trs = []
        for f in rows:
            exempt = " <span class='bucket'>הפורמט אינו דורש</span>" if f.get("bucket") == "kit_format_exempt" else ""
            trs.append(f"<tr class='{f['severity']}'><td class='sev'>{SEV_HE[f['severity']]}{exempt}</td><td class='where'>{_ltr(f['where'])}</td>"
                       f"<td class='msg'>{_e(f['msg'])}{('<div class=detail>' + _e(f['detail']) + '</div>') if f.get('detail') else ''}</td>"
                       f"<td class='fix'>{_e(f.get('fix',''))}</td><td class='code'>{_ltr(f['code'])}</td></tr>")
        c = {s: sum(1 for f in rows if f["severity"] == s) for s in ("error", "warning", "info")}
        sections.append(f"""<section><h2>{SEC_HE.get(sec, sec)} <span class='badges'><b class='e'>{c['error']}</b><b class='w'>{c['warning']}</b><b class='i'>{c['info']}</b></span></h2>
<table class='f' dir='ltr'><thead><tr><th class='rtl'>חומרה</th><th>where</th><th class='rtl'>ממצא</th><th class='rtl'>תיקון מוצע</th><th>code</th></tr></thead><tbody>{''.join(trs)}</tbody></table></section>""")
    # inventory
    inv = ""
    if scan:
        rows = []
        for e in scan["files"]:
            if e["role"] == "sidecar":
                continue
            nf = len(e.get("fields") or [])
            extra = ""
            if e.get("kind") == "gis":
                extra = f"{e.get('geometry_type','')} · {((e.get('crs') or {}).get('mot_value') or '?')}"
            elif e.get("format") == "ZIP":
                extra = "GTFS" if e.get("gtfs") else f"{e.get('n_members', 0)} קבצים בארכיון"
            elif e.get("encoding"):
                extra = e["encoding"]
            rows.append(f"<tr><td>{_ltr(e['name'])}</td><td>{_e(e['role'])}</td><td>{_ltr(e.get('format') or e['ext'])}</td><td>{_e(e.get('size') or e['size_mb'])}</td><td>{e.get('n_rows','')}</td><td>{nf or ''}</td><td>{_ltr(extra)}</td><td>{_e(e.get('error',''))}</td></tr>")
        inv = f"""<section><h2>מצאי התיקייה</h2><div class='sub'>{_ltr(scan['folder'])} · {scan['n_files']} קבצים · {_e(scan.get('total_size') or (str(scan['total_size_mb']) + ' MB'))}</div>
<table class='f' dir='ltr'><thead><tr><th>file</th><th>role</th><th>format</th><th>size</th><th>rows</th><th>fields</th><th>notes</th><th>error</th></tr></thead><tbody>{''.join(rows)}</tbody></table></section>"""
    todo = (meta or {}).get("_meta", {}).get("todo") or []
    refused = (meta or {}).get("_meta", {}).get("refused_wording") or []
    todo_html = ""
    if todo:
        todo_html = f"<section><h2>פריטים להשלמה ידנית (TODO)</h2><ol dir='ltr'>{''.join('<li>' + _e(x) + '</li>' for x in todo)}</ol></section>"
    if refused:
        items = "".join(f"<li><b>{_e(r['key'])}</b>: הנוסח '{_e(r['value'])}' לא נכתב (מכיל '{_e(r['term'])}') – הערך הוחזר ל-TODO</li>" for r in refused)
        todo_html += f"<section><h2>נוסח שנדחה בכיסוי המרחבי</h2><p class='sub'>כיסוי מרחבי נכתב בשמות המנהליים הרשמיים (ארצי / מטרופולין / יישוב / מחוז / אזור יהודה ושומרון), לא בכינוי פוליטי.</p><ul>{items}</ul></section>"
    # KP-28: a value the publisher documented as unknown is an answer, and a different thing
    # from a TODO - so it is printed as its own list and never inside the one above.
    unknown = [f for f in findings if f.get("code") == "value_unknown_documented"]
    unknown_html = ""
    if unknown:
        items = "".join("<li><b dir='ltr'>" + _e(f["where"]) + "</b> – " + _e(f["msg"]) + "</li>" for f in unknown)
        unknown_html = ("<section><h2>ערכים שתועדו כלא ידועים</h2>"
                        "<p class='sub'>אלו תשובות, לא פריטים שנותרו להשלמה – נרשמו במפורש ונשארים גלויים.</p>"
                        f"<ul>{items}</ul></section>")
    verdict = "המטא-דאטה עומד בדרישות הנוהל (אין שגיאות)" if ok else f"נמצאו {counts.get('error',0)} שגיאות שיש לתקן לפני הפצה"
    n_exempt = (summary.get("buckets") or {}).get("kit_format_exempt", 0)
    exempt_kpi = f"<div class='kpi'><b>{n_exempt}</b>ממצאים שהפורמט אינו דורש</div>" if n_exempt else ""
    return f"""<!doctype html><html lang='he' dir='rtl'><head><meta charset='utf-8'><title>{_e(t)} – דוח מטא-דאטה</title>
<style>
 body {{ font-family: Arial, 'Segoe UI', 'Noto Sans Hebrew', sans-serif; font-size: 13px; color:#1b1b1b; background:#fafafa; margin:0; }}
 main {{ max-width: 1180px; margin: 0 auto; padding: 20px 24px 60px; background:#fff; }}
 h1 {{ font-size: 22px; margin: 0 0 4px; }} h2 {{ font-size: 16px; margin: 26px 0 8px; border-bottom: 2px solid #2b4c7e; padding-bottom: 3px; }}
 .sub {{ color:#666; font-size: 12px; }}
 .verdict {{ margin: 14px 0; padding: 12px 16px; border-radius: 8px; font-size: 15px; font-weight: 600; }}
 .verdict.ok {{ background:#e7f6e7; color:#1e6b1e; border:1px solid #9ccc9c; }} .verdict.bad {{ background:#fdecea; color:#8b1a12; border:1px solid #f1a9a0; }}
 .kpis {{ display:flex; gap:12px; flex-wrap:wrap; margin: 10px 0 4px; }}
 .kpi {{ flex:1; min-width:130px; padding:10px 14px; border-radius:8px; background:#f3f5f9; border:1px solid #dde3ee; }}
 .kpi b {{ display:block; font-size: 22px; }} .kpi.e b {{ color:#b3261e; }} .kpi.w b {{ color:#b26a00; }} .kpi.i b {{ color:#2b4c7e; }}
 table.f {{ border-collapse: collapse; width:100%; font-size: 12.5px; }}
 table.f {{ direction: ltr; }}
 table.f th, table.f td {{ border:1px solid #d6d6d6; padding: 5px 7px; vertical-align: top; text-align: left; }}
 table.f th.rtl, td.sev, td.msg, td.fix {{ direction: rtl; text-align: right; }}
 td.sev {{ white-space: nowrap; }}
 table.f th {{ background:#eef2f8; }}
 tr.error td.sev {{ color:#b3261e; font-weight:700; }} tr.warning td.sev {{ color:#b26a00; font-weight:700; }} tr.info td.sev {{ color:#2b4c7e; }}
 td.where, td.code {{ direction:ltr; text-align:left; font-family: Consolas, monospace; font-size: 11.5px; white-space: pre-wrap; }}
 td.code {{ color:#888; }} .detail {{ color:#666; font-size: 11.5px; margin-top: 3px; }}
 .bucket {{ display:inline-block; font-size:10.5px; font-weight:400; color:#4a4a4a; background:#efefef; border:1px solid #ddd; border-radius:8px; padding:0 5px; margin-inline-start:4px; }}
 .badges b {{ display:inline-block; min-width:22px; text-align:center; border-radius:10px; padding:1px 7px; margin-inline-start:4px; font-size:12px; color:#fff; }}
 .badges b.e {{ background:#b3261e; }} .badges b.w {{ background:#b26a00; }} .badges b.i {{ background:#2b4c7e; }}
 span[dir=ltr] {{ unicode-bidi: embed; }}
 footer {{ margin-top: 40px; color:#777; font-size: 11px; }}
</style></head><body><main>
<h1>דוח בדיקת מטא-דאטה – {_e(t)}</h1>
<div class='sub'>לפי {_e(gl.get('name',''))} גרסה {_e(gl.get('version',''))} ({_e(gl.get('date',''))}){(' · פרופיל: ' + _e(ps.get('name')) + ' גרסה ' + _e(ps.get('version'))) if ps else ''} · הופק {now}</div>
<div class='verdict {'ok' if ok else 'bad'}'>{verdict}</div>
<div class='kpis'><div class='kpi e'><b>{counts.get('error',0)}</b>שגיאות</div><div class='kpi w'><b>{counts.get('warning',0)}</b>אזהרות</div><div class='kpi i'><b>{counts.get('info',0)}</b>הערות</div>
<div class='kpi'><b>{summary.get('n_files_described',0)}</b>קבצים מתוארים</div><div class='kpi'><b>{summary.get('n_fields_described',0)}</b>שדות מתוארים</div>
<div class='kpi'><b>{_e(summary.get('dataset_kind') or '?')}</b>סוג סט הנתונים{' · בלוק סקר נבדק' if summary.get('survey_block_checked') else ''}</div>{exempt_kpi}</div>
<div class='sub'>מקור המטא-דאטה: {_ltr(summary.get('metadata_source') or '—')} · תיקייה: {_ltr(summary.get('folder') or '—')}</div>
<p class='sub'>הדוח בודק מבנה, שלמות והתאמה בין המטא-דאטה לקבצים בלבד – הוא אינו בודק את נכונות הנתונים עצמם.</p>
{''.join(sections) if sections else '<p>לא נמצאו ממצאים.</p>'}
{todo_html}
{unknown_html}
{inv}
<footer>mot-metadata-kit · {now}</footer>
</main></body></html>"""


def write_findings_json(findings: list[dict], summary: dict, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "findings": list(findings)}, f, ensure_ascii=False, indent=2)
