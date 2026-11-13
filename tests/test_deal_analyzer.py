from src.models import Product
from src.deal_analyzer import find_deals


def test_deals_filter_and_sort():
    def p(i, price=3150, discount=94, **kw):
        return Product("app", i, "게임", price, discount=discount, app_type="game", **kw)
    good = p(1)
    assert find_deals([good, good, p(2, 0), p(3, None), p(4, 5001), p(5, 100, 89), p(6, currency="USD"), p(7, country="US"), p(8, 1000)]) == [p(8, 1000), good]


def test_dlc_excluded():
    assert not find_deals([Product("app", 1, "DLC", 100, discount=99, app_type="dlc")])
