#!/usr/bin/env python3
"""mot_metadata - create / validate / report MoT dataset metadata (נוהל הפצת מידע תחבורתי v1.3).

Usage (run from anywhere; the script finds its own references/ and profiles):

  python mot_metadata.py scan      <folder> [--recursive] [--out scan.json]
  python mot_metadata.py init      <folder> [--profile onboard|sensors]        # write metadata-config.json template
  python mot_metadata.py build     <folder> [--profile P] [--config FILE] [--name NAME] [--formats json,xlsx,pdf,csv] [--force] [--allow-unverified-pdf]
  python mot_metadata.py validate  <folder> [--metadata FILE] [--profile P] [--kind survey|monitoring|...] [--deep values,temporal,joins,zones] [--report FILE] [--findings FILE]
  python mot_metadata.py render    <metadata.json|xlsx> [--profile P] [--pdf FILE] [--html FILE]
  python mot_metadata.py package   <folder> [--metadata FILE] [--out FILE.zip]   # build the הפצה zip + checklist
  python mot_metadata.py check-spec [--online]
  python mot_metadata.py setup                    # install / verify dependencies (also done automatically on first run)

Exit codes: 0 ok, 1 validation errors found, 2 usage / runtime error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

REQUIRED = {"openpyxl": "openpyxl>=3.1"}
OPTIONAL = {"shapefile": "pyshp>=2.3", "pyproj": "pyproj>=3.4", "xlrd": "xlrd>=2.0", "pyarrow": "pyarrow>=14",
            "pypdf": "pypdf>=4.0"}


def ensure_deps(install_optional: bool = False, quiet: bool = True) -> list[str]:
    """Install missing Python packages with pip (user site if needed). Returns the list installed."""
    import importlib
    import subprocess
    installed = []
    wanted = dict(REQUIRED)
    if install_optional:
        wanted.update(OPTIONAL)
    for mod, req in wanted.items():
        try:
            importlib.import_module(mod)
        except ImportError:
            cmd = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", req]
            if quiet:
                cmd.insert(4, "-q")
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:  # retry in the user site (no admin rights)
                r = subprocess.run(cmd + ["--user"], capture_output=True, text=True)
            if r.returncode == 0:
                installed.append(req)
            elif mod in REQUIRED:
                sys.stderr.write(f"cannot install {req}: {r.stderr[-300:]}\n")
                sys.exit(2)
    return installed


if "--no-auto-install" not in sys.argv:
    _inst = ensure_deps()
    if _inst:
        print("installed missing packages: " + ", ".join(_inst))

from motmeta.spec import Spec, BUILTIN_PROFILES, SKILL_DIR  # noqa: E402
from motmeta.scan import scan_folder  # noqa: E402
from motmeta.build import build_metadata, default_config, load_config, suggested_metadata_basename, config_from_metadata, CONFIG_NAME  # noqa: E402
from motmeta.io import (read_metadata, write_json, write_xlsx, write_csv, metadata_html, html_to_pdf,
                        assert_hebrew_roundtrip, hebrew_sample_strings)  # noqa: E402
from motmeta.validate import validate  # noqa: E402
from motmeta.report import render_report, write_findings_json  # noqa: E402

META_RE = re.compile(r"metadata", re.I)


def _out(msg: str) -> None:
    """Print a line, and SAY SO when the console could not carry it (KP-R3).

    The fallback stays - a cp1255 console must not crash the run - but a line that came out
    with `?` in it is marked, so nobody ever copies a degraded line back into a config file
    believing it is the value the kit computed.
    """
    try:
        print(msg)
    except UnicodeEncodeError:  # Windows consoles with cp1255/cp437
        enc = getattr(sys.stdout, "encoding", None) or "ascii"
        degraded = ("[console: degraded encoding] " + msg).encode(enc, "replace").decode(enc, "replace")
        try:
            print(degraded)
        except Exception:
            print(degraded.encode("ascii", "replace").decode("ascii", "replace"))


def _ensure_pypdf(allowed: bool) -> bool:
    """pypdf reads the PDF back to prove its Hebrew is really there. Optional: without it the
    PDF check is skipped with an `info`, never guessed at."""
    import importlib
    try:
        importlib.import_module("pypdf")
        return True
    except ImportError:
        pass
    if not allowed:
        return False
    return bool(ensure_deps_for({"pypdf": OPTIONAL["pypdf"]}))


def ensure_deps_for(wanted: dict) -> list[str]:
    import importlib
    import subprocess
    installed = []
    for mod, req in wanted.items():
        try:
            importlib.import_module(mod)
            continue
        except ImportError:
            pass
        cmd = [sys.executable, "-m", "pip", "install", "-q", "--disable-pip-version-check", req]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            r = subprocess.run(cmd + ["--user"], capture_output=True, text=True)
        if r.returncode == 0:
            installed.append(req)
    return installed


def find_metadata_file(folder: Path) -> Path | None:
    cands = sorted([p for p in folder.iterdir() if p.is_file() and META_RE.search(p.name) and p.suffix.lower() in (".xlsx", ".json")],
                   key=lambda p: (p.suffix != ".xlsx", p.name))
    return cands[0] if cands else None


# --------------------------------------------------------------------------- commands
def cmd_scan(a) -> int:
    s = scan_folder(a.folder, recursive=not a.no_recursive)
    out = Path(a.out) if a.out else Path(a.folder) / "scan.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)
    _out(f"scanned {s['n_files']} files ({s['n_data_files']} data) -> {out}")
    for e in s["files"]:
        if e["role"] == "sidecar":
            continue
        _out(f"  [{e['role']:8}] {e['name']}  {e.get('format', e['ext'])}  {e['size_mb']} MB  rows={e.get('n_rows', '')}  fields={len(e.get('fields') or [])}" + (f"  ERROR {e['error']}" if e.get("error") else ""))
    return 0


def cmd_init(a) -> int:
    folder = Path(a.folder)
    cfg_path = folder / CONFIG_NAME
    if cfg_path.exists() and not a.force:
        _out(f"{cfg_path} already exists (use --force to overwrite)")
        return 0
    spec = Spec(a.profile)
    cfg = default_config(a.profile, spec)
    s = scan_folder(folder)
    cfg["dataset_name"] = re.sub(r"[^A-Za-z0-9_]+", "_", folder.name).strip("_") or "dataset"
    if spec.dataset_kind:
        cfg["dataset_kind"] = spec.dataset_kind
    cfg["files"] = {}
    for e in s["files"]:
        if e["role"] != "data":
            continue
        dh = e.get("doc_hints") or {}
        entry = {"File description": (dh.get("file", {}).get("auto") or {}).get("text", ""), "fields": {}}
        if dh.get("file", {}).get("mentions"):
            entry["_hints"] = [m["text"] for m in dh["file"]["mentions"]]
        for c in (e.get("fields") or []):
            fh = (dh.get("fields") or {}).get(c["name"]) or {}
            fe = {"Description": (fh.get("auto") or {}).get("text", "")}
            if fh.get("mentions"):
                fe["_hints"] = [m["text"] for m in fh["mentions"]]
            if c.get("candidate_values"):
                fe["_values_seen"] = c["candidate_values"]
            entry["fields"][c["name"]] = fe
        cfg["files"][e["name"]] = entry
    dhs = s.get("doc_harvest", {})
    cfg["_doc_harvest"] = dhs
    cfg["_questions"] = [
        "dataset_kind: survey (סקר סטטיסטי – מחייב בלוק סקר) / monitoring / administrative / gis / model / other",
        "header.Publisher, header.Contact (+Email), header.Author (אם שונה מהמפרסם)",
        "header.Title, header.Description (שורות), header.Keywords (מנספח א'), header.Temporal coverage, header.Spatial coverage (ארצי / מטרופולין / יישוב / מחוז – בשמות מנהליים רשמיים; הנוסח 'השטחים הכבושים' אינו נכתב לעולם)",
        "header.Version / Frequency of update / License / Legal constrains (אם רלוונטי)",
        "files.<name>.File description לכל קובץ, ו-Description לכל שדה (Values לשדות מקודדים)",
        "keys: file.field -> file.field (אם לא יזוהו אוטומטית)",
    ] + [q["q"] for q in spec.profile.get("intake_questions", [])]
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    _out(f"wrote {cfg_path} - fill in the answers (see _questions) then run: build")
    return 0


def _write_outputs(meta, spec, out_dir: Path, base: str, formats: list[str], include_survey: bool, force: bool,
                   verify: bool = True) -> tuple[dict, list[dict]]:
    """Write every requested format and, KP-R3, read each one back to prove its Hebrew survived."""
    written = {}
    checks: list[dict] = []
    samples = hebrew_sample_strings(meta, int(spec.encoding_integrity.get("roundtrip_sample", 20)))

    def verify_one(path: Path):
        if not verify:
            return
        chk = assert_hebrew_roundtrip(path, samples, spec.encoding_integrity)
        checks.append(chk)
        if chk.get("skipped"):
            _out(f"  check {path.name}: skipped - {chk['skipped']}")
        elif not chk["ok"]:
            _out(f"  check {path.name}: HEBREW DID NOT SURVIVE - {chk['detail']}")

    for fmt in formats:
        p = out_dir / f"{base}.{fmt}"
        if p.exists() and not force:
            _out(f"  skip {p.name} (exists; use --force)")
            continue
        if fmt == "json":
            write_json(meta, p)
        elif fmt == "xlsx":
            write_xlsx(meta, p, spec, include_survey)
        elif fmt == "csv":
            write_csv(meta, p, spec, include_survey)
        elif fmt in ("pdf", "html"):
            h = metadata_html(meta, spec, include_survey)
            if fmt == "html":
                p.write_text(h, encoding="utf-8")
            else:
                ok, msg = html_to_pdf(h, p)
                if not ok:
                    hp = out_dir / f"{base}.html"
                    hp.write_text(h, encoding="utf-8")
                    _out(f"  pdf: {msg}; wrote {hp.name} instead")
                    written["html"] = str(hp)
                    verify_one(hp)
                    continue
        else:
            _out(f"  unknown format {fmt}")
            continue
        written[fmt] = str(p)
        _out(f"  wrote {p}")
        verify_one(p)
    return written, checks


def _roundtrip_findings(checks: list[dict], fx, spec, allow_unverified_pdf: bool) -> int:
    """Turn the round-trip results into findings, and say what the exit code must be (KP-R3).

    A json/xlsx/csv/html output that does not come back as it was written is the KIT's bug, not
    the user's data - it exits 2, the code the CLI already uses for "the tool failed". A PDF
    whose Hebrew cannot be extracted is a rendering problem (a font without Hebrew glyphs, a
    browser that printed nothing): it is reported and it still fails the build, because a PDF
    of question marks is what a ministry reviewer would open - unless the operator has said
    --allow-unverified-pdf.
    """
    ei = spec.encoding_integrity
    worst = 0
    for chk in checks:
        name = Path(chk["path"]).name
        if chk.get("skipped"):
            fx.add("info", "outputs", name, "output_roundtrip_skipped",
                   f"העברית בקובץ '{name}' לא אומתה", chk["skipped"],
                   "התקן pypdf (pip install pypdf) כדי לאמת שהעברית ב-PDF באמת נדפסה")
            continue
        if chk["ok"]:
            continue
        if chk["format"] == "pdf":
            fx.add(spec.encoding_severity("pdf_hebrew_not_rendered", "warning"), "outputs", name,
                   "pdf_hebrew_not_rendered",
                   f"לא ניתן לחלץ את העברית מ-'{name}' – ייתכן שה-PDF הודפס ללא גופן עברי",
                   chk.get("detail", ""), ei.get("pdf_font_hint", ""))
            if not allow_unverified_pdf:
                worst = max(worst, 1)
        else:
            missing = ", ".join(chk.get("missing") or [])
            fx.add(spec.encoding_severity("output_roundtrip_failed"), "outputs", name,
                   "output_roundtrip_failed",
                   f"הפלט '{name}' לא חזר כפי שנכתב – העברית שבו נפגעה",
                   (chk.get("detail", "") + (f" · חסר: {missing}" if missing else "")).strip(),
                   "זהו באג של הערכה עצמה, לא של הנתונים – אין להפיץ את הקובץ; דווח עליו")
            worst = 2
    return worst


def cmd_build(a) -> int:
    folder = Path(a.folder).resolve()
    cfg = load_config(folder, Path(a.config) if a.config else None)
    profile = a.profile or cfg.get("profile")
    spec = Spec(profile)
    if a.from_metadata:
        old = read_metadata(Path(a.from_metadata), spec)
        seed = config_from_metadata(old, spec)
        # explicit config answers win over values copied from the old document
        norm = lambda x: re.sub(r"[​-‏‪-‮﻿]", "", str(x)).strip().lower()
        merged_files = {norm(k): v for k, v in seed["files"].items()}
        for n, fc in cfg.get("files", {}).items():
            tgt = merged_files.setdefault(norm(n), {"fields": {}})
            tgt.setdefault("fields", {})
            tgt.update({k: v for k, v in fc.items() if k != "fields"})
            for fname, fd in fc.get("fields", {}).items():
                key = next((k for k in tgt["fields"] if norm(k) == norm(fname)), fname)
                tgt["fields"].setdefault(key, {}).update(fd)
        cfg = {**seed, **{k: v for k, v in cfg.items() if k not in ("header", "files", "keys")},
               "header": {**seed["header"], **cfg.get("header", {})}, "files": merged_files,
               "keys": cfg.get("keys") or seed["keys"], "dataset_name": cfg.get("dataset_name") or seed.get("dataset_name")}
        _out(f"seeded config from {a.from_metadata}: {len(seed['header'])} header keys, {len(seed['files'])} files")
    if a.name:
        cfg["dataset_name"] = a.name
    if a.kind:
        cfg["dataset_kind"] = a.kind
    gl = spec.base["spec"]
    ps = spec.profile.get("spec") if spec.profile else None
    _out(f"spec snapshot: {gl['name']} v{gl['version']} ({gl['date']})" + (f" + {ps['name']} v{ps['version']}" if ps else "")
         + " — check gov.il for newer versions (check-spec)")
    meta, scan = build_metadata(folder, spec, cfg)
    out_dir = Path(a.out_dir) if a.out_dir else folder
    out_dir.mkdir(parents=True, exist_ok=True)
    base = a.basename or suggested_metadata_basename(meta, cfg, spec)
    formats = [f.strip() for f in a.formats.split(",") if f.strip()]
    include_survey = meta["_meta"]["survey_block"]
    _out(f"profile={spec.profile_name} kind={meta['_meta']['dataset_kind']} files={len(meta['Files'])} todo={len(meta['_meta']['todo'])}")
    if "pdf" in formats:
        _ensure_pypdf(not a.no_auto_install)
    written, checks = _write_outputs(meta, spec, out_dir, base, formats, include_survey, a.force)
    # always validate what we just built
    deep = {x.strip() for x in (a.deep or "").split(",") if x.strip()}
    fx, summary = validate(meta, spec, folder, scan, deep=deep)
    rt = _roundtrip_findings(checks, fx, spec, a.allow_unverified_pdf)
    summary["counts"], summary["buckets"] = fx.counts(), fx.buckets()
    summary["output_checks"] = checks
    summary["metadata_source"] = written.get("json") or written.get("xlsx") or "(in-memory)"
    rep = out_dir / (a.report or "metadata-report.html")
    rep.write_text(render_report(fx, summary, meta, scan, spec.describe()), encoding="utf-8")
    write_findings_json(fx, summary, out_dir / "findings.json")
    c = summary["counts"]
    _out(f"report: {rep}  (errors={c['error']} warnings={c['warning']} info={c['info']})")
    if meta["_meta"]["todo"]:
        _out("TODO items to complete in metadata-config.json (then re-run build --force):")
        for t in meta["_meta"]["todo"][:40]:
            _out(f"  - {t}")
        if len(meta["_meta"]["todo"]) > 40:
            _out(f"  ... and {len(meta['_meta']['todo']) - 40} more (see report)")
    if rt == 2:
        _out("an output the kit wrote did not come back with its Hebrew intact - see findings.json (output_roundtrip_failed)")
        return 2
    if rt:
        _out("the PDF's Hebrew could not be verified - re-run with --allow-unverified-pdf to accept it anyway")
    return 1 if (c["error"] or rt) else 0


def cmd_validate(a) -> int:
    target = Path(a.folder).resolve()
    if target.is_file():
        meta_path, folder = target, target.parent
    else:
        folder = target
        meta_path = Path(a.metadata) if a.metadata else find_metadata_file(folder)
    if not meta_path or not Path(meta_path).exists():
        _out("no metadata file found (expected *metadata*.xlsx or *metadata*.json; use --metadata)")
        return 2
    cfg = load_config(folder)
    profile = a.profile or cfg.get("profile")
    spec = Spec(profile)
    meta = read_metadata(Path(meta_path), spec)
    kind = a.kind or cfg.get("dataset_kind") or meta.get("_meta", {}).get("dataset_kind")
    if kind and "|" in kind:
        kind = None
    exclude = set(cfg.get("exclude", [])) | {CONFIG_NAME, "metadata-report.html", "findings.json", "scan.json"}
    scan = None if a.no_folder else scan_folder(folder, recursive=bool(cfg.get("recursive", True)), exclude=exclude)
    deep = {x.strip() for x in (a.deep or "").split(",") if x.strip()}
    fx, summary = validate(meta, spec, folder if not a.no_folder else None, scan=scan, dataset_kind=kind, deep=deep)
    out_dir = Path(a.out_dir) if a.out_dir else folder
    out_dir.mkdir(parents=True, exist_ok=True)      # as cmd_build already does
    rep = Path(a.report) if a.report else out_dir / "metadata-report.html"
    rep.parent.mkdir(parents=True, exist_ok=True)
    rep.write_text(render_report(fx, summary, meta, scan, spec.describe()), encoding="utf-8")
    write_findings_json(fx, summary, Path(a.findings) if a.findings else out_dir / "findings.json")
    c = summary["counts"]
    _out(f"validated {meta_path} against guideline {spec.base['spec']['version']} profile={spec.profile_name} kind={summary['dataset_kind']}")
    _out(f"errors={c['error']} warnings={c['warning']} info={c['info']} -> {rep}")
    for f in fx:
        if f["severity"] == "error":
            _out(f"  E {f['where']}: {f['msg']}")
    return 1 if c["error"] else 0


def cmd_render(a) -> int:
    spec = Spec(a.profile)
    meta = read_metadata(Path(a.metadata), spec)
    include_survey = any(k in meta for k in ("Statistical population", "Survey method"))
    h = metadata_html(meta, spec, include_survey)
    base = Path(a.metadata).with_suffix("")
    if a.html or not a.pdf:
        hp = Path(a.html) if a.html else base.with_suffix(".html")
        hp.write_text(h, encoding="utf-8")
        _out(f"wrote {hp}")
    samples = hebrew_sample_strings(meta, int(spec.encoding_integrity.get("roundtrip_sample", 20)))
    if a.html or not a.pdf:
        chk = assert_hebrew_roundtrip(hp, samples, spec.encoding_integrity)
        if not chk["ok"]:
            _out(f"html: HEBREW DID NOT SURVIVE - {chk['detail']}")
            return 2
    if a.pdf:
        _ensure_pypdf(not a.no_auto_install)
        ok, msg = html_to_pdf(h, Path(a.pdf))
        _out(f"pdf: {msg}")
        if not ok:
            return 2
        chk = assert_hebrew_roundtrip(Path(a.pdf), samples, spec.encoding_integrity)
        if chk.get("skipped"):
            _out(f"pdf check skipped: {chk['skipped']}")
        elif not chk["ok"]:
            _out(f"pdf: the Hebrew could not be verified - {chk['detail']}")
            _out(spec.encoding_integrity.get("pdf_font_hint", ""))
            return 0 if a.allow_unverified_pdf else 1
    return 0


def cmd_setup(a) -> int:
    import importlib
    import platform
    _out(f"python {platform.python_version()} at {sys.executable}")
    if sys.version_info < (3, 10):
        _out("python 3.10+ is required")
        return 2
    inst = ensure_deps(install_optional=True, quiet=False)
    if inst:
        _out("installed: " + ", ".join(inst))
    for mod, req in {**REQUIRED, **OPTIONAL}.items():
        try:
            importlib.import_module(mod)
            _out(f"  ok   {req}")
        except ImportError:
            _out(f"  MISSING {req} (optional)" if mod in OPTIONAL else f"  MISSING {req}")
    from motmeta.io import find_browsers
    b = find_browsers()
    _out(f"  pdf  {'browser found: ' + b[0] if b else 'no Chromium/Edge found - PDF output will fall back to HTML (set MOTMETA_BROWSER)'}")
    _out("setup complete")
    return 0


def cmd_package(a) -> int:
    """Build the distribution ZIP named by `Dataset file`: data files of Files list + metadata files + Related documents."""
    import zipfile
    folder = Path(a.folder).resolve()
    cfg = load_config(folder)
    spec = Spec(a.profile or cfg.get("profile"))
    meta_path = Path(a.metadata) if a.metadata else find_metadata_file(folder)
    if not meta_path or not meta_path.exists():
        _out("no metadata file found (use --metadata)")
        return 2
    meta = read_metadata(meta_path, spec)
    from motmeta.io import as_lines, to_text
    from motmeta.scan import SHP_SIDECARS
    inv = lambda x: re.sub(r"[​-‏‪-‮﻿]", "", x)
    ds = to_text(meta.get("Dataset file")) or f"{folder.name}.zip"
    if not ds.lower().endswith(".zip"):
        ds += ".zip"
    out = Path(a.out) if a.out else folder / ds
    wanted: list[str] = []
    for n in as_lines(meta.get("Files list")):
        n = inv(to_text(n))
        if "/" in n and (folder / n.split("/")[0]).suffix.lower() == ".zip":
            n = n.split("/")[0]          # member of an archive: pack the archive once
        if n not in wanted:
            wanted.append(n)
    docs = [inv(to_text(d)) for d in as_lines(meta.get("Related documents")) if not re.match(r"^https?://", to_text(d), re.I)]
    meta_files = [p for p in folder.iterdir() if p.is_file() and META_RE.search(p.name) and p.suffix.lower() in (".xlsx", ".json", ".pdf", ".csv", ".html")
                  and not p.name.startswith("metadata-report") and p.name != "metadata-config.json"]
    problems, members = [], []
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        def add(rel: str, arc: str | None = None):
            p = folder / rel
            if not p.exists():
                problems.append(f"missing: {rel}")
                return
            zf.write(p, arc or rel)
            members.append(arc or rel)
            if p.suffix.lower() == ".shp":
                for sc in p.parent.iterdir():
                    if sc.with_suffix("") == p.with_suffix("") and sc.suffix.lower() in SHP_SIDECARS:
                        zf.write(sc, str(Path(rel).with_suffix(sc.suffix)))
                        members.append(str(Path(rel).with_suffix(sc.suffix)))
        for n in wanted:
            add(n)
        for d in docs:
            if d not in wanted:
                add(d)
        for mp in meta_files:
            if mp.resolve() == out.resolve():
                continue
            add(str(mp.relative_to(folder)))
    # checklist
    listed = {inv(to_text(x)).lower() for x in as_lines(meta.get("Files list"))}
    inzip = {m.lower() for m in members}
    extra_in_folder = [str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file() and p.resolve() != out.resolve()
                       and str(p.relative_to(folder)).replace("\\", "/").lower() not in inzip
                       and p.suffix.lower() not in SHP_SIDECARS and not p.name.startswith(("metadata-report", "findings", "scan.json", "metadata-config", "fix-", "_mot_backup"))
                       and not any(part.startswith(("_mot_backup", ".")) for part in p.relative_to(folder).parts)]
    checklist = {
        "zip": str(out), "members": members, "size_mb": round(out.stat().st_size / 1048576, 2),
        "dataset_file_in_metadata": ds, "files_list_count": len(listed), "problems": problems,
        "in_folder_not_packed": extra_in_folder[:200],
        "checks": {
            "zip_name_matches_dataset_file": out.name == ds,
            "all_files_list_present": not any(p.startswith("missing") for p in problems),
            "metadata_inside": any(META_RE.search(m) for m in members),
            "related_documents_inside": all(d.lower() in inzip for d in docs),
        },
    }
    (folder / "package-checklist.json").write_text(json.dumps(checklist, ensure_ascii=False, indent=2), encoding="utf-8")
    _out(f"packed {len(members)} members -> {out} ({checklist['size_mb']} MB)")
    for k, v in checklist["checks"].items():
        _out(f"  [{'ok' if v else 'NO'}] {k}")
    for p in problems:
        _out(f"  ! {p}")
    if extra_in_folder:
        _out(f"  note: {len(extra_in_folder)} file(s) in the folder were not packed (not in Files list / Related documents) - see package-checklist.json")
    return 1 if problems or not all(checklist["checks"].values()) else 0


def cmd_check_spec(a) -> int:
    src = SKILL_DIR / "references" / "spec-sources.json"
    with open(src, encoding="utf-8") as f:
        sources = json.load(f)
    _out("bundled spec snapshots:")
    for s in sources["sources"]:
        _out(f"  {s['id']:10} v{s['version'] or '?':6} {s['date'] or '-':11} {s.get('page') or '(no page yet)'}")
    for r in sources.get("profile_revisions", []):
        _out(f"  profile '{r['profile']}' revised in kit {r['kit_version']} ({r['date']}) - spec text unchanged ({r['spec_version_unchanged']})")
        _out(f"    source: {r['source']}")
    if not a.online:
        _out("run with --online to compare with gov.il (needs a browser session or working network; gov.il blocks plain HTTP clients)")
        return 0
    try:
        import urllib.request
        changed = False
        for s in sources["sources"]:
            if not s.get("page"):
                continue
            req = urllib.request.Request(s["page"], headers={"User-Agent": "Mozilla/5.0"})
            try:
                body = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
            except Exception as e:
                _out(f"  {s['id']}: fetch failed ({e}) - open the page manually and compare the version/date")
                continue
            m = re.findall(s.get("version_regex", r"(\d+\.\d+)"), body)
            found = sorted(set(m))
            if found and s["version"] not in found:
                _out(f"  {s['id']}: NEWER VERSION CANDIDATE online {found} (bundled {s['version']}) - update references/")
                changed = True
            else:
                _out(f"  {s['id']}: no newer version detected ({found or 'page is JS-rendered; verify manually'})")
        return 1 if changed else 0
    except Exception as e:
        _out(f"online check failed: {e}")
        return 2


# --------------------------------------------------------------------------- main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="mot_metadata", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("scan"); p.add_argument("folder"); p.add_argument("--no-recursive", action="store_true"); p.add_argument("--out"); p.set_defaults(fn=cmd_scan)
    p = sub.add_parser("init"); p.add_argument("folder"); p.add_argument("--profile", choices=list(BUILTIN_PROFILES)); p.add_argument("--force", action="store_true"); p.set_defaults(fn=cmd_init)
    p = sub.add_parser("build"); p.add_argument("folder"); p.add_argument("--profile"); p.add_argument("--config"); p.add_argument("--name"); p.add_argument("--basename")
    p.add_argument("--from", dest="from_metadata", help="seed values from an existing metadata xlsx/json and regenerate a corrected document")
    p.add_argument("--kind"); p.add_argument("--deep", help="extra checks: values,temporal,joins,zones (or all)"); p.add_argument("--out-dir"); p.add_argument("--formats", default="json,xlsx,pdf"); p.add_argument("--report"); p.add_argument("--force", action="store_true")
    p.add_argument("--allow-unverified-pdf", action="store_true", help="accept a PDF whose Hebrew could not be extracted (KP-R3) - it is still reported")
    p.set_defaults(fn=cmd_build)
    p = sub.add_parser("validate"); p.add_argument("folder"); p.add_argument("--metadata"); p.add_argument("--profile"); p.add_argument("--kind"); p.add_argument("--deep", help="extra checks: values,temporal,joins,zones (or all)"); p.add_argument("--report"); p.add_argument("--findings")
    p.add_argument("--out-dir"); p.add_argument("--no-folder", action="store_true", help="check the document only, do not compare with files"); p.set_defaults(fn=cmd_validate)
    p = sub.add_parser("render"); p.add_argument("metadata"); p.add_argument("--profile"); p.add_argument("--pdf"); p.add_argument("--html")
    p.add_argument("--allow-unverified-pdf", action="store_true", help="accept a PDF whose Hebrew could not be extracted (KP-R3)")
    p.set_defaults(fn=cmd_render)
    p = sub.add_parser("check-spec"); p.add_argument("--online", action="store_true"); p.set_defaults(fn=cmd_check_spec)
    p = sub.add_parser("package", help="zip the dataset (Files list + metadata + related documents) as Dataset file, with a checklist")
    p.add_argument("folder"); p.add_argument("--metadata"); p.add_argument("--profile"); p.add_argument("--out"); p.set_defaults(fn=cmd_package)
    p = sub.add_parser("setup", help="install/verify Python dependencies and the PDF browser"); p.set_defaults(fn=cmd_setup)
    ap.add_argument("--no-auto-install", action="store_true", help="do not pip-install missing packages automatically")
    a = ap.parse_args(argv)
    try:
        return a.fn(a)
    except (FileNotFoundError, NotADirectoryError, ValueError) as e:
        _out(f"error: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
