import argparse
import logging
from pathlib import Path
import sys
import yaml
from .collector import collect
from .deal_analyzer import find_deals
from .edition_matcher import compare_editions
from .exporter import export_results
from .models import Product, utcnow

DEFAULTS = {"min_discount": 90, "max_price": 5000, "max_pages": 4, "search_sort": "_ASC", "max_games": 100,
            "max_packages_per_game": 12, "request_interval": 1.5, "retries": 3,
            "timeout": 30, "max_price_age_seconds": 600, "watch_app_ids": [], "output_dir": "docs"}


def configuration(args):
    cfg = DEFAULTS.copy()
    path = Path(args.config)
    if not path.is_file():
        raise ValueError(f"설정 파일을 찾을 수 없습니다: {path}")
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if loaded is None:
        loaded = {}
    if not isinstance(loaded, dict) or set(loaded) - set(DEFAULTS):
        raise ValueError("설정 형식 또는 키가 올바르지 않습니다")
    cfg.update(loaded)
    for key in DEFAULTS:
        value = getattr(args, key, None)
        if value is not None:
            cfg[key] = value
    for key in ("min_discount", "max_price", "max_pages", "max_games", "max_packages_per_game", "retries", "max_price_age_seconds"):
        if type(cfg[key]) is not int or cfg[key] < 0:
            raise ValueError(f"{key}: 0 이상의 정수가 필요합니다")
    if cfg["min_discount"] > 100 or not all(cfg[k] > 0 for k in ("max_pages", "max_games", "max_packages_per_game", "max_price_age_seconds")):
        raise ValueError("할인율은 0~100, 수집 한도 및 가격 유효 시간은 1 이상이어야 합니다")
    if not isinstance(cfg["request_interval"], (int, float)) or cfg["request_interval"] < 1:
        raise ValueError("요청 간격은 최소 1초입니다")
    if not isinstance(cfg["timeout"], (int, float)) or cfg["timeout"] <= 0:
        raise ValueError("timeout은 양수여야 합니다")
    if not isinstance(cfg["watch_app_ids"], list) or any(type(x) is not int or x <= 0 for x in cfg["watch_app_ids"]):
        raise ValueError("watch_app_ids는 양의 App ID 목록이어야 합니다")
    if not isinstance(cfg["output_dir"], str) or not cfg["output_dir"].strip():
        raise ValueError("output_dir이 필요합니다")
    if cfg["search_sort"] not in ("_ASC", "Price_ASC", "Price_DESC", "Released_DESC", "Name_ASC", "Reviews_DESC"):
        raise ValueError("지원하지 않는 search_sort입니다")
    return cfg


def analyze(raw, cfg):
    confirmed, unknown = [], []
    inspected = []
    for base, products in raw.pop("comparisons"):
        inspected.append({"base_app_id": base.id, "offers": [p.to_dict() for p in products]})
        yes, no = compare_editions(base, products, cfg["max_price_age_seconds"])
        confirmed.extend(yes)
        unknown.extend(no)
    apps = raw.pop("apps")
    return {**raw, "filters": {"min_discount": cfg["min_discount"], "max_price": cfg["max_price"]},
            "products": [p.to_dict() for p in apps],
            "deals": [p.to_dict() for p in find_deals(apps, cfg["min_discount"], cfg["max_price"])],
            "edition_inversions": sorted(confirmed, key=lambda x: -x["inversion_percent"]),
            "inspected_offers": inspected, "unverified": unknown}


def demo():
    now = utcnow()
    base = Product("app", 1, "모의 Racing Game", 53000, app_type="game", scan_id=now)
    standard = Product("sub", 2, "모의 Racing Game", 53000, app_ids=[1], composition_verified=True, unconditional=True, scan_id=now)
    edition = Product("sub", 3, "모의 Racing Fan Edition", 3150, app_ids=[1, 4],
                      contents=[{"id": 1, "name": "모의 본편"}, {"id": 4, "name": "모의 추가 콘텐츠"}],
                      composition_verified=True, unconditional=True, scan_id=now, evidence="synthetic demo fixture")
    deal = Product("app", 5, "모의 할인 게임", 3000, original_price=30000, discount=90, app_type="game", scan_id=now)
    return {"scan_id": now, "started_at": now, "finished_at": now, "demo": True, "status": "complete",
            "country": "KR", "currency": "KRW", "errors": [], "scope": {"max_games": 2, "notes": ["모의 데이터"]},
            "apps": [base, deal], "comparisons": [(base, [standard, edition])], "request_count": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Steam KR 할인 및 구성 검증 기반 에디션 가격 역전 탐지")
    parser.add_argument("--config", default="config.yaml")
    for name in ("min-discount", "max-price", "max-pages", "max-games"):
        parser.add_argument("--" + name, type=int)
    parser.add_argument("--watch-app-ids", type=int, nargs="+")
    parser.add_argument("--output-dir")
    parser.add_argument("--demo", action="store_true", help="실제 결과와 구분되는 모의 데이터")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        cfg = configuration(args)
    except (ValueError, yaml.YAMLError) as exc:
        parser.error(str(exc))
    result = analyze(demo() if args.demo else collect(cfg), cfg)
    export_results(result, cfg["output_dir"])
    logging.info("status=%s apps=%s deals=%s inversions=%s unverified=%s requests=%s",
                 result["status"], len(result["products"]), len(result["deals"]),
                 len(result["edition_inversions"]), len(result["unverified"]), result["request_count"])
    return 0 if result["status"] == "complete" else 2


if __name__ == "__main__":
    sys.exit(main())
