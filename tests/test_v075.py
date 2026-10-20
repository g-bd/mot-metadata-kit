"""0.7.5 — a document named in the Files list is not reported as missing when it is in the folder.

Raised on the Red Line LRT 2025 v2 package (20/10/2026): `RedLineLRT2025_report.pdf` sat next to the data
and was listed in `Files list`, yet `file_not_found` said it was not in the folder — the folder index
held data files only. The missing description block (`listed_not_described`) is still a real finding.
"""
from __future__ import annotations

from pathlib import Path


def _codes(tmp_path: Path, spec, listed: list[str]) -> list[tuple[str, str]]:
    from motmeta.scan import scan_folder
    from motmeta.validate import Findings, check_files
    meta = {"Files list": listed, "Files": [{"File name": "counts.csv"}]}
    fx = Findings()
    check_files(meta, spec, scan_folder(tmp_path), fx)
    return [(f["code"], f["where"]) for f in fx]


def test_listed_document_in_folder_is_not_missing(tmp_path, spec):
    (tmp_path / "counts.csv").write_text("id,v\n1,2\n", encoding="utf-8")
    (tmp_path / "survey_report.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
    codes = _codes(tmp_path, spec, ["counts.csv", "survey_report.pdf"])
    assert ("file_not_found", "survey_report.pdf") not in codes
    assert ("listed_not_described", "survey_report.pdf") in codes


def test_listed_document_absent_is_still_missing(tmp_path, spec):
    (tmp_path / "counts.csv").write_text("id,v\n1,2\n", encoding="utf-8")
    codes = _codes(tmp_path, spec, ["counts.csv", "survey_report.pdf"])
    assert ("file_not_found", "survey_report.pdf") in codes
