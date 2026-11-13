from unittest.mock import Mock
from src.collector import collect
from src.main import analyze, DEFAULTS


def test_offline_collect_to_verified_inversion():
    c = Mock(requests=7)
    def get_json(path, **params):
        if path == "/search/results/":
            return {"results_html": '<a class="search_result_row" href="https://store.steampowered.com/app/1/"></a>', "total_count": 1}
        if path == "/api/appdetails":
            return {"1": {"success": True, "data": {"steam_appid": 1, "name": "Race", "type": "game", "packages": [2, 3], "price_overview": {"currency": "KRW", "initial": 5300000, "final": 5300000}}}}
        package_id = params["packageids"]
        apps = [{"id": 1, "name": "Race"}]
        if package_id == 3:
            apps.append({"id": 4, "name": "DLC"})
        return {str(package_id): {"success": True, "data": {"name": "Race" if package_id == 2 else "Racing Fan Edition", "apps": apps, "price": {"currency": "KRW", "final": 5300000 if package_id == 2 else 315000}}}}
    def get_html(path, **params):
        if path.startswith("/app/"):
            return Mock(text="")
        package_id = path.split("/")[2]
        return Mock(text=f'<div class="game_area_purchase_game"><input name="subid" value="{package_id}"></div>')
    c.json.side_effect = get_json
    c.get.side_effect = get_html
    result = analyze(collect(DEFAULTS, c), DEFAULTS)
    assert result["status"] == "complete"
    assert result["edition_inversions"][0]["inversion_percent"] == 94.06
    assert len(result["inspected_offers"][0]["offers"]) == 2
    assert not result["unverified"]
