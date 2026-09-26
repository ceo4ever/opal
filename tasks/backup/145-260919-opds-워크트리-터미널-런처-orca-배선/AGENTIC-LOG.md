# AGENTIC-LOG — 145 워크트리 전용 터미널 런처 orca 경로 배선

> 모드: agentic (2026-09-19 14:30 전환, 이전 semi-agentic) | 판단 주체: 알투[PM]

## GATE: TASK 사용자 확인 — auto-approved

- 근거: 캡틴이 TASK 범위를 2회 직접 검토하고 수정 지시(handoff.json 철회, 복귀 통지 포함)를 반영한 뒤 `--agentic` 전환을 승인했다.
- 확인 항목: sdlc-v2 5절 충족(`state-tool verify --clarification-check` pass), Acceptance criteria 10건이 전부 관측 가능한 형태.
- 판정: Pass.

## 결정 기록

| # | 결정 | 근거 |
|---|---|---|
| D-1 | `handoff.json` 캡슐 파일 도입 철회, 시작 발화는 기동 명령 argv가 소유 | 태스크 식별은 워크트리 1:1 + `state.json` + 부트스트랩 브리핑이 이미 해결. SessionStart hook은 컨텍스트를 주입하지 않으며 파일은 첫 턴을 유발하지 못한다 |
| D-2 | 어댑터는 상속 계층 없이 덕타이핑 seam 유지, 동사 3종·보고 스키마만 표준화 | OPAL 도구는 모듈 함수 스타일이고 orca·cmux는 공유할 공통 구현이 없어 빈 ABC만 남는다 |
| D-3 | 이번 범위는 orca 어댑터 하나 | 캡틴 지시. cmux·generic은 계약 확장 가능한 형태로만 둔다 |
| D-4 | 복귀 감지를 범위에 포함하되 새 통지 채널 없이 registry `attribution_state` 조회로 한정 | 기존 SSOT만 읽으므로 축이 늘지 않는다 |

## 이슈: 3행(PLAN 작업) 조기 마킹

- 2026-09-19 14:5x, PM이 opal-plan-agent 디스패치 직후 3행을 `done`으로 마킹했다. 워커는 아직 실행 중이었다.
- `state-tool`에 ✅→⬜ 역전이가 없어 되돌릴 수 없다. 워커 결과 수신 시 PM Gate(5행)에서 실산출물로 판정하고, 워커가 실패하거나 PLAN.md가 부재하면 3행을 `block`으로 전환해 사실을 맞춘다.
- 재발 방지: 워커 디스패치는 비동기다. 작업 행 마킹은 **결과 수신 후**에만 수행한다.

## GATE: PLAN 워커 결과 1차 검토 (3행)

- 산출물 `PLAN.md` 83행 직접 Read 완료. AC-1~AC-10 전건이 Work item에 연결됨을 표에서 직접 확인(AC-1→W-6, AC-2→W-1·W-4·W-8, AC-3→W-6·W-11, AC-4→W-5, AC-5→W-9·W-11, AC-6→W-3, AC-7→W-2·W-6, AC-8→W-4·W-7·W-8·W-10, AC-9→W-3, AC-10→W-3·W-11).
- 3행 조기 마킹은 결과적으로 사실과 일치한다(PLAN.md 실재·계약 검증 통과). `block` 전환 불필요.

### 설계 이탈 승인: D-I (스텝 4.5 → 스텝 5.5 신설)

- 디스패치 프롬프트는 배선 지점을 "스텝 4.5 `ok: true` 경로"로 지정했으나 워커가 스텝 5.5 신설로 변경했다.
- **승인.** 근거를 직접 확인했다 — `task-process.md`에서 워크트리 생성은 4.5, `state init`은 스텝 5다. 4.5에서 기동하면 워크트리 세션의 첫 턴이 읽을 `state.json`이 아직 없다. 5.5 비차단 규율도 4.5 `ok: false`의 기존 폴백 규율 승계라 새 게이트를 만들지 않는다.

### 승인하되 기록하는 저하: D-A의 receipt 독립성

- `launch_receipt`·`prompt_receipt` 2종은 원래 "터미널이 떴다"와 "프롬프트가 제출됐다"를 **독립 관측**으로 요구하는 가드였다. D-A는 둘 다 같은 `orca terminal create` 1회 관측에서 파생하므로 2중 가드가 1중으로 붕괴한다.
- 그럼에도 승인한다 — 폐기 대안(lease 폴링)은 `run()` 블로킹·플레이키·AC-4 실패 표면 확대를 대가로 요구하고, PLAN이 H-3에서 이 한계를 숨기지 않고 "첫 턴 자기시작은 W-11 실물 관측으로만 확정"으로 분리했다.
- **조건**: W-11 실물 완주 관측을 이 저하의 유일한 보상 관문으로 삼는다. 단위 테스트 통과만으로 AC-5를 충족 처리하지 않는다.

### 미충족: TEST-SCENARIO 부재

- 5행 PM Gate가 요구하는 산출물 3종 중 `TEST-SCENARIO.md`가 없다. 4행 목표-커버 게이트도 이 산출물을 소비한다.
- 원인은 워커가 아니라 PM의 디스패치 범위 지정("PLAN.md 1건")이다. 후속 디스패치로 보완한다.

## GATE: PLAN 목표-커버 게이트 (4행) — pass

- 결정론 증거: `test-tool scenario-coverage-check` → `all_covered: true` (requirements 20 / features 0 / hypotheses 6 / scenarios 15).
- 판단 증거: `opal-evaluator-agent` `scenario-rubric` verdict `pass` — goal 2 / adoption 2 / boundary 2, 평균 2.0, gaps 0.
- 두 증거가 모두 성립해 `scenario-gate.md` §통과 증거를 충족한다. `.scenario-gate-history.json` iteration 1 기록.
- Producer(PM) ≠ Evaluator(opal-evaluator-agent) 분리 유지.

### 평가자 비차단 관찰의 게이트 조건화

- S-10·S-11은 `OPAL_LIVE_ORCA=1` + `orca` PATH opt-in이라 skip될 수 있다. 목표축의 유일한 관문이 skip 가능하다는 지적을 수용한다.
- **TEST 단계 조건**: S-11을 `skip`이 아닌 `pass`로 실제 실행한 로그와, S-11이 요구한 관측 증거(명령·스코프·출력)의 태스크 폴더 기록이 둘 다 있어야 AC-3·AC-5를 충족 처리한다. 둘 중 하나라도 없으면 TEST PM Gate를 Fail로 판정한다.

## GATE: PLAN PM Gate (5행) — pass

| 검사 | 결과 |
|---|---|
| TASK/PLAN/TEST-SCENARIO frontmatter `template: sdlc-v2` | 3종 전건 확인 |
| AC/C → Work items 완료 기준 연결 | AC-1~AC-10·C-1~C-10 전건 매핑 (PM 직접 대조) |
| `state-tool verify --plan-contract-check` | `pass`, W-1~W-11 |
| PLAN Risks 절 | H-1~H-6 존재 |
| PLAN Release and recovery 절 | 존재 (P1~P5 순서·배포 선행 조건·롤백 경로) |
| TEST-SCENARIO Setup/Scenarios + op-scenario-gate | 존재 + verdict `pass` |
| `state-tool verify --code-scan-citation-check` | `pass` |

## GATE: PLAN 사용자 확인 (6행) — auto-approved

- 근거: 캡틴이 `--agentic`을 명시했고, PLAN 범위의 모든 쟁점(handoff 철회·orca 한정·복귀 통지 포함·비-orca 환경 무변경)을 이 세션에서 직접 확인하고 지시했다.
- CLOSE 진입 승인은 모드와 무관하게 캡틴이 소유한다(`guards.md` §CLOSE 진입 게이트) — 자동 승인 대상이 아니다.

## EXECUTE P1 — W-1 완료 (PM 직접)

- 임시 워크트리 `task_997`을 만들어 `orca terminal create|read|close --json` 각 1회 실행, stdout 원문을 캡처했다(2026-09-19 15:03 KST, orca 1.4.205, darwin).
- fixture 3종 교체: `orca-json-response.json`(가정 스키마 → 실측) · `orca-terminal-read-response.json`(신규) · `orca-terminal-close-response.json`(신규). 워크트리 경로 성분만 `{WT}`로 치환하고 각 파일에 `_captured_at`·`_orca_version`을 기록했다.
- `fixtures/README.md`의 "stdout 스키마는 미실측" 행을 실측 사실로 교체했다.
- **결함 재확인**: 교체 전 fixture는 `{"ok":true,"terminal":{"handle":"orca-term-0001","worktree_selector":...}}` — 실물에 없는 `worktree_selector` 키를 가진 가정 스키마였다. 이것이 목킹 전용 검증이 결함을 통과시킨 물증이다.
- **H-1 완화 확인**: 실측 `worktreeId`의 `repoId` 성분(`ce5d0068-fabe-451d-b68d-5604d6495c34`)에 `::`가 없어 첫 `::` 1회 분리가 성립한다.
- **H-6 변동 관측**: 이번 캡처에서는 Orca 자동 fallback 탭이 생기지 않았다(`close --all` → `closed: 0`). 앞선 목업 998에서는 1개가 생겼다 — 자동 탭 존재가 환경·타이밍에 따라 달라진다는 H-6이 실측으로 확인됐고, D-C의 2스코프 분리가 이 변동을 흡수한다.
- 정리 완료: 터미널 0개, 워크트리·브랜치·메타 회수, `git worktree list`에 `main`과 `task_142`만 남음.

## EXECUTE P1 — W-2 검토 Pass

- PM 직접 재실행: `pytest tests/test_settings.py -q` → **21 passed**. 워커 보고(RED 3 failed/18 errors → GREEN 21 passed)와 일치.
- `setting.default.json` 직접 확인: `launcher` 블록에 `adapter` 키 **부재**(D-E 준수), `_help`에 `models` 미설정 중단과의 비대칭 근거 문장 존재(D-F·C-9 충족).
- 경계 준수 확인: `worktree_tool.py`·`adapters/`·`launcher_core.py`·`cli.py`·`run.sh` 무수정.

### 워커 제기 항목 판정: `resolve_command` 반환이 셸 문자열

- **결함 아님.** `orca terminal create --command <text>`의 `--text`는 터미널 셸이 실행하는 **명령 문자열**이므로 argv 리스트가 아니라 문자열이 옳다. PM이 대화 중 "argv는 배열로"라고 조언했던 것은 generic 어댑터(`shlex.split` 소비)를 전제한 것이고, orca 경로에는 적용되지 않는다.
- **잔여 리스크(기록만)**: `argv_template`의 `"{utterance}"` 인용은 `{task_path}`에 큰따옴표가 섞이면 깨진다. 태스크 폴더 규칙이 공백을 금지하고 따옴표는 실무상 등장하지 않아 이번 범위에서 방어 코드를 넣지 않는다. 이름이 `argv_template`인데 값이 셸 문자열인 불일치도 같은 이유로 이번에 바꾸지 않는다(W-10 README에 형태를 명시하는 것으로 대체).

## EXECUTE P1 — W-3 검토 Pass / P1 완료

- PM 직접 재실행: `pytest test_worktree_tool.py -q` → **146 passed in 110.28s**. 워커 보고와 일치하고 기존 145건 대비 회귀 0건.
- 소스 직접 확인: 스윕 호출이 `check_guards` 루프 **직후**·`git worktree remove` 루프 **직전**에 있고 주석에 근거가 명시돼 있다(D-H 준수).
- `cmd_status`는 additive 분기로 `attribution_state` + `completed_unmerged` 하나만 추가했고 legacy는 판정에서 제외된다(D-G 준수).
- 테스트 설계 승인: 가짜 `run.sh`의 probe 파일로 **호출 시점**(worktree 경로 실재 `yes`)과 **미호출**(probe 부재)을 증명한 방식은 mock 없이 실 subprocess 경계를 유지하므로 이 파일의 기존 규율과 일치한다.
- **P1 완료** — W-1(PM 직접) · W-2 · W-3 전건 Pass.

## EXECUTE P2 — W-5 검토 Pass (조건부) + 워커 제기 2건 판정

- PM 직접 재실행: `pytest opal/tools/worktree-launcher/tests/ -q` → **55 passed**. 워커 보고(기준선 5 → RED 5 failed/6 passed → GREEN 11, 스위트 55)와 일치.
- 제약 확인: `launcher_core`에 registry 직접 쓰기 0건(C-5), 신규 class·ABC 0건(C-2).

### 판정 1 — S-4 문면과 안전 규칙의 충돌: 워커 해석 채택

- `adapter_report_invalid`는 보고가 dict가 아니어서 `adapter_handle` 원천 자체가 없다. PLAN W-5의 "대상을 추측하지 않는다"가 S-4의 "4경로 전건" 문면보다 우선한다.
- 구현은 그대로 두고 **TEST-SCENARIO S-4 문면을 PM이 정정**했다("handle이 실재하는 복귀 경로 전건"). 커버리지 축(AC-4)은 변하지 않으므로 게이트 재실행 대상이 아니다.

### 판정 2 — 5번째 복귀 경로 `ownership_set_rejected`: 확장 승인

- `launcher_core.py:310`은 터미널이 **확실히 살아 있는** 복귀 경로인데 정리하지 않아 고아를 남긴다. W-5의 목적(AC-4 "고아 터미널 0")을 직접 위배한다.
- PRINCIPLES §3 위반이 아니라고 판단한다 — 인접 코드 개선이 아니라 **같은 함수·같은 결함 유형**의 열거 누락이다.
- 워커에게 재디스패치: 기존 `_close_terminal()`·`terminal_close` 스키마 재사용, 전용 테스트 1건 추가, 변경 범위 2파일 유지.
- TEST-SCENARIO S-4 조건도 "복귀 5경로"로 함께 정정했다.

## EXECUTE P2 — W-4 검토 Pass + 워커 제기 2건 판정

- PM 직접 재실행: `pytest opal/tools/worktree-launcher/tests/ -q` → **56 passed**(W-5 보완분 랜딩 포함). 구형 토큰 grep **0건**.
- 워커 보고(RED 13 failed/3 passed → GREEN 16, 회귀 55)와 일치.

### 판정 1 — `read` 플래그: 워커의 실측 채택 (PM 디스패치 문면이 틀렸다)

- PM이 프롬프트에 적은 `--scrollback`·`--lines`는 **오기**였다. `orca terminal read --help` 직접 확인 결과 실제 플래그는 `--cursor <n>`·`--limit <n>`·`--screen`이고, PLAN 시그니처 `read(handle, *, cursor, limit, screen)`와 1:1로 맞는 쪽도 실측이다.
- 워커가 PM 문면 대신 실측을 채택한 것은 옳다. 이 태스크의 근본 원인이 "실측 없이 가정한 스키마"였으므로, 문면 추종이 아니라 실측 우선이 이 태스크의 규율이다.
- `--screen`과 `--cursor`의 상호 배타 처리도 orca 선언을 따른 것으로 승인한다.

### 판정 2 — `close` 미지정 2조합을 실패로 확정: 승인

- (a) `worktree_root`만 + `all=False`, (b) `handle` + `all=True` → `close_scope_invalid`, exit 64, orca 미호출.
- orca 문법이 `--worktree <selector> --all`만 받으므로 문법상 성립하지 않는 argv를 만들지 않는 것이 옳다. S-13의 4조합을 좁히는 것이 아니라 **문법 밖 조합을 추가로 닫는** additive 강화다.
- `_closed_handles()`가 스윕 응답 형태를 추측해 채우지 않고 S-10(live)로 미룬 판단도 이 태스크의 규율과 일치한다.

- **P2 완료** — W-4 · W-5 Pass(W-5 5번째 경로 보완분 반영됨).

## EXECUTE P2 — W-5 보완분 Pass / P2 완료

- 5번째 복귀 경로(`ownership_set_rejected`) 배선 완료. RED 1 failed/11 passed → GREEN 12, 스위트 56 passed(PM 직접 실행으로도 56 확인).
- 배선은 `_revert(...)` 호출에 `adapter=adapter, report=report`를 추가한 것뿐이고 `_close_terminal()` 본문은 한 줄도 바뀌지 않았다 — 새 분기·새 스키마 0건이라는 요구를 지켰다.
- 테스트 설계 승인: `ownership_set` seam만 monkeypatch해 전이 거부를 주입하고 **복귀 전이는 실제 subprocess에 위임**했다. `worktree_tool.py`를 동시 수정 중인 다른 워커와의 크로스 플레이키를 피하면서도 registry 최종 상태 단언이 실제 쓰기 경로의 증거로 남는다.
- **P2 완료** — W-4 · W-5 Pass.

## EXECUTE P3 착수

- W-6(CLI 표면) · W-7(적합성 스위트) · W-8(live 대조 1건) 병렬 디스패치.
- W-8에는 **live 실행 금지**를 명시했다 — 실제 터미널 생성은 PM이 P5에서 증거와 함께 수행하고, 워커는 skip 경로만 확인한다. 워크트리 신규 생성도 금지(태스크 번호 소모·허브 registry 변경 방지).

## EXECUTE P3 — W-8 검토 Pass

- PM 직접 재실행: `env -u OPAL_LIVE_ORCA pytest tests/test_adapter_orca.py -q` → **16 passed, 1 skipped**. 기존 16건 무변경.
- live 테스트 안전성 소스 직접 확인:
  - `finally`에서 `close(handle=…)` **정밀 1개**만 호출하고 `--worktree … --all` 스윕을 쓰지 않는다(사용자 탭 보호).
  - close 결과 단언을 `finally` **밖**에 둬 원래 예외를 가리지 않는다.
  - 대상 워크트리는 `OPAL_LIVE_ORCA_WORKTREE` 또는 `orca worktree list --json`의 레포 루트 일치 항목으로만 정하고, 못 찾으면 skip한다 — 경로 문자열 추론 0건, 워크트리 신규 생성 0건.
  - `LIVE_COMMAND`가 `printf`라 에이전트를 띄우지 않는다.
- 지시 준수 확인: live 실행 0회, 읽기 전용 orca 호출만 수행.

## EXECUTE P3 — W-6·W-7 검토 Pass / P3 완료

- PM 직접 재실행: `pytest opal/tools/worktree-launcher/tests/ -q` → **110 passed, 1 skipped**. `run.sh`의 `not_implemented` 문자열 **0건** 확인.
- W-6: 폐쇄 목록 `SUPPORTED_ADAPTERS = {"orca": …}` 하나뿐이고 목록 밖 이름은 import를 시도조차 하지 않는다(AC-1 충족). `--adapter` 누락(`adapter_required`)과 목록 밖(`adapter_unsupported`)을 서로 다른 안정 코드로 분리한 것은 계약 강화이므로 승인한다. argparse usage 누수를 `invalid_arguments` JSON + exit 1로 막은 것도 단일 라인 JSON 계약을 지키는 올바른 처리다.
- W-6 경로 추측 금지 확인: `--command` 미지정 시 registry canonical `task_path`만 쓰고, 없으면 `--worktree-root`로 대체하지 않고 `task_path_unresolved`로 거부한다(worktree.md §발급 계약 준수).
- W-7: 어댑터 등록이 상단 상수 2개(`CONFORMANCE_ADAPTERS`·`ADAPTER_FIXTURES`)에만 있어 새 어댑터 추가가 실제로 1줄이다(AC-8 충족). C-4 정적 검사를 **docstring 제외 AST**로 구현한 판단을 승인한다 — orca.py @header가 금지 문구를 서술로 담고 있어 순진한 grep은 오탐이 난다.

### PM 직접 보완 1건: `orca.name` 노출

- W-6이 보고한 사실 — `launcher_core.run()`은 `getattr(adapter, "name", None)`을 읽는데 `orca.py`에는 `ADAPTER_NAME`만 있었다. 정상 경로는 보고 dict의 `adapter` 키가 이름을 채우지만, 보고가 dict가 아닌 `adapter_report_invalid` 복귀에서는 그 키에 도달하지 못해 **어댑터가 망가졌을 때 정확히 어느 어댑터인지 잃는다**.
- PM이 `orca.py`에 `name = ADAPTER_NAME` 1줄과 근거 주석을 추가했다. 계약 변경 0건(README가 `name`을 선택 seam으로 이미 선언). 재실행 110 passed, 1 skipped 유지.

### 기록만: W-7의 C-1 검사 한계

- `test_c1_out_of_scope_adapters_are_untouched`는 `git status --porcelain` 기반이라 **커밋 이후에는 자동 통과**한다. working tree 구간에서만 강한 검사다.
- merge-base diff 대조로 강화하는 것은 이번 범위 밖으로 둔다 — C-1의 본래 목적(이번 태스크에서 범위 밖 어댑터를 건드리지 않음)은 working tree 구간에서 충족된다.

- **P3 완료** — W-6 · W-7 · W-8 Pass.

## EXECUTE P4 — W-9 완료 (PM 직접)

- `task-process.md`:
  - 4.5 `ok: true` 목록에 "워크트리 전용 터미널 기동은 여기서 하지 않는다 — 스텝 5 완료 후 5.5에서 수행한다" **1줄만** 추가(명령 블록 중복 0건, grep으로 확인).
  - **스텝 5.5 신설** — `worktree-launcher/run.sh launch` 명령 블록과 규율 7개를 5.5가 단독 소유한다: state init 이후 기동 [MUST], `--adapter` 필수·자동 폴백 없음, `--command` 생략 시 설정 결정, 시작 발화는 argv 소유, 실패 비차단(허브가 이어감), 성공 시 writer 이전, 어댑터 미구성 환경은 워크트리만 생성.
  - §`--wt` 체크포인트 커밋과 merge 경계에 6항 추가 — 회수 시 터미널 스윕 선행과 `completed_unmerged` 복귀 판정.
- `worktree.md`: §실행 세션 기동과 터미널 회수 경계 1개 절 추가. 국면×주체×경계 5행 표 + [MUST] 2건. 절차 원문은 `task-process.md`를 가리키고 복제하지 않는다.
- **C-8/S-15 자기검사**: 신설·수정 절에 "merge를 워크트리에서 수행" 취지 문구 **0건**. merge 승인 경계는 `guards.md` 포인터로만 두고 규정 원문을 복제하지 않았다(초안의 재서술 1행을 포인터로 교체).

## RED-first 원장 기록 (절차 이탈 1건, 사실대로 기록)

- `test-scenario.json`에 RED 대상 9건(S-1·S-2·S-3·S-4·S-5·S-6·S-7·S-8·S-13)의 RED 증거를 기록하고 `scenario-lock`을 통과시켰다(`locked: true`, 15시나리오 / red_confirmed 9 = red_required 9).
- **이탈**: 원장 기록 시점이 GREEN 이후다. 계약은 "RED 관측 → `scenario-red` 기록 → `scenario-lock` → GREEN 구현" 순서인데, PM이 워커들에게 RED-first를 프롬프트로만 강제하고 도구 기록을 각 워커 완료 후로 미뤘다.
- **증거 자체는 실측이다** — 각 워커가 구현 전에 실제로 실패를 관측하고 수치와 실패 원인을 보고했고(예: W-6 `20 failed, 5 errors, passed 0`, W-5 `KeyError: 'terminal_close'`), 그 원문을 `--evidence`에 그대로 실었다. 사후 합리화가 아니다.
- **재발 방지**: `scenario-init` → `scenario-red` → `scenario-lock`은 EXECUTE **첫 워커 디스패치 전에** 끝내야 한다. RED 관측 자체를 워커에게 맡기면 원장이 항상 늦는다.

## EXECUTE P4 — W-10 검토 Pass / P4 완료

- PM 직접 검사: README에서 stale 3종(`후속 Work item`·`한 메서드만`·`not_implemented`) **0건**, 수기 변경이력 절 **0건**(`.opal/AGENT.md` §금지사항 준수).
- 워커가 서술 전건을 코드와 1:1 대조한 방법(파일 목록 `find`, 오류 코드 `_fail()` 호출부 전수, 보고 스키마 반환 dict 키, 복귀 5경로 `_revert()` 호출부 detail 문자열, 설정은 `setting.default.json` 파싱 값 대조)을 승인한다 — 이 태스크의 근본 원인이 "문서가 코드와 어긋난 채 방치됨"이므로 대조 방법 자체가 산출물의 일부다.
- 잔존 grep 1건(`close seam 미구현(AttributeError)`)은 `_close_terminal`의 실제 분기를 가리키는 정확한 서술이라 stale이 아니다 — PM 확인 완료.
- **P4 완료** — W-9(PM 직접) · W-10 Pass.

## P5 진입 전 차단: 배포 승인 필요

- PLAN §Release and recovery: "P4 완료 후 `./scripts/install-mac.sh`로 재배포한 뒤에만 P5에 진입한다 — 스텝 5.5는 배포본 `~/.opal/tools/worktree-launcher/run.sh`를 호출하므로 배포 전 검증은 무의미하다."
- [MUST] `opal/core/references/harness/guards.md` §독립 검증 경계: 배포는 "직접 수행 선택은 작업 방식 승인일 뿐"인 항목 목록에 포함된 **별도 승인 경계**다. agentic 모드도 이 경계를 해제하지 않는다.
- 따라서 PM은 여기서 멈추고 캡틴의 배포 승인을 받는다. 이것은 자율 진행 위반이 아니라 guards가 명시한 승인 경계다.

## S-12 회귀 판정 pass (AC-10)

| 스위트 | 결과 |
|---|---|
| `worktree-launcher/tests` | 110 passed, 1 skipped (live opt-in) |
| `worktree-tool/tests` | 146 passed in 120.11s (기존 145 대비 실패 0) |
| `state-tool/tests` | 535 passed, 3 skipped, 339 subtests in 365.05s |

- 스위트별 병렬 실행(한 호출로 합치면 conftest 충돌). `--wt` 미사용 경로의 실패·skip 증가 0건.

## EXECUTE P5 — W-11 실물 완주 완료 (PM 직접)

- 배포는 캡틴이 직접 수행했다. PM은 소스 트리 밖에서 배포본을 검증했다 — `~/.opal/tools/worktree-launcher/`에 `cli.py`·`settings.py` 존재, `run.sh`의 `not_implemented` 0건, CLI가 `invalid_arguments` JSON 반환.
- **AC-3 충족**: 목업 `task_996`에서 `worktree_session_owned` 전이 + receipt 2종 registry 객체 기록.
- **AC-5 충족**: 워크트리 터미널 상태줄이 `task_996 │ feat/OP-TASK-996 │ 🎯 996`을 표시하고, 사람 입력 0회로 첫 턴이 시작·완료(`Brewed for 1m 10s`)됐으며 PostToolUse hook 3종이 발화했다.
- **AC-4 부분**: 실패 주입(`PATH`에서 orca 제거)에서 `hub_owned` 복귀·`generation` 증가·receipt 소거·터미널 0개. 단 이 경로는 터미널이 생성된 적이 없어 "이미 만든 터미널 정리"는 S-4 단위 증거가 소유한다.
- **AC-6 충족**: 클린 워크트리 `task_994` 회수에서 `terminals_closed.exit_code = 0`, 잔존 0개. dirty `task_996`은 가드에서 거부돼 스윕에 도달하지 않았고 그 시점 터미널 1개가 그대로였다(H-4 실측).
- **AC-7 보강**: 배포본 `~/.opal/setting.json`에 `launcher` 블록이 **없는 상태**로 실행돼 코드 기본값 폴백(D-F)이 실경로에서 성립함을 확인했다.
- 정리 완료: 목업 3건(994·995·996) 워크트리·브랜치·메타·터미널 전부 회수. `git worktree list`에 `main`과 `task_142`만 남는다.
- 증거 원문: `evidence/S-11-live.md`.

### 실측으로 드러난 발견 3건 (이번 AC 밖 — 후속 후보)

1. **`owner_session_id`가 `None`으로 남는다.** 허브가 launch 시점에 새 세션 id를 알 수 없다. registry 전이는 receipt 2종만 요구해 성공하지만, `worktree-tool checkpoint`는 `owner_session_id == OPAL_SESSION_ID`를 요구하므로 **워크트리 세션이 자율 체크포인트 커밋 자격을 얻지 못한다.**
2. **`--worktree … --all` 스윕의 `closed`가 항상 비어 있다.** orca가 실제로는 닫으면서 `closed: 0`을 보고한다(raw CLI로도 재현). 판정은 `terminal list` 재조회로 해야 한다.
3. **실행 중인 에이전트 TUI 스윕에서 orca가 비-0을 반환한다.** `task_996` `--force` 회수에서 `close_failed`/`orca_nonzero_exit` 경고가 났지만 실제로는 닫혔고 회수도 성공했다 — H-5의 비차단 설계가 의도대로 작동했으나 경고가 false negative다. `sleep` 프로세스에서는 exit 0이었다.

- **EXECUTE 완료** — 시나리오 15/15 pass, RED 9/9 confirmed, locked.

## TEST — 독립 검증 수신 및 PM Gate

- `opal-test-agent`가 `TEST.md`를 산출하고 **All Pass(15/15)** 판정. 재실행 수치가 PM 수치와 일치한다 — launcher 110 passed/1 skipped, worktree-tool 146 passed in 111.28s, 구형 토큰 0건. S-9·S-14·S-15 정적 주장도 git diff·AST·테스트 본문으로 직접 재확인했다.
- AC-1~AC-10 **역방향 대조**(AC→시나리오) 전건 성립 확인.

### 검증자가 잡아낸 증거 품질 결함 1건 — 수용

- **S-3의 RED 증거는 실제 관측이 아니다.** W-7(적합성 스위트)은 P3에서 디스패치돼 W-4 GREEN(P2) **이후**에 작성됐으므로 구현 전 실패를 관측한 적이 없다. PM이 원장에 적은 "W-4 GREEN 전 상태 기준" 표현은 사후 추론(counterfactual)이었다.
- 나머지 8건의 RED 증거는 각 워커의 실제 보고 수치와 대조 가능해 실측 인용으로 확인됐다(검증자 판정).
- **정정 시도와 결과**: `scenario-red`로 S-3 증거를 정정하려 했으나 `scenario_already_locked`로 거부됐다. 원장은 lock 이후 불변이며 이것이 정상 동작이다 — 따라서 정정은 이 로그와 `TEST.md`가 소유한다. **S-3의 유효한 증거는 GREEN 결과(29 passed)뿐이며 RED 근거는 없다.**
- 게이트를 뒤집지 않는 이유: S-3의 검사 대상(적합성 7항목)은 현재 코드에서 실제로 통과하고, AC-8은 S-3 외에 S-2·S-10·S-13이 함께 덮는다.
- **재발 방지(재확인)**: RED 원장은 EXECUTE 첫 디스패치 **전에** 확정해야 한다. 스위트를 나중에 신설하면 그 스위트는 구조적으로 RED를 관측할 수 없다.

## GATE: TEST PM Gate (9행) — Pass

| 검사 | 결과 |
|---|---|
| `test-scenario.json` 전 시나리오 PASS | 15/15, locked, red 9/9 |
| 실제 실행 증거 | 독립 검증자 재실행 수치가 PM 수치와 일치 |
| S-11 skip 아닌 실행 | `evidence/S-11-live.md`에 명령·응답·registry·터미널 stdout 기록 확인 (사전 조건 충족) |
| AC 역방향 대조 | AC-1~AC-10 전건 시나리오 대응 |
| 독립 검증 경계 | 생성자(PM) ≠ 평가자(opal-test-agent) 분리 유지 |
| 증거 품질 | S-3 1건 결함 수용·기록. 게이트 판정에는 영향 없음 |
