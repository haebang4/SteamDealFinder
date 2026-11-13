from dataclasses import replace
import pytest
from src.models import Product
from src.edition_matcher import compare_editions


@pytest.fixture
def products():
    base = Product("app", 1, "Racing", 53000, app_type="game", scan_id="run")
    standard = Product("sub", 2, "Racing", 53000, app_ids=[1], composition_verified=True, unconditional=True, scan_id="run")
    edition = Product("sub", 3, "Racing Fan Edition", 3150, app_ids=[1, 4], composition_verified=True, unconditional=True, scan_id="run")
    return base, standard, edition


def test_verified_inversion(products):
    base, standard, edition = products
    yes, unknown = compare_editions(base, [standard, edition])
    assert not unknown and yes[0]["difference"] == 49850
    assert yes[0]["inversion_percent"] == 94.06


@pytest.mark.parametrize("change", [dict(app_ids=[4]), dict(composition_verified=False), dict(unconditional=False), dict(currency="USD"), dict(country="US"), dict(price=None), dict(price=0), dict(scan_id="old"), dict(collected_at="2020-01-01T00:00:00+00:00"), dict(app_ids=[1])])
def test_false_positives(products, change):
    base, standard, edition = products
    yes, unknown = compare_editions(base, [standard, replace(edition, **change)])
    assert not yes and len(unknown) == 1


def test_no_baseline_or_free(products):
    base, standard, edition = products
    for candidates in ([edition], [replace(standard, price=0), edition]):
        assert not compare_editions(base, candidates)[0]


def test_dlc_is_not_base(products):
    base, standard, edition = products
    assert not compare_editions(replace(base, app_type="dlc"), [standard, edition])[0]


def test_no_inversion(products):
    base, standard, edition = products
    assert compare_editions(base, [standard, replace(edition, price=60000)]) == ([], [])
