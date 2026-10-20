"""0.7.5 — a document named in the Files list is not reported as missing when it is in the folder.

Raised on the Red Line LRT 2025 v2 package (20/10/2026): `RedLineLRT2025_report.pdf` sat next to the data
and was listed in `Files list`, yet `file_not_found` said it was not in the folder — the folder index
held data files only. Listing a document is enough: it needs no description block under Files
(`listed_not_described` is for data files only).
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
    # listing a document is enough - it needs no description block under Files (owner, 20/10/2026)
    assert ("listed_not_described", "survey_report.pdf") not in codes


def test_listed_data_file_without_block_is_still_an_error(tmp_path, spec):
    (tmp_path / "counts.csv").write_text("id,v\n1,2\n", encoding="utf-8")
    (tmp_path / "extra.csv").write_text("id,v\n1,2\n", encoding="utf-8")
    codes = _codes(tmp_path, spec, ["counts.csv", "extra.csv"])
    assert ("listed_not_described", "extra.csv") in codes


def test_listed_document_absent_is_still_missing(tmp_path, spec):
    (tmp_path / "counts.csv").write_text("id,v\n1,2\n", encoding="utf-8")
    codes = _codes(tmp_path, spec, ["counts.csv", "survey_report.pdf"])
    assert ("file_not_found", "survey_report.pdf") in codes


# --------------------------------------------------------------------------- --deep report
# The survey report against the files (owner, 20/10/2026): a sanity check that the report's
# headline numbers and table rows are the ones the delivered files give. Raised on the same Red
# Line package, whose report prints walk 64,258 / bus 29,646 while survey.csv gives 62,571 / 31,333.

def test_split_run_reads_glued_cells():
    from motmeta.reportcheck import split_run
    counts, shares = split_run("64,25855.6%")
    assert 64258 in counts and (55.6, 1) in shares
    counts, shares = split_run("4550.4%")          # 455 and 0.4% glued
    assert 455 in counts and (0.4, 1) in shares


def _report_case(tmp_path, monkeypatch, report_text):
    from motmeta import reportcheck
    from motmeta.scan import scan_folder
    from motmeta.validate import Findings
    rows = ["id,mode,weight"] + [f"{i},{1 if i <= 6 else 2},{1.5}" for i in range(1, 11)]
    (tmp_path / "survey.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    (tmp_path / "survey_report.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
    monkeypatch.setattr(reportcheck, "pdf_text", lambda p, pages=0: report_text)
    meta = {"Files": [{"File name": "survey.csv", "File fields": [
        {"Name": "mode", "Values": [{"value": 1, "label": "ברגל"}, {"value": 2, "label": "באוטובוס"}]}]}]}
    fx = Findings()
    reportcheck.check_report_vs_data(meta, tmp_path, scan_folder(tmp_path), fx)
    return fx


def test_report_rows_that_agree_with_the_files(tmp_path, monkeypatch):
    # 10 rows, weight 1.5 -> 15 passengers: walk 9 (60%), bus 6 (40%)
    fx = _report_case(tmp_path, monkeypatch, "טבלה 4\nברגל960.0%\nבאוטובוס640.0%\nסה\"כ15100%")
    assert not [f for f in fx if f["code"] == "report_figure_mismatch"]
    assert [f for f in fx if f["code"] == "report_check_summary"]


def test_report_row_that_disagrees_is_a_warning(tmp_path, monkeypatch):
    fx = _report_case(tmp_path, monkeypatch, "טבלה 4\nברגל1173.3%\nבאוטובוס640.0%")
    bad = [f for f in fx if f["code"] == "report_figure_mismatch"]
    assert len(bad) == 1 and bad[0]["severity"] == "warning" and "ברגל" in bad[0]["msg"]
    assert not [f for f in fx if f["severity"] == "error"]


def test_headline_figures_found_exact_or_rounded(tmp_path, monkeypatch):
    from motmeta.reportcheck import _rounded_match
    assert _rounded_match(91300, 91292) and not _rounded_match(91300, 91100)
