# 개발 검증 기록

검증일: 2026-11-14 (한국시간). 로컬: Windows, Python 3.12.14. 원격: GitHub Actions Ubuntu 26.04, Python 3.11.18. 두 환경에서 최신 테스트 51개 통과를 확인했습니다.

## 구현 범위

Phase 1~3의 코드(수집·초특가·구성 검증 기반 역전·CSV/JSON/HTML)를 구현했습니다. Phase 4의 예약 실행·수동 실행·Artifact·Pages 워크플로 및 사용 설명서를 작성했고, 원격 수동 실행과 공개 배포까지 검증했습니다. 매일 09:00 KST 예약 이벤트의 첫 실제 실행은 해당 시각 이후 별도 확인이 필요합니다.

## 로컬 실제 Steam 검증 (배포 전 기록)

최종 네트워크 수집 명령:

```powershell
.\.venv\Scripts\python.exe -m src.main --max-pages 1 --max-games 12 --watch-app-ids 244210 255710 --output-dir docs
```

- 종료: 2026-11-14 02:36:19 KST. `status=complete`, 오류 0건, 공개 요청 62회.
- 관련도 순 할인 검색 1페이지(50개 발견), Steam 검색 총 표시 수 6,303개. 전체 목록을 수집하지 않았습니다.
- 관심 게임 2개를 우선 포함해 본편 12개 조사.
- 초특가(90% 이상, 5,000원 이하): **0건**.
- 구성과 조건이 검증된 가격 역전: **0건**. 실제 가격 역전 사례를 발견했다고 주장하지 않습니다.
- 확인 필요: **32건**. 개인화 번들·본편 미포함 등 사유를 `docs/unverified.csv`와 JSON에 저장했습니다.
- 예시 관측 가격: Assetto Corsa 20,500원(0%), Cities: Skylines 33,000원(0%), Euro Truck Simulator 2 6,750원(75%), Hearts of Iron IV 16,500원(70%). 관측 시점 이후 변경될 수 있습니다.
- Assetto Corsa Ultimate Edition은 `m_bMustPurchaseAsSet=0`인 개인화 번들로 확인되어 확정 결과에서 제외했습니다.
- 앞선 소규모 검증도 5개 게임·32회 요청·오류 0건으로 완료했습니다. 최종 보관 결과는 12개 게임 실행입니다.

가격 수집 시각, 검사한 상품 구성과 조건, 범위, 오류를 결과 JSON에 기록했습니다. 이후 로컬 `docs/`는 아래 GitHub 성공 실행의 공개 배포 결과로 동기화했습니다.

## 자동 테스트

- `python -m pytest -q`: 최신 **51개 통과**.
- `python -m compileall -q src`: 통과.
- `python -m pip check`: 의존성 충돌 없음.
- 모의 입력 기준 53,000원 일반판 vs 3,150원 Racing Fan Edition: 차이 49,850원, 역전율 **94.06%** 확인.
- DLC를 기준 본편으로 사용하거나, 구성에 다른 App ID만 있거나, KRW/KR가 아니거나, 일반판이 무료/미확인인 경우 확정하지 않음.
- 서로 다른 수집 실행·오래된 가격·개인화 번들·추가 콘텐츠 없는 에디션·손상된 번들 응답을 검증.
- HTTP 429/5xx/타임아웃 재시도, Retry-After, 401/403 중지, robots 금지 경로, 페이지 이동을 모의 검증.
- UTF-8 BOM CSV, 수식 문자열 방어, HTML 스크립트 삽입 방어, 빈 결과, CLI 오류를 검증.
- 수집기→상품 구성→역전 계산을 연결한 오프라인 통합 테스트 통과.

## 브라우저 검증

설치된 Chrome을 Playwright headless로 사용했습니다. 모의 결과와 실제 결과의 로컬 HTML을 열었습니다.

- 브라우저 JavaScript 오류 없음.
- 게임명 검색, 최대 가격·최소 할인/역전율 필터, 3가지 정렬 동작 확인.
- 1360px 데스크톱 및 390px 모바일 렌더링 확인. 좁은 화면에서는 표 내부를 가로 스크롤합니다.
- 화면 캡처: `data/qa/demo-desktop.png`, `data/qa/demo-mobile.png`, `data/qa/live-desktop.png`.
- 모의 데이터는 실제 결과와 별도로 `data/demo/`에 보관하며 명확한 모의 표시가 있습니다.

## GitHub Actions 및 Pages 최종 검증

- 저장소: https://github.com/haebang4/SteamDealFinder
- 성공 실행: https://github.com/haebang4/SteamDealFinder/actions/runs/43481751611
- 실행 코드 커밋: `8d473a4ae2dbc43cd3e7df64d95d807774de412f`.
- Ubuntu 26.04·Python 3.11.18에서 pytest **49개 통과**.
- 수동 실행의 `max_games=20`. 예약 실행은 입력값 없이 config.yaml 기본 100개를 사용합니다.
- 2026-11-14 **03:23:19 KST** 수집 완료: 게임 **20개**, 조사 상품 **76개**, 요청 **91회**, 오류 **0건**.
- Steam 표시 검색 결과 총 6,309개 중 4페이지의 제한된 후보만 탐색하고 게임 20개를 상세 조사했습니다.
- 초특가 **0건**, 확정 가격 역전 **0건**, 확인 필요 **55건**. 실제 가격 역전 발견을 검증한 것은 아닙니다.
- `scan` 및 `deploy` 작업 모두 success. `steam-scan-43481751611` Artifact 보존(30일) 및 Pages 배포 성공을 확인했습니다.
- 공개 주소: https://haebang4.github.io/SteamDealFinder/
- 브라우저에서 실제 생성 시각·수집 완료 상태·55건 미확인 목록과 다운로드 링크가 표시되는 것을 확인했습니다.
- HTML, results.json, deals.csv, edition_inversions.csv, unverified.csv 모두 HTTP 200 및 CSV BOM을 검증했습니다.
- 최초 원격 실행에서는 테스트가 별도 생성 객체의 미세한 시각 차이까지 비교해 1개 실패했습니다. 같은 입력 객체를 재사용해 정렬을 검증하도록 고친 뒤 새 실행에서 49개 모두 통과했습니다.

## 가격 표시 수정 및 재배포 검증 (03:42 KST)

- 실행: https://github.com/haebang4/SteamDealFinder/actions/runs/43484814915
- 코드 커밋: `34d561a3f46be152edf0fc67de9a30aaea760b7a`. 테스트 51개 및 scan/deploy 모두 성공했습니다.
- 초특가 조건을 통과하지 못한 상품도 포함하는 `all_products.csv`를 추가했습니다. 본편 20개와 관련 상품 76개, 총 **96개 상품**의 관측 가격을 저장했습니다.
- 가격 비교와 확인 필요 CSV에 일반판·상위 상품의 현재가·정가·할인율을 추가했습니다. 일반판 패키지 미확인 시 본편 App의 참고 가격은 별도 열로 표시합니다.
- 확인 필요 목록 **54건** 모두 상위 상품 정가가 저장된 것을 검증했습니다. 스토어에서 원가격을 확인하지 못한 경우는 추정하지 않고 빈칸으로 남깁니다.
- 예시: Euro Truck Simulator 2 현재가 **6,750원**, 정가 **27,000원**, 할인율 **75%**. CSV 값과 JSON 값을 대조했습니다.
- HTML·JSON·4개 CSV가 모두 HTTP 200을 반환하고 CSV의 UTF-8 BOM을 검증했습니다.
- 웹에 전체 본편 가격 표와 전체 상품 CSV 다운로드 링크를 추가했고, 로컬 Chrome에서 렌더링·필터·정렬·다운로드 링크를 확인했습니다.
- 코드 변경 시 20개 게임을 검증 수집해 Pages를 자동 갱신하도록 push 트리거를 추가했습니다. 예약 실행은 config.yaml 한도를 계속 사용합니다.

## 남은 작업과 제한 (가격 수정 후에도 동일)

- 초기 빈 작업 폴더에서 시작했으며, 사용자가 저장소를 지정한 후 소스를 업로드하고 Pages의 Source를 GitHub Actions로 설정했습니다.
- 예약 설정은 매일 오전 9시(KST)입니다. 첫 예약 이벤트와 장기 자동 실행 안정성은 향후 실제 로그에서 확인해야 합니다.
- HTTP 가격은 동시 원자적 스냅샷이 아니고, 신규 비로그인 구매 기준입니다. 실제 계정별 구매 가능 여부는 검증하지 않습니다.
- 전체 카탈로그, 숨겨진/별도 App ID 에디션, 구성 노출이 없는 상품과 개인화 번들에 대한 발견률 개선이 필요합니다.
- README에 데이터 출처, 비공식 인터페이스 변경 위험, 수집 범위와 보수적인 제외 규칙을 설명했습니다.
