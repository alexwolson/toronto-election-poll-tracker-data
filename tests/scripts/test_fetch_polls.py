"""Tests for fetch_polls.py parsing logic."""
from __future__ import annotations

import importlib.util
import pathlib

import pytest

_REPO_ROOT = pathlib.Path(__file__).parent.parent.parent


@pytest.fixture(scope="module")
def fp():
    path = _REPO_ROOT / "scripts" / "fetch_polls.py"
    spec = importlib.util.spec_from_file_location("scripts.fetch_polls", str(path))
    assert spec is not None, f"Could not load fetch_polls.py — expected at {path}"
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def test_parse_date_april(fp):
    assert fp._parse_date("April 13, 2026") == "2026-04-13"


def test_parse_date_march(fp):
    assert fp._parse_date("March 8, 2026") == "2026-03-08"


def test_parse_date_invalid(fp):
    with pytest.raises(ValueError, match="Unparseable poll date"):
        fp._parse_date("not-a-date")


def test_parse_share_percentage(fp):
    assert fp._parse_share("46%") == pytest.approx(0.46)


def test_parse_share_integer_percent(fp):
    assert fp._parse_share("35%") == pytest.approx(0.35)


def test_parse_share_em_dash(fp):
    assert fp._parse_share("—") is None


def test_parse_share_en_dash(fp):
    assert fp._parse_share("–") is None


def test_parse_share_empty(fp):
    assert fp._parse_share("") is None


def test_parse_share_small_value(fp):
    assert fp._parse_share("8%") == pytest.approx(0.08)


from bs4 import BeautifulSoup


def test_firm_slug_known(fp):
    assert fp._firm_slug("Liaison Strategies") == "liaison"


def test_firm_slug_variant(fp):
    assert fp._firm_slug("Pallas") == "pallas"


def test_firm_slug_unknown(fp):
    with pytest.raises(ValueError, match="Unknown polling firm"):
        fp._firm_slug("Mystery Pollsters Inc.")


def test_candidate_col_names_maps_known(fp):
    headers = ["Polling Firm", "Methodology", "Poll Date", "Sample Size", "MOE",
               "Bradford", "Chow", "Lead"]
    result = fp._candidate_col_names(headers)
    assert result == {"Bradford": "bradford", "Chow": "chow"}


def test_candidate_col_names_skips_metadata(fp):
    headers = ["Polling Firm", "Poll Date", "MOE", "Lead"]
    assert fp._candidate_col_names(headers) == {}


def _make_table(headers: list[str]) -> "BeautifulSoup":
    ths = "".join(f"<th>{h}</th>" for h in headers)
    html = f"<table class='wikitable'><tbody><tr>{ths}</tr></tbody></table>"
    return BeautifulSoup(html, "lxml").find("table")


def test_is_polling_table_true(fp):
    table = _make_table(["Polling Firm", "Methodology", "Poll Date", "Sample Size"])
    assert fp._is_polling_table(table) is True


def test_is_polling_table_false_missing_poll_date(fp):
    table = _make_table(["Polling Firm", "Methodology", "Sample Size"])
    assert fp._is_polling_table(table) is False


def test_is_polling_table_false_non_polling(fp):
    table = _make_table(["Candidate", "Party", "Status"])
    assert fp._is_polling_table(table) is False


def test_candidate_col_names_skips_empty_headers(fp):
    headers = ["Polling Firm", "Poll Date", "", "Chow"]
    result = fp._candidate_col_names(headers)
    assert "" not in result
    assert result == {"Chow": "chow"}


def test_cell_text_strips_footnotes(fp):
    from bs4 import BeautifulSoup as BS4

    html = "<td>Poll Date<sup>[a]</sup></td>"
    cell = BS4(html, "lxml").find("td")
    assert fp._cell_text(cell) == "Poll Date"


FIXTURE_HTML = """
<html><body>
<table class="wikitable">
<tbody>
<tr>
<th>Polling Firm</th><th>Methodology</th><th>Poll Date</th>
<th>Sample Size</th><th>MOE</th>
<th>Bradford</th><th>Chow</th><th>Furey</th><th>Lead</th>
</tr>
<tr>
<td>Liaison Strategies</td><td>IVR</td><td>April 13, 2026</td>
<td>1000</td><td>±3.1%</td>
<td>35%</td><td>46%</td><td>11%</td><td>11</td>
</tr>
<tr>
<td>Pallas Data</td><td>IVR</td><td>March 8, 2026</td>
<td>735</td><td>±3.6%</td>
<td>26%</td><td>44%</td><td>—</td><td>18</td>
</tr>
</tbody>
</table>
<table class="wikitable">
<tbody>
<tr>
<th>Polling Firm</th><th>Methodology</th><th>Poll Date</th>
<th>Sample Size</th><th>MOE</th>
<th>Bradford</th><th>Chow</th><th>Lead</th>
</tr>
<tr>
<td>Pallas Data</td><td>IVR</td><td>March 8, 2026</td>
<td>735</td><td>±3.6%</td>
<td>38%</td><td>47%</td><td>9</td>
</tr>
</tbody>
</table>
<table class="wikitable">
<tbody>
<tr><th>Candidate</th><th>Party</th></tr>
<tr><td>Someone</td><td>Independent</td></tr>
</tbody>
</table>
</body></html>
"""

DUPLICATE_HTML = """
<html><body>
<table class="wikitable">
<tbody>
<tr>
<th>Polling Firm</th><th>Methodology</th><th>Poll Date</th>
<th>Sample Size</th><th>MOE</th><th>Bradford</th><th>Chow</th><th>Lead</th>
</tr>
<tr>
<td>Liaison Strategies</td><td>IVR</td><td>April 13, 2026</td>
<td>1000</td><td>±3.1%</td><td>35%</td><td>46%</td><td>11</td>
</tr>
<tr>
<td>Liaison Strategies</td><td>IVR</td><td>April 13, 2026</td>
<td>1000</td><td>±3.1%</td><td>35%</td><td>46%</td><td>11</td>
</tr>
</tbody>
</table>
</body></html>
"""

EMPTY_HTML = "<html><body><p>No tables here.</p></body></html>"


def test_parse_polls_multi_candidate_count(fp):
    rows = fp.parse_polls(FIXTURE_HTML)
    main_rows = [r for r in rows if "v" not in r["poll_id"].split("-", 2)[-1]]
    assert len(main_rows) == 2


def test_parse_polls_multi_candidate_poll_id(fp):
    rows = fp.parse_polls(FIXTURE_HTML)
    ids = [r["poll_id"] for r in rows]
    assert "liaison-2026-04-13" in ids


def test_parse_polls_multi_candidate_shares(fp):
    rows = fp.parse_polls(FIXTURE_HTML)
    row = next(r for r in rows if r["poll_id"] == "liaison-2026-04-13")
    assert row["chow"] == pytest.approx(0.46)
    assert row["bradford"] == pytest.approx(0.35)
    assert row["furey"] == pytest.approx(0.11)


def test_parse_polls_multi_candidate_missing_share(fp):
    rows = fp.parse_polls(FIXTURE_HTML)
    row = next(r for r in rows if r["poll_id"] == "pallas-2026-03-08")
    assert row["furey"] is None


def test_parse_polls_multi_candidate_field_tested(fp):
    rows = fp.parse_polls(FIXTURE_HTML)
    row = next(r for r in rows if r["poll_id"] == "liaison-2026-04-13")
    assert row["field_tested"] == "bradford,chow,furey"


def test_parse_polls_multi_candidate_sample_size(fp):
    rows = fp.parse_polls(FIXTURE_HTML)
    row = next(r for r in rows if r["poll_id"] == "liaison-2026-04-13")
    assert row["sample_size"] == 1000


def test_parse_polls_head_to_head_poll_id(fp):
    rows = fp.parse_polls(FIXTURE_HTML)
    ids = [r["poll_id"] for r in rows]
    assert "pallas-2026-03-08-bradford-v-chow" in ids


def test_parse_polls_head_to_head_shares(fp):
    rows = fp.parse_polls(FIXTURE_HTML)
    row = next(r for r in rows if "bradford-v-chow" in r["poll_id"])
    assert row["bradford"] == pytest.approx(0.38)
    assert row["chow"] == pytest.approx(0.47)


def test_parse_polls_skips_non_polling_table(fp):
    rows = fp.parse_polls(FIXTURE_HTML)
    assert len(rows) == 3  # 2 main + 1 head-to-head


def test_parse_polls_duplicate_id_raises(fp):
    with pytest.raises(ValueError, match="Duplicate poll_id"):
        fp.parse_polls(DUPLICATE_HTML)


def test_parse_polls_no_tables_raises(fp):
    with pytest.raises(RuntimeError, match="No polling tables found"):
        fp.parse_polls(EMPTY_HTML)


def test_parse_polls_methodology_ivr_preserved(fp):
    rows = fp.parse_polls(FIXTURE_HTML)
    row = next(r for r in rows if r["poll_id"] == "liaison-2026-04-13")
    assert row["methodology"] == "IVR"


def test_parse_table_skips_mismatched_rows(fp):
    from bs4 import BeautifulSoup
    # Table where second data row has one fewer cell (rowspan artifact)
    html = """<html><body><table class="wikitable"><tbody>
    <tr><th>Polling Firm</th><th>Poll Date</th><th>Sample Size</th><th>MOE</th><th>Bradford</th><th>Chow</th><th>Lead</th></tr>
    <tr><td>Liaison Strategies</td><td>April 13, 2026</td><td>1000</td><td>±3.1%</td><td>35%</td><td>46%</td><td>11</td></tr>
    <tr><td>April 13, 2026</td><td>500</td><td>±4.4%</td><td>28%</td><td>40%</td><td>12</td></tr>
    </tbody></table></body></html>"""
    rows = fp.parse_polls(html)
    assert len(rows) == 1  # second row skipped due to cell count mismatch
