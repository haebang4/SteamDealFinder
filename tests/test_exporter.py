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


def test_prices_in_all_and_comparison_csvs(tmp_path):
    result = analyze(demo(), DEFAULTS)
    inversion = result["edition_inversions"][0]
    inversion["standard"].update(original_price=60000, discount=12)
    inversion["edition"].update(original_price=53000, discount=94)
    result["unverified"] = [{**inversion, "reason": "구성 미확인"}]
    # No deals still leaves an unfiltered list of all observed products.
    result["deals"] = []
    result["inspected_offers"].append(result["inspected_offers"][0])
    export_results(result, tmp_path)
    def read(name):
        with (tmp_path / name).open(encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    all_products = read("all_products.csv")
    assert len(all_products) == 4  # two apps and two packages; duplicate group removed
    game = next(p for p in all_products if p["id"] == "5")
    assert (game["price"], game["original_price"], game["discount"]) == ("3000", "30000", "90")
    for filename in ("edition_inversions.csv", "unverified.csv"):
        row = read(filename)[0]
        assert (row["standard_price"], row["standard_original_price"], row["standard_discount"]) == ("53000", "60000", "12")
        assert (row["edition_price"], row["edition_original_price"], row["edition_discount"]) == ("3150", "53000", "94")


def test_unknown_prices_remain_blank(tmp_path):
    result = analyze(demo(), DEFAULTS)
    item = result["edition_inversions"][0]
    item["edition"].update(price=None, original_price=None)
    result["unverified"] = [{**item, "standard": None, "reason": "가격 미확인"}]
    export_results(result, tmp_path)
    with (tmp_path / "unverified.csv").open(encoding="utf-8-sig", newline="") as f:
        row = next(csv.DictReader(f))
    assert row["edition_price"] == row["edition_original_price"] == row["standard_price"] == ""
    assert row["edition_discount"] == ""
    assert row["base_app_price"] == "53000"
