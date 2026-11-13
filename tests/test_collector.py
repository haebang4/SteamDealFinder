from unittest.mock import Mock
import pytest
import requests
from src.collector import SteamClient, CollectionError, BlockedError, collect
from src.main import DEFAULTS


def response(status=200, data=None, headers=None, text="{}"):
    r = Mock(status_code=status, headers=headers or {}, text=text)
    r.json.return_value = data
    if status >= 400:
        r.raise_for_status.side_effect = requests.HTTPError(str(status))
    return r


def client_with(responses):
    session = Mock()
    session.get.side_effect = responses
    sleep = Mock()
    return SteamClient(session=session, sleep=sleep, retries=2), session, sleep


def test_retry_backoff_and_retry_after():
    c, session, sleep = client_with([response(429, headers={"Retry-After": "7"}), response(503), response()])
    c.get("/api/appdetails")
    assert session.get.call_count == 3
    assert any(call.args == (7.0,) for call in sleep.call_args_list)
    assert any(call.args == (2,) for call in sleep.call_args_list)


@pytest.mark.parametrize("status", [401, 403])
def test_block_stops_immediately(status):
    c, session, _ = client_with([response(status)])
    with pytest.raises(BlockedError):
        c.get("/api/appdetails")
    assert session.get.call_count == 1


def test_throttling_stops_after_limit():
    c, session, _ = client_with([response(429)] * 3)
    with pytest.raises(BlockedError):
        c.get("/api/appdetails")
    assert session.get.call_count == 3


def test_timeout_and_invalid_json():
    c, _, _ = client_with([requests.Timeout()] * 3)
    with pytest.raises(CollectionError):
        c.get("/search/results/")
    r = response()
    r.json.side_effect = ValueError("bad json")
    c, _, _ = client_with([r])
    with pytest.raises(CollectionError):
        c.json("/api/appdetails")


def test_robots_respected():
    c, session, _ = client_with([response(text="User-agent: *\nDisallow: /search/")])
    c.check_robots()
    with pytest.raises(CollectionError, match="robots"):
        c.get("/search/results/")
    assert session.get.call_count == 1


def test_failed_scan_is_not_successful_empty_result():
    c, _, _ = client_with([response(403)])
    result = collect(DEFAULTS, c)
    assert result["status"] == "failed" and result["errors"]


def test_search_pagination_uses_actual_row_count():
    c = Mock(requests=0)
    c.json.side_effect = [
        {"results_html": '<a class="search_result_row" href="https://store.steampowered.com/app/10/"></a>', "total_count": 2},
        {"results_html": '<a class="search_result_row" href="https://store.steampowered.com/app/20/"></a>', "total_count": 2},
        {"10": {"success": True, "data": {"steam_appid": 10, "name": "DLC", "type": "dlc"}}},
        {"20": {"success": True, "data": {"steam_appid": 20, "name": "DLC", "type": "dlc"}}}]
    result = collect(DEFAULTS, c)
    assert result["status"] == "complete"
    assert c.json.call_args_list[1].kwargs["start"] == 1
