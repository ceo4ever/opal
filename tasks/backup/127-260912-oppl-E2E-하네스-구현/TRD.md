# TRD: OPAL 범용 E2E 하네스

> 대상 태스크: `tasks/127-260912-oppl-E2E-하네스-구현/TASK.md`
> 입력 요구사항: `tasks/127-260912-oppl-E2E-하네스-구현/PRD.md` (R-1~R-19, NR-1~NR-7)
> 설계 원천: `docs/proposals/opal-e2e-harness.md` (구현 태스크 2~9)
> 범위 경계: 이 문서는 **무엇을 어디에 만들지**까지 정한다. 함수 시그니처·JSON 필드의 확정 스키마는 D4 `CONTRACT.md`가 소유한다.

---

## 1. 참조 문서

| # | 유형 | 문서/소스 | 경로 | 참조 이유 |
|---|------|----------|------|----------|
| T-1 | 기획 | 요구사항 | `tasks/127-260912-oppl-E2E-하네스-구현/PRD.md` | R/NR ID 체계의 원천. 모든 TD가 여기로 역추적된다 |
| T-2 | 기획 | 태스크 정의 | `tasks/127-260912-oppl-E2E-하네스-구현/TASK.md` | C-1~C-8 제약, AC-1~AC-14 |
| T-3 | 설계 | E2E 하네스 제안서 | `docs/proposals/opal-e2e-harness.md` | 아키텍처·profile 계약·driver 적용안·태스크 분해 |
| T-4 | 기획 | 태스크 125 완료 기록 | `tasks/125-260912-opd-E2E-프로필-판정-계약/DONE.md` | 재설계 금지 경계(C-1) |
| T-5 | 소스 | E2E 계약 owner | `opal/tools/test-tool/lib/e2e_contract.py` | 소비 대상 계약 전문 |
| T-6 | 소스 | cmux provider adapter | `opal/tools/test-tool/lib/e2e_adapter.py` | 현행 유일한 실행 경로 |
| T-7 | 소스 | 시나리오 SSOT | `opal/tools/test-tool/lib/scenario.py` | 시나리오 형식과 mark/resume 게이트 |
| T-8 | 소스 | 러너 해석 | `opal/tools/test-tool/lib/resolver.py` | E2E 후보 테이블 |
| T-9 | 소스 | Console 실행 스크립트 | `opal/tools/opal-cli/lib/console.sh` | 배포본 고정 포트 기동·광역 종료 |
| T-10 | 소스 | Console backend | `dashboard/backend/main.py` | CORS·정적 서빙·health |
| T-11 | 소스 | Console frontend | `dashboard/frontend/src/lib/api.ts`, `vite.config.ts` | 고정 API 주소 |
| T-12 | 소스 | worktree 도구 | `opal/tools/worktree-tool/worktree_tool.py` | portOffset 힌트 |
| T-13 | 소스 | 설치 스크립트 | `scripts/install-mac.sh` | 배포 경로·Playwright 기본 설치·2차 광역 종료 |
| T-14 | 기획 | 아키텍처 | `docs/ARCHITECTURE.md` §OPAL Console | Console 배포 모델 |
| T-15 | 기획 | 컨벤션 | `docs/CONVENTIONS.md` §구현 규칙 | 배포 경계·플랫폼 분기·State·Citation |
| T-16 | 기획 | 프로젝트 구성 | `docs/PROJECT.md` §프로젝트 구성 | 영역·전문 에이전트 매핑(D5 `area` 배정 근거) |

---

## 2. 현행 구조 실측 (AS-IS)

### 2.1 확정된 계약 (태스크 125 — 재설계 대상 아님)

`opal/tools/test-tool/lib/e2e_contract.py`가 이번 범위가 **소비만 할** 계약을 전부 소유한다.

| 계약 요소 | 근거 | 값 |
|---|---|---|
| 스키마 버전 | `e2e_contract.py:37` | `E2E_CONTRACT_SCHEMA_VERSION = "2.0"` |
| profile 5종 | `e2e_contract.py:38` | `browser`, `api`, `hybrid`, `collaborative`, `manual` |
| 최종 상태 5종 | `e2e_contract.py:39` | `pass`, `fail`, `executor_unavailable`, `infra_error`, `blocked` |
| 운영 상태 | `e2e_contract.py:40` | `awaiting_human` |
| executor 3종 | `e2e_contract.py:41` | `browser`, `api`, `human` |
| 상태→exit | `e2e_contract.py:42-49` | 0 / 6 / 7 / 18 / 19 / 20 |
| profile→executor 행렬 | `e2e_contract.py:57-66` | `hybrid.required = ("api","browser")` 등 |
| handoff 필수 8필드 | `e2e_contract.py:67-76` | `server_policy`·`submission_path` 포함 |
| legacy 결과 정규화 | `e2e_contract.py:203-260` | reason별 `provider_unavailable` / `infra_error` / `fail` |
| 다음 후보 전환 허용 판정 | `e2e_contract.py:269-273` | **`provider_unavailable`만** `True` |
| pass 게이트 | `e2e_contract.py:292-364` | surface 일치 → executor 행렬 → assertion expected/actual → required_evidence |
| v2 시나리오 검증 | `e2e_contract.py:418-502` | assertion·evidence·handoff 필수 |

`HANDOFF_REQUIRED_FIELDS`가 `server_policy`를 이미 요구한다(`e2e_contract.py:74`). 즉 125 계약은 **사람 대기 중 서버를 유지할지 종료할지를 handoff가 선언하는 구조**를 이미 전제하고 있으며, 이번 범위는 그 선언을 집행할 주체만 만들면 된다.

### 2.2 실행 주체 공백

현행 유일한 실행 경로는 cmux adapter 하나다.

- `e2e_adapter.py:129-231` `run_integration()` — `open → navigate → close`만 수행한다(`:170-215`). 서버를 기동하지 않고, URL은 호출자가 넘긴 값을 그대로 쓴다(`:132`).
- `e2e_adapter.py:217-225`는 `assertion_results: []`, `observed_evidence: []`로 `build_verdict`를 호출하므로 **pass 게이트에서 반드시 `assertion_required`로 떨어진다**(`e2e_contract.py:330-336`). 현재 이 경로는 구조적으로 `pass`를 낼 수 없다 — 계약은 있으나 집행자가 없다는 PRD §2 문제 4의 코드 근거다.
- E2E 후보 테이블은 resolver의 추론 폴백에만 존재한다 — `resolver.py:98-113`(package.json), `:148-163`(pyproject). `playwright`는 `priority: 2` 후보로 이름만 선언되어 있고 실행 코드는 없다.

### 2.3 Console 실행·소유권

| 사실 | 근거 |
|---|---|
| 기동 대상이 **배포본 고정** | `console.sh:34` `opal_home="${OPAL_HOME:-$HOME/.opal}"`, `:37` `dashboard_server="$opal_home/dashboard-server"` |
| host·port **하드코딩** | `console.sh:39-40` `host="127.0.0.1"`, `port="7823"` |
| 기동 명령 | `console.sh:75-80` `nohup "$venv_uvicorn" --app-dir "$dashboard_server" dashboard.backend.main:app --host "$host" --port "$port" >"$log_file" 2>&1 &` |
| **PID 파일 없음** | `console.sh:81`이 `$!`를 메시지로만 출력한다 |
| 로그 경로 고정 | `console.sh:42` `log_file="/tmp/opal-console.log"` |
| stop이 **광역 패턴 종료** | `console.sh:88` `pkill -f "dashboard.backend.main:app"` |
| 설치 스크립트에도 **동일 광역 종료** | `scripts/install-mac.sh:1844` `pkill -f "dashboard.backend.main:app"` |
| frontend는 기동하지 않음 | `console.sh` 전체에 vite/npm 호출 없음. 배포 `dist/`를 backend가 서빙 |

**핵심 위험**: source E2E backend도 같은 ASGI 경로 문자열 `dashboard.backend.main:app`으로 기동될 수밖에 없다(패키지 절대 import 구조, `console.sh:73-74` 주석). 따라서 현행 `pkill -f` 패턴은 **E2E backend를 반드시 오탐 종료**한다. AC-3(양방향 비간섭)이 성립하지 않는 직접 원인이다.

### 2.4 주소·CORS

| 사실 | 근거 |
|---|---|
| FE API 주소 고정 | `dashboard/frontend/src/lib/api.ts:14` `export const API_BASE_URL = "http://127.0.0.1:7823";` |
| 호출 결합 방식 | `api.ts:69` `fetch(\`${API_BASE_URL}${path}\`)` — 호출자가 `/api/...`·`/health` 완전 경로를 넘긴다 |
| `import.meta.env` 사용처 **0건** | `dashboard/frontend/src` 전수 grep 무결과. `vite-env.d.ts` 부재 |
| `API_BASE_URL`을 import하는 파일 **0개** | 같은 모듈 내부에서만 소비. 외부 13개 파일은 `apiClient`만 import |
| vite 설정에 port·proxy·outDir 없음 | `dashboard/frontend/vite.config.ts:8-17` — `base: './'`와 alias뿐 (전체 18줄) |
| CORS origin **모듈 상수** | `dashboard/backend/main.py:76-79` `["http://localhost:5173", "http://127.0.0.1:5173"]` |
| CORS 등록 | `main.py:81-87` (`allow_credentials=False`, `allow_methods=["GET","POST"]`) |
| backend가 env를 읽는 곳 **없음** | `main.py:142-146` 하드코딩 `host="127.0.0.1", port=7823`. `dashboard/backend/config.py`에 `os.environ` 사용 0건 |
| 정적 서빙 | `main.py:116-117` `_dist_dir = (_here/".."/".."/"dist").resolve()`, `:119-132` mount·SPA fallback |
| health | `main.py:102-105` `GET /health` → `{"status":"ok","version":"0.1.0"}` |

`api.ts:69`가 base와 경로를 **단순 결합**하므로, base를 `""`로 두면 동일 출처 호출이 그대로 성립한다. 제안서 §6.4의 `import.meta.env.VITE_API_BASE_URL ?? ""` 형태가 현행 코드와 호환된다는 실측 확인이다.

### 2.5 포트

| 사실 | 근거 |
|---|---|
| `portOffset`은 검증·전달만 | `worktree_tool.py:324-330` 타입 검증, `:340` 정규화 반환 |
| 유일한 반환 지점 | `worktree_tool.py:1230` `cmd_create` 응답 필드 `port_offset=cfg["portOffset"]` |
| `.opal/worktree.json` 기본값 | `worktree_tool.py:751` `"portOffset": 0`. 실제 파일 `.opal/worktree.json:24`도 `0` |
| **lease·bind 검사 코드 없음** | `worktree_tool.py` 전체에 `lease`/`bind`/`socket` 무결과 |
| worktree 메타에 포트 필드 없음 | `_meta_path` `worktree_tool.py:820-821` (`.opal-worktrees/.meta/task_{NNN}.json`) |

즉 현재 저장소에 포트 임대 구현은 존재하지 않는다. 신설 대상이다.

### 2.6 산출물·환경 변수 네임스페이스

- `.gitignore:28` `dist/` — 저장소 전역. `dashboard/frontend/dist`도 매칭된다. `.e2e-runs/`·`.test-run/` 항목은 **없다**(`.gitignore` 39줄 전수).
- `OPAL_E2E_*` 접두 변수는 **코드에 0건**이며 제안서·TASK 문서에만 등장한다(전수 grep). `VITE_*`도 코드 사용 0건.
- 기존 OPAL 환경 변수 중 이번 설계와 접점이 있는 것: `OPAL_HOME`(전 도구 공용), `OPAL_CMUX_TOOL_CMD`(`e2e_adapter.py:55`), `OPAL_TEST_TOOLS_GLOBAL`(`resolver.py:237`).

### 2.7 설치본 배포 경로

- `install_dashboard()` `scripts/install-mac.sh:1756-1805` — FE를 **소스 트리에서 빌드**한 뒤(`:1772` `cd "$src/frontend" && npm install --silent && npm run build`) `dashboard/frontend/dist`를 `~/.opal/dashboard-server/dist`로 복사한다(`:1774`). BE는 `$dst/dashboard/backend`로 복사(`:1787`), 패키지 루트 `__init__.py` 생성(`:1789`).
- `console_autostart()` `:1813-1868` — `opal-cli console stop` 우선, 미존재 시 `pkill` 폴백(`:1844`).

**따라서 설치 스크립트를 하네스가 호출하면 소스 트리 `dashboard/frontend/dist`가 갱신된다.** C-5·R-6와 충돌한다(→ TD-9).

---

## 3. 목표 아키텍처 (TO-BE)

### 3.1 소유권 경계

```text
[test-tool]  ── E2E 판정·실행 SSOT ─────────────────────────────
  e2e_contract.py     계약 owner (125, 무변경)
  e2e/orchestrator    run 수명주기·profile 결정·최종 verdict
  e2e/runtime         target 해석·포트 임대·SUT 기동·health·종료
  e2e/drivers/*       Browser 실행 후보 (agent-browser / cmux / playwright-opt)
  e2e/executors/*     API · Human
  e2e/evidence        증적 수집·redaction
  scenario.py         시나리오 spec/result SSOT (무변경 원칙)

[opal-cli]   ── 사용자 상시 Console 소유 ─────────────────────────
  console.sh          $OPAL_HOME 배포 daemon 1개만 소유·종료

경계 규칙: 두 도구는 서로를 호출하지 않는다.
공유하는 것은 "PID 레코드 파일 포맷" 문서 계약뿐이며 런타임 의존은 0이다.
```

이 분리가 R-4(양방향 비간섭)의 구조적 근거다. Console stop은 자기 PID 레코드만 보고, 하네스는 자기 run 레코드만 본다. 어느 쪽도 프로세스 이름 패턴을 쓰지 않는다.

### 3.2 구성요소와 책임

제안서 §5.1의 10개 구성요소를 이 저장소의 실제 모듈로 확정한다.

| 제안서 구성요소 | 실제 배치 | 소유하지 않는 것 |
|---|---|---|
| E2E Orchestrator | `lib/e2e/orchestrator.py` (신설) | executor별 명령 구현 |
| Runtime Manager | `lib/e2e/runtime.py` (신설) | 사용자 Console daemon |
| Port lease | `lib/e2e/ports.py` (신설) | worktree 생성·`portOffset` 의미 |
| Target resolver | `lib/e2e/target.py` (신설) | git 작업(읽기 전용 조회만) |
| Profile Resolver | `e2e_contract.resolve_profile` (**기존 소비**, `e2e_contract.py:137`) | — |
| Scenario Adapter | `lib/e2e/scenario_adapter.py` (신설) | `test-scenario.json` 스키마 변경 |
| Browser Session Resolver | `lib/e2e/drivers/__init__.py` (신설) | 제품 성공 판정 |
| Browser Driver | `lib/e2e/drivers/agent_browser.py`·`cmux.py`·`playwright.py` (신설/이관) | API·사람 단계 |
| API Executor | `lib/e2e/executors/api.py` (신설) | UI 행동 대체 |
| Human Handoff | `lib/e2e/executors/human.py` (신설) | 사용자 응답만으로 pass 선언 |
| Evidence Collector | `lib/e2e/evidence.py` + `lib/e2e/redaction.py` (신설) | 제품 성공 추정 |
| Verdict Gate | `e2e_contract.build_verdict` / `validate_pass_requirements` (**기존 소비**) | 다음 후보 선택 |
| 프로세스·플랫폼 어댑터 | `lib/e2e/process.py` (신설) | 업무 로직 |

### 3.3 실행 흐름

```text
test-tool e2e run --scenario <id> --task-path <p> --target <t>
  → target 해석 (source-main | source-worktree | installed) + commit/dirty 기록
  → 포트 임대 (backend, frontend)
  → SUT 기동 (env 주입) → health gate
  → profile 결정 (e2e_contract.resolve_profile)
  → executor/driver 후보 probe
  → step 실행 (browser | api | human)
        └ human → 증적·journal 저장 → exit 20 (awaiting_human)
  → assertion → 증적 수집 → redaction
  → build_verdict → validate_pass_requirements
  → 소유 자원만 정리 → run.json 저장 → status_to_exit
```

---

## 4. 핵심 기술 결정

### TD-1. `test-tool` 확장으로 구현하고 신규 도구를 신설하지 않는다
**대응**: NR-1, R-14, R-19 | **제안서 §5.1의 미결 판단을 여기서 확정한다.**

- 결정: E2E Orchestrator·Runtime Manager·모든 executor를 `opal/tools/test-tool/lib/e2e/` 서브패키지로 신설한다. 새 CLI 도구(`e2e-runtime-tool` 등)를 만들지 않는다.
- 근거:
  1. pass 게이트(`e2e_contract.py:292`)와 시나리오 result존 기록(`scenario.py:402`)이 이미 한 도구 안에 있다. 실행자를 밖으로 빼면 **verdict를 우회해 결과를 기록하는 경로**가 생긴다 — R-14의 "어떤 경로로도 pass가 되지 않는다"를 도구 경계로 보장할 수 없게 된다.
  2. 계약 소비는 in-process import로 끝난다(`e2e_adapter.py:34` 선례). 별도 도구면 계약을 JSON으로 재직렬화해야 하고 그 지점이 두 번째 SSOT가 된다 — R-19 위반 위험.
  3. 진입점이 하나(`opal/tools/test-tool/run.sh:12`)로 유지되어 exit code 계약(`status_to_exit`)이 갈라지지 않는다.
- 검토한 대안과 탈락 사유:
  - **별도 Runtime Manager 도구 신설**: Console stop과의 비간섭이 도구 의존을 요구한다고 가정했으나, TD-5에서 Console이 자기 PID 레코드만 보도록 바꾸면 의존이 0이 된다. 분리 근거가 소멸한다.
  - **`opal-cli`에 E2E 서브커맨드 추가**: `opal-cli`는 설치·배포·MCP 등 배포본 운영 도구다(`opal/tools/opal-cli/lib/` 5개 모듈). 검증 판정 책임을 여기 두면 도구 성격이 섞인다.
- 계약 준수: `test_tool.py:25-26`의 "test-tool은 1회 실행·판정만, 재시도 루프는 오케스트레이터 책임"을 유지한다. `e2e run`은 **1회 실행**이며 재시도 루프를 내장하지 않는다. `awaiting_human` 재개는 루프가 아니라 별도 호출이다(TD-18).

### TD-2. 공개 CLI 표면은 `e2e` 서브명령군으로 신설하고 기존 `integration`은 이행기 별칭으로 남긴다
**대응**: R-1, R-5, NR-2

- 신설: `test-tool e2e run`, `test-tool e2e resume`, `test-tool e2e status`, `test-tool e2e clean`.
- 기존 `integration`(`test_tool.py:41`, `e2e_adapter.run_integration`)은 시그니처를 바꾸지 않고 유지하되, 내부적으로 새 Browser driver 계층을 호출하도록 이관한다(제안서 태스크 6). 기존 호출자(oppl·oppd·`opal-test-agent`)를 한 번에 끊지 않는다.
- exit code는 전부 `status_to_exit`(`e2e_contract.py:125`) 소비. 새 exit code를 배정하지 않는다(C-1).
- `ERROR_CODES` 카탈로그(`test_tool.py:50-62`)에 신규 키를 추가할 때는 기존 6종 E2E 키를 재정의하지 않는다. `escalation`(`test_tool.py:57`)은 이행기 alias로 유지한다(제안서 §7.9).

### TD-3. 포트 임대는 원자적 lockfile + strict-port 기동 + lease record 3단으로 구현한다
**대응**: R-2, R-3, NR-6

- 배치: `lib/e2e/ports.py` (신설). `worktree-tool`은 건드리지 않는다 — `portOffset`(`worktree_tool.py:1230`)은 **호환용 hint로만 남기고 allocator로 승격하지 않는다**(제안서 §6.6).
- 메커니즘:
  1. allocator lock: `os.open(lock_path, O_CREAT|O_EXCL)` 기반 원자적 lockfile. **`fcntl.flock`을 쓰지 않는다** — fcntl은 Windows에 없어 플랫폼 분기를 낳고, C-7 "플랫폼 분기는 어댑터 계층에서만"을 어기게 된다. O_EXCL은 POSIX·Windows 공통 의미를 가진다.
  2. 후보 포트 `127.0.0.1` bind 검사.
  3. lease record 기록: `{run_id, owner_pid, port, role, created_at}`.
  4. child를 **strict port**로 즉시 기동. uvicorn은 지정 포트 점유 시 기동 실패하고, vite는 `--strictPort`를 명시한다.
  5. 기동 실패(EADDRINUSE)면 record 폐기 후 제한 횟수(기본 5회) 재할당.
  6. health 통과 뒤 lease 확정, 소유 프로세스 종료 확인 뒤 해제.
- stale 회수: lease record는 있으나 `owner_pid`가 살아 있지 않으면 다음 실행이 회수한다(R-2 마지막 문장). PID 생존 판정은 TD-16의 단일 어댑터 함수만 사용한다.
- lease 디렉터리: 산출물 루트 하위 `{artifact_root}/.leases/` (TD-10). 저장소·`~/.opal` 배포 트리에 쓰지 않는다.

### TD-4. 대상 소스 증명은 실행 전에 확정하고 run 메타데이터로 봉인한다
**대응**: R-1, R-5

- 배치: `lib/e2e/target.py` (신설).
- `source-main`: 프로젝트 루트. `source-worktree`: canonical worktree root(`--worktree-root` 인자 또는 `git rev-parse --show-toplevel`). `installed`: 격리된 임시 `OPAL_HOME` 경로(TD-9).
- 기록 항목(R-5): `profile`, `actors`, `target`, `project_root`, `worktree_root`, `commit`, `dirty`(+변경 파일 목록), `urls.{frontend,backend}`, `executors[].{type,driver,session_mode,driver_version}`, `session`, `artifact_dir`.
- git 조회는 **읽기 전용 명령만** 사용한다(`rev-parse`, `status --porcelain`). 하네스가 저장소 상태를 바꾸지 않는다(R-6).

### TD-5. Console 프로세스 소유권을 PID 레코드로 전환하고 광역 종료를 2곳에서 제거한다
**대응**: R-4, C-2 | **AC-3의 유일한 해결 경로**

- 변경 1 — `opal/tools/opal-cli/lib/console.sh`:
  - `start`(`:75-81`)에서 기동 직후 PID 레코드를 기록한다. 위치: `$opal_home/run/console.pid`(JSON: `pid`, `opal_home`, `app_dir`, `host`, `port`, `started_at`). `$OPAL_HOME` 하위 런타임 사용자 데이터 쓰기이며 `docs/CONVENTIONS.md` §배포 경계의 "런타임 사용자 데이터 쓰기는 이 금지의 대상이 아니다"에 해당한다.
  - `stop`(`:87-93`)에서 `pkill -f "dashboard.backend.main:app"`(`:88`)을 **제거**하고, 레코드의 `pid`가 살아 있고 `app_dir`가 이 `$OPAL_HOME`의 `dashboard-server`와 일치할 때만 종료한다. 레코드가 없거나 identity 불일치면 **아무것도 죽이지 않고** 경고로 끝낸다.
  - `start`(`:54-57`)는 현재 health 응답만으로 "이미 실행 중"을 판정한다. E2E backend가 7823을 쓰지 않으므로 오탐은 없으나, 레코드 기반 판정으로 함께 정리한다.
  - `status`(`:95-106`)에 레코드의 pid·app_dir를 함께 출력해 소유권을 관측 가능하게 한다(R-15 관점).
- 변경 2 — `scripts/install-mac.sh:1844`: `opal-cli` 미존재 폴백의 `pkill`을 같은 레코드 기반 종료로 교체한다. 이 지점을 놓치면 설치·업데이트 경로에서 R-4가 다시 깨진다.
- 하네스 쪽 대칭 규칙: E2E가 기동한 backend/frontend는 **절대 `$opal_home/run/console.pid`를 읽거나 쓰지 않는다.** 자기 프로세스는 run artifact dir의 `server/*.pid`로만 추적한다.
- 프로세스 그룹: 하네스가 띄우는 모든 child는 새 세션/프로세스 그룹으로 기동해 종료 시 그룹 단위로 회수한다(vite가 esbuild 등 손자 프로세스를 남기는 것을 R-6로 막는다).

### TD-6. FE API 주소는 빌드·기동 시점 주입으로 바꾸고 dev 기본값을 파일로 고정한다
**대응**: NR-4, R-3, C-8

- 변경: `dashboard/frontend/src/lib/api.ts:14`
  `export const API_BASE_URL = "http://127.0.0.1:7823";` → `import.meta.env.VITE_API_BASE_URL ?? ""` 형태.
  `api.ts:69`의 결합 방식은 유지한다 — base에 `/api` 접두사를 넣지 않는다(C-8).
- 신설 1: `dashboard/frontend/src/vite-env.d.ts` — `ImportMetaEnv.VITE_API_BASE_URL` 타입 선언. 현재 `.d.ts`가 하나도 없어(전수 검색 무결과) `npm run typecheck`(`package.json:11`)가 깨진다. **선언 파일 없이 이 변경만 하면 기존 타입 검사가 회귀한다.**
- 신설 2: `dashboard/frontend/.env.development` — `VITE_API_BASE_URL=http://127.0.0.1:7823`.
  이유: 현재 개발자가 `npm run dev`(5173)로 띄우면 하드코딩된 절대 주소 덕분에 7823 backend를 호출한다. base를 `""`로 바꾸면 그대로는 5173 자신을 호출하게 되어 **기존 개발 흐름이 회귀한다.** 제안서 §6.4는 이 회귀를 다루지 않았다. dev 기본값을 파일로 고정해 오늘 동작을 보존하고, E2E는 기동 시 env 주입으로 덮어쓴다.
- production/installed: env 미설정 → `""` → 동일 출처. `main.py:119-132`의 SPA 서빙과 정합한다.
- 영향 범위 확인: `API_BASE_URL`을 import하는 외부 파일은 0개이고 `apiClient` 소비자만 13개이므로, 변경 표면은 `api.ts` 한 파일이다.

### TD-7. backend CORS는 환경 변수 추가 허용만 지원한다
**대응**: NR-4, C-8

- 변경: `dashboard/backend/main.py:76-79`의 모듈 상수 `CORS_ORIGINS`를 "기본 dev origin 2종 + 환경 변수로 추가된 origin 목록"으로 바꾼다. 등록부(`main.py:81-87`)의 `allow_credentials=False`·`allow_methods=["GET","POST"]`는 유지한다.
- 허용은 **정확한 origin 문자열 추가만**이다. 와일드카드·정규식·전체 허용을 도입하지 않는다(NR-4 명시 금지).
- 환경 변수명: `OPAL_CONSOLE_CORS_ORIGINS`(쉼표 구분). 접두사 근거는 TD-8의 네임스페이스 결정.
- backend는 여전히 포트를 env에서 읽지 않는다. 포트는 기동 명령 인자로만 전달한다(현행 `console.sh:78-79` 방식 유지) — `main.py:142-146`의 `__main__` 분기는 개발 편의 경로이므로 이번 범위에서 바꾸지 않는다.

### TD-8. 환경 변수 네임스페이스를 확정한다 (미해결 질문 Q-1 결정)
**대응**: NR-4, R-2, R-6 | **PRD §12 Q-1 결정**

실측: `OPAL_E2E_*`와 `VITE_*`는 이 저장소 **코드에 0건**이며 제안서·TASK 문서에만 등장한다. 충돌은 없다.

| 변수 | 용도 | 상태 | 주입 주체 |
|---|---|---|---|
| `OPAL_E2E_RUN_ID` | 실행 식별자 | 신설 | 하네스 → child |
| `OPAL_E2E_TARGET` | `source-main`\|`source-worktree`\|`installed` | 신설 | 하네스 → child |
| `OPAL_E2E_BACKEND_PORT` | 임대한 backend 포트 | 신설 | 하네스 → child |
| `OPAL_E2E_FRONTEND_PORT` | 임대한 frontend 포트 | 신설 | 하네스 → child |
| `OPAL_E2E_ARTIFACT_DIR` | run 단위 증적 디렉터리 | 신설 | 하네스 → child |
| `OPAL_E2E_ARTIFACT_ROOT` | 산출물 루트(기본 `${TMPDIR}/opal-e2e-runs`) | 신설 | 사용자 → 하네스 |
| `VITE_API_BASE_URL` | FE가 호출할 backend URL | 신설 | 하네스 → vite |
| `OPAL_CONSOLE_CORS_ORIGINS` | backend 추가 허용 origin | 신설 | 하네스 → backend |
| `OPAL_HOME` | `installed` target의 격리 배포 루트 | **기존 재사용** | 하네스 → child 한정 |
| `OPAL_CMUX_TOOL_CMD` | cmux-tool 실행 경로 | **기존 재사용**(`e2e_adapter.py:55`) | 기존 그대로 |
| `OPAL_TEST_TOOLS_GLOBAL` | 글로벌 러너 템플릿 | **기존 재사용**(`resolver.py:237`) | child에 그대로 상속 |

결정 규칙 3가지:
1. **기존 변수를 재정의하지 않는다.** 특히 `OPAL_HOME`은 291곳에서 참조되는 전역 변수이므로, 하네스가 자기 프로세스의 `OPAL_HOME`을 바꾸지 않고 **child env에만** 격리 값을 주입한다.
2. `AGENT_BROWSER_*` 계열은 standalone 실행 시 child env에서 **제거한 뒤** 하네스 소유 값만 주입한다(제안서 §8.3 ambient config 차단).
3. 새 변수는 모두 `OPAL_E2E_` 접두사를 쓴다. 단 `VITE_API_BASE_URL`은 Vite가 `VITE_` 접두사만 노출하므로 예외이며, 이는 프레임워크 제약이지 네이밍 이탈이 아니다.

### TD-9. `installed` target은 배포를 수행하지 않고 사전 배포본을 입력으로 받는다
**대응**: R-1, R-6, NR-5, C-5 | **제안서 §6.3과 다른 결론 — 근거 명시**

- 제안서 §6.3은 "임시 `OPAL_HOME`에 install artifact를 **배포해** smoke test한다"고 했다.
- 실측 반증: `install_dashboard()`는 FE를 **소스 트리 안에서** 빌드한다 — `scripts/install-mac.sh:1772` `(cd "$src/frontend" && npm install --silent && npm run build)`. 산출물 `dashboard/frontend/dist`를 만든 뒤 `:1774`에서 복사한다. 또한 `:1798`에서 `opal-cli console scan "$USER_HOME"`을 호출해 **사용자의 `~/.opal/console.config.json`을 갱신**한다.
- 따라서 하네스가 설치 스크립트를 호출하면 (a) 소스 트리 `dist/`를 변경하고 (b) 사용자 설치본 설정을 건드린다. R-6("저장소에 새 파일이 남지 않고 설치본이 변경되지 않는다")·C-2·C-5와 정면 충돌한다.
- 결정: `installed` target은 `--opal-home <path>` 인자로 **이미 배포된 격리 `OPAL_HOME`을 입력받아 기동·검증만** 한다. 배포 자체는 하네스 범위 밖이며, 필요해지면 설치 스크립트에 FE 출력 경로 분리 옵션을 넣는 별도 작업으로 다룬다(§10 위험 RK-4).
- 사용자의 실제 `~/.opal`을 target으로 지정하는 것은 **거부**한다(경로 동일성 검사). C-2 집행 지점이다.

### TD-10. 산출물은 OS 임시 위치에만 쓰고 저장소 내부 경로를 지원하지 않는다
**대응**: R-6, NR-5, C-5

- 기본 루트: `${OPAL_E2E_ARTIFACT_ROOT:-${TMPDIR}/opal-e2e-runs}/{project-id}/{run-id}/`.
- 결정: 제안서 §5.3이 조건부로 열어둔 **저장소 내부 `.e2e-runs/`·`.test-run/`을 지원하지 않는다.** 근거: 지원하면 같은 변경에서 `.gitignore` 갱신 의무가 따라붙고(NR-5), 실수로 추적되는 경로가 생겨 AC-13이 깨질 표면이 늘어난다. 지원하지 않으면 `.gitignore` 변경 자체가 불필요하다 — 현행 `.gitignore`(39줄)에 `.e2e-runs/`·`.test-run/`이 없다는 사실이 이 결정의 유지 비용을 0으로 만든다.
- FE 빌드: source E2E 기본은 **Vite dev server**이며 `dist/`를 만들지 않는다. production asset 검증이 필요한 별도 profile만 `--outDir ${OPAL_E2E_ARTIFACT_DIR}/dist`로 빌드하고 그 경로에서 preview한다. 저장소 공유 `dist/`와 backend의 `../../dist`(`main.py:117`)에는 E2E 포트가 bake된 산출물을 쓰지 않는다.
- 디렉터리 구조는 제안서 §5.3을 그대로 채택한다(`run.json`, `actions.jsonl`, `assertions.json`, `server/`, `browser/`, `api/`, `human/`, `screenshots/`). capability↔artifact 대응도 고정한다: `console`→`console.jsonl`, `errors`→`errors.jsonl`, `network_har`→`network.har`.

### TD-11. Browser driver는 하나의 adapter 계층에 두고 세션 소유권 모드로 구분한다
**대응**: R-7, R-8, R-9, R-10, NR-6, NR-7

- 배치: `lib/e2e/drivers/` — `agent_browser.py`(orca-managed·standalone 공용), `cmux.py`(기존 `e2e_adapter.py` 로직 이관), `playwright.py`(opt-in), `manifest.json`(버전 SSOT: `minimum_version`·`tested_range`·`ci_pin`).
- 후보 순서: `agent-browser/orca-managed` → `cmux/owned surface` → `agent-browser/standalone` → `playwright(opt-in)`.
- **가용성 판정은 각 후보가 반환한 결과만 소비한다**(NR-7). 하네스가 `uname`·`--version` 문자열·번들 파일 존재로 가용성을 추정하지 않는다. 이는 `e2e_adapter.py:18`이 이미 명문화한 [MUST]이며 새 driver에도 그대로 적용한다.
- 전환 허용은 `e2e_contract.can_try_next_provider()`(`e2e_contract.py:269`) 판정에만 의존한다. adapter가 자체 전환 조건을 만들지 않는다(C-3).
- cmux 이관 시 유지할 것: mode A 강제(`e2e_adapter.py:21`, `:169-170` `--surface` 미전달), `user_owned` surface 미정리. 보강할 것: open·navigate만으로 pass 불가 — 이미 `e2e_adapter.py:217-225`가 구조적으로 pass를 못 내므로, **assertion·증적을 실제로 채우는 것이 이관의 본질**이다.
- `wait_kind` 발행 책임: `e2e_contract.py:223-231`은 `wait_kind == "assertion_condition"`일 때만 `fail`로 판정한다. 즉 **하네스가 wait을 발행할 때 `wait_kind`를 action log에 기록해야** 이 분기가 살아난다. 기록하지 않으면 전부 `infra_error`로 fail-safe된다. driver adapter의 `wait` 연산이 `wait_kind`를 필수 인자로 받도록 한다.

### TD-12. 시나리오 형식은 교체하지 않고 실행 인자와 기존 필드로 대응한다 (미해결 질문 Q-4 결정)
**대응**: R-11, R-12, R-13, NR-1 | **PRD §12 Q-4 결정**

- 결정 1 — **`test-scenario.json` 스키마에 신규 필드를 추가하지 않는다.** 125가 확정한 v2 필드(`surface_kind`, `profile`, `actors`, `steps`, `assertions`, `required_evidence`, `handoff`)로 실행 계약을 전부 표현한다(`e2e_contract.py:418-502`, `scenario.py:274-299`).
- 결정 2 — **run 파라미터는 시나리오가 아니라 CLI 인자다.** `target`, `--worktree-root`, `--opal-home`, `entrypoint` 경로는 `e2e run` 인자로 받는다. 근거: 같은 시나리오가 main·worktree·installed에서 동일하게 실행되어야 하므로(R-3, NR-6) 실행 위치를 spec에 고정하면 시나리오가 환경에 결합된다.
- 결정 3 — **capability 요구는 `required_evidence` 값으로 표현한다.** `console`·`errors`·`network_har`·`screenshot`·`snapshot`을 `required_evidence` 원소로 쓰고, TD-10의 capability↔artifact 고정 매핑으로 해석한다. 별도 `requires` 필드를 만들지 않는다.
- 결정 4 — **기존 v1 문서·데이터 대응 규칙**:

| 기존 자산 | 새 실행 계약 대응 | 규칙 |
|---|---|---|
| `TEST-SCENARIO.md`(사람용 문서) | 변경 없음 | 실행 SSOT는 `test-scenario.json`이다. md는 서술 문서로 유지 |
| `schema_version != "2.0"` spec | `validate_scenario_contract(legacy_defaults=True)` 경로로 **읽기만** 가능(`e2e_contract.py:504-535`) | `profile=None`·`required_evidence=[]`로 보정되므로 `e2e run` 대상이 될 수 없다. `e2e run`은 v2 spec을 요구한다 |
| `id` / `acceptance_ref` / `type` | 그대로 | 추적축 무변경 |
| `expected`(자유 문장) | `assertions[].expected`로 **수동 이행** | 자동 변환하지 않는다. 문장을 구조화 expected로 바꾸는 것은 사람의 판단이며, 자동 변환은 §9.2 "정상으로 보인다는 서술은 assertion이 아니다"를 우회한다 |
| `surface_ref` | `surfaces.json` 조회 → `surface_kind` → profile | `resolve_profile`(`e2e_contract.py:136-169`) 소비 |
| `required_fidelity: real-usage` | pass 게이트 + `scenario-fidelity-check`(`scenario.py:642-678`) | 무변경 |
| `scenario-mark --result pass` | 이미 차단됨 — `scenario.py:531-542`가 `profile != None` 또는 `required_fidelity == real-usage`일 때 `--verdict-json` 없는 pass를 거부한다 | 하네스는 항상 `--verdict-json`을 쓴다 |

- 결정 5 — **`scenario.py`·`e2e_contract.py`는 이번 범위에서 기능 변경 대상이 아니다.** 하네스는 이 두 모듈의 **소비자**다. `_normalize_scenario`(`scenario.py:169-225`)에 필드를 늘리지 않는다.

### TD-13. `infra_error`는 어떤 하위 유형에서도 다음 실행 후보로 전환하지 않는다 (미해결 질문 Q-5 결정)
**대응**: R-10, NR-1, NR-7, C-3 | **PRD §12 Q-5 결정**

- 결정: `infra_error`에서 다음 Browser/executor 후보로의 전환을 **전면 금지**한다. 예외 목록을 두지 않는다.
- 근거 1(계약): `can_try_next_provider()`는 `provider_unavailable`에만 `True`를 반환한다(`e2e_contract.py:269-273`). 예외를 두려면 이 함수를 고쳐야 하고 그것은 C-1·NR-1이 금지한 계약 재설계다.
- 근거 2(의미): 제안서 §7.9의 `infra_error` 유발 사유는 전부 **가용한 provider의 실행 실패**다(`open_failed`, `goto_failed`, `eval_failed`, `surface_parse_failed`, 계약 파손, 알 수 없는 코드). "실행 수단이 없음"이 아니라 "실행 수단이 있는데 깨졌음"이므로 다른 수단의 성공이 이 실패를 해소하지 못한다.
- 근거 3(재현성): mode를 바꾸면 재현 조건이 달라지므로 자동으로 제품 성공으로 해석할 수 없다(제안서 §7.8).
- 허용되는 유일한 재시도: **같은 후보 안에서의 명시된 일시적 transport 오류 재시도**. 대상 목록은 D4 CONTRACT가 확정하며, 제품의 4xx/5xx는 절대 포함하지 않는다(제안서 §7.4).
- 진단 목적 재실행은 금지하지 않는다. 단 **별도 run으로 저장**하고 최초 실패를 덮어쓰지 않는다(제안서 §11).
- 부수 결정: `tested_range` 밖 binary의 호환성 probe 실패도 `infra_error`이며 조용한 fallback 없이 중단한다(제안서 §8.3).

### TD-14. 증적 redaction은 저장 경로의 단일 관문으로 구현한다
**대응**: R-16, C-6

- 배치: `lib/e2e/redaction.py`. 모든 증적 쓰기는 `evidence.py`를 거치고 `evidence.py`는 저장 직전 반드시 redaction을 통과시킨다. driver·executor가 파일을 직접 쓰지 않는다 — 우회 경로를 만들지 않기 위한 구조 제약이다.
- 대상: `Authorization`·`Cookie`·`Set-Cookie` 헤더, URL query의 비밀값, HAR 포함.
- 실패 처리: redaction 또는 안전한 저장 실패 시 **원문을 남기지 않고** 해당 run을 `infra_error`로 판정한다(C-6). TD-13에 따라 전환 없이 중단한다.
- browser profile은 run 종료 후 삭제하고 사용자 profile을 재사용하지 않는다(R-16).
- raw network body는 기본 미수집이며 시나리오가 선언한 allowlist endpoint만 선택한다.

### TD-15. 정리는 소유 자원 목록 기반으로만 수행한다
**대응**: R-6, R-8, C-2

- run 단위 소유 자원 대장을 artifact dir에 유지한다: 프로세스 그룹 id, 포트 lease id, browser page/profile id, cmux surface handle(`user_owned=false`인 것만), API fixture id(run-id namespace).
- 정리는 이 대장에 있는 것만 대상으로 한다. 패턴 매칭·전역 스캔·사용자 소유 표시 자원은 대상에서 제외한다.
- cleanup 결과는 verdict를 바꾸지 않고 별도 필드로 기록한다. 단 **프로세스·포트 누출처럼 다음 실행을 오염시키는 실패는 `infra_error`로 승격**한다(제안서 §5.2).

### TD-16. OS·실행기 분기는 단일 어댑터 모듈에 격리한다
**대응**: NR-3, NR-6, C-7

- 배치: `lib/e2e/process.py`가 유일한 분기 지점이다. 담당: 프로세스 생성(새 세션), PID 생존 판정, 프로세스 그룹 종료, 임시 디렉터리 해석.
- 그 외 모듈(orchestrator·runtime·drivers·executors)은 OS 조건문을 갖지 않는다. `.opal/AGENT.md` §금지사항 "하드코딩된 플랫폼 분기 추가 금지 — 어댑터 계층에서만 수행"의 집행 지점이다.
- driver 가용성은 OS 분기가 아니라 후보 probe 결과로 판정한다(NR-7, TD-11).

### TD-17. API·Hybrid는 surface fidelity gate를 실행 전·후 두 지점에서 집행한다
**대응**: R-11, R-12

- 배치: `lib/e2e/executors/api.py`.
- 실행 전(정적): 시나리오 v2 검증이 이미 `steps[].executor`와 profile 행렬을 대조해 거부한다(`e2e_contract.py:476-482`). `browser` profile 시나리오에 browser step이 없으면 `executor contract mismatch`다.
- 실행 후(동적): `validate_pass_requirements`가 `observed_executors`를 행렬과 대조한다(`e2e_contract.py:311-321`). 실제로 browser executor가 동작하지 않은 hybrid run은 pass가 되지 않는다.
- 추가로 하네스가 집행할 것: **setup·cleanup API와 검증 대상 API를 step 단위로 구분 표시**한다. 핵심 UI 행동에 대응하는 assertion이 API step만으로 충족되면 거부한다(R-12, AC-8). 이 구분 표시는 `steps[]`의 기존 필드로 표현하며 신규 최상위 필드를 만들지 않는다(TD-12).
- API fixture는 run-id로 namespace하고 자기 것만 정리한다. DB 직접 조회는 후속 state verifier로만 쓰고 공개 API 행동을 대체하지 않는다.

### TD-18. 사람 협업 재개는 기존 `scenario-mark --resume` 계약을 재사용한다
**대응**: R-13

- 실측: 재개 검증은 이미 구현되어 있다 — `scenario.py:482-528`이 `operational_status == "awaiting_human"`, `run_id` 일치, `resume_token` 일치, 제출물의 `run_id`·`resume_token` 일치를 모두 확인한 뒤 `validate_pass_requirements`를 다시 통과해야만 pass로 기록한다(`scenario.py:504-513`). "사람 제출만으로는 pass가 되지 않는다"는 R-13 조건이 이미 코드로 존재한다.
- 결정: `e2e resume`은 **새 판정 경로를 만들지 않고** 이 계약을 호출한다. 하네스가 담당하는 것은 (a) handoff 8필드 생성(`e2e_contract.py:67-76`), (b) run journal·서버 정책 집행, (c) 제출 증적 정규화, (d) 재개 후 자동 verifier 실행이다.
- `server_policy`(필수 필드)로 대기 중 서버·lease 유지 여부를 선언한다. "유지"면 lease와 프로세스 그룹을 살린 채 exit 20으로 제어를 넘기고, "종료"면 정리한 뒤 재개 시 재기동한다.
- timeout은 자동 `fail`이 아니라 `blocked`(exit 19)로 종료하고 resume token 만료 여부를 기록한다.

### TD-19. Playwright 제거는 "지원 제거"와 "기본 설치 제거"를 분리해 마지막에 수행한다
**대응**: R-17, R-18, R-19, NR-2

- 순서 고정: 대체 실행 경로(agent-browser standalone) 검증 완료 → 9개 area 소비자 이전 → 기본 설치 제거. 앞 단계 없이 제거하면 웹 수집 기능이 회귀한다(`playwright-tool/main.py:249-262`가 유일한 브라우저 기동점).
- **경쟁 SSOT 제거의 실제 대상**(R-19, AC-14): `real-usage` 정의를 **소유**하는 문서는 `opal/tools/test-tool/lib/scenario.py:119`(`FIDELITY_ORDER`)와 `e2e_contract.py:434`다. 정의 문장을 **중복 보유**한 곳은 `opal/skills/opal-pilot-project-loop/references/verification.md:30,32,43`이 가장 강하고, `opal/core/references/tools.md:682`, `opal/skills/opal-pilot-project-loop/SKILL.md:202`가 뒤따른다. 모범 사례는 `opal/core/references/test-tools-schema.yaml:135`로, 이미 "`e2e_contract.py`가 소유한다"로 위임하고 있다 — 나머지를 이 형태로 맞춘다.
- **제안서 §8.4의 9개 area 밖에서 발견된 추가 소비자 7건**을 인벤토리에 포함한다(§6.8).

---

## 5. 인터페이스 개요 (경계만 — 상세 스키마는 D4 소유)

### 5.1 실행 계약 표면

| 명령 | 입력(경계) | 출력(경계) | exit |
|---|---|---|---|
| `e2e run` | scenario id, task path, target, (worktree-root \| opal-home), artifact root | `run.json` 경로 + 상태 JSON | `status_to_exit` |
| `e2e resume` | run-id, resume token, submission 경로 | 최종 상태 JSON | `status_to_exit` |
| `e2e status` | run-id 또는 artifact dir | run 메타데이터 요약 | 0 |
| `e2e clean` | run-id 또는 stale 전체 | 회수된 lease·프로세스 목록 | 0 |

상태·exit·error 코드는 전부 `e2e_contract`에서 가져온다. **이 표에 새 상태나 새 exit 값이 등장하지 않는 것**이 NR-1 준수의 관측 지점이다.

### 5.2 상태 전이

제안서 §5.2를 채택한다. 중간 상태를 건너뛴 `pass`를 허용하지 않으며, 전이 이력은 `run.json`에 기록되어 R-15의 원인 추적 입력이 된다.

```text
created → context_resolved → ports_leased → sut_starting → sut_ready
→ profile_resolved → executor_ready → scenario_running
   (↔ awaiting_human)
→ evidence_captured → {pass|fail|executor_unavailable|blocked|infra_error}
→ {cleanup_complete|cleanup_warning}
```

### 5.3 오류 분류 경계

| 분류 | 판정 주체 | 전환 |
|---|---|---|
| `provider_unavailable` | driver 후보가 반환 → `can_try_next_provider` | 다음 Browser 후보 |
| `executor_unavailable` | Orchestrator(후보 소진) | 없음 |
| `fail` | assertion·제품 동작 | 없음 |
| `infra_error` | 서버·포트·redaction·driver 실행 오류 | **없음**(TD-13) |
| `blocked` | 인증·외부 승인·handoff timeout | 없음 |
| `awaiting_human` | handoff 발행 | resume |

---

## 6. 컴포넌트별 변경 지점 (D5 백로그 입력)

경로는 전부 **프로젝트 소스**다(`.opal/AGENT.md` §금지사항: `~/.opal/` 직접 편집 금지). `area` 열은 `docs/PROJECT.md` §프로젝트 구성의 영역 구분이다.

### 6.1 제안서 태스크 2 — Console 실행·프로세스 소유권

| 구분 | 파일 | 지점 | 내용 | area |
|---|---|---|---|---|
| 수정 | `opal/tools/opal-cli/lib/console.sh` | `:45-85` | start 시 PID 레코드 기록(`$opal_home/run/console.pid`) | Framework |
| 수정 | `opal/tools/opal-cli/lib/console.sh` | `:87-93` | `pkill -f` 제거 → 레코드 identity 검증 종료 | Framework |
| 수정 | `opal/tools/opal-cli/lib/console.sh` | `:95-106` | status에 소유권 정보 노출 | Framework |
| 수정 | `scripts/install-mac.sh` | `:1844` | 폴백 `pkill` 제거 → 레코드 기반 종료 | Framework |
| 수정 | `dashboard/backend/main.py` | `:76-79` | CORS origin env 추가 허용 | Console BE |
| 수정 | `dashboard/frontend/src/lib/api.ts` | `:14` | `import.meta.env.VITE_API_BASE_URL ?? ""` | Console FE |
| 신설 | `dashboard/frontend/src/vite-env.d.ts` | — | `ImportMetaEnv` 타입 선언(typecheck 회귀 차단) | Console FE |
| 신설 | `dashboard/frontend/.env.development` | — | dev 기본 backend 주소 고정 | Console FE |
| 신설 | `dashboard/backend/tests/` 내 1건 | — | CORS env 주입 테스트 | Console BE |
| 신설 | `opal/tools/opal-cli/` 테스트 또는 `scripts/tests/` 내 1건 | — | 양방향 비간섭 회귀 테스트(AC-3) | Framework |

### 6.2 제안서 태스크 3 — E2E Runtime Manager

| 구분 | 파일 | 내용 | area |
|---|---|---|---|
| 신설 | `opal/tools/test-tool/lib/e2e/__init__.py` | 서브패키지 | Framework |
| 신설 | `opal/tools/test-tool/lib/e2e/target.py` | target 해석·commit/dirty 수집 | Framework |
| 신설 | `opal/tools/test-tool/lib/e2e/ports.py` | allocator lock·lease record·stale 회수 | Framework |
| 신설 | `opal/tools/test-tool/lib/e2e/process.py` | 프로세스 생성·PID 생존·그룹 종료(**유일 플랫폼 분기**) | Framework |
| 신설 | `opal/tools/test-tool/lib/e2e/runtime.py` | 기동·env 주입·health gate·로그·종료 | Framework |
| 신설 | `opal/tools/test-tool/lib/e2e/orchestrator.py` | run 수명주기·상태 머신·최종 verdict 호출 | Framework |
| 수정 | `opal/tools/test-tool/test_tool.py` | `e2e` 서브파서 등록, `ERROR_CODES` 보강 | Framework |
| 신설 | `opal/tools/test-tool/tests/test_e2e_runtime.py` | lease 경쟁·stale 회수·동시 3 run(AC-1) | Framework |

`opal/tools/worktree-tool/worktree_tool.py`는 **변경하지 않는다** — `portOffset`은 hint로 남긴다(TD-3).

### 6.3 제안서 태스크 4 — Browser driver·session 계약

| 구분 | 파일 | 내용 | area |
|---|---|---|---|
| 신설 | `opal/tools/test-tool/lib/e2e/drivers/__init__.py` | session resolver·후보 순서·probe 소비 | Framework |
| 신설 | `opal/tools/test-tool/lib/e2e/drivers/manifest.json` | `minimum_version`·`tested_range`·`ci_pin` SSOT | Framework |
| 신설 | `opal/tools/test-tool/lib/e2e/evidence.py` | 공통·profile·시나리오 증적 수집 관문 | Framework |
| 신설 | `opal/tools/test-tool/lib/e2e/redaction.py` | 민감정보 마스킹(C-6) | Framework |
| 수정 | `opal/tools/test-tool/lib/e2e_adapter.py` | `wait_kind` 발행 경로 추가, driver 계층 위임 | Framework |
| 신설 | `opal/tools/test-tool/tests/test_e2e_drivers.py` | capability·legacy 변환·`wait_kind` 분기 | Framework |

### 6.4 제안서 태스크 5 — agent-browser 공용 driver

| 구분 | 파일 | 내용 | area |
|---|---|---|---|
| 신설 | `opal/tools/test-tool/lib/e2e/drivers/agent_browser.py` | orca-managed·standalone 공용 adapter | Framework |
| 수정 | `opal/tools/test-tool/lib/e2e/drivers/manifest.json` | 실측 버전 반영 | Framework |
| 신설 | `opal/tools/test-tool/tests/test_agent_browser_driver.py` | 격리 키·config·allowed domains | Framework |

### 6.5 제안서 태스크 6 — cmux driver 이전

| 구분 | 파일 | 지점 | 내용 | area |
|---|---|---|---|---|
| 신설 | `opal/tools/test-tool/lib/e2e/drivers/cmux.py` | — | `e2e_adapter.py:129-231` 로직 이관 + assertion 필수화 | Framework |
| 수정 | `opal/tools/test-tool/lib/e2e_adapter.py` | `:129-231` | 신규 driver 위임, mode A 규칙(`:21`) 유지 | Framework |
| 수정 | `opal/tools/test-tool/tests/test_test_tool.py` | 기존 integration 케이스 | 회귀 유지 | Framework |

### 6.6 제안서 태스크 7 — API·Hybrid executor

| 구분 | 파일 | 내용 | area |
|---|---|---|---|
| 신설 | `opal/tools/test-tool/lib/e2e/executors/__init__.py` | — | Framework |
| 신설 | `opal/tools/test-tool/lib/e2e/executors/api.py` | HTTP 호출·후속 state assertion·fixture 정리 | Framework |
| 신설 | `opal/tools/test-tool/lib/e2e/scenario_adapter.py` | 시나리오 → step/assertion/handoff 정규화 | Framework |
| 신설 | `opal/tools/test-tool/tests/test_e2e_api_executor.py` | UI 우회 거부(AC-8) | Framework |

### 6.7 제안서 태스크 8 — Human handoff executor

| 구분 | 파일 | 내용 | area |
|---|---|---|---|
| 신설 | `opal/tools/test-tool/lib/e2e/executors/human.py` | handoff 발행·journal·timeout·서버 정책 | Framework |
| 수정 | `opal/tools/test-tool/test_tool.py` | `e2e resume` 라우팅 | Framework |
| 신설 | `opal/tools/test-tool/tests/test_e2e_human_executor.py` | pause→resume→verifier(AC-9) | Framework |

`opal/tools/test-tool/lib/scenario.py:482-528`(resume 검증)은 **변경하지 않는다** — 재사용한다(TD-18).

### 6.8 제안서 태스크 9 — Playwright 기본 설치 제거

9개 area의 실측 인벤토리다. 각 행이 D5 백로그 1건 이상으로 분해된다.

| area | 파일:줄 | 조치 | area 구분 |
|---:|---|---|---|
| 1 | `opal/tools/test-tool/lib/e2e_adapter.py` | playwright 직접 참조 **0건**. 실행 경로는 resolver 후보 이름을 통한 **간접**뿐 | Framework |
| 1 | `opal/tools/test-tool/test_tool.py:56`, `:221` | 사용자 노출 문구("cmux/playwright 모두 실패", "playwright 폴백") 갱신 | Framework |
| 2 | `opal/tools/test-tool/lib/resolver.py:106-112`, `:156-162` | 추론 후보 테이블에서 playwright 항목 제거 또는 opt-in 표시 | Framework |
| 2 | `opal/core/references/test-tools-schema.yaml:140`, `:220` | 예시·note 갱신 | Framework |
| 2 | `opal/templates/test-tools.yaml:130` | **신규 프로젝트 기본 생성 항목** 제거 | Framework |
| 2 | `opal/tools/test-tool/tests/test_test_tool.py:158,181,599,643,728` | yaml 픽스처 갱신 | Framework |
| 3 | `opal/tools/playwright-tool/run.sh:13`, `main.py:249-262` | 웹 수집 기능 대체 또는 opt-in 격리 | Framework |
| 4 | `opal/agents/opal-wtm-agent/AGENT.md:5,44,66,96,99,100,119,132,136` | 폴백 정책 이전 | Framework |
| 4 | `skills/web-to-markdown/SKILL.md` (다수) | 같은 폴백 계약 중복 기술 갱신 | Framework |
| 4 | `opal/tools/tool-scan/tests/test_tool_scan.py:843-880` | **"playwright 폴백" 문구를 강제하는 회귀 테스트** — 먼저 갱신하지 않으면 RED | Framework |
| 5 | `opal/core/mcps/playwright.json` | MCP 정의 제거/opt-in | Framework |
| 5 | `opal/tools/opal-cli/lib/mcp.sh:70-88,120,252,321` | 등록기 목록·예시 | Framework |
| 5 | `scripts/install-mac.sh:2009-2010,2058,2076,2094` | cache 디렉터리 생성·플랫폼 등록 분기 | Framework |
| 6 | `opal/tools/requirements.txt:28-29` | `playwright>=1.40.0` 기본 의존성 제거 | Framework |
| 6 | `scripts/install-mac.sh:1289-1293,1700-1732` | 실행 권한 부여·Chromium 자동 설치 제거 | Framework |
| 6 | `scripts/install/windows.ps1:1030-1045` | Windows 안내 제거 | Framework |
| 7 | `opal/tools/doctor/lib/checks.sh:50,179-183,268,293` | 의존성·공식 MCP 분모에서 제외 | Framework |
| 7 | `opal/tools/doctor/run.sh:6`, `doctor/README.md` | 진단 설명 갱신 | Framework |
| 7 | `dashboard/backend/tests/test_doctor_adapter.py:22,31` | 파서 픽스처 갱신 | Console BE |
| 8 | `opal/skills/opal-pilot-project-loop/references/verification.md:30,32,39,43,207,208` | **경쟁 SSOT 핵심** — 정의를 `e2e_contract` 참조로 대체 | Framework |
| 8 | `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md:57,98` | `npx playwright test` 예시·자동 감지 키워드 | Framework |
| 8 | `opal/skills/opal-pilot-project-loop/SKILL.md:202`, `references/journey-flow.md:89,108` | 문구 참조화 | Framework |
| 9 | `opal/core/references/tools.md:526,528,530,682` | **존재하지 않는 명령 문서화 오류 포함**(`run.sh extract`·`click`/`fill`은 `main.py`에 없다) | Framework |
| 9 | `opal/core/references/agents.md:273,287` | AGENT.md와 **불일치**(Phase 번호·`webfetch` 잔존) | Framework |
| 9 | `opal/core/references/mcps.md:12,53-60,88,90,101` | MCP 항목·버전 불일치(`^0.0.75` vs `@latest`) | Framework |
| 9 | `opal/core/references/skills.md:70`, `community-skills-registry.json:20` | 외부 선택지 catalog — **이번 범위 제외**(PRD §4.2) | Framework |

**제안서 9개 area 밖의 추가 소비자(신규 발견 — 인벤토리에 편입해야 R-17의 "0 또는 opt-in" 판정이 성립한다)**

| # | 파일:줄 | 성격 |
|---|---|---|
| A-1 | `opal/templates/test-tools.yaml:130` | 신규 프로젝트에 playwright 후보를 **기본 생성** |
| A-2 | `opal/tools/tool-scan/tests/test_tool_scan.py:843-880` | 문구를 **강제**하는 회귀 테스트 |
| A-3 | `dashboard/backend/tests/test_doctor_adapter.py:22,31` | doctor 출력 파서 픽스처 |
| A-4 | `opal/skills/opal-pilot-sdd/SKILL.md:66,289,432,444` | opsdd Phase 5가 "Playwright E2E"를 직접 지정 |
| A-5 | `docs/SECURITY.md:92,98,100` | MCP 버전 핀·cache 경로 보안 정책 |
| A-6 | `docs/ARCHITECTURE.md:88,177,344,364,365,410,429,479`, `docs/CONVENTIONS.md:248`, `docs/PROJECT.md:100` | 문서 레지스트리 현재 사실 |
| A-7 | `opal/agents/opal-test-agent/AGENT.md:89`, `personas/test-engineer.md:35` | 역량 서술 |

### 6.9 문서 갱신 대상 (코드 변경이 현재 사실을 바꾸는 것)

| 문서 | 바뀌는 사실 |
|---|---|
| `docs/ARCHITECTURE.md` §OPAL Console | Console 기동·종료 소유권 모델, FE API 주소 주입 방식 |
| `docs/CONVENTIONS.md:248` | 도구 목록(playwright-tool 처리 결과) |
| `docs/PROJECT.md` | 도구·에이전트 구성 변경분 |
| `opal/tools/test-tool/README.md` | `e2e` 서브명령군 신설 |
| `opal/tools/opal-cli/README.md` | console stop 동작 변경 |
| `.opal/brain/pages/concept/e2e-cmux-first-playwright-fallback.md` | 과거 결정 대체(→ Q-7, E4 완료 후) |

---

## 7. 데이터·산출물 구조

```text
${OPAL_E2E_ARTIFACT_ROOT:-${TMPDIR}/opal-e2e-runs}/
├── .leases/                     ← allocator lock + lease record (TD-3)
└── {project-id}/{run-id}/       ← = $OPAL_E2E_ARTIFACT_DIR
    ├── run.json                 ← R-5 실행 증명 (공통 필수)
    ├── journal.json             ← 상태 전이 이력 · awaiting_human 재개 입력
    ├── owned.json               ← 소유 자원 대장 (TD-15)
    ├── probe.json               ← 후보별 capability probe 결과 배열 (CONTRACT §A.8)
    ├── actions.jsonl            ← 공통 필수 (wait_kind 포함)
    ├── assertions.json          ← 공통 필수 (expected/actual)
    ├── cleanup.json             ← 공통 필수
    ├── server/{backend.log, frontend.log, *.pid}   ← 공통 필수(하네스 기동 run)
    ├── browser/{before.snapshot, after.snapshot, console.jsonl, errors.jsonl, network.har}
    ├── api/{requests.jsonl, responses.jsonl}       ← api·hybrid 필수
    ├── human/{handoff.json, submission.json}       ← collaborative·manual 필수
    └── screenshots/{scenario-id}-{step}.png
```

- 공통 필수 증적 5종: 실행 metadata, server log, action log, assertion expected/actual, cleanup 결과. 이 중 하나라도 없으면 pass가 될 수 없다 — 판정은 `validate_pass_requirements`의 `required_evidence` 대조(`e2e_contract.py:357-366`)가 수행한다.
- 저장소·설치본에는 아무것도 쓰지 않는다(TD-10, R-6).

---

## 8. 기존 자산 재사용과 확장 판단

제안서 §5.1이 "확장 우선, 분리는 근거 있을 때만"으로 남긴 판단의 결론이다.

| 자산 | 판단 | 근거 |
|---|---|---|
| `e2e_contract.py` | **그대로 소비. 변경 0** | C-1·NR-1. 상태·exit·pass 게이트를 전부 이미 소유 |
| `scenario.py` | **그대로 소비. 변경 0** | resume 검증(`:482-528`)·fidelity 게이트(`:642-678`)가 이미 요구를 충족 |
| `resolver.py` | 후보 테이블만 수정 | `:106-112`, `:156-162` playwright 항목(태스크 9) |
| `e2e_adapter.py` | driver 계층으로 이관 + `wait_kind` 추가 | 기존 mode A 소유권 모델 유지 |
| `test_tool.py` | 서브파서·ERROR_CODES 확장 | 진입점 단일 유지 |
| `worktree-tool` | **변경 0** | `portOffset`은 hint. lease는 신규 책임(제안서 §6.6) |
| `cmux-tool` | **변경 0** | 기존 error code 계약을 adapter가 소비(NR-7) |
| `opal-cli/console.sh` | 소유권 모델 교체 | R-4의 유일한 해결 경로 |
| 신규 독립 도구 | **신설하지 않음** | TD-1 |

---

## 9. 미해결 질문 결정

| # | 질문 | 결정 | 위치 |
|---|---|---|---|
| Q-1 | 환경 변수명 충돌 | **충돌 없음.** `OPAL_E2E_*`·`VITE_*` 모두 코드 사용 0건. 표 확정, 기존 변수 재정의 금지, `OPAL_HOME`은 child env에만 주입 | TD-8 |
| Q-4 | 기존 시나리오 형식 대응 | **스키마 무변경.** run 파라미터는 CLI 인자, capability는 `required_evidence`, v1 spec은 읽기 전용 호환, `expected`는 수동 이행 | TD-12 |
| Q-5 | `infra_error` 전환 정책 | **전면 금지.** 예외 목록 없음. 허용은 같은 후보 내 명시된 transport 재시도뿐 | TD-13 |
| Q-2 | Orca 관리 세션에 실행 범위 격리 설정 적용 가능 여부 | **실측 의존** — E3에서 비파괴 probe로 확인. 확인 전에는 격리를 보장하거나 pass 전제로 삼지 않고 run 전용 page/profile만 격리 수단으로 쓴다 | — |
| Q-3 | `console`·`errors`·`network_har` 수집 가능 실행 경로 | **실측 의존** — E3 probe. `probed=false`는 보수적으로 `available=false` | — |
| Q-6 | 제거 후 opt-in driver 유지 기간 | **실측 의존** — E6에서 유지 비용·사용 근거 검토 후 결정 | — |
| Q-7 | 과거 도구 우선순위 결정 기록 대체 시점 | **실측 의존** — E4 완료 후. 이번 TRD는 대상 페이지만 지목(`.opal/brain/pages/concept/e2e-cmux-first-playwright-fallback.md`) | — |

Q-2·Q-3·Q-6·Q-7은 이 TRD에서 결정하지 않는다. 설계는 이들이 **미확정인 상태에서도 성립하도록** 구성했다 — capability 미확인은 `available=false`로 보수 판정되어 해당 시나리오가 실행되지 않을 뿐, 다른 경로의 판정을 바꾸지 않는다(R-15 마지막 문장).

---

## 10. 위험과 완화

| # | 위험 | 영향 | 완화 |
|---|---|---|---|
| RK-1 | E2E backend와 사용자 Console이 **같은 ASGI 경로 문자열**을 쓰므로 패턴 종료가 남아 있으면 AC-3이 즉시 깨진다 | R-4 불성립 | `console.sh:88`과 `install-mac.sh:1844` **두 지점 모두** 교체. 어느 하나라도 남기면 완화되지 않는다 |
| RK-2 | `api.ts:14` 변경이 `npm run dev` 개발 흐름과 `npm run typecheck`를 동시에 회귀시킨다 | Console FE 회귀 | `.env.development`와 `vite-env.d.ts`를 **같은 변경에 포함**(TD-6). 둘 중 하나만 하면 회귀 |
| RK-3 | vite가 남기는 손자 프로세스·포트가 회수되지 않아 다음 run을 오염시킨다 | R-3·R-6 | 프로세스 그룹 단위 종료 + stale lease 회수 + 누출 시 `infra_error` 승격(TD-15) |
| RK-4 | `installed` target의 배포 자동화가 소스 트리 `dist/`와 사용자 설정을 변경한다 | C-2·C-5 위반 | 하네스가 install을 호출하지 않는다(TD-9). **격리 `OPAL_HOME` 배포본 생성은 이번 프로젝트 범위 밖이며**(PRD §4.2 비목표), `installed` target은 이미 준비된 경로를 `--opal-home`으로 받는다. 준비 절차 부재 시 `e2e run --target installed`는 실행되지 않고 입력 오류로 거부된다 |
| RK-5 | `tool-scan/tests/test_tool_scan.py:843-880`이 "playwright 폴백" 문구를 강제해, 문서 이전이 테스트 RED를 유발한다 | 태스크 9 진행 차단 | 문구 이전과 테스트 갱신을 **같은 작업 단위**로 묶는다 |
| RK-6 | `wait_kind`를 발행하지 않으면 모든 wait 실패가 `infra_error`가 되어 실제 assertion 실패가 감춰진다 | R-10·R-15 품질 저하 | driver `wait` 연산이 `wait_kind`를 필수 인자로 받게 한다(TD-11) |
| RK-7 | Q-2·Q-3 실측 결과에 따라 Orca 경로에서 요구 증적을 못 모아 시나리오가 실행 불가가 된다 | E3 범위 축소 | standalone 경로가 같은 계약을 재사용하므로 대체 경로가 존재한다(TD-11). 축소는 판정 기준이 아니라 실행 후보 수의 문제 |
| RK-8 | 신규 모듈이 `e2e_contract`를 우회해 자체 상태 문자열을 만든다 | NR-1 붕괴 | 상태·exit·error 생성은 `e2e_contract` 함수 호출로만 허용. 테스트로 고정(§6.2) |

---

## 11. R/NR 역추적표

| ID | 대응 기술 결정 | 변경 지점 |
|---|---|---|
| R-1 | TD-4, TD-9 | `lib/e2e/target.py`, `lib/e2e/runtime.py` |
| R-2 | TD-3 | `lib/e2e/ports.py` |
| R-3 | TD-3, TD-6 | `lib/e2e/ports.py`, `api.ts:14` |
| R-4 | TD-5 | `console.sh:75-93`, `install-mac.sh:1844` |
| R-5 | TD-2, TD-4 | `lib/e2e/target.py`, `run.json` |
| R-6 | TD-10, TD-15 | `lib/e2e/evidence.py`, `lib/e2e/process.py` |
| R-7 | TD-11 | `lib/e2e/drivers/agent_browser.py` |
| R-8 | TD-11, TD-15 | `drivers/*`, `owned.json` |
| R-9 | TD-11 | `drivers/agent_browser.py`(standalone) |
| R-10 | TD-11, TD-13 | `can_try_next_provider` 소비, `wait_kind` 발행 |
| R-11 | TD-17 | `lib/e2e/executors/api.py` |
| R-12 | TD-17 | `e2e_contract.py:311-321` 소비 + step 구분 표시 |
| R-13 | TD-18 | `lib/e2e/executors/human.py`, `scenario.py:482-528` 재사용 |
| R-14 | TD-1, TD-14 | `validate_pass_requirements` 단일 관문 |
| R-15 | TD-4, TD-11, §7 | `run.json`·`journal.json`·`actions.jsonl` |
| R-16 | TD-14 | `lib/e2e/redaction.py` |
| R-17 | TD-19, §6.8 | 9개 area + 추가 7건 |
| R-18 | TD-19 | `requirements.txt:28-29`, `install-mac.sh`, `doctor/lib/checks.sh` |
| R-19 | TD-19 | `verification.md:30,32,43` 등 → `e2e_contract` 참조화 |
| NR-1 | TD-1, TD-13, §8 | `e2e_contract.py` 변경 0 |
| NR-2 | TD-19, §6 순서 | 태스크 2·3·4 → 5~8 → 9 |
| NR-3 | TD-16, §6 서두 | 프로젝트 소스 경로만, 분기 단일화, 변경이력 절 미작성 |
| NR-4 | TD-6, TD-7, TD-8 | `api.ts:14`, `main.py:76-79`, env 표 |
| NR-5 | TD-10 | 산출물 루트 고정, `.gitignore` 변경 불요 |
| NR-6 | TD-11, TD-16 | driver 후보 계약, `lib/e2e/process.py` |
| NR-7 | TD-11, TD-16 | 후보 반환 결과 소비, 자체 환경 재구현 금지 |

전 26건(R-1~R-19, NR-1~NR-7) 대응 완료.
