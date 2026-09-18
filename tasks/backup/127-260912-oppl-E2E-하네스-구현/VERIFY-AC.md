---
template: sdlc-v2
---
# VERIFY-AC: W-14 전체 통합 검증 (AC-1~AC-16 관통)

> 수행: EXECUTE / W-14 (P7) · 대상 커밋 `591348b` (워킹트리 clean) · 실행일 2026-09-15
> 성격: **관측·기록 전용.** 코드·문서를 고치지 않는다. 발견한 결함은 고치지 않고 블로커로 반환한다.
> 실행 증적 루트(저장소 밖, C-5): `${SCRATCH}/w14-evidence/` 및 `${TMPDIR}/w14-run-*`

## 0. 사용자 환경 보존 근거 (C-2)

| 자원 | 실행 전 | 실행 후 |
|---|---|---|
| 사용자 Console `127.0.0.1:7823/health` | 200 | 200 (PID 28736 불변) |
| Orca `agent-browser session list` | `default` 1건 | `default` 1건 |
| Chrome 프로필 | Default · Profile 1 · 2 · 4 · 6 (5종) | 동일 5종 |
| 설치본 `~/.opal/dashboard-server/` | — | 세션 시작(21:10) 이후 변경 파일 **0건** (`find -newermt` 실측) |

- 모든 SUT는 임대 포트(57xxx·61xxx)에서만 기동했고 `7823`을 SUT로 쓴 run은 0건이다.
- brain prewarm 부수효과를 피하기 위해 browser 후보가 필요 없는 run은 전부 격리 `HOME`(빈 `prewarm_projects`)에서 돌렸다. browser run만 실 `HOME`을 쓴다 — orca-managed 세션 해석이 `HOME`에 매여 있기 때문이다(§3 F-2).

## 1. AC 판정표

| AC | 판정 | 실행 근거 |
|---|---|---|
| AC-1 | **충족** | main(`21c9d62`) + worktree `task_126`(`710800d`) + worktree `task_127`(`591348b`) 3 run 동시 실행. 전건 `status=pass`. 포트 `61384~61389` 6개 전부 상이(중복 0), `project_root` 3종 상이, `cleanup.result=complete`·`leaked=[]`, lease 6건 전부 released. 종료 후 해당 포트 LISTEN 0건 |
| AC-2 | **충족** | 위 3 run의 `run.json`에 `profile·actors·target·project_root·worktree_root·commit·dirty·dirty_files·urls·executors·candidates·driver_version` 결손 0. `commit`은 `git -C <root> rev-parse HEAD`와 3/3 일치, `dirty`도 3/3 일치. browser run에서 `driver_version=0.27.0`·`resolution_source=orca-bundle`이 실제로 실린다 |
| AC-3 | **충족(기존) + 회귀 재측정** | `scripts/tests/test_console_ownership.sh` 재실행: **22 PASS / 1 FAIL**. FAIL은 기능 회귀가 아니라 경계 감시 grep 1건(§3 F-6). AC-3 기능 케이스 S-4·S-5·S-6·S-7 전건 PASS, 스크립트 자체 단언인 "사용자 7823 health 시작=종료 200"도 PASS |
| AC-4 | **충족** | 실 Orca(`orca-managed`, binary `0.27.0`) 후보 selected → 실 UI 행동 `reload` 수행 → 브라우저에서 읽어 온 `title`로 `expected==actual` 판정 → `status=pass`, `fidelity=real-usage`. `owned.json.browser_pages`는 `page_id==run_id` 1건·`user_owned=false`뿐이고, 정리 후에도 사용자 `default` 세션이 그대로 살아 있다. 증적 `${SCRATCH}/w14-evidence/browser-ops/` |
| AC-5 | **충족** | 격리 `HOME`으로 Orca 활성 세션을 비파괴로 없앤 뒤 실행 → 후보1 `orca-managed` `provider_unavailable(orca_runtime_no_active_session)` → 후보2 `cmux` `provider_unavailable(cmux_not_installed)` → 후보3 `agent-browser/standalone` **selected**(`resolution_source=path`) → 실 UI 행동 + assertion → `status=pass`, `fidelity=real-usage`. 자체 profile `opal-e2e-<run_id>` 생성·해제. 증적 `${SCRATCH}/w14-evidence/ac5-standalone/` |
| AC-6 | **충족** | (a) `required_evidence`에 `screenshot`을 넣은 api run → `status=fail`, `missing_evidence=["screenshot"]`, `evidence_complete=false`, `fidelity=mock`(real-usage 승격 차단). (b) assertion 공백 시나리오 → `status=blocked`, `detail="semantic assertion required"`. 두 경로 모두 `pass`·`real-usage` 도달 불가 |
| AC-7 | **충족** | 브라우저 없이 `api` profile로 실 임대 SUT 관통: `GET /health` 200 실호출(`api/requests.jsonl`·`responses.jsonl` 기록). 이번 세션 pytest 재실행에서 `test_e2e_sut_http_surfaces.py`의 선언 HTTP 표면 16건이 전부 실 SUT 위에서 통과(후속 observable state는 `verifier:"state"` 별도 실호출로 확인) |
| AC-8 | **충족(단서 있음)** | `hybrid` 시나리오에서 `core_ui:true` assertion을 `step_role=verify`인 **api** step으로 대체 → `detail_code=e2e_core_ui_behavior_substituted_by_api`, `fidelity`가 `real-usage`가 아닌 **`real-http`로 상한 적용**. 대조군(같은 단언을 browser step이 충족)은 `real-usage`. **단서**: 거부는 "충실도 상한 + 하류 게이트(`scenario-conformance`/`fidelity-check`)"로 표현되고 run 자체는 `status=pass`·exit 0으로 끝난다 |
| AC-9 | **미충족** | `collaborative` 시나리오를 `e2e run`으로 실행하면 `awaiting_human`(exit 20)에 **도달하지 못한다**. `status=blocked`(exit 19), `detail_code=executor_unknown_operation`, `detail="'prepare' is not one of ('probe','handoff','resume')"`. `handoff.json` 미발행 → resume 3종(불완전 제출·완전 제출·잘못된 토큰) 전부 `e2e_resume_state_not_found`. 원인은 §3 F-4 |
| AC-10 | **충족** | 일부러 틀린 `expected`로 실패시킨 run에서 `missing_evidence=[]`, 공통 필수 증적 5종 전건 + `probe` 확보. 산출 파일: `run.json·journal.json·owned.json·cleanup.json·assertions.json·actions.jsonl·probe.json·redaction.json·api/requests.jsonl·api/responses.jsonl·server/{backend,frontend}.{log,err.log}`. assertion에 `expected=599 / actual=200 / passed=false / evidence_refs / observed_via_step` 전건 기록 |
| AC-11 | **충족(단서 있음)** | 기본 설치에서 Playwright 제거 확인 — `opal/tools/requirements.txt:28-31`은 opt-in 주석만, `install-mac.sh:1712`·`windows.ps1:1030` 기본 설치 제외·기존 캐시 보존, `doctor/lib/checks.sh:50,261` 진단 분모 제외, `templates/test-tools.yaml:130-132` 주석 선언형, `drivers/__init__.py:75` `opt_in:True`. 소비자 12건 분류(이전 8·opt-in 2·범위제외 2)는 `AGENTIC-LOG.md` #43에 기록. **단서**: oppd `verification-loop-guide.md`에 `npx playwright test` 실행 예시가 잔존(AC-14에서 미충족으로 계상) |
| AC-12 | **blocked (S-21)** | 격리가 성립하지 않는다. `install-mac.sh` 비대화형 경로는 `install_opal → install_dashboard → console_autostart`가 **항상** 실행되고, `console_autostart():1811-1813`이 `port=7823`을 **하드코딩**한다. 격리 `HOME`으로 돌려도 이 단계는 캡틴의 7823을 health 대상으로 삼아 "설치본 Console 정상"을 오판정하며, 격리본 Console의 기동 자체를 관측할 수 없다. 추가로 `install_dashboard():1765`의 FE 빌드가 **소스 트리 `dashboard/frontend/dist`에 씀** → C-5·AC-13과 충돌. 따라서 pass로 올리지 않고 blocked로 남긴다 |
| AC-13 | **충족** | 전 실행 후 `git status --porcelain` = 보고서 1건 + `test-scenario.json`(도구 `scenario-mark` 기록분)뿐. 저장소 `dashboard/frontend/dist` 미생성. 설치본 `~/.opal/dashboard-server/`는 세션 시작 이후 변경 파일 0건(`__pycache__` 포함 0건). 모든 산출물은 OS 임시 경로·`OPAL_E2E_ARTIFACT_DIR` 아래 |
| AC-14 | **미충족** | 경쟁 SSOT 문장이 **2건 잔존**. `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md:57` — L3b를 "브라우저 기반 시나리오 테스트 / `npm run test:e2e`, `npx playwright test`"로 **정의**한다. 같은 파일 `:98` — E2E(L3b) 판별을 `test:e2e`·`e2e`·`playwright` 스크립트 이름으로 규정. 제안서 §8.4 area 8이 지목한 oppd 문서이며 TASK "포함" 범위다. oppl `verification.md:39`는 계약 참조형으로 이전 완료(정상) |
| AC-15 | **충족** | `test_console_ownership.sh` `[B-신규] S-13(AC-15)` PASS — 격리 `OPAL_HOME`에 `started_at`을 부팅 이전으로 둔 레코드 + 생존 센티넬 조건에서 `console stop` 실행 시 **센티넬이 죽지 않고** `stopped=false reason=stale_record`. 대조군 `S-14(a)`(부팅 이후 기록 → `stopped=true`·센티넬 종료)와 `S-14(b)`(파싱 실패 → fail-open) 모두 PASS |
| AC-16 | **충족** | `.gitignore:41` = `.oppl-run/`. `git status --porcelain`에 `.oppl-run` 매치 0건(스크립트 S-16이 동일 사실을 "전제불일치"로 기록) |

**집계: 충족 12 · 미충족 2(AC-9, AC-14) · blocked 1(AC-12) · 충족(기존 재확인) 1(AC-3)**

## 2. C-9 기준선 4종 재측정

| 지표 | 기준선 | 실측 | 판정 |
|---|---|---|---|
| `~/.opal/.venv/bin/python -m pytest opal/tools/test-tool/tests/ -q` | 88 passed 이상 | **424 passed, 330 subtests passed** (167.78s) | 충족 |
| `bash scripts/tests/test_console_ownership.sh` | 20/20 + AC-15 신규 케이스 | **22 PASS / 1 FAIL** (AC-15 신규 3케이스 포함 PASS) | **미충족 1건** — §3 F-6 |
| vitest | 161 passed | **131 passed / 11 files** (0 failed) | 기준선 도달 불가 — §3 F-7 (main 상속) |
| `console.sh`·`install-mac.sh`의 `pkill`·`pgrep`·`killall` | 각각 0건 | `console.sh` 0 · `install-mac.sh` 0 | 충족 |

부수 계약 검사: `git diff --stat opal/tools/test-tool/lib/e2e_contract.py opal/tools/test-tool/lib/scenario.py` → **빈 출력**(C-1 유지).

## 3. 발견 사항 — 고치지 않고 기록한다

### F-4 [Critical] `collaborative`·`manual` profile은 `e2e run`으로 절대 실행되지 않는다 (AC-9 원인)
- `lib/e2e/orchestrator.py` `_open_executor()`가 browser가 아닌 모든 executor에 **무조건 `prepare`를 dispatch**한다.
- `lib/e2e/executors/__init__.py:48` `HUMAN_OPERATIONS = ("probe","handoff","resume")` — human executor에 `prepare`가 없다.
- 결과: human이 required인 profile은 step 실행 이전에 `executor_unknown_operation` → `blocked`(exit 19)로 끝난다. `awaiting_human`·`handoff.json`·resume 경로 전체가 CLI에서 도달 불가.
- 기존 단위 테스트가 이를 못 잡은 이유: `test_e2e_human_executor.py`는 human executor를 **직접** 호출해 orchestrator 배선을 우회한다.
- 영향: AC-9 미충족, 표면 `human-executor-handoff`·`human-executor-resume` 검증 불가.

### F-5 [Critical] cleanup이 `complete`·`leaked:[]`를 보고하고도 프로세스를 남긴다
관측된 누출 2종(모두 해당 run의 `cleanup.json`이 `result=complete`, `leaked=[]`였다):

| 누출 | PID | 기동 | 상태 |
|---|---|---|---|
| SUT backend (worktree 129·132, 프런트 `vite: command not found`로 `sut_startup_failed`) | 11892, 11896 | 21:25:01 | PPID 1로 고아화, `61110`·`61112` LISTEN 유지 |
| standalone `agent-browser` + 자식 Chrome (AC-5 run) | 30690, 30697 | 21:29:06 | PPID 1로 고아화, `61641`·`61642` LISTEN 유지 |

- 같은 계열의 선행 누출도 확인된다 — `task_127/dashboard/frontend`의 vite 2건(PID 38420·41841, 10:25 기동)이 이 세션 이전부터 남아 있다.
- **정리 권한이 없어 회수하지 못했다**(자동화 정책이 `kill`과 `e2e clean` 호출을 차단). 위 4개 PID는 사용자 소유 자원이 아니라 run 소유 자원이므로 회수 대상이다.
- 의미: `cleanup.json`의 `complete`/`leaked:[]`는 현재 **실제 프로세스 생존을 확인한 값이 아니다**. AC-1의 "독립적으로 종료된다"와 §C.3의 신뢰도를 직접 깎는다.

### F-1 [Major] `--target source-main`이 main이 아니라 cwd의 git toplevel을 가리킨다
- `lib/e2e/target.py:157-158` — `source-main`은 `_cwd_toplevel()`만 본다. worktree 안에서 실행하면 `target:"source-main"`인데 `project_root`·`commit`은 그 worktree 값이 실린다.
- 실측: worktree `task_127`에서 `--target source-main` 실행 → `project_root=.../task_127`, `commit=591348ba`(main은 `21c9d62`). **run.json의 출처 기록이 거짓이 된다**(AC-2의 존재 이유와 충돌).
- AC-1 판정은 cwd를 main 체크아웃으로 옮겨 다시 측정한 값이다.

### F-2 [Major] browser 후보 해석이 `HOME`에 매여 있어 격리 실행과 양립하지 않는다
- 격리 `HOME`에서는 orca-managed가 항상 `orca_runtime_no_active_session`이 된다. 즉 **AC-4 경로(orca-managed)는 캡틴의 실 `HOME`에서만 재현된다.**
- 실 `HOME`으로 도는 SUT는 `dashboard/backend/config.py`의 `CONFIG_PATH`(= `Path.home()/".opal"/"console.config.json"`, `OPAL_HOME` 미참조) 때문에 캡틴의 실 설정을 읽고 **기동 시 brain prewarm으로 실 프로젝트에 claude 세션을 띄운다**(첫 AC-1 시도의 `server/backend.err.log`에서 `[brain] claude 호출 시작 ... prewarm 대상 ['/Volumes/Data/StoreLinkStudio/pointail']` 실관측).
- 결론: "browser 검증"과 "C-2 격리"가 현재 설계에서 동시에 성립하지 않는다.

### F-3 [Major] 동결 spec의 `required_fidelity`와 profile이 모순돼 7개 표면이 구조적으로 green 불가
- `_resolve_fidelity()`(orchestrator)는 **선택된 후보에 browser가 있을 때만** `real-usage`를 준다. `EXECUTOR_MATRIX["api"]`는 `api`만 허용하므로 **api profile run의 충실도 상한은 `real-http`**다.
- 그런데 다음 시나리오는 `profile:"api"` + `required_fidelity:"real-usage"`다 — S-10(`sut-health`), S-40~S-44·S-7(`api-executor-*` 6종).
- `scenario-conformance`의 문턱은 `required_fidelity`이므로, 이 7개 표면은 **실제로 관통해 `pass`를 받아도 영원히 unverified로 남는다.** 실측으로 확인했다(7건 전부 `pass`·`real-http`로 표시했으나 conformance 미검증 유지).
- C-8에 따라 동결 spec을 고치지 않았다. **`all_surfaces_green`은 현재 계약에서 도달 불가능한 목표다.**

### F-6 [Major] `test_console_ownership.sh` S-2(MV-22 경계 감시)가 회귀 FAIL
- 판정: `grep -rq 'console\.pid' opal/tools/test-tool/` → hit 1건.
- hit 위치: `opal/tools/test-tool/tests/test_e2e_status_clean.py:336,340` — **"clean은 `console.pid`를 보지 않는다"를 단언하는 테스트 자신**이 문자열을 갖고 있다.
- 즉 기능 회귀가 아니라 **뭉툭한 grep 감시와 신규 경계 테스트의 충돌**이다. 그러나 C-9 기준선 "20/20"은 현재 성립하지 않는다. 감시 grep을 좁힐지, 테스트 문구를 바꿀지는 소유자 판단이다(W-14는 고치지 않는다).

### F-7 [Normal] vitest 161 → 131은 main 상속이며 이 태스크의 회귀가 아니다
- `de293e9`(main 동기화 전) 프런트 테스트 파일 12개 → 현재 11개. 사라진 파일은 `dashboard/frontend/src/workbench/WorkbenchApp.test.tsx`(케이스 **30건**).
- 삭제 커밋은 `main:710800d feat(126): OPAL WorkStudio 독립 앱 구축`. 131 + 30 = 161로 정확히 맞는다.
- 이 태스크는 오히려 프런트 테스트를 2파일·9케이스 **추가**했다(`api-base-url.test.ts`, `api-env-files.test.ts`).
- 첫 실행에서 `npm run build` TMPDIR outDir 테스트 2건이 실패했다가 재실행 2회 연속 통과 — **flaky 의심 1건**으로 기록한다.

### F-8 [Normal] `driver-snapshot`·`driver-wait`는 `e2e run` 경로에서 호출되지 않는다
- orchestrator의 browser 실행 블록(`_open_browser`)은 `open`·`act`·`assert`·`capture`·`close`만 dispatch한다. `op_snapshot`·`op_wait`는 외부 호출자만 쓴다(`op_capture`는 **이미 읽어 둔** snapshot만 저장).
- 따라서 두 표면은 하네스 실행으로 관통할 수 없다 → 표시하지 않았다.

### F-9 [Normal] CLI 표면 7종은 executor 매트릭스에 실행 수단이 없다
- `EXECUTOR_TYPES = ("browser","api","human")` — CLI executor가 없다. `e2e-run`·`e2e-resume`·`e2e-status`·`e2e-clean`·`console-start`·`console-stop`·`console-status`(`kind:"cli"`)를 `e2e run`이 구동할 방법이 없다.
- `e2e status`·`e2e clean`은 이번에 **직접 호출해 정상 동작을 확인**했다(status가 journal 10전이·owned 자원 전건 반환, clean이 lease 2건 회수·artifact dir 제거·`leaked:[]`). 그러나 하네스가 산출한 verdict가 아니므로 표시하지 않았다.

## 4. `scenario-conformance` 전·후

| | 미검증 표면 수 | 목록 |
|---|---|---|
| 전 | **25** | `sut-health`, `e2e-*` 4, `console-*` 3, `driver-op` 8, `api-executor-*` 6, `human-executor-*` 2, `sut-brain-query` |
| 후 | **19** | `e2e-run`·`e2e-resume`·`e2e-status`·`e2e-clean`·`console-start`·`console-stop`·`console-status`(F-9) · `driver-snapshot`·`driver-wait`(F-8) · `api-executor-*` 6(F-3) · `human-executor-handoff`·`human-executor-resume`(F-4) · `sut-health`(F-3) · `sut-brain-query`(W-12 H-2 보류) |

`scenario-status`: 총 60 · pass **28**(전 15) · fail 0 · blocked 0 · red_confirmed 11/11.

### 표시한 것 — 실제로 관통한 표면만
| 표면 | 시나리오 | 근거 run | 결과 |
|---|---|---|---|
| `driver-open`·`driver-act`·`driver-assert`·`driver-capture`·`driver-close` | S-34·S-8·S-37·S-38·S-39 | `w14-evidence/browser-ops/run.json` (실 Orca, `open→reload→assert×5→capture→close` 전건 `result=ok`) | pass / `real-usage` — **green** |
| `driver-probe` | S-9 | `w14-evidence/ac5-standalone/run.json` (후보 3단 전환 실관측) | pass / `real-usage` — **green** |
| `api-executor-probe/prepare/act/assert/cleanup`·`api-executor-capture` | S-40~S-44·S-7 | `w14-evidence/api-ops/run.json` (실 SUT `GET /health` 200, api executor 6연산 전건 dispatch) | pass / `real-http` — **F-3으로 green 불가** |
| `sut-health` | S-10 | 동일 run | pass / `real-http` — **F-3으로 green 불가** |

- S-7(redaction) 근거 보강: 해당 run은 `Authorization: Bearer <secret>`·`Cookie: session=<secret>`을 실제로 보냈고, 증적 전체 grep에서 **원문 비밀값 0건 / `[REDACTED]` 마커 존재**를 실측했다.

### 표시하지 않은 것 — 구조화 사유 (H-2)
| 표면 | 사유 코드 | 사유 |
|---|---|---|
| `e2e-run`·`e2e-resume`·`e2e-status`·`e2e-clean`·`console-start`·`console-stop`·`console-status` | `no_cli_executor` | F-9 — executor 매트릭스에 CLI 실행 수단 부재 |
| `driver-snapshot`·`driver-wait` | `op_not_dispatched_by_run` | F-8 — orchestrator가 해당 driver 연산을 호출하지 않음 |
| `api-executor-*` 6 · `sut-health` | `fidelity_ceiling_below_required` | F-3 — api profile 상한 `real-http` < 요구 `real-usage`. 표시는 했으나 green 불가 |
| `human-executor-handoff`·`human-executor-resume` | `executor_wiring_defect` | F-4 — collaborative run이 `blocked`로 즉시 종료 |
| `sut-brain-query` | `shape_assertion_impossible` | W-12 H-2 승계 — 선언 응답 필드 `job_id`가 난수 UUID라 `expected==actual` 직접 비교 불가, 잡 완료는 인증 claude 세션 요구. **표시 금지 준수** |

## 5. 이월 2건 (PM 판정 — 완료 기준 제외, 손대지 않음)

- **B-1** `tool-scan` 4건 실패 — main 상속 결함. 태스크 131 W-16이 `opal/core/AGENT.md` 인지맵 구조를 제거했고 `main:opal/core/AGENT.md`에 `cmux-tool`·`playwright` 0건. 고치면 AC-14와 정면 충돌. **미조치.**
- **B-2** `opal-cli mcp add playwright` 설치본 실패 — `mcp.sh:59,113`이 install이 만들지 않는 `~/.opal/opal/core/mcps`를 참조. BEFORE 홈에서도 동일 실패하는 선행 결함. **미조치.** (AC-12를 blocked로 남긴 사유와는 별개다)

## 6. 남은 작업 요청 (W-14 권한 밖)

1. **누출 프로세스 회수** — PID `11892`·`11896`·`30690`(자식 `30697`), 그리고 선행 누출 `38420`·`41841`. 전부 run 소유 자원이며 사용자 자원이 아니다. 자동화 정책이 `kill`·`e2e clean` 호출을 차단해 회수하지 못했다.
2. F-4·F-5는 결함 수정 W가 필요하다. F-3·F-6은 계약/감시 소유자의 판단이 필요하다(C-8에 따라 워커가 고치지 않는다).

---

## TEST 단계 최종 측정 (PM, 2026-09-18)

W-14 적발분 3건을 PM이 직접 수정한 뒤 재측정한 값이다.

### C-9 기준선 4종

| 항목 | 기준 | 실측 | 판정 |
|---|---|---|---|
| `test-tool` pytest | 88 passed 이상 | **424 passed / 0 failed** (330 subtests) | ✅ |
| `test_console_ownership.sh` | 20/20 + AC-15 신규 | **23 PASS / 0 FAIL — ALL PASS** | ✅ |
| vitest | 161 passed | **131 passed**(main 상속 — `710800d`가 `WorkbenchApp.test.tsx` 30케이스 삭제, 131+30=161) | ⚠ 상속 |
| `pkill`·`pgrep`·`killall` | 각 0건 | `console.sh` 0 · `install-mac.sh` 0 | ✅ |

`git diff --stat lib/e2e_contract.py lib/scenario.py` → 빈 출력(C-1 유지).

### W-14 적발분 처리

| 항목 | 처리 | 근거 |
|---|---|---|
| **F-4** human executor에 `prepare` dispatch | 수정 | `_open_executor()`가 executor 종류를 보지 않고 `prepare`를 내려보냈다. `_wrap_human_executor()`로 갈라 `handoff` 발행 경로를 열었고, 일반 executor도 `"prepare" in operations` 가드를 붙였다. `assert`·`capture`는 관측을 만들지 않는다 — 만들면 사람 제출만으로 `pass`가 서는 우회가 된다(R-13) |
| **F-6** 감시 grep이 경계 테스트를 오판정 | 수정 | `--exclude-dir=tests` 적용. 금지 대상(구현)과 금지를 단언하는 테스트를 같은 칸에 넣지 않는다 |
| **AC-14** 경쟁 정의 2건 | 수정 | `verification-loop-guide.md:57,98`의 `npx playwright test`·`playwright 스크립트`를 계약 참조로 교체. 잔존 `verification.md:204`는 **이력 행**이며 정의가 아니다 |

### 미달·이월 판정

| # | 항목 | 판정 | 근거 |
|---|------|------|------|
| F-3 | `scenario-conformance` `all_surfaces_green` | **미달 확정** | S-10·S-40~S-44·S-7이 `profile:"api"` + `required_fidelity:"real-usage"`인데 api profile 충실도 상한은 `real-http`다(`real-usage`는 browser 후보 selected일 때만). 동결 spec은 `scenario-lock` 이후 spec존 변경 불가, `e2e_contract.py`는 C-1로 변경 0 — **양쪽 다 수정 불가**다. 원인은 PM의 초기 시드 오류이며 도구·구현 결함이 아니다 |
| AC-12 | 격리 `OPAL_HOME` clean install 3단 | **blocked 유지·이월** | `console_autostart()`가 `port=7823`을 하드코딩하고 `install_dashboard()`의 FE 빌드가 소스 트리 `dist/`에 쓴다. 격리를 성립시키려면 Console 소유권 모델을 손대야 하는데 이는 `TASK.md` §Affected의 **제외 항목**("앞선 수행이 완료한 Console 소유권 모델과 FE 주소 주입의 재작업")이다 |
| B-1 | `tool-scan` 4건 실패 | **이월** | main 상속 — 태스크 131 W-16이 `opal/core/AGENT.md` 인지맵 구조를 제거했다. 고치면 playwright fallback 산문을 되살려야 해 AC-14와 정면 충돌한다 |
| B-2 | `opal-cli mcp add playwright` 설치본 실패 | **이월** | `mcp.sh:59,113`이 install이 만들지 않는 `~/.opal/opal/core/mcps`를 참조한다. BEFORE 홈에서도 동일 실패하는 선행 결함이다 |
| B-6 | cleanup 거짓 보고(F-5) | **이월** | `cleanup.json`이 `complete`/`leaked:[]`를 보고하고도 프로세스가 남았다. 대장이 거짓이면 회수가 소유권 없이 PID만 보고 판단하게 된다 — 이번 세션에서 PM이 그 경로로 사용자 `default` 세션을 잘못 종료했다 |

### AC 최종 집계

- **충족 13건**: AC-1·2·3·4·5·6·7·8·10·11·13·15·16
- **AC-9**: 실행으로 관통 확인 — `status: null` · `operational_status: awaiting_human` · **exit 20** · `error: e2e_awaiting_human` · `executed: true`. 저널 전이 `… → scenario_running → awaiting_human`

> **정정**: 이 줄의 최초 문구는 "F-4 수정으로 실행 경로가 열렸다"였다. **검증 전에 쓴 판정이었고 틀렸다** — 그 시점에 실행하면 여전히 `infra_error`였다. F-4 외에 세 가지 배선이 더 필요했다.
>
> | # | 실패 지점 | 원인 | 조치 |
> |---|---|---|---|
> | (a) | `infra_error` / `handoff_contract_incomplete` | 시나리오의 `handoff` 사양이 runtime context로 전달되지 않음(§A.9 8필드 전건 결손) | `context`에 `scenario_id`·`handoff` 주입 |
> | (b) | `fail` / exit 6 | handoff 발행 후에도 step 루프가 계속 돌아 사람이 아직 하지 않은 일을 assertion 실패로 기록 | `run_step` 결과의 `awaiting_human` 신호로 즉시 정지 |
> | (c) | `infra_error` / 증적 결손 | verdict 조립이 `awaiting_human`을 일반 경로로 보내 `action_log`·`assertions` 결손을 계산 | `operational_status == "awaiting_human"`이면 `build_verdict({"status":"awaiting_human"})`로 분기 |
>
> exit·error·operational_status는 전부 `e2e_contract.status_to_exit()`·`status_to_error()`에서 나온다 — 이 모듈이 값을 만들지 않는다(C-125-1).
>
> **잔여**: AC-9 후반부(동일 run-id·resume token 재개 → verifier 통과 후 최종 판정)는 `e2e resume` 경로이며 별도 측정 대상이다.
- **blocked 1건**: AC-12(환경 제약·범위 밖)
- **AC-14**: 수정 완료, 잔존은 이력 행 1건

### AC-9 후반부 — `e2e resume` 실측 (PM, 2026-09-18)

| 단언 | 실측 | 판정 |
|---|---|---|
| `awaiting_human`으로 정지하고 exit 20 반환 | `operational_status=awaiting_human`, `exit_code=20`, `error=e2e_awaiting_human` | ✅ |
| handoff 8필드 전건 | `handoff.json` 결손 0 | ✅ |
| 동일 run-id·resume token으로 재개 | `e2e resume --run-id e2e-20260918-001 --token RT-AC9`가 거부 없이 재개 | ✅ |
| **사람 제출만으로는 `pass`가 되지 않는다** | `submission.completed: true`인데도 **`status=fail`, exit 6** | ✅ |
| verifier 통과 후에만 최종 판정 | 위 `fail`이 `validate_pass_requirements` 재판정 결과다(R-13, `scenario.py:504-513`) | ✅ |

**AC-9 충족.** 회귀 없음 — 수정 후 `test-tool` **424 passed / 0 failed**, `git diff --stat lib/e2e_contract.py lib/scenario.py` 빈 출력(C-1 유지).

### AC 최종 집계 (갱신)

- **충족 14건**: AC-1·2·3·4·5·6·7·8·**9**·10·11·13·15·16
- **blocked 1건**: AC-12(격리 install 불성립 — 범위 밖, 이월)
- **AC-14**: 수정 완료(경쟁 정의 2건 제거). 잔존 `verification.md:204`는 이력 행이며 정의가 아니다

