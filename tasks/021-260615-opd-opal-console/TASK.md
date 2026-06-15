# TASK: OPAL Console — 로컬 OPAL 프로젝트 통합 관리 대시보드 (1차 뷰어)

> 작성일: 2026-06-15 | 작업 유형: 신규 | 적용 스킬: opd | 모드: semi-agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

로컬에서 OPAL 프레임워크로 작업하는 **모든 프로젝트를 한 웹 화면에서 조망·관리**하는 대시보드 웹사이트(OPAL Console)를 구축한다. 본 태스크는 **1차 = 전체 뷰어(읽기 전용)** 범위를 대상으로 하며, shadcn/ui로 세련된 UI를 구현하고 자동 설치까지 포함한다.

## 배경

OPAL은 프로젝트별로 `.opal/`(AGENT.md·MEMORY.md·brain·memory), `tasks/*/`(state.json·산출물 .md), `docs/PROJECT.md` 등에 데이터를 분산 보관하지만, 이를 **여러 프로젝트에 걸쳐 한눈에 보고 관리하는 인터페이스가 없다**. 현재는 파일을 직접 열거나 CLI 도구를 개별 호출해야 한다. 프로젝트가 늘어날수록 현황 파악·태스크 추적·메모리/브레인 관리 비용이 커진다.

## 배경 분석 (대화에서 도출)

대화 중 병렬 탐색 에이전트 3종으로 OPAL 구조를 조사한 결과:

### 1. 도구들이 이미 JSON 출력 — 대시보드 백엔드의 데이터 소스

| 도구 | 읽기 전용 커맨드 | 출력 | 용도 |
|------|-----------------|------|------|
| state-tool | `show --format json`, `validate` | JSON `{ok, rows[...]}` | 파이프라인 현황판 |
| brain-tool | `search`, `lint`, `validate` | JSON | 지식 검색·무결성 |
| code-scan | `scan --json`, `domain`, `depends` | JSON | 코드 구조·의존성 |
| skill-registry | `list`, `get` | JSON | 설치 스킬 카탈로그 |
| opal-cli | `doctor` | 텍스트(파싱 필요) | 환경 진단 |

### 2. 프로젝트 식별 마커 = `.opal/AGENT.md` 존재

- 부트스트랩 근거: `~/.opal/AGENT.md` Step 6.5 — `.opal/AGENT.md` 존재 시 OPAL 프로젝트로 판별
- 로컬 프로젝트 **중앙 레지스트리 없음** → 디스크 스캔으로 발견해야 함
- 현재 로컬 OPAL 프로젝트는 ai-framework 1개, 나머지(`ai-auto-content`, `ai-product-detail` 등)는 구버전/미초기화 → "OPAL 도입 현황"까지 보여주면 가치 큼

### 3. 데이터 형식 — 기계용 JSON vs 사람용 마크다운

- **JSON(SSOT)**: `tasks/*/state.json` (행 기반 파이프라인 상태)
- **마크다운(파싱 필요)**: `MEMORY.md`(인덱스 표), `memory/*.md`(frontmatter), `brain/index.md`·`pages/*`(YAML frontmatter), `STATE.md`, `PROJECT.md`, TASK/PLAN/DONE.md

### 4. 결정적 제약 — 쓰기는 도구 경유 강제

- `state.json`·`brain/index.md`·`log.md`는 LLM/사람 직접 편집 금지, state-tool/brain-tool 전담 (헌법 + AGENT.md §state-tool 사용 의무)
- → 향후 "편집(쓰기)" 기능 추가 시 마크다운 직접 쓰기 금지, **반드시 도구 run.sh 래핑** 필요. 1차 뷰어는 읽기 전용이라 이 제약을 자연 회피

### 5. 기술 스택 현황

- OPAL 도구: Node.js(code-scan, skill-registry, date) + Python venv(state-tool, brain-tool, xlsx-tool — anthropic·pandas·openpyxl·playwright 기설치)
- 설치: `install-mac.sh`(+windows.ps1)가 `~/.opal/`에 배포, 어댑터 계층에서 플랫폼 분기 흡수
- 기존 웹/대시보드 코드·계획 **전무**(그린필드)

## 확정된 설계 방향 (대화에서 합의)

| # | 항목 | 확정 내용 |
|---|------|----------|
| C-1 | 서비스명 | OPAL Console (로컬 OPAL 프로젝트 통합 관제 웹) |
| C-2 | 1차 범위 | **전체 뷰어 (읽기 전용)** — 모든 쓰기/편집은 2차로 분리 |
| C-3 | UI 라이브러리 | **shadcn/ui** — 다양하게 검토·활용, "매우 세련되고 멋지게" |
| C-4 | 소스 경로 | `{프로젝트 루트}/dashboard/` (여기서만 개발·수정) |
| C-5 | 배포 경로 | `~/.opal/dashboard-server/` (install이 빌드 산출물 배포) |
| C-6 | 태스크 뷰 | **칸반 UI** — 1차는 읽기 전용(드래그=상세 열기, 상태전환은 2차) |
| C-7 | 자동 설치 | `install-mac.sh` 어댑터에 콘솔 설치 단계 추가 + `opal-cli` 신규 서브커맨드로 기동 |
| C-8 | ANALYSIS 산출물 | ANALYSIS 단계에서 **UI 와이어프레임을 작성·제안** (캡틴 명시 요청) |
| C-9 | 아키텍처 원칙 | 데몬은 도구 오케스트레이터일 뿐, 데이터 SSOT를 새로 만들지 않는다(각 프로젝트 파일이 SSOT) |
| C-10 | 데이터 SSOT | OPAL 도구의 read-only JSON 커맨드 + 마크다운 파서로 수집·정규화 |
| C-11 | 브레인 범위 제외 | **브레인(지식 그래프·검색·lint) 전용 화면은 1차 범위에서 제외 — 2차 이관**. 대시보드의 brain 관련 알림(stale brain)도 1차 제외. 메모리 화면은 유지. → 1차 화면 6개 → **5개**(대시보드/프로젝트/태스크/메모리/환경) |
| C-12 | 컬러 3색 전역변수화 | 시그니처(`--primary`)·서브 시그니처(`--secondary`)·3번째(`--tertiary`/accent) **3색을 한 곳(:root)의 전역 CSS 변수로 정의해 쉽게 교체 가능**하게 한다. 모든 UI 색상은 토큰 경유 — 하드코딩 hex 금지 |

### 1차 뷰어 화면 구성 (확정)

| 화면 | 내용 | 데이터 소스 |
|------|------|------------|
| 대시보드 | 전 프로젝트 현황 집계 + 진행중 태스크·블로커 알림 | 스캔 → 각 state.json + git |
| 프로젝트 | OPAL 도입 현황 맵 + PM프로필·문서·기술스택 | AGENT.md·PROJECT.md |
| 태스크(칸반) | 읽기 전용 칸반 보드 + 산출물(TASK/PLAN/DONE.md) 뷰어 | tasks/*/state.json + .md |
| 메모리 | 카테고리별 메모리 + 작업 히스토리 타임라인 | MEMORY.md·memory/* |
| 환경(doctor) | 의존성·MCP·부트스트래퍼 체크 | opal-cli doctor |

> ~~브레인 화면~~ — C-11에 따라 1차 범위 제외(2차 이관).

## 요구사항

- [ ] **R-1 프로젝트 스캐너**: 설정된 스캔 루트 하위에서 `.opal/AGENT.md` 마커로 OPAL 프로젝트를 발견·열거한다.
  - 무엇을: 디스크 스캔으로 OPAL 프로젝트 목록(경로·이름·OPAL 적용 여부) 산출
  - 어디에: `dashboard/backend/` 스캐너 모듈
  - 왜: 중앙 레지스트리 부재 → 마커 기반 발견 필요 (배경 분석 §2)
  - AC: 스캔 루트에 OPAL 프로젝트가 N개 있을 때 API가 N개를 정확히 반환하고, 비OPAL 프로젝트는 "미적용"으로 구분 표시된다.

- [ ] **R-2 도구 어댑터 계층**: OPAL 도구의 read-only 커맨드를 subprocess로 호출해 JSON으로 정규화하는 어댑터를 구현한다.
  - 무엇을: state-tool `show --format json` / code-scan `scan --json` / skill-registry `list` / doctor 호출·정규화 (brain-tool 어댑터는 C-11에 따라 1차 제외)
  - 왜: 도구가 SSOT, 데몬은 오케스트레이터 (C-9, C-10)
  - AC: 각 어댑터가 해당 도구의 정상 JSON을 파싱해 반환하고, `ok:false`·exit≠0·타임아웃을 에러로 구분 처리한다.

- [ ] **R-3 마크다운 파서**: MEMORY.md·memory/*·STATE.md·PROJECT.md를 구조화 데이터로 파싱한다. (brain frontmatter는 C-11에 따라 1차 제외)
  - AC: MEMORY.md의 메모리 표·작업 히스토리 표, memory 파일 frontmatter가 각각 구조화 JSON으로 반환된다.

- [ ] **R-4 백엔드 API 데몬**: 위 데이터를 제공하는 로컬 HTTP API 서버를 구현한다.
  - AC: 대시보드/프로젝트/태스크/메모리/브레인/환경 6개 화면이 필요한 모든 데이터를 API로 받을 수 있고, 데몬이 localhost에서 기동된다.

- [ ] **R-5 프론트엔드 뷰어 (shadcn/ui)**: 5개 화면(대시보드/프로젝트/태스크/메모리/환경)을 shadcn/ui 기반으로 세련되게 구현한다.
  - 어디에: `dashboard/frontend/`
  - AC: 5개 화면이 라우팅되고 실제 데이터를 렌더하며, 다크모드 포함 일관된 디자인 시스템(타이포·간격·컬러 토큰)이 적용되고, **시그니처 3색이 :root 전역 CSS 변수로 한 곳에 정의되어 변경 시 전 화면에 일괄 반영된다(C-12)**.

- [ ] **R-6 태스크 칸반 보드 (읽기 전용)**: 태스크 현황을 칸반으로 시각화한다.
  - AC: 태스크 카드가 상태별 컬럼에 배치되고, 카드 클릭 시 파이프라인 단계 현황과 산출물 .md를 볼 수 있다. (드래그앤드롭 상태전환은 1차 제외)

- [ ] **R-7 자동 설치 + 기동 CLI**: install 스크립트로 소스를 빌드해 `~/.opal/dashboard-server/`에 배포하고, CLI 한 줄로 기동한다.
  - 어디에: `scripts/install-mac.sh`(+windows.ps1) 어댑터 + `opal-cli` 서브커맨드
  - 왜: 자동 설치 요구 (C-7), 배포 경계 원칙 — 소스는 프로젝트, 배포는 ~/.opal (AGENT.md §금지사항)
  - AC: install 실행 시 `~/.opal/dashboard-server/`에 빌드 산출물이 배포되고, `opal-cli {서브커맨드}` 실행으로 데몬이 기동되어 브라우저에서 대시보드가 열린다.

- [ ] **R-8 ANALYSIS UI 와이어프레임 제안**: ANALYSIS 단계에서 6개 화면 + 칸반의 와이어프레임을 작성해 PLAN 전에 캡틴에게 제안한다.
  - AC: ANALYSIS.md에 화면별 레이아웃 와이어프레임(구조·컴포넌트 배치)이 포함되고 캡틴 검토를 받는다.

## 제약 조건

- **읽기 전용(1차)**: 파일을 쓰거나 OPAL 도구의 쓰기 커맨드(init/advance/mark/add-page 등)를 호출하지 않는다.
- **배포 경계**: 소스는 `{프로젝트}/dashboard/`에서만 수정, 배포는 install로 `~/.opal/dashboard-server/`에 (직접 편집 금지).
- **플랫폼 분기 격리**: macOS/Windows 설치 차이는 install 스크립트 어댑터 계층에만 둔다.
- **데이터 SSOT 불변**: 데몬은 각 프로젝트 파일을 변형/이동/캐시 오염시키지 않는다(읽기만).
- **보안**: 로컬 데몬은 localhost 바인딩 기본, 외부 노출 금지.
- **재사용성**: 특정 프로젝트(ai-framework)에 하드코딩 의존 없이 임의 OPAL 프로젝트에 동작.

## 기술 스택

- **FE (신규)**: React + TypeScript + Vite + shadcn/ui(+ Tailwind, Radix), 칸반(dnd-kit 후보), 그래프 시각화(라이브러리 PLAN 확정)
- **BE (신규, 권고)**: Python + FastAPI — 기존 `~/.opal/.venv` 재사용·도구 subprocess 호출 친화 (최종 확정은 ANALYSIS/PLAN)
- **연동**: 기존 OPAL 도구(state-tool/brain-tool/code-scan/skill-registry/doctor) read-only 커맨드
- **설치**: Bash(install-mac.sh) + PowerShell(windows.ps1) + opal-cli(run.sh)

## 미확정 사항 (ANALYSIS/PLAN에서 결정)

- [ ] U-1 백엔드 프레임워크 최종 확정 (FastAPI 권고 vs 대안)
- [ ] U-2 스캔 루트 설정 방식 — 어디를 스캔할지(설정 파일/환경변수/기본값), 깊이 제한
- [ ] U-3 칸반 컬럼 정의 — 프로젝트 보드(태스크 카드를 상태 컬럼에) vs 태스크 보드(단계를 컬럼에), 둘 다 vs 택1
- [ ] U-4 실시간 갱신 방식 — 폴링 vs SSE/WebSocket vs 수동 새로고침
- [ ] U-5 데이터 수집 캐싱 전략 — state.json 변경 빈도 낮음, 캐시 vs 매 호출
- [ ] U-6 차트 시각화 라이브러리 선택 (대시보드 집계 차트) — brain 지식 그래프는 C-11로 범위 제외
- [ ] U-7 추가 기능 중 1차 포함 범위 확정 — 도입 현황 맵·doctor·코드맵·통합 검색 중 우선순위
- [ ] U-8 데몬 기동 CLI 서브커맨드 이름 (`opal-cli dashboard` vs `console` 등)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | PROJECT.md | `docs/PROJECT.md` | 프로젝트 정의·구조·2-Layer·도구 |
| D-2 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | 시스템 구조·배포 모델 |
| D-3 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 코드/문서 컨벤션·배포 경계·플랫폼 분기 규칙 |
| D-4 | 설계 | AGENT.md (PM 프로필) | `.opal/AGENT.md` | 배포 경계·state-tool 사용 의무 금지사항 |
| D-5 | 소스 | state-tool | `~/.opal/tools/state-tool/` | show --format json 스키마 |
| D-6 | 소스 | brain-tool | `~/.opal/tools/brain-tool/` | search/lint JSON 스키마 |
| D-7 | 소스 | code-scan | `~/.opal/tools/code-scan/code-scan.js` | scan --json 스키마 |
| D-8 | 소스 | install-mac.sh | `scripts/install-mac.sh` | 배포 어댑터 패턴 |
| D-9 | 외부 | shadcn/ui | [shadcn/ui](https://ui.shadcn.com) | UI 컴포넌트·dashboard 블록 |
| D-10 | 외부 | FastAPI | [FastAPI](https://fastapi.tiangolo.com) | 백엔드 데몬(권고) |
