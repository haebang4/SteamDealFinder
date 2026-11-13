# Steam Deal Finder

대한민국 Steam 스토어의 초특가와 **일반판보다 저렴한 상위 상품**을 찾는 Python 3.11+ 프로그램입니다. GitHub Actions가 수집하고 GitHub Pages가 결과를 보여주므로, 사용자는 Python이나 IDE를 설치하지 않아도 됩니다.

**[결과 페이지 열기](https://haebang4.github.io/SteamDealFinder/)** · [GitHub Actions](https://github.com/haebang4/SteamDealFinder/actions/workflows/daily_scan.yml) · [배포 검증 실행](https://github.com/haebang4/SteamDealFinder/actions/runs/43481751611)

## 구현 및 검증 상태

- KRW 할인 수집, 조건 필터, 패키지·번들 구성 기반 비교, 확인 필요 목록, CSV/JSON/정적 HTML 생성 구현.
- 이름 유사성으로 게임을 연결하지 않습니다. 동일한 본편 App ID와 추가 App ID가 포함되어야 확정합니다.
- 오프라인 pytest와 실제 Steam 소량 수집을 수행했습니다. 자세한 수치는 `data/validation.md`를 참조하세요.
- GitHub Actions의 Linux·Python 3.11 환경에서 테스트 49개, 실제 Steam 수집, Pages 배포를 검증했습니다. 2026-11-14 첫 성공 실행은 게임 20개·상품 76개를 조사했고 초특가 0건·확정 역전 0건·확인 필요 55건입니다.
- 매일 09:00 KST 예약과 수동 실행을 설정했습니다. 첫 예약 이벤트 자체의 실행 여부는 해당 시각 이후 Actions 로그에서 확인해야 합니다.
- 전체 카탈로그 수집기나 가격 보장 서비스가 아닙니다. 결과가 0건이어도 해당 특가가 Steam 전체에 없다는 뜻은 아닙니다.

## GitHub에서만 사용하기

1. 자신의 GitHub 계정에 저장소를 만들고 이 프로젝트 파일을 업로드합니다. 기본 브랜치는 `main`을 사용합니다. `.github/workflows/daily_scan.yml`, `src`, `tests`, `config.yaml`, `requirements.txt`, `pyproject.toml`을 포함합니다. `.venv`는 업로드하지 않습니다.
2. 저장소 **Settings → Pages → Build and deployment → Source → GitHub Actions**를 선택합니다.
3. **Actions → Daily Steam KR scan → Run workflow**를 실행합니다. 워크플로 실행을 비활성화한 저장소에서는 먼저 허용합니다.
4. `scan`과 `deploy`가 모두 성공하면 **Settings → Pages** 또는 Actions 배포 환경의 URL을 엽니다. 이 저장소는 `https://haebang4.github.io/SteamDealFinder/`에 배포되어 있습니다. 다른 저장소에서는 `https://<사용자명>.github.io/<저장소명>/` 형식의 주소를 사용합니다.
5. 매일 오전 9시(KST, cron `0 0 * * *` UTC) 자동 실행합니다. GitHub 예약 실행은 지연되거나 누락될 수 있으며, 비활성 공개 저장소에서는 스케줄이 비활성화될 수 있습니다.

처음에는 공개 저장소를 권장합니다. 비공개 저장소의 Pages 제공 여부는 GitHub 요금제에 따라 다릅니다. 현재 수집은 API 키나 Secrets가 필요하지 않습니다. 비밀번호·개인 토큰을 코드나 이슈에 입력하지 마세요.

설정은 GitHub에서 `config.yaml`을 편집하고 커밋하면 됩니다. 수동 실행 화면의 `max_games`에 조사 게임 수를 지정할 수 있으며, 비워 두면 설정 파일의 값을 사용합니다. 예약 실행은 설정 파일을 사용합니다. 결과를 Git 커밋으로 매일 누적하지 않으며, Pages와 실행별 Artifact로 배포·보관합니다.

`main`의 수집 코드·테스트·설정·워크플로를 수정하면 20개 게임의 검증 수집과 Pages 갱신을 자동 실행합니다. 매일 예약 실행은 이 검증 한도와 별개로 `config.yaml`의 수집 한도를 사용합니다.

## 로컬 실행 (선택)

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m src.main
```

Linux/macOS에서는 `.venv/bin/python`을 사용합니다. 프로젝트 루트에서 실행하세요.

```bash
python -m src.main --min-discount 90 --max-price 5000 --max-pages 2 --max-games 30
python -m src.main --watch-app-ids 244210 255710
python -m src.main --demo --output-dir data/demo
```

`docs/index.html`은 파일을 더블클릭해 열 수 있습니다. 데이터가 HTML 안에 포함되어 있어 서버가 필요 없습니다. 데모는 `data/demo/`에 별도로 생성하며 화면과 JSON에 모의 데이터임을 표시합니다. 데모의 Steam ID와 링크는 가짜이며 실제 구매에 사용하면 안 됩니다.

종료 코드 `0`은 설정된 범위 내 수집 완료, `2`는 부분 수집·실패 또는 잘못된 설정입니다. 완료는 전체 카탈로그 조사나 특가 발견을 뜻하지 않습니다.

## 설정

| 키 | 기본값 | 설명 |
| --- | --- | --- |
| `min_discount` | 90 | 초특가 최소 할인율(%) |
| `max_price` | 5000 | 초특가 최대 원화 판매 가격, 무료 제외 |
| `max_pages` | 4 | 할인 검색 페이지 상한 |
| `search_sort` | `_ASC` | Steam 관련도 순. `Price_ASC`, `Price_DESC`, `Released_DESC`, `Name_ASC`, `Reviews_DESC`도 지원 |
| `max_games` | 100 | 상세 조사할 App 수 상한 |
| `max_packages_per_game` | 12 | 게임당 패키지 조회 상한 |
| `request_interval` | 1.5 | 요청 사이 최소 초, 1초 미만 불가 |
| `retries` | 3 | 일시 오류 최대 재시도 횟수 |
| `timeout` | 30 | 요청 연결·응답 타임아웃(초) |
| `max_price_age_seconds` | 600 | 비교 가격 간 허용 수집 시각 차이 |
| `watch_app_ids` | `[]` | 할인 여부와 무관하게 우선 조사할 본편 App ID 목록 |
| `output_dir` | `docs` | 결과 디렉터리 |

CLI의 `--min-discount`, `--max-price`, `--max-pages`, `--max-games`, `--watch-app-ids`, `--output-dir`은 YAML을 덮어씁니다. 국가는 KR, 통화는 KRW로 고정합니다. 할인·가격 필터는 초특가 목록에 적용하며, 가격 역전은 별도로 모두 검사합니다. 웹 필터는 이미 수집된 결과 안에서만 작동합니다.

**핵심 활용법:** 가격 역전은 일반판이 할인되지 않은 게임에서도 발생합니다. 관심 있는 본편 ID를 `watch_app_ids`에 등록하세요. 검색은 할인된 게임의 일부만 발견하므로 이 목록이 실용적인 보완 수단입니다. Steam URL의 `/app/244210/`에서 숫자를 복사할 수 있습니다.

## 가격 역전 검증 규칙

1. `appdetails.type == game`인 본편을 기준으로 조사합니다. DLC·데모를 본편으로 사용하지 않습니다.
2. 본편 구매 영역과 `appdetails.packages`에서 Package ID 및 Bundle ID를 발견합니다. 게임 이름은 후보 표시 용도로만 사용합니다.
3. `packagedetails.apps` 또는 스토어의 `data-ds-bundle-data.m_rgItems`에 **동일한 본편 App ID와 추가 App ID**가 있어야 상위 상품으로 판단합니다.
4. 일반판 기준은 본편 App ID 하나만 포함하며 공개 일회성 구매 양식이 확인되는 패키지 중 최저가입니다. 에디션 명칭이 있는 단일 App 패키지는 기준에서 보수적으로 제외합니다. `appdetails.price_overview`는 초특가에만 사용하며 일반판 가격 기준으로 사용하지 않습니다.
5. 패키지는 공개 구매 양식과 업그레이드·구독·본편 필요 안내를 검사합니다. Steam의 모든 계정별 구매 자격을 검증하는 것은 아닙니다. 구성이나 조건이 불명확하면 `확인 필요`로 분리합니다.
6. Complete The Set 개인화 번들은 확정에서 제외합니다. `m_bMustPurchaseAsSet`이 참인 번들만 비로그인 신규 구매자 기준으로 비교할 수 있습니다. 이 번들도 기존 소유자는 구매할 수 없는 조건이 있을 수 있습니다.
7. 양쪽 모두 동일 실행에서 조회한 KR/KRW 유료 가격이며 수집 시각 차이가 설정 범위 이내여야 합니다. HTTP 원자적 스냅샷이 아니므로 수집 중 할인 변경 가능성은 남습니다.
8. 역전율 = `(일반판 판매가 - 상위 상품 판매가) / 일반판 판매가 × 100`. 일반판이 무료·미확인인 경우 계산하지 않습니다. 정가가 아닌 **현재 일반판 판매가**와 비교합니다.

숫자 통화는 Steam 응답의 1/100 단위를 원으로 변환합니다. `KRW`가 아닌 통화, 비정상 값 또는 분수 원 가격은 확정하지 않습니다. 할인이 종료되는 시각을 확실히 확인할 수 없는 경우 추정하지 않고 `null`/미확인으로 남깁니다.

## 결과 파일

| 파일 | 내용 |
| --- | --- |
| `deals.csv` | 필터 조건을 만족하는 본편 할인 목록 |
| `all_products.csv` | 조건 충족 여부와 무관한 전체 수집 상품(본편·패키지·번들)의 현재가·정가·할인율 |
| `edition_inversions.csv` | 검증된 역전, 가격 차이·비율·구성·증거·각 URL·가격 수집 시각 |
| `unverified.csv` | 본편 미포함, 개인화, 구성·가격 미확인 등의 사유 |
| `results.json` | 실행 상태, 검색 범위, 오류, 수집한 App, 조사한 모든 offer, 확정/미확인 결과 |
| `index.html` | 검색·필터·정렬·다운로드를 갖춘 정적 대시보드 |

`price`는 현재 판매가(원), `original_price`는 정가(원), `discount`는 할인율(%)입니다. 비교 CSV는 일반판에 `standard_`, 상위 상품에 `edition_` 접두사를 사용합니다. 확인 필요 CSV도 양쪽 가격을 포함하며, 일반판 패키지를 확인하지 못한 경우 참고용 본편 App 가격을 `base_app_price`, `base_app_original_price`, `base_app_discount`로 별도 표시합니다. 가격이 확인되지 않으면 0원으로 채우지 않고 빈칸으로 남깁니다. 번들 정가도 Steam이 표시한 값을 확인할 수 있을 때만 저장합니다.

초특가나 가격 역전이 0건이어도 `all_products.csv`에는 수집한 상품 가격이 저장됩니다. 웹페이지의 **수집한 전체 본편** 표에서도 본편의 정가·현재 가격·할인율을 확인할 수 있습니다.

CSV는 UTF-8 BOM이며 Excel 수식 실행 방지를 위해 수식 문자로 시작하는 문자열에 작은따옴표를 붙입니다. HTML은 게임명을 HTML로 실행하지 않도록 이스케이프하고 `textContent`로 표시합니다.

## 데이터 출처와 접근 제한

- 공식 [IStoreService 문서](https://partner.steamgames.com/doc/webapi/IStoreService)는 전체 App 목록 조회에 API 키를 요구합니다. 목록만으로 한국 가격이나 에디션 구성을 알 수 없으므로 현재는 비로그인 공개 Steam Store 응답을 제한된 범위로 사용합니다.
- `https://store.steampowered.com/search/results/`: `specials=1`, `category1=998`, `cc=kr`. 서버가 요청한 count를 무시할 수 있어 실제 파싱된 행 수로 페이지를 이동합니다. 총 검색 결과 수와 실제 조사 수를 기록합니다.
- `/api/appdetails`, `/api/packagedetails`, `/app/<id>/`, `/sub/<id>/`: 공개 스토어의 **비공식·미보장 인터페이스**입니다. 응답·선택자 변경으로 누락될 수 있으며 API 호환성은 보장되지 않습니다. 파서는 `src/parser.py`에 분리했습니다.
- [Steam 패키지 개념](https://partner.steamgames.com/doc/store/application/packages), [번들 유형·소유권별 가격](https://partner.steamgames.com/doc/store/application/bundles)을 기준으로 보수적으로 구분합니다.
- 먼저 `robots.txt`를 확인하고 금지된 경로는 요청하지 않습니다. 로그인·연령 확인·CAPTCHA·접근 차단을 우회하지 않습니다. HTTP 401/403과 도전 페이지는 즉시 중지합니다. 429는 Retry-After를 지키며 제한 횟수 후 전체 수집을 중지합니다. 5xx·타임아웃은 지수 백오프로 재시도합니다. 긴 Retry-After(300초 초과)는 조기 재시도하지 않고 중지합니다.
- 공개 비로그인 지역 요청이 실제 계정의 결제 가능 여부를 증명하지 않습니다. 최종 구매는 자신의 한국 스토어 계정에서 확인해야 합니다.

## 자동화와 장애 처리

`.github/workflows/daily_scan.yml`에서 테스트 → 수집 → 결과 Artifact → Pages 배포 순서로 실행합니다. 기본 Python은 3.11입니다. Actions 로그와 `steam-scan-<run_id>` Artifact에 CSV/HTML/JSON 및 `scan.log`를 30일 보존합니다.

부분 실패 시 로컬 결과에 `partial`/`failed`와 오류를 기록하고 비정상 종료합니다. Artifact는 보존하고 배포는 건너뛰므로 기존 Pages 결과가 유지됩니다. 따라서 **웹의 최종 검색 시각과 Actions 상태를 함께 확인**하세요. 설치·테스트 단계에서 실패하면 `scan.log`가 없을 수 있고 해당 단계의 Actions 로그를 확인해야 합니다. 실행 시간 상한은 55분이며 조사 한도를 크게 늘리면 시간 초과할 수 있습니다.

워크플로 참고: [GitHub Pages 커스텀 워크플로](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages). 권한은 수집 작업 `contents: read`, 배포 작업 `pages: write`, `id-token: write`로 분리했습니다.

## 테스트와 남은 과제

```bash
python -m pytest -q
```

실제 Steam 없이 가격 변환, 할인 경계, 무료/DLC 제외, App 구성 관계, 53,000원↔3,150원 역전, 지역·시각·실행 불일치, 미확인 구성, HTTP 재시도·차단, robots, CLI 설정, BOM CSV·HTML 및 수집부터 분석까지 검사합니다.

선택적인 브라우저 점검은 Playwright/Chromium이 있는 개발 환경에서 `python -m src.main --demo --output-dir data/demo` 후 `node tools/browser_smoke.cjs`로 실행합니다. 이는 일반 실행에 필요한 의존성이 아닙니다. 기존 Chrome 경로를 `BROWSER_EXECUTABLE`, Playwright 모듈 경로를 `PLAYWRIGHT_MODULE` 환경변수로 지정할 수 있습니다.

다음은 아직 지원 범위 밖이거나 추가 검증이 필요합니다.

- 전체 Steam 카탈로그·숨겨진 패키지·전체 bundlelist 탐색. 검색 상한과 지역·연령 제한에 따른 누락이 있습니다.
- 별도 App ID로 판매되는 에디션과 동일 App 내부 잠금 해제형 에디션의 관계. 이름으로 추정하지 않으므로 놓칠 수 있습니다.
- 개인화 번들의 신규 구매자 가격과 소유자별 가격 비교. 현재는 확인 필요로 남깁니다.
- 추가 콘텐츠가 실제 DLC인지, 별도 게임인지의 상세 분류. 포함 App ID와 알려진 상품명을 표시하며, 번들에선 이름 대신 App ID만 표시될 수 있습니다.
- 공개 구매 양식에서 드러나지 않는 계정·지역·소유권 조건. 최종 구매 가능 여부를 보장하지 않습니다.
- 정밀 할인 종료일, 장기 가격 이력, 알림, 데이터베이스, 실제 특가 역전의 실시간 검증.
- 매일 예약 실행의 장기 안정성과 Steam 응답 변경에 대한 지속 점검. 수동 실행·첫 배포는 검증했으며 향후 예약 실행은 Actions에서 확인해야 합니다.
