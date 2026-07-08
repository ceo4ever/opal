# AGENTIC-LOG: OPAL Console — 로컬 OPAL 프로젝트 통합 관리 대시보드 (1차 뷰어)

> 모드: semi-agentic | 시작: 2026-06-15 12:41 | 스킬: //opd

semi-agentic 모드 경계(TEST-SCENARIO 사용자 확인, 행 10)를 통과하여 EXECUTE부터 PM(알투) 자율 진행한다. CLOSE 진입(행 15)은 캡틴 승인 필수.

---

## EXECUTE 진입 판단 (2026-06-15 12:41)

- **RED-first 트랙 운용 판단 (PM, red-first.md §1.5)**: BE 데이터 계층(S-1~S-6)은 RED-first 강제 트랙. 그린필드 신규 구현 35+ 파일 규모에서 모듈별 작성자분리 RED-first(test-agent red → be-agent green)를 매 모듈 적용하는 것은 과도하므로, PM 절충안 채택:
  - EXECUTE: BE 워커가 모듈 구현 시 **RED→GREEN 순서 준수**(실패 테스트 선작성·실패 확인 후 구현), 자체 pytest 작성.
  - TEST 단계: **opal-test-agent(BE mode)가 TEST-SCENARIO 기반 독립 검증** → 작성자(test-agent)≠구현자(be-agent) 분리를 단계로 보장 + 동작 증거 확보.
  - 근거: red-first.md §1.5 "공통 불변 ① 테스트 코드 산출물 ② 작성자≠구현자 ③ TEST 단계 검증"을 opd의 EXECUTE→TEST 단계 분리로 충족.
- **EXECUTE = PM 대행 승인**: 구현 금지 원칙의 "실행 허가"를 캡틴의 TEST-SCENARIO 승인(행 10)으로 갈음. PM이 EXECUTE 진입을 대행 승인.

## Phase 1 디스패치 (2026-06-15 12:41)

PLAN §4.1 Phase 1: BE 데이터 계층 + FE 스캐폴딩 병렬.
- Batch: opal-be-agent(Step 1 venv 게이트 → 2 스캐너 → 3 어댑터 → 4 파서, `dashboard/backend/`) ∥ opal-task-agent(Step 5 FE 스캐폴딩, `dashboard/frontend/`).
- 디렉토리 분리(backend/ vs frontend/)로 파일 충돌 없음 → 동일 워킹트리 병렬.
- **선행 게이트(H-1)**: be-agent가 Step 1 `pip install fastapi[standard] --dry-run`을 먼저 수행, starlette 1.0.0 충돌 시 즉시 블로커 반환(나머지 Step 중단).

## Phase 1 완료 (2026-06-15 12:50)

- **BE (Step 1~4)**: pip dry-run 충돌 0건(fastapi 0.137.0 / starlette 1.0.0 satisfied) → requirements.txt 반영. scanner+config·어댑터 5종·파서 4종 신규. **RED-first 준수**(실패 테스트 선작성→실패 확인→GREEN). pytest **31/31 PASS**(S-1 5/S-2 7/S-3 7/S-4 12). 실 도구 호출·실 파일 mtime 불변·쓰기 커맨드 미호출 검증.
- **FE 스캐폴딩 (Step 5)**: Vite+React19+TS6+Tailwind4+shadcn init, 의존성(TanStack Query5/Zustand5/Recharts3/dnd-kit6/router7/lucide/react-markdown), ReactFlow 제외(C-11). build 성공·dev 기동.
- **PM 검토**: 버전 드리프트(PLAN React18→실제19, Recharts2→3 등 최신 상위호환) — 정상 수용, 동작 영향 무. 게이트 통과.

## Phase 2 디스패치 (2026-06-15 12:50)

PLAN §4.1 Phase 2: BE 데몬 통합 + FE 셸/토큰 병렬(backend/ vs frontend/ 분리).
- opal-be-agent(Step 6: main·routers5·cache·models, 127.0.0.1:7823, 칸반4컬럼 정규화, S-5·S-6 자가검증) ∥ opal-fe-agent(Step 7: index.css 3색 토큰·앱셸 5네비·api.ts·ui-store·router, hex 0건, S-7 일부).

## Phase 2 완료 (2026-06-15 13:10)

- **BE 데몬(Step 6)**: main(127.0.0.1:7823)·cache(TTL30s+mtime)·models·routers5. **pytest 54 passed/2 skipped**(기존 31 회귀0 + 신규23). S-5(localhost 바인딩)·S-6(5엔드포인트 200+스키마, 칸반4컬럼 정규화, /api/brain 404) PASS. 2 skipped=~/workspace 환경 의존.
- **FE 셸+토큰(Step 7)**: `--brand-primary`(violet)/`--brand-secondary`(teal)/`--brand-tertiary`(amber) :root 1곳, shadcn 토큰이 참조. 앱셸 5네비(브레인 제외)·스위처·상단바. build 성공·hex 0건.

## Phase 3 완료 (2026-06-15 13:10)

- **5개 화면(Step 8~12)**: 단일 fe-agent 순차(components/ui 경합 방지). 대시보드(section-cards+Recharts)·프로젝트(resizable+탭+도입현황)·칸반(상태4컬럼+Drawer 스테퍼+산출물뷰어)·메모리(타임라인)·환경(accordion+상태아이콘). shadcn 13개 추가. build 성공. **S-8 읽기전용 PASS**(🔒 badge·dnd 0건·클릭=상세)·**S-7 hex 0건**.

## Phase 4 디스패치 (2026-06-15 13:10)

PLAN §4.1 Phase 4: 설치+CLI(opal-task-agent Step 13·14 순차) → docs(PM 직접 Step 15).
- 배포 경계: 소스(`scripts/`·`opal/tools/`)만 수정, `~/.opal/dashboard-server/`는 install이 생성.

## TEST 단계 — 캡틴 실테스트로 결함 4종 발견 (2026-06-15 14:11)

캡틴이 `opal-cli install` + `console start`로 **배포본 실기동**을 테스트한 결과, 자동검증이 놓친 결함 노출. 추가작업(add-row --after 14, current_status=in_progress)으로 fix 착수.

| # | 심각도 | 결함 | 근본 원인 |
|---|--------|------|----------|
| 1 | Critical | 데몬 즉시 크래시 `ModuleNotFoundError: No module named 'dashboard'` | `main.py`가 `from dashboard.backend.routers import`(루트기준 절대 import). 배포본은 `backend/`만 복사돼 `dashboard` 패키지 루트 부재. uvicorn `--app-dir backend`에서 import 실패 |
| 2 | High | 데몬이 떠도 화면 없음 | `main.py`에 `dist` 정적 서빙(StaticFiles) 미구현 |
| 3 | Med | 프로젝트 0개 | config 기본 scan_roots(`$HOME/workspace`)가 캡틴 경로(`/Volumes/Data/...`)와 불일치 |
| 4 | 프로세스 | 자동검증 self-confirming 틈 | pytest·smoke가 **소스 루트(cwd)**에서 기동해 `dashboard.backend` import 성공 → 배포본 컨텍스트(`--app-dir`) 미재현. S-10c가 배포 시나리오를 정확히 검증 못함 |

**fix 방향 (단일 워커 일관 처리 + 배포본 기준 재검증)**:
- (1) 배포 패키징 정합: `install_dashboard`가 `dashboard/__init__.py`+`dashboard/backend/` 패키지 구조 유지 배포 + `console.sh` `--app-dir ~/.opal/dashboard-server`에서 `dashboard.backend.main:app` 기동 (코드 import 무수정).
- (2) `main.py` StaticFiles로 `dist` mount (SPA fallback).
- (3) config 첫 기동 시 캡틴 경로 추론/생성.
- (4) TEST에 **배포본 기준 smoke**(실 `--app-dir` 기동→`/health`+`/` 200) 추가 — 재발 방지. 기존 pytest 54 회귀 불변.
- **학습**: 동작검증은 "소스 트리"가 아니라 "배포 산출물" 기준으로 재현해야 한다(self-confirming 방지). [[feedback]] 후보.

## 021 후속 — 메뉴 [5] + 자동 기동 구현 (2026-06-15)

**수행**: `scripts/install-mac.sh` + `scripts/install/windows.ps1` 수정.

### install-mac.sh 변경
- `show_menu()`: `[5] OPAL Console` 항목 추가, 프롬프트 `(0-5)` 확장.
- `console_autostart()` 신설: dashboard-server/uvicorn 전제 점검 → 기존 데몬 stop(opal-cli console stop 우선, pkill 폴백) → nohup uvicorn 기동 → /health 폴링(10초) → 접속 안내.
- `main()` case 5: `install_dashboard` + `console_autostart` 순차 실행.
- `print_summary()`: `dashboard-server` 경로 항목 추가.
- 버전: v2.9 → v3.0.

### windows.ps1 변경
- `Stop-OpalConsole()` 신설: WMI `Get-CimInstance Win32_Process` + CommandLine 필터로 uvicorn 프로세스 종료.
- `Start-OpalConsole()` 신설: Stop-OpalConsole → Start-Process uvicorn 백그라운드 → /health 폴링(10초) → 접속 안내.
- `Invoke-OpalWindowsInstall()`: `Install-Dashboard` 직후 `Start-OpalConsole` 추가.
- 버전: v1.11.0 → v1.12.0.

### 동작검증 (헌법 §4 실행 증거)
- `bash -n scripts/install-mac.sh` → **SYNTAX OK**.
- 1차 실행: 메뉴 [5] → FE 빌드 성공 → 배포 → PID **90323** 기동 → `/health: {"status":"ok","version":"0.1.0"}`.
- 2차 실행: 메뉴 [5] → 기존 PID 90323 종료 확인 → 신규 PID **90885** 기동 → `/health: {"status":"ok","version":"0.1.0"}`. 중복 기동 없음 확인.
- `~/.opal/dashboard-server/dashboard/backend/` 배포 확인.
