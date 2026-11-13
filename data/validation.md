# 개발 검증 기록

검증일: 2026-11-14 (한국시간). 실행 환경: Windows, Python 3.12.14. GitHub Actions는 Python 3.11로 설정했으며 그 환경에서의 실제 실행은 아직 수행하지 못했습니다.

## 구현 범위

Phase 1~3의 코드(수집·초특가·구성 검증 기반 역전·CSV/JSON/HTML)를 구현했습니다. Phase 4의 예약 실행·수동 실행·Artifact·Pages 워크플로 및 사용 설명서를 작성했습니다. 원격 저장소가 연결되지 않았으므로 원격 실행·배포 완료로 표시하지 않습니다.

## 실제 Steam 검증

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

`docs/results.json`에 가격 수집 시각, 검사한 상품 구성과 조건, 범위, 오류를 기록했습니다. 최종 결과 HTML은 최신 템플릿으로 다시 렌더링했으며 가격 수집 시각은 유지했습니다.

## 자동 테스트

- `python -m pytest -q`: **49개 통과**.
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

## 미검증 및 남은 작업

- 작업 폴더는 초기 빈 디렉터리였고 `.git`과 remote가 없었습니다. 연결된 GitHub 저장소 목록에서도 해당 프로젝트를 찾지 못했습니다.
- GitHub Actions 실제 실행 결과: **미실행**. Pages 실제 배포·외부 접속: **미검증**.
- 사용자가 사용할 저장소 URL을 정한 후 업로드하고 Settings → Pages → Source: GitHub Actions 설정 및 첫 실행 검증이 필요합니다.
- HTTP 가격은 동시 원자적 스냅샷이 아니고, 신규 비로그인 구매 기준입니다. 실제 계정별 구매 가능 여부는 검증하지 않습니다.
- 전체 카탈로그, 숨겨진/별도 App ID 에디션, 구성 노출이 없는 상품과 개인화 번들에 대한 발견률 개선이 필요합니다.
- README에 데이터 출처, 비공식 인터페이스 변경 위험, 수집 범위와 보수적인 제외 규칙을 설명했습니다.
