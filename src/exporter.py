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
    # Keep all observed prices accessible even when no deal matches the filters.
    products = {(p["kind"], p["id"]): {**p, "base_app_ids": [p["id"]]} for p in result["products"]}
    for group in result.get("inspected_offers", []):
        for p in group["offers"]:
            key = (p["kind"], p["id"])
            if key not in products:
                products[key] = {**p, "base_app_ids": []}
            if group["base_app_id"] not in products[key]["base_app_ids"]:
                products[key]["base_app_ids"].append(group["base_app_id"])
    for p in products.values():
        if p.get("price") is None:
            p["discount"] = None
    write_csv(target / "all_products.csv", products.values(),
              ["name", "kind", "id", "price", "original_price", "discount", "currency", "country", "base_app_ids", "app_ids", "collected_at", "url"])
    rows = []
    for item in result["edition_inversions"]:
        b, e = item["standard"], item["edition"]
        rows.append({"base_app_id": item["base_app_id"], "base_name": item["base_name"],
                     "standard_price": b["price"], "edition_name": e["name"], "edition_price": e["price"],
                     "standard_original_price": b["original_price"], "standard_discount": b["discount"],
                     "edition_original_price": e["original_price"], "edition_discount": e["discount"],
                     "difference": item["difference"], "inversion_percent": item["inversion_percent"],
                     "contents": e["contents"], "standard_url": b["url"], "edition_url": e["url"],
                     "standard_collected_at": b["collected_at"], "edition_collected_at": e["collected_at"],
                     "evidence": e["evidence"]})
    write_csv(target / "edition_inversions.csv", rows,
              ["base_app_id", "base_name", "standard_price", "standard_original_price", "standard_discount", "edition_name", "edition_price", "edition_original_price", "edition_discount", "difference", "inversion_percent", "contents", "standard_url", "edition_url", "standard_collected_at", "edition_collected_at", "evidence"])
    unknown = []
    for i in result["unverified"]:
        b, e = i.get("standard") or {}, i["edition"]
        base_app = products.get(("app", i["base_app_id"]), {})
        unknown.append({"base_app_id": i["base_app_id"], "base_name": i["base_name"],
                        "base_app_price": base_app.get("price"), "base_app_original_price": base_app.get("original_price"), "base_app_discount": base_app.get("discount"),
                        "standard_price": b.get("price"), "standard_original_price": b.get("original_price"), "standard_discount": b.get("discount"),
                        "edition_name": e["name"], "edition_price": e.get("price"), "edition_original_price": e.get("original_price"), "edition_discount": e.get("discount") if e.get("price") is not None else None,
                        "currency": e.get("currency"), "collected_at": e.get("collected_at"),
                        "reason": i["reason"], "standard_url": b.get("url"), "url": e["url"]})
    write_csv(target / "unverified.csv", unknown,
              ["base_app_id", "base_name", "base_app_price", "base_app_original_price", "base_app_discount", "standard_price", "standard_original_price", "standard_discount", "edition_name", "edition_price", "edition_original_price", "edition_discount", "currency", "collected_at", "reason", "standard_url", "url"])
    template = Path(__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    embedded = data.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    (target / "index.html").write_text(template.replace("__RESULTS_JSON__", embedded), encoding="utf-8")
    (target / ".nojekyll").touch()
