import pytest
from src.main import main


@pytest.mark.parametrize("content", ["min_discount: 101", "max_games: 0", "request_interval: 0", "watch_app_ids: [x]", "unknown: 1", "max_price: -1", "[]", "search_sort: unknown"])
def test_bad_config_rejected(tmp_path, content):
    config = tmp_path / "config.yaml"
    config.write_text(content, encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        main(["--config", str(config), "--demo", "--output-dir", str(tmp_path / "output")])
    assert exc.value.code == 2
