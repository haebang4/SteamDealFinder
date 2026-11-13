"""Adapters for undocumented public Store responses. Fail closed on missing fields."""
import json
import re
from bs4 import BeautifulSoup
from .models import Product


def won(cents):
    # Steam Store API uses hundredths even for zero-decimal KRW.
    if isinstance(cents, bool) or not isinstance(cents, int) or cents < 0 or cents % 100:
        return None
    return cents // 100


def parse_app(payload, app_id, scan_id):
    item = payload.get(str(app_id), {})
    if not item.get("success"):
        raise ValueError(f"appdetails unavailable: {app_id}")
    d = item["data"]
    if d.get("steam_appid") != app_id:
        raise ValueError("App ID mismatch")
    p = d.get("price_overview", {})
    product = Product("app", app_id, d["name"], won(p.get("final")),
                      won(p.get("initial")), int(p.get("discount_percent", 0)),
                      currency=p.get("currency", "UNKNOWN"), scan_id=scan_id,
                      app_type=d.get("type", ""), app_ids=[app_id])
    if d.get("is_free"):
        product.price = 0
    return product, d


def parse_package(payload, package_id, scan_id):
    item = payload.get(str(package_id), {})
    if not item.get("success"):
        raise ValueError(f"packagedetails unavailable: {package_id}")
    d = item["data"]
    apps = d.get("apps", [])
    p = d.get("price", {})
    return Product("sub", package_id, d["name"], won(p.get("final")),
                   won(p.get("initial")), int(p.get("discount_percent", 0)),
                   currency=p.get("currency", "UNKNOWN"), scan_id=scan_id,
                   app_ids=[int(a["id"]) for a in apps], contents=apps,
                   composition_verified=bool(apps), evidence="packagedetails.apps")


def search_items(html):
    result = []
    for row in BeautifulSoup(html, "html.parser").select("a.search_result_row"):
        m = re.search(r"store\.steampowered\.com/(app|sub|bundle)/(\d+)", row.get("href", ""))
        if m:
            result.append((m[1], int(m[2])))
    return list(dict.fromkeys(result))


def purchase_candidates(html, scan_id):
    soup = BeautifulSoup(html, "html.parser")
    packages, bundles = set(), []
    for block in soup.select(".game_area_purchase_game_wrapper, .game_area_purchase_game"):
        for node in block.select('input[name="subid"], input[name="subid[]"]'):
            if node.get("value", "").isdigit():
                packages.add(int(node["value"]))
    for block in soup.select("[data-ds-bundleid][data-ds-bundle-data], .game_area_purchase_game_wrapper[data-ds-bundleid]"):
        title = block.select_one("h2, h1")
        price = block.select_one("[data-price-final]")
        try:
            d = json.loads(block["data-ds-bundle-data"])
            items = d["m_rgItems"]
            ids = sorted({int(a) for item in items for a in item["m_rgIncludedAppIDs"]})
            formatted = block.select_one(".discount_final_price")
            krw = formatted is not None and "₩" in formatted.get_text()
            bundles.append(Product(
                "bundle", int(block["data-ds-bundleid"]),
                title.get_text(" ", strip=True) if title else "Bundle",
                won(int(price["data-price-final"])) if price and krw else None,
                discount=int(price.get("data-discount", 0)) if price else 0,
                currency="KRW" if krw else "UNKNOWN", scan_id=scan_id,
                app_ids=ids, contents=[{"id": i, "name": f"App {i}"} for i in ids],
                composition_verified=bool(ids),
                unconditional=d.get("m_bMustPurchaseAsSet") in (1, True),
                evidence="Store data-ds-bundle-data; m_bMustPurchaseAsSet"))
        except (ValueError, KeyError, TypeError):
            if str(block.get("data-ds-bundleid", "")).isdigit():
                bundles.append(Product("bundle", int(block["data-ds-bundleid"]),
                                       title.get_text(" ", strip=True) if title else "Bundle",
                                       None, scan_id=scan_id, evidence="Bundle composition schema unavailable"))
    return packages, bundles


def package_unconditional(html, package_id):
    soup = BeautifulSoup(html, "html.parser")
    form = soup.select_one(f'input[name="subid"][value="{package_id}"], input[name="subid[]"][value="{package_id}"]')
    area = form.find_parent(class_="game_area_purchase_game") if form else None
    if area is None:
        return False
    # A known base app in the package plus a public one-time purchase form is required.
    notices = " ".join(n.get_text(" ", strip=True) for n in soup.select(
        ".game_area_dlc_bubble, .game_area_purchase_game, .notice_box_content"))
    return not re.search(r"requires.*(?:base game|ownership)|upgrade|subscription|구독|업그레이드|본편.*필요", notices, re.I)
