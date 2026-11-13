import csv
import json
from pathlib import Path


def safe_cell(value):
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False)
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: safe_cell(row.get(k)) for k in fields})


def export_results(result, directory):
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    data = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    (target / "results.json").write_text(data, encoding="utf-8")
    write_csv(target / "deals.csv", result["deals"],
              ["name", "id", "price", "original_price", "discount", "currency", "country", "collected_at", "sale_end", "url"])
    rows = []
    for item in result["edition_inversions"]:
        b, e = item["standard"], item["edition"]
        rows.append({"base_app_id": item["base_app_id"], "base_name": item["base_name"],
                     "standard_price": b["price"], "edition_name": e["name"], "edition_price": e["price"],
                     "difference": item["difference"], "inversion_percent": item["inversion_percent"],
                     "contents": e["contents"], "standard_url": b["url"], "edition_url": e["url"],
                     "standard_collected_at": b["collected_at"], "edition_collected_at": e["collected_at"],
                     "evidence": e["evidence"]})
    write_csv(target / "edition_inversions.csv", rows,
              ["base_app_id", "base_name", "standard_price", "edition_name", "edition_price", "difference", "inversion_percent", "contents", "standard_url", "edition_url", "standard_collected_at", "edition_collected_at", "evidence"])
    write_csv(target / "unverified.csv", [
        {"base_app_id": i["base_app_id"], "base_name": i["base_name"], "edition_name": i["edition"]["name"],
         "reason": i["reason"], "url": i["edition"]["url"]} for i in result["unverified"]],
        ["base_app_id", "base_name", "edition_name", "reason", "url"])
    template = Path(__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    embedded = data.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    (target / "index.html").write_text(template.replace("__RESULTS_JSON__", embedded), encoding="utf-8")
    (target / ".nojekyll").touch()
