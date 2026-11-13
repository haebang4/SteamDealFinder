import csv
import json
from bs4 import BeautifulSoup
from src.exporter import export_results
from src.main import analyze, demo, DEFAULTS, main


def test_exports_and_html_escaping(tmp_path):
    raw = demo()
    raw["apps"][1].name = '=HYPERLINK("evil")</script><script>alert(1)</script>'
    result = analyze(raw, DEFAULTS)
    export_results(result, tmp_path)
    assert (tmp_path / "deals.csv").read_bytes().startswith(b"\xef\xbb\xbf")
    with (tmp_path / "deals.csv").open(encoding="utf-8-sig", newline="") as f:
        row = next(csv.DictReader(f))
        assert row["name"].startswith("'=")
    page = BeautifulSoup((tmp_path / "index.html").read_text(encoding="utf-8"), "html.parser")
    assert len(page.select("script")) == 2
    assert json.loads(page.select_one("#data").string) == result
    assert json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))["demo"]
    assert (tmp_path / "edition_inversions.csv").exists()
    assert (tmp_path / "unverified.csv").exists()


def test_cli_demo(tmp_path):
    assert main(["--demo", "--output-dir", str(tmp_path)]) == 0
    data = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))
    assert len(data["edition_inversions"]) == 1 and len(data["deals"]) == 1


def test_empty_exports(tmp_path):
    result = analyze(demo(), DEFAULTS)
    result.update(deals=[], edition_inversions=[], unverified=[])
    export_results(result, tmp_path)
    with (tmp_path / "deals.csv").open(encoding="utf-8-sig") as f:
        assert list(csv.DictReader(f)) == []
