# TASK: OPAL Console 프로젝트별 환경 설정 화면 — 프라임 풀 토글 + console.config + 프로젝트 로컬 설정

> 작성일: 2026-07-14 | 작업 유형: 신규 | 적용 스킬: opd | 모드: agentic
> 입력: 사용자 요청 (예약 메모리 `.opal/memory/061_콘솔_설정_화면_예약.md` + "061 착수해줘")
> 출력: TASK.md

## 작업 목표

OPAL Console에 프로젝트별 환경 설정 화면을 신설하여, 프라임 풀 토글·`console.config.json` 전반·프로젝트 로컬 `.opal/setting.local.json`을 화면에서 조회·스위칭할 수 있게 한다.

## 배경

- OPAL Console은 읽기 전용 관리 대시보드로 신설되었고(→ D-5 §OPAL Console), 예외적 쓰기는 브레인 POST 라우터 격리 선례만 존재한다.
- 태스크 060에서 `console.config.json`의 `prewarm_projects` 기반 브레인 프라임 연결 풀이 완성되었으나(→ D-2), 현재 prewarm 대상 지정은 파일 직접 편집으로만 가능하다.
- 캡틴이 060 CLOSE 직후 후속 태스크로 범위를 확정했다(→ D-1, D-2 §잔여·후속 액션 3).

## 배경 분석 (대화에서 도출)

- 060 산출 API `BrainSessionRegistry.prewarm()`이 존재하여, 토글 ON 시 서버 재기동 없이 즉시 선프라임이 가능하다 (→ D-1, `dashboard/backend/adapters/brain_session.py`).
- `console.config.json`은 `opal-cli console scan`이 생성·머지 갱신하며 scan_roots(스캔 루트)를 관리한다 (→ D-5 §OPAL Console).
- 프로젝트 로컬 `.opal/setting.local.json`은 부트스트랩 게이트(`bootstrap`)와 모델 매핑(`models`)을 전역 위에 셀 단위 오버라이드한다 (→ D-6).

## 확정된 설계 방향 (대화에서 합의)

- 콘솔 "읽기 전용" 원칙의 예외는 브레인 POST 라우터 격리 선례를 따른다 — **설정 라우터만 쓰기 허용**, 쓰기 대상 파일을 명시 화이트리스트로 한정한다 (→ D-1 §설계 방향).
- 범위는 캡틴 선택 "프로젝트 로컬 설정까지" 3종: ① 프라임 풀 토글 ② console.config 전반 ③ 프로젝트 로컬 설정 (→ D-1 §확정 범위).

## 범위 축소 (2026-07-14 18:10 캡틴 지시 — TEST 단계 중)

> "일단 복잡하니, 스위칭을 하는 것만 이번에는 반영합시다. json 수정은 수동으로 하는 것이 좋을듯 함. 설정 화면에서 필요하면 기능을 하나씩 추가를 하는 식으로 하는 것이 좋을 듯함."

- **유지**: R-1(쓰기 라우터 격리·화이트리스트 — prewarm 한정으로 축소), R-2(프라임 풀 토글), R-5(설정 화면 — 토글 단일 섹션으로 축소)
- **이번 범위 제외(구현 후 회수)**: R-3 console.config 화면 편집, R-4 프로젝트 로컬 설정 화면 편집 — JSON 파일 수동 편집으로 대체, 미사용 쓰기 API는 보안 표면 최소화를 위해 제거
- 향후 필요 시 기능 단위로 하나씩 추가 (후속 태스크)

## 명확화 결과

> TASK 4요소를 잠근다.

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | Console에 프로젝트별 환경 설정 화면 신설 — 설정 3종(프라임 풀 토글·console.config·프로젝트 로컬 설정)을 화면에서 조회·변경 | - | 060 프라임 풀 API 존재 (→ D-2) |
| 범위 | 포함: 설정 쓰기 라우터(BE)+설정 화면(FE)+화이트리스트 쓰기 경계. 제외: 브레인 화면 개편, opbr_adapter 이관(059 후속), install 배포 자동화 변경 | 화면 배치(기존 "환경" 메뉴 확장 vs 신설 메뉴)는 ANALYSIS/PLAN에서 결정 | 현재 6개 화면 구성 (→ D-5 §OPAL Console) |
| 제약 | 쓰기는 설정 라우터 1곳에 격리+파일 화이트리스트 한정 / 127.0.0.1 로컬 데몬 전제 / 소스는 `dashboard/` 수정 후 install 배포(`~/.opal/` 직접 수정 금지) / 기존 read-only API 계약 불변 | - | 브레인 POST 격리 선례 (→ D-1 §설계 방향) |
| 완료기준 | 아래 요구사항 AC 전건 Pass + 화이트리스트 외 쓰기 거부가 테스트로 검증됨 | - | - |

## 요구사항

- [ ] **R-1 설정 쓰기 라우터(BE) 신설** — 무엇을: 쓰기 허용 API를 별도 설정 라우터로 격리하고 쓰기 대상 파일을 명시 화이트리스트(`~/.opal/console.config.json`, `{스캔된 프로젝트}/.opal/setting.local.json`)로 한정 / 어디에: `dashboard/backend/` / 왜: 읽기 전용 원칙의 예외 격리 (→ D-1 §설계 방향) / AC: 화이트리스트 외 경로·비스캔 프로젝트 경로 쓰기 요청이 4xx로 거부되고, 이를 검증하는 테스트가 존재하며 Pass한다.
- [ ] **R-2 프라임 풀 토글** — 무엇을: 프로젝트별 prewarm ON/OFF 스위치 / 어디에: 설정 화면(FE)+설정 라우터(BE), `console.config.json` `prewarm_projects` / 왜: 060 후속 — 파일 직접 편집 없이 스위칭 (→ D-2 §잔여·후속 액션 3) / AC: ON 시 `prewarm_projects`에 추가되고 재기동 없이 `BrainSessionRegistry.prewarm()`으로 즉시 선프라임되며, OFF 시 목록에서 제거된다 — config 파일 반영이 테스트로 검증된다.
- [ ] **R-3 console.config 전반 관리** — 무엇을: scan_roots 추가/삭제, 프로젝트 숨김 등 `console.config.json` 항목 관리 UI / 어디에: 설정 화면(FE)+설정 라우터(BE) / 왜: 확정 범위 ② (→ D-1 §확정 범위) / AC: 화면에서 변경 시 `~/.opal/console.config.json`에 머지 반영되고 기존 키가 유실되지 않는다(머지 보존 테스트 Pass).
- [ ] **R-4 프로젝트 로컬 설정 편집** — 무엇을: 프로젝트별 `.opal/setting.local.json`의 `bootstrap`·`models` 조회·편집 / 어디에: 설정 화면(FE)+설정 라우터(BE), 대상 프로젝트 파일 / 왜: 확정 범위 ③ — 쓰기 경계가 프로젝트 파일까지 확장되므로 설계·보안 검토 비중 큼 (→ D-1 §확정 범위) / AC: 저장 시 대상 프로젝트에 파일이 생성/갱신되고, 유효하지 않은 JSON 구조(스키마 위반)는 저장이 거부된다 — 생성·갱신·거부 3경로 테스트 Pass.
- [ ] **R-5 설정 화면(FE) 신설** — 무엇을: 프로젝트별 설정 조회·스위칭 화면 / 어디에: `dashboard/frontend/` / 왜: 작업 목표의 사용자 접점 / AC: 화면에서 R-2~R-4의 설정 3종을 조회·변경할 수 있고 변경 결과가 재조회 시 반영 표시된다.

## 제약 조건

- [MUST] `.opal/memory/061_콘솔_설정_화면_예약.md` §설계 방향: "콘솔 '읽기 전용' 원칙의 예외는 브레인 POST 라우터 격리 선례를 따름 — **설정 라우터만 쓰기 허용**, 쓰기 대상 파일을 명시 화이트리스트로 한정."
- 배포 경계: 소스(`dashboard/`)만 수정하고 install 재배포로 반영한다 — `~/.opal/` 배포본 직접 수정 금지 (→ D-4 §금지사항).
- 기존 브레인 API 5종 등 read-only API 계약 불변 (→ D-2 §목표 달성).
- 데몬은 127.0.0.1:7823 로컬 바인딩·무인증 전제 — 쓰기 API의 경로 탈출(path traversal)·임의 파일 쓰기 방어를 설계에 포함한다.
- 커밋은 캡틴 명시 요청 시에만 수행한다.

## 기술 스택

- Console FE: React, TypeScript, Vite, Tailwind, shadcn/ui (`dashboard/frontend/`)
- Console BE: Python, FastAPI, uvicorn (`dashboard/backend/`)
- 테스트: pytest (BE 기존 스위트 235건 GREEN 유지)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 기획 | 061 예약 메모리 | `.opal/memory/061_콘솔_설정_화면_예약.md` | 확정 범위 3종 + 설계 방향 합의 원문 |
| D-2 | 설계 | 060 DONE | `tasks/060-260713-opd-브레인-프라임-연결풀/DONE.md` | prewarm API 산출·후속 액션 3 원문 |
| D-3 | 설계 | 브레인 프라임 풀 설계 | `.opal/brain/pages/concept/brain-prime-connection-pool-design.md` | 풀 구조·prewarm 동작의 WHY/HOW |
| D-4 | 설계 | PM 프로필 | `.opal/AGENT.md` | 배포 경계·금지사항 |
| D-5 | 설계 | PROJECT.md | `docs/PROJECT.md` | Console 구성(6화면·config scan)·프로젝트 구성 라우팅 |
| D-6 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | Console 구조·브레인 표(프라임 연결 풀 행) |
| D-7 | 소스 | brain_session.py | `dashboard/backend/adapters/brain_session.py` | `BrainSessionRegistry.prewarm()` 재사용 지점 |
| D-8 | 소스 | config.py | `dashboard/backend/config.py` | `ConsoleConfig.prewarm_projects` 현행 파싱 |
