import pytest
from src.parser import parse_app, parse_package, won, search_items, purchase_candidates, package_unconditional


def test_app_krw():
    p, _ = parse_app({"1": {"success": True, "data": {"steam_appid": 1, "name": "게임", "type": "game", "price_overview": {"currency": "KRW", "initial": 5300000, "final": 315000, "discount_percent": 94}}}}, 1, "run")
    assert (p.price, p.original_price, p.discount, p.app_type) == (3150, 53000, 94, "game")


def test_missing_price_and_api_error():
    p, _ = parse_app({"1": {"success": True, "data": {"steam_appid": 1, "name": "X"}}}, 1, "run")
    assert p.price is None and p.currency == "UNKNOWN"
    with pytest.raises(ValueError):
        parse_app({"1": {"success": False}}, 1, "run")


def test_explicit_free_flag_excluded_despite_stale_price():
    p, _ = parse_app({"1": {"success": True, "data": {"steam_appid": 1, "name": "Free", "is_free": True, "price_overview": {"currency": "KRW", "final": 10000}}}}, 1, "run")
    assert p.price == 0


@pytest.mark.parametrize("value", [None, -100, 123, True, "100"])
def test_invalid_money(value):
    assert won(value) is None


def test_search_dedup():
    assert search_items('<a class="search_result_row" href="https://store.steampowered.com/app/10/"></a>' * 2) == [("app", 10)]


def test_package_composition():
    p = parse_package({"2": {"success": True, "data": {"name": "Gold", "apps": [{"id": 1, "name": "Game"}, {"id": 3, "name": "DLC"}], "price": {"currency": "KRW", "final": 315000}}}}, 2, "run")
    assert p.composition_verified and p.app_ids == [1, 3] and not p.unconditional


def test_purchase_verification():
    html = '<div class="game_area_purchase_game"><input name="subid" value="2"></div>'
    assert package_unconditional(html, 2)
    assert not package_unconditional(html.replace('</div>', 'Upgrade</div>'), 2)
    assert not package_unconditional("", 2)


def test_personalized_bundle():
    html = '''<div data-ds-bundleid="5" data-ds-bundle-data='{"m_bMustPurchaseAsSet":0,"m_rgItems":[{"m_rgIncludedAppIDs":[1,3]}]}'><h2>Gold</h2><div data-price-final="315000" data-discount="94"><div class="discount_original_price">₩ 53,000</div><div class="discount_final_price">₩ 3,150</div></div></div>'''
    _, bundles = purchase_candidates(html, "run")
    assert bundles[0].app_ids == [1, 3] and bundles[0].price == 3150
    assert bundles[0].original_price == 53000 and bundles[0].discount == 94
    assert not bundles[0].unconditional
    _, bundles = purchase_candidates(html.replace('AsSet":0', 'AsSet":1'), "run")
    assert bundles[0].unconditional


def test_broken_bundle_is_preserved_for_review():
    _, bundles = purchase_candidates('<div class="game_area_purchase_game_wrapper" data-ds-bundleid="5"><h2>Gold</h2></div>', "run")
    assert len(bundles) == 1 and not bundles[0].composition_verified
