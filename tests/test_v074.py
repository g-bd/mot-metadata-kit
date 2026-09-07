"""One fixture per behaviour added in 0.7.4 — KP-R3 (encoding integrity) and KP-R4
(the format's accepted tokens, at the bottom of the file).

KP-R3, the owner 06/09/2026: "שיוודא שאין בעייה של כתיבת סימני שאלה במקום מלל בעברית".

Hebrew is never written as question marks. The kit checks that at the three points where it
can silently happen, and never anywhere else:

* **the data files it describes** - a text column holding `????`, a value holding U+FFFD, or a
  column whose Hebrew is cp1252 mojibake, reported once per column with a count and examples
  (`text_lost_as_question_marks`, `hebrew_mojibake`);
* **the metadata document** - a description, label or header value that was destroyed the same
  way (`metadata_value_question_marks`);
* **the kit's own outputs** - every json / xlsx / csv / html it writes is read back and its
  Hebrew must be there character for character (`output_roundtrip_failed`, the kit's own bug,
  exit 2), and a PDF's first pages must yield the title's Hebrew to a text extractor
  (`pdf_hebrew_not_rendered`).

This is a check on ENCODING INTEGRITY, not on data content (hard rule 1): it never asks whether
a value is right, only whether the value arrived at all. Everything here is synthetic.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

HE = "תל אביב"
HEB_ROWS = ["חיפה מרכז", "באר שבע צפון", "ירושלים יצחק נבון", "מודיעין מרכז", "לוד גני אביב"]


def _by(fx, code):
    return [f for f in fx if f["code"] == code]


def _mojibake(text: str, wrote: str = "utf-8") -> str:
    """The text as it looks when written in one codec and READ as Windows-1252 / Latin-1."""
    return text.encode(wrote).decode("latin-1")


def _minimal_meta() -> dict:
    return {"Title": HE, "Files": []}


# =========================================================================== the helpers
def test_question_mark_ratio_counts_and_does_not_judge():
    from motmeta.scan import is_question_mark_run, question_mark_ratio
    assert question_mark_ratio("????") == 1.0
    assert question_mark_ratio("a?b?") == 0.5
    assert question_mark_ratio(HE) == 0.0
    assert question_mark_ratio("") == 0.0
    # a lone `?` is a placeholder answer, which the dictionary already rejects elsewhere -
    # it is not text that was destroyed, so this check leaves it alone
    assert not is_question_mark_run("?")
    assert is_question_mark_run("??")
    assert is_question_mark_run("????")
    assert is_question_mark_run("��" + HE)      # U+FFFD anywhere = something was lost
    assert not is_question_mark_run(HE)
    assert not is_question_mark_run("מה קרה?")            # one question mark in a sentence


def test_mojibake_is_recognised_in_both_directions_and_nowhere_else():
    from motmeta.scan import looks_like_cp1252_mojibake as moji
    assert moji(_mojibake(HE))                        # UTF-8 Hebrew read as cp1252: ×ª× ...
    assert moji(_mojibake(HE, "cp1255"))              # cp1255 Hebrew read as cp1252: úì àáéá
    assert not moji(HE)
    assert not moji("Élan café naïve")                # accents are not mojibake
    assert not moji("3 × 4 × 5")                      # a multiplication sign is a sign
    assert not moji("plain ascii text")


def test_the_scanner_and_the_dictionary_agree_on_the_thresholds():
    """`scan` has no Spec, so it carries its own copy of the numbers; the two may not drift."""
    from motmeta.scan import ENCODING_INTEGRITY
    from motmeta.spec import BASE_SPEC
    dic = json.loads(BASE_SPEC.read_text(encoding="utf-8"))["encoding_integrity"]
    for k, v in ENCODING_INTEGRITY.items():
        assert dic[k] == v, f"{k}: scan says {v!r}, spec.json says {dic[k]!r}"


def test_a_profile_may_tighten_the_thresholds_but_never_the_severities(tmp_path: Path):
    from motmeta.spec import Spec
    prof = tmp_path / "profile.json"
    prof.write_text(json.dumps({
        "profile": "strict",
        "encoding_integrity": {"question_mark_min_run": 1, "mojibake_min_hits": 5,
                               "severities": {"text_lost_as_question_marks": "info"}},
    }, ensure_ascii=False), encoding="utf-8")
    s = Spec(str(prof))
    ei = s.encoding_integrity
    assert ei["question_mark_min_run"] == 1        # tightened
    assert ei["mojibake_min_hits"] == 2            # a profile cannot loosen it
    assert s.encoding_severity("text_lost_as_question_marks") == "error"


# =========================================================================== data files
@pytest.fixture()
def qmark_folder(tmp_path: Path) -> Path:
    rows = ["station_id,station_name,note"]
    for i, n in enumerate(HEB_ROWS):
        rows.append(f"{100 + i},????,{n}")
    tmp_path.joinpath("stations.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    return tmp_path


def test_a_column_written_as_question_marks_is_an_error(qmark_folder, spec):
    from motmeta.scan import scan_folder
    from motmeta.validate import validate
    s = scan_folder(qmark_folder)
    col = next(c for c in s["files"][0]["fields"] if c["name"] == "station_name")
    assert col["n_question_mark_values"] == 5 and col["question_mark_examples"][0] == "????"
    fx, _ = validate(_minimal_meta(), spec, qmark_folder, s)
    lost = _by(fx, "text_lost_as_question_marks")
    assert len(lost) == 1
    assert lost[0]["severity"] == "error"
    assert lost[0]["where"] == "stations.csv.station_name"
    assert "5" in lost[0]["msg"] and "????" in lost[0]["detail"]
    # the clean Hebrew column beside it is not touched
    assert not [f for f in lost if f["where"].endswith(".note")]


def test_a_cp1252_mojibake_column_is_an_error(tmp_path: Path, spec):
    from motmeta.scan import scan_folder
    from motmeta.validate import validate
    rows = ["station_id,station_name"]
    for i, n in enumerate(HEB_ROWS):
        rows.append(f"{100 + i},{_mojibake(n)}")
    tmp_path.joinpath("stations.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    s = scan_folder(tmp_path)
    fx, _ = validate(_minimal_meta(), spec, tmp_path, s)
    moji = _by(fx, "hebrew_mojibake")
    assert len(moji) == 1 and moji[0]["severity"] == "error"
    assert moji[0]["where"] == "stations.csv.station_name"
    assert not _by(fx, "text_lost_as_question_marks")


def test_clean_hebrew_raises_nothing(tmp_path: Path, spec):
    from motmeta.scan import scan_folder
    from motmeta.validate import validate
    rows = ["station_id,station_name,comment"]
    for i, n in enumerate(HEB_ROWS):
        rows.append(f"{100 + i},{n},מה נספר כאן?")
    tmp_path.joinpath("stations.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    fx, _ = validate(_minimal_meta(), spec, tmp_path, scan_folder(tmp_path))
    assert not _by(fx, "text_lost_as_question_marks")
    assert not _by(fx, "hebrew_mojibake")


def test_a_cp1255_file_read_correctly_raises_nothing(tmp_path: Path, spec):
    """The scanner detects cp1255 and decodes it; a correctly-read file is a clean file."""
    from motmeta.scan import scan_folder
    from motmeta.validate import validate
    rows = ["station_id,station_name"] + [f"{100 + i},{n}" for i, n in enumerate(HEB_ROWS)]
    tmp_path.joinpath("stations.csv").write_bytes(("\n".join(rows) + "\n").encode("cp1255"))
    fx, _ = validate(_minimal_meta(), spec, tmp_path, scan_folder(tmp_path))
    assert not _by(fx, "text_lost_as_question_marks")
    assert not _by(fx, "hebrew_mojibake")


# =========================================================================== the metadata document
def test_a_metadata_description_written_as_question_marks_is_an_error(tmp_path: Path, spec):
    """Written and re-read as a real xlsx, the way a hand-made document arrives."""
    from motmeta.io import read_xlsx, write_xlsx
    from motmeta.validate import validate
    meta = {
        "Publisher": "נתיבי איילון", "Contact": "גולן", "Title": "סקר נוסעים",
        "Description": ["??"],
        "Files": [{"File name": "stations.csv", "File format": "CSV", "File description": "????",
                   "File fields": [{"Name": "station_id", "Type": "Integer", "Description": "מזהה תחנה"},
                                   {"Name": "station_name", "Type": "Text", "Description": _mojibake(HE)}]}],
    }
    path = tmp_path / "metadata.xlsx"
    write_xlsx(meta, path, spec, include_survey=False)
    back = read_xlsx(path, spec)
    fx, _ = validate(back, spec, None, None)
    got = _by(fx, "metadata_value_question_marks")
    where = {f["where"] for f in got}
    assert all(f["severity"] == "error" for f in got)
    assert "Description" in where
    assert "stations.csv.File description" in where
    assert "stations.csv.station_name.Description" in where
    assert not [w for w in where if w.endswith("station_id.Description")]


def test_a_clean_metadata_document_raises_nothing(tmp_path: Path, spec):
    from motmeta.validate import validate
    meta = {"Publisher": "נתיבי איילון", "Title": "סקר נוסעים", "Description": ["רשימת תחנות"],
            "Files": [{"File name": "stations.csv", "File description": "התחנות",
                       "File fields": [{"Name": "station_id", "Type": "Integer", "Description": "מזהה", "Comments": "?"}]}]}
    fx, _ = validate(meta, spec, None, None)
    assert not _by(fx, "metadata_value_question_marks")


# =========================================================================== the kit's own outputs
@pytest.fixture()
def built(tmp_path: Path, spec):
    """A small Hebrew dataset, built into a folder, ready to have its outputs re-read."""
    from motmeta.build import build_metadata
    rows = ["station_id,station_name"] + [f"{100 + i},{n}" for i, n in enumerate(HEB_ROWS)]
    tmp_path.joinpath("stations.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    cfg = {"dataset_name": "rail_smoke", "dataset_kind": "administrative",
           "header": {"Publisher": "נתיבי איילון", "Contact": "גולן", "Title": "סקר נוסעים בתחנות רכבת",
                      "Description": ["רשימת תחנות הרכבת וקוויהן"], "Spatial coverage": "ארצי"},
           "files": {"stations.csv": {"File description": "רשימת התחנות",
                                      "fields": {"station_id": {"Description": "מזהה תחנה"},
                                                 "station_name": {"Description": "שם התחנה"}}}}}
    meta, _scan = build_metadata(tmp_path, spec, cfg)
    return tmp_path, meta


def test_the_hebrew_sample_is_taken_from_the_document_itself(built, spec):
    from motmeta.io import hebrew_sample_strings
    _folder, meta = built
    samples = hebrew_sample_strings(meta, 20)
    assert samples[0] == "סקר נוסעים בתחנות רכבת"          # the title leads
    assert "רשימת תחנות הרכבת וקוויהן" in samples
    assert "רשימת התחנות" in samples
    assert len(samples) <= 20
    assert all(len(x) >= 4 for x in samples)               # a two-letter word matches by accident


def test_every_written_output_round_trips(built, spec):
    from motmeta.io import assert_hebrew_roundtrip, hebrew_sample_strings, metadata_html, write_csv, write_json, write_xlsx
    folder, meta = built
    samples = hebrew_sample_strings(meta)
    write_json(meta, folder / "m.json")
    write_xlsx(meta, folder / "m.xlsx", spec, include_survey=False)
    write_csv(meta, folder / "m.csv", spec, include_survey=False)
    (folder / "m.html").write_text(metadata_html(meta, spec, include_survey=False), encoding="utf-8")
    for name in ("m.json", "m.xlsx", "m.csv", "m.html"):
        chk = assert_hebrew_roundtrip(folder / name, samples)
        assert chk["ok"], (name, chk)
        assert chk["checked"] == len(samples) and not chk["missing"]


def test_the_metadata_never_publishes_the_machine_path(built, spec, tmp_path):
    """`_meta.folder` and `summary.folder` are the folder's NAME, never its path.

    `<name>_metadata.json` is a DISTRIBUTION file - it goes into the הפצה zip
    and up to data.gov.il - so an absolute path in it publishes the producer's
    disk to every reader. Caught by the rail package's `no_machine_detail`
    guard, 06/09/2026.
    """
    from motmeta.validate import validate
    folder, meta = built
    assert meta["_meta"]["folder"] == folder.name
    assert "\\" not in meta["_meta"]["folder"] and "/" not in meta["_meta"]["folder"]
    _fx, summary = validate(meta, spec, folder)
    assert summary["folder"] == folder.name


def test_a_gershayim_in_a_hebrew_string_still_round_trips(built, spec):
    """`מק"ט` is the commonest abbreviation in this corpus, and JSON escapes its quote.

    Measured on the rail package (2026-09-06): three field descriptions reading
    `מק"ט תחנת הרכבת` were reported as "the Hebrew did not survive" because the
    check compared them against the RAW json text, where the file honestly holds
    `מק\\"ט`. The document was perfect; the reader was not. The json branch now
    reads the parsed VALUES, the way the xlsx branch always has.
    """
    from motmeta.io import assert_hebrew_roundtrip, write_json, write_xlsx
    folder, meta = built
    quoted = 'מק"ט תחנת הרכבת'
    meta = dict(meta)
    meta["Description"] = quoted
    write_json(meta, folder / "q.json")
    write_xlsx(meta, folder / "q.xlsx", spec, include_survey=False)
    raw = (folder / "q.json").read_text(encoding="utf-8")
    assert '\\"' in raw                                    # the file really does escape it
    for name in ("q.json", "q.xlsx"):
        chk = assert_hebrew_roundtrip(folder / name, [quoted])
        assert chk["ok"] and not chk["missing"], (name, chk)


def test_a_lossy_writer_is_caught(built):
    """What the guard exists for: an output written through an ASCII/replace path."""
    from motmeta.io import assert_hebrew_roundtrip, hebrew_sample_strings, write_json
    folder, meta = built
    samples = hebrew_sample_strings(meta)
    write_json(meta, folder / "good.json")
    good = (folder / "good.json").read_text(encoding="utf-8")
    (folder / "bad.json").write_text(good.encode("ascii", "replace").decode("ascii"), encoding="utf-8")
    chk = assert_hebrew_roundtrip(folder / "bad.json", samples)
    assert not chk["ok"] and chk["missing"] and chk["question_marks"] > 0


def test_html_without_a_charset_declaration_is_caught(built):
    from motmeta.io import assert_hebrew_roundtrip, hebrew_sample_strings
    folder, meta = built
    samples = hebrew_sample_strings(meta)
    (folder / "nocharset.html").write_text("<html><body>" + samples[0] + "</body></html>", encoding="utf-8")
    chk = assert_hebrew_roundtrip(folder / "nocharset.html", samples)
    assert not chk["ok"] and "charset" in chk["detail"]


def test_a_missing_output_is_not_silently_ok(tmp_path: Path):
    from motmeta.io import assert_hebrew_roundtrip
    chk = assert_hebrew_roundtrip(tmp_path / "never-written.json", [HE])
    assert not chk["ok"] and not chk["skipped"]


# =========================================================================== PDF
def _pdf_ready():
    from motmeta.io import find_browsers
    try:
        import pypdf  # noqa: F401
    except ImportError:
        return "pypdf is not installed"
    if not find_browsers():
        return "no Chromium/Edge to print a PDF with"
    return ""


def test_a_pdf_with_hebrew_is_verified(built, spec):
    reason = _pdf_ready()
    if reason:
        pytest.skip(reason)
    from motmeta.io import assert_hebrew_roundtrip, hebrew_sample_strings, html_to_pdf, metadata_html
    folder, meta = built
    ok, msg = html_to_pdf(metadata_html(meta, spec, include_survey=False), folder / "m.pdf")
    if not ok:
        pytest.skip(f"the browser did not produce a PDF: {msg}")
    chk = assert_hebrew_roundtrip(folder / "m.pdf", hebrew_sample_strings(meta))
    assert chk["ok"], chk
    assert chk["checked"] == 1 and chk["question_marks"] == 0


def test_a_pdf_whose_hebrew_never_arrived_is_reported(built, spec):
    reason = _pdf_ready()
    if reason:
        pytest.skip(reason)
    from motmeta.io import assert_hebrew_roundtrip, hebrew_sample_strings, html_to_pdf, metadata_html
    folder, meta = built
    html = metadata_html(meta, spec, include_survey=False)
    ok, msg = html_to_pdf(html.encode("ascii", "replace").decode("ascii"), folder / "bad.pdf")
    if not ok:
        pytest.skip(f"the browser did not produce a PDF: {msg}")
    chk = assert_hebrew_roundtrip(folder / "bad.pdf", hebrew_sample_strings(meta))
    assert not chk["ok"] and chk["format"] == "pdf"


def test_the_pdf_check_skips_cleanly_without_pypdf(built, spec, monkeypatch):
    """No pypdf = not verified, and SAID so - never a pass by default."""
    import builtins
    from motmeta.io import assert_hebrew_roundtrip, hebrew_sample_strings
    folder, meta = built
    (folder / "fake.pdf").write_bytes(b"%PDF-1.4 not really a pdf")
    real_import = builtins.__import__

    def no_pypdf(name, *a, **kw):
        if name == "pypdf":
            raise ImportError("pypdf is not installed")
        return real_import(name, *a, **kw)

    monkeypatch.setattr(builtins, "__import__", no_pypdf)
    chk = assert_hebrew_roundtrip(folder / "fake.pdf", hebrew_sample_strings(meta))
    assert chk["ok"] and chk["skipped"] and "pypdf" in chk["skipped"]


# =========================================================================== the CLI's verdict
def _cli():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "mot-metadata" / "scripts"))
    import mot_metadata
    return mot_metadata


def test_a_broken_own_output_exits_2_and_a_bad_pdf_exits_1(spec):
    from motmeta.validate import Findings
    cli = _cli()
    fx = Findings()
    rt = cli._roundtrip_findings([{"ok": False, "path": "m.json", "format": "json", "missing": ["תל אביב"],
                                   "question_marks": 3, "skipped": "", "detail": "lost"}], fx, spec, False)
    assert rt == 2
    got = _by(fx, "output_roundtrip_failed")
    assert len(got) == 1 and got[0]["severity"] == "error" and got[0]["section"] == "outputs"

    fx = Findings()
    bad_pdf = {"ok": False, "path": "m.pdf", "format": "pdf", "missing": [], "question_marks": 2,
               "skipped": "", "detail": "no Hebrew"}
    assert cli._roundtrip_findings([bad_pdf], fx, spec, False) == 1
    got = _by(fx, "pdf_hebrew_not_rendered")
    assert len(got) == 1 and got[0]["severity"] == "warning" and got[0]["fix"]
    # the operator may accept it - it is still reported, it just no longer fails the build
    fx2 = Findings()
    assert cli._roundtrip_findings([bad_pdf], fx2, spec, True) == 0
    assert len(_by(fx2, "pdf_hebrew_not_rendered")) == 1

    fx3 = Findings()
    assert cli._roundtrip_findings([{"ok": True, "path": "m.pdf", "format": "pdf", "missing": [],
                                     "question_marks": 0, "skipped": "pypdf is not installed",
                                     "detail": ""}], fx3, spec, False) == 0
    assert _by(fx3, "output_roundtrip_skipped")[0]["severity"] == "info"


def test_the_console_says_when_a_line_had_to_be_degraded(monkeypatch, capsys):
    """The cp1255 fallback stays; a line that lost characters is marked, so nobody pastes it back."""
    cli = _cli()

    class Cp1255Console:
        encoding = "cp1255"

        def __init__(self):
            self.lines: list[str] = []

        def write(self, s):
            s.encode("cp1255")            # raises UnicodeEncodeError on anything cp1255 cannot carry
            self.lines.append(s)
            return len(s)

        def flush(self):
            pass

    fake = Cp1255Console()
    monkeypatch.setattr(sys, "stdout", fake)
    cli._out("русский текст")             # cp1255 cannot carry Cyrillic
    out = "".join(fake.lines)
    assert out.startswith("[console: degraded encoding] ")
    fake.lines.clear()
    cli._out("תל אביב")                    # cp1255 carries Hebrew: nothing is marked
    assert "".join(fake.lines).strip() == "תל אביב"


def test_the_report_prints_the_outputs_section(spec):
    from motmeta.report import render_report
    from motmeta.validate import Findings
    fx = Findings()
    fx.add("error", "outputs", "m.json", "output_roundtrip_failed", "הפלט לא חזר כפי שנכתב")
    html = render_report(fx, {"counts": {"error": 1, "warning": 0, "info": 0}})
    assert "output_roundtrip_failed" in html and "פלטי הערכה" in html


# ============================================ KP-R4: a token the format accepts is not a type error
# `not_recorded` sits in an Integer column of the rail package's `obod.csv` beside the codes,
# exactly as `profile.json -> accepted_tokens` declares it may. It is a category of its own -
# not a missing value, not an encoding accident - so no check that CLASSIFIES a cell value may
# read it as data: not `value_undocumented` (which already ignored it) and not `type_implausible`.
# The token list is dictionary data (`Spec.accepted_tokens`); with no profile there is no token
# and a stray word in an Integer column is still reported.
TOKENS_PROFILE = {
    "profile": "tokens",
    "accepted_tokens": {
        "note": "אסימונים המותרים כערך בשדה, נוסף על הקטגוריות של הסקר עצמו",
        "values": [{"value": "Null", "label": "אין נתון בשדה"},
                   {"value": "not_recorded", "label": "השאלה לא נשאלה"}],
    },
}


@pytest.fixture()
def tokens_spec(tmp_path: Path):
    """A profile that accepts `Null` and `not_recorded` as a cell value - nothing else."""
    from motmeta.spec import Spec
    p = tmp_path / "tokens-profile.json"
    p.write_text(json.dumps(TOKENS_PROFILE, ensure_ascii=False), encoding="utf-8")
    return Spec(str(p))


def _int_column_folder(tmp_path: Path, values: list[str]) -> Path:
    """A one-column `obod.csv` documented as Integer, holding `values`."""
    folder = tmp_path / "pkg"
    folder.mkdir()
    rows = ["trip_index,answer"] + [f"{i + 1},{v}" for i, v in enumerate(values)]
    (folder / "obod.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    return folder


def _int_column_meta(values_list=None) -> dict:
    fd = {"Name": "answer", "Type": "Integer", "Description": "תשובה מקודדת"}
    if values_list is not None:
        fd["Values"] = values_list
    return {"Title": HE, "Files": [{"File name": "obod.csv", "File fields": [
        {"Name": "trip_index", "Type": "Integer (key)", "Description": "מזהה נסיעה"}, fd]}]}


def _type_findings(folder: Path, spec, meta: dict, deep=None):
    from motmeta.scan import scan_folder
    from motmeta.validate import validate
    fx, _ = validate(meta, spec, folder, scan_folder(folder), deep=deep)
    return fx


def test_the_scanner_says_which_values_are_not_numeric(tmp_path: Path):
    from motmeta.scan import scan_folder
    folder = _int_column_folder(tmp_path, ["1", "2", "not_recorded", "not_recorded", "3"])
    s = scan_folder(folder)
    col = next(c for c in s["files"][0]["fields"] if c["name"] == "answer")
    # the scanner never decides what a token MEANS - it reports what is in the column
    assert col["inferred_type"] == "Text"
    assert col["n_non_numeric_sampled"] == 2
    assert col["non_numeric_values"] == {"not_recorded": 2}


def test_the_spec_reads_the_accepted_tokens_from_the_profile(tmp_path: Path, spec, tokens_spec):
    from motmeta.spec import Spec
    assert spec.accepted_token_set == set()                 # the base נוהל names none
    assert not spec.is_accepted_token("not_recorded")
    assert tokens_spec.accepted_token_set == {"null", "not_recorded"}
    assert tokens_spec.is_accepted_token("NOT_RECORDED") and tokens_spec.is_accepted_token(" Null ")
    assert not tokens_spec.is_accepted_token("not recorded")
    # the shipped profile that declares the token really does carry it
    for name in ("onboard",):
        assert Spec(name).accepted_token_set == {"null", "not_recorded"}


def test_an_accepted_token_in_an_integer_column_is_not_a_type_error(tmp_path: Path, tokens_spec):
    folder = _int_column_folder(tmp_path, ["1", "2", "not_recorded"])
    assert _by(_type_findings(folder, tokens_spec, _int_column_meta()), "type_implausible") == []


def test_the_same_column_is_still_flagged_with_no_profile(tmp_path: Path, spec):
    folder = _int_column_folder(tmp_path, ["1", "2", "not_recorded"])
    imp = _by(_type_findings(folder, spec, _int_column_meta()), "type_implausible")
    assert len(imp) == 1 and imp[0]["where"] == "obod.csv.answer"
    assert "not_recorded" in imp[0]["detail"]


def test_a_column_of_tokens_only_keeps_its_declared_type(tmp_path: Path, tokens_spec):
    folder = _int_column_folder(tmp_path, ["not_recorded", "Null", "not_recorded", "Null"])
    assert _by(_type_findings(folder, tokens_spec, _int_column_meta()), "type_implausible") == []


def test_an_empty_column_says_nothing_about_its_type(tmp_path: Path, spec):
    # nothing is in the column, so nothing in it contradicts `Integer` - the old check
    # reported "the file holds non-numeric values" with no value to show for it
    folder = _int_column_folder(tmp_path, ["", "", ""])
    assert _by(_type_findings(folder, spec, _int_column_meta()), "type_implausible") == []


def test_real_text_beside_a_token_is_still_reported_without_it(tmp_path: Path, tokens_spec):
    folder = _int_column_folder(tmp_path, ["1", "not_recorded", "not_recorded", "לא רלוונטי", "2"])
    imp = _by(_type_findings(folder, tokens_spec, _int_column_meta()), "type_implausible")
    assert len(imp) == 1
    assert "(1 מתוך 5 במדגם)" in imp[0]["msg"]          # the two tokens are not counted
    assert imp[0]["detail"] == "דוגמאות: לא רלוונטי"    # and are not shown as evidence


def test_deep_values_reads_the_same_token_list(tmp_path: Path, spec, tokens_spec):
    folder = _int_column_folder(tmp_path, ["1", "2", "not_recorded"])
    meta = _int_column_meta([{"value": "1", "label": "כן"}, {"value": "2", "label": "לא"}])
    assert _by(_type_findings(folder, tokens_spec, meta, deep={"values"}), "value_undocumented") == []
    und = _by(_type_findings(folder, spec, meta, deep={"values"}), "value_undocumented")
    assert len(und) == 1 and "not_recorded" in und[0]["msg"]
