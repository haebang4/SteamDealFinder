import logging
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.robotparser import RobotFileParser
import requests
from .models import utcnow
from .parser import parse_app, parse_package, search_items, purchase_candidates, package_unconditional

LOG = logging.getLogger(__name__)
ROOT = "https://store.steampowered.com"


class CollectionError(RuntimeError):
    pass


class BlockedError(CollectionError):
    pass


class SteamClient:
    def __init__(self, interval=1.5, retries=3, timeout=30, session=None, sleep=time.sleep):
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": "SteamDealFinder/1.0 (public KR price research; no login)"})
        self.interval, self.retries, self.timeout = interval, retries, timeout
        self.sleep = sleep
        self.last_request = 0.0
        self.requests = 0
        self.robots = None

    def get(self, path, **params):
        url = ROOT + path
        if self.robots and not self.robots.can_fetch("SteamDealFinder", url):
            raise CollectionError(f"robots.txt disallows {path}")
        for attempt in range(self.retries + 1):
            self.sleep(max(0, self.interval - (time.monotonic() - self.last_request)))
            try:
                self.last_request = time.monotonic()
                self.requests += 1
                r = self.session.get(url, params=params, timeout=self.timeout)
                if r.status_code in (401, 403):
                    raise BlockedError(f"Steam access denied ({r.status_code}); scan stopped")
                if r.status_code == 429 or r.status_code >= 500:
                    if attempt == self.retries:
                        if r.status_code == 429:
                            raise BlockedError("Steam HTTP 429: retry limit reached; scan stopped")
                        raise CollectionError(f"Steam HTTP {r.status_code}: retry limit reached")
                    retry = r.headers.get("Retry-After", "0")
                    try:
                        wait = float(retry)
                    except ValueError:
                        try:
                            wait = (parsedate_to_datetime(retry) - datetime.now(timezone.utc)).total_seconds()
                        except (ValueError, TypeError):
                            wait = 0
                    if wait > 300:
                        raise BlockedError("Long Retry-After; scan stopped instead of retrying early")
                    self.sleep(max(2 ** attempt, wait))
                    continue
                r.raise_for_status()
                if "captcha" in r.text.lower() and "<html" in r.text.lower():
                    raise BlockedError("Challenge page received; scan stopped")
                return r
            except (requests.ConnectionError, requests.Timeout) as exc:
                if attempt == self.retries:
                    raise CollectionError(str(exc)) from exc
                self.sleep(2 ** attempt)
            except requests.HTTPError as exc:
                raise CollectionError(str(exc)) from exc
        raise CollectionError("No response")

    def check_robots(self):
        response = self.get("/robots.txt")
        parser = RobotFileParser()
        parser.parse(response.text.splitlines())
        self.robots = parser

    def json(self, path, **params):
        try:
            return self.get(path, cc="kr", l="koreana", **params).json()
        except ValueError as exc:
            raise CollectionError("Invalid JSON from Steam") from exc


def collect(config, client=None):
    client = client or SteamClient(config["request_interval"], config["retries"], config["timeout"])
    scan_id = utcnow()
    result = {"scan_id": scan_id, "started_at": scan_id, "country": "KR", "currency": "KRW",
              "status": "complete", "errors": [], "apps": [], "comparisons": [],
              "scope": {"max_pages": config["max_pages"], "max_games": config["max_games"],
                        "search_sort": config["search_sort"],
                        "max_packages_per_game": config["max_packages_per_game"],
                        "catalog_complete": False, "search_total": None,
                        "notes": ["할인 검색의 제한된 페이지와 watch_app_ids만 조사합니다.",
                                  "일반판이 할인 중이 아닌 게임은 watch_app_ids에 없으면 누락될 수 있습니다.",
                                  "게임 구매 영역에 노출된 패키지/번들만 비교하며 숨겨진 상품은 누락됩니다.",
                                  "개인화 번들, 별도 App ID 에디션, 본편만 포함하는 콘텐츠 내장형 에디션은 확정하지 않습니다."]}}
    def error(context, exc):
        LOG.warning("%s: %s", context, exc)
        result["status"] = "partial"
        result["errors"].append({"context": context, "message": str(exc)})
    try:
        client.check_robots()
        discovered = []
        start = 0
        seen_pages = set()
        for page in range(config["max_pages"]):
            try:
                response = client.json("/search/results/", start=start, count=50, specials=1,
                                       json=1, infinite=1, sort_by=config["search_sort"], category1=998)
                if "results_html" not in response or "total_count" not in response:
                    raise CollectionError("Search schema changed")
                result["scope"]["search_total"] = int(response["total_count"])
                items = search_items(response["results_html"])
                signature = tuple(items)
                if not items:
                    if start < int(response["total_count"]):
                        raise CollectionError("Search returned no parseable rows before total_count")
                    break
                if signature in seen_pages:
                    raise CollectionError("Repeated search page; pagination stopped")
                seen_pages.add(signature)
                discovered.extend(items)
                start += len(items)
                if start >= int(response["total_count"]):
                    break
            except (CollectionError, ValueError, KeyError) as exc:
                if isinstance(exc, BlockedError):
                    raise
                error(f"search page {page}", exc)
                break
        ids = list(dict.fromkeys([*config.get("watch_app_ids", []),
                                  *(i for kind, i in discovered if kind == "app")]))
        result["scope"].update(discovered_items=len(set(discovered)), discovered_apps=len(ids),
                                search_pages=len(seen_pages), selected_apps=min(len(ids), config["max_games"]))
        for app_id in ids[:config["max_games"]]:
            LOG.info("Collecting app/%s", app_id)
            try:
                base, data = parse_app(client.json("/api/appdetails", appids=app_id), app_id, scan_id)
                result["apps"].append(base)
                if base.app_type != "game":
                    continue
                html = client.get(f"/app/{app_id}/", cc="kr", l="english").text
                package_ids, bundles = purchase_candidates(html, scan_id)
                package_ids.update(data.get("packages", []))
                packages = []
                for bundle in bundles:
                    for content in bundle.contents:
                        if content["id"] == base.id:
                            content["name"] = base.name
                ordered = sorted(package_ids)
                if len(ordered) > config["max_packages_per_game"]:
                    result["scope"]["notes"].append(f"App {app_id}: package limit; {len(ordered)} available")
                for package_id in ordered[:config["max_packages_per_game"]]:
                    try:
                        p = parse_package(client.json("/api/packagedetails", packageids=package_id), package_id, scan_id)
                        page = client.get(f"/sub/{package_id}/", cc="kr", l="english").text
                        p.unconditional = package_unconditional(page, package_id)
                        p.evidence += "; public purchase form, no detected upgrade/subscription notice"
                        packages.append(p)
                    except (CollectionError, ValueError, KeyError, TypeError) as exc:
                        if isinstance(exc, BlockedError):
                            raise
                        error(f"sub/{package_id}", exc)
                        from .models import Product
                        packages.append(Product("sub", package_id, f"Package {package_id}", None,
                                                scan_id=scan_id, evidence=str(exc)))
                result["comparisons"].append((base, packages + bundles))
            except (CollectionError, ValueError, KeyError, TypeError) as exc:
                if isinstance(exc, BlockedError):
                    raise
                error(f"app/{app_id}", exc)
        if not result["apps"]:
            result["status"] = "failed"
    except (CollectionError, requests.RequestException) as exc:
        error("scan stopped", exc)
        result["status"] = "partial" if result["apps"] else "failed"
    result["finished_at"] = utcnow()
    result["request_count"] = client.requests
    return result
