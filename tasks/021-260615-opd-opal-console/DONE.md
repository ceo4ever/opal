# DONE: OPAL Console — 로컬 OPAL 프로젝트 통합 관리 대시보드 (1차 뷰어)

> 완료일: 2026-06-15 18:13 | 적용 스킬: opd | 모드: semi-agentic
> 태스크: 021-260615-opd-opal-console

## 1. 완료 요약

로컬에서 OPAL로 작업하는 모든 프로젝트를 한 웹 화면에서 조망하는 **읽기 전용 대시보드(OPAL Console)** 1차 뷰어 구축 완료. FastAPI 데몬이 OPAL 도구의 read-only 커맨드 + 마크다운 파서로 데이터를 수집하고, React+shadcn/ui가 5개 화면을 렌더한다. 소스는 `dashboard/`, 배포는 `~/.opal/dashboard-server/`(install), 기동은 `opal-cli console`.

## 2. 산출물

### 신규 — `dashboard/`
- **backend/** (FastAPI): `scanner.py`(`.opal/AGENT.md` 마커 스캔)·`config.py`·`cache.py`(TTL+mtime)·`main.py`(127.0.0.1:7823 + dist 정적서빙 SPA)·`models.py`·어댑터 5종(`base`/`state`/`scan`/`skill`/`doctor`)·파서 4종(`memory`/`memory_file`/`project`/`markdown_reader`)·라우터 5종(`dashboard`/`projects`/`tasks`/`memory`/`doctor`) + pytest 76
- **frontend/** (React 19+TS+Vite+Tailwind4+shadcn): 앱셸(5네비+스위처)·디자인토큰 3색(`--brand-primary/secondary/tertiary` :root)·공통 `MarkdownView`(prose+@header 아코디언+TOC)·5화면(대시보드/프로젝트/태스크칸반/메모리/환경)

### 수정
- `opal/tools/opal-cli/run.sh` + `lib/console.sh`(신규, console start/stop/status/open)
- `scripts/install-mac.sh`(`install_dashboard()` 신설, 패키지 구조 배포) + `scripts/install/windows.ps1` 동기화
- `opal/tools/requirements.txt`(`fastapi[standard]`)
- `docs/ARCHITECTURE.md`·`docs/PROJECT.md`(OPAL Console 섹션)

### 런타임 설정 (배포물 아님)
- `~/.opal/console.config.json`(scan_roots 3개: AIStudio/workspace·ProjectStudio/workspace·StoreLinkStudio)

## 3. 핵심 설계 결정 (캡틴 합의)

| # | 결정 |
|---|------|
| C-2 | 1차 = 읽기 전용 뷰어 (쓰기/편집·브레인 화면은 2차) |
| C-3/C-12 | shadcn/ui + 시그니처 3색 `:root` 전역 CSS 변수(교체 용이) |
| C-9 | 데몬은 도구 오케스트레이터 — 데이터 SSOT는 각 프로젝트 파일 |
| C-11 | 브레인 전용 화면 1차 제외 |
| - | 프로젝트 목록 = OPAL 적용분만 / 절대경로 식별자는 query param |
| - | 5화면 전역 `contextProject`(스위처) 구독 — 전체↔개별 일관 |
| - | 문서/산출물/메모리 상세 = 오른쪽 Sheet(`min(50vw,800px)`) + MarkdownView 통일 |
| - | 칸반 5컬럼(대기/진행중/블로킹/완료/아카이브), 완료·아카이브 최근순, archive=`tasks/backup/` |

## 4. QA / 검증

- **정식 배포 실측**: `install_dashboard` 명령(npm build + cp 패키지 배포)으로 깨끗이 배포 → 데몬 UP·5 API JSON·SPA 렌더 확인 (R-7 자동 설치 충족)
- **pytest 76 passed** (스캐너·어댑터 에러3종·doctor 파싱·파서 mtime불변·보안 바인딩·API 계약·산출물추론·배포 smoke 등)
- **cmux 실렌더 검증**: 5화면 + 전역 컨텍스트 전환 + 칸반 아카이브/정렬 + 오른쪽 패널 스크롤 + 라이트모드 코드블록 대비 + @header 아코디언 + TOC 클릭 스크롤
- **보안**: 127.0.0.1 바인딩 · 읽기 전용(쓰기 커맨드 미호출) · SSOT 파일 mtime 불변

## 5. 동작검증 과정의 핵심 교훈

캡틴 실테스트(cmux)가 **자동검증(build 성공·pytest)이 놓친 결함들**(배포본 import 크래시, 레이아웃 겹침, resizable 버전 불일치, 식별자 path segment 등)을 잡았다. 원인은 "소스 트리 기준 검증 + build 성공만으로 통과". **cmux 실렌더/배포본 기준 검증을 도입한 뒤** 결함을 제대로 잡았다. → 동작검증은 "배포 산출물 + 실 브라우저" 기준으로 재현해야 한다.

## 6. 잔여 / 후속 (Known Issue)

- WARN: eslint(shadcn 자동생성 파일)·tsc(baseUrl deprecation) — 빌드 블로커 아님
- **2차 후보**: SSE 실시간 푸시(현 폴링 30s) · 미적용 프로젝트 보기 토글 · 쓰기/편집(state-tool/brain-tool 래핑)
- **별도 태스크 후보**: md→html **프레임워크 공통 스킬/툴** (현재는 대시보드 FE `MarkdownView`로 한정)
- `opal-cli install` **전체** 흐름은 인터랙티브라 캡틴 직접 1회 실행 권장 (`install_dashboard` 함수 단독은 실측 완료)

## 7. 커밋

미커밋 (`dashboard/` 등 untracked). 캡틴 지시 시 커밋.
