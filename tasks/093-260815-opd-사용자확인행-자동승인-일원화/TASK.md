# TASK: 파이프라인 사용자 확인 행 — 자동 승인 경로 일원화

> 작성일: 2026-08-15 | 작업 유형: 개선 | 적용 스킬: opd | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

파이프라인 "사용자 확인" 행의 상태 전이를 **미확인(pending) → 자동 승인(done/auto) 또는 캡틴 승인(done/user)** 단일 축으로 일원화한다. 현재 agentic 모드에만 존재하는 init 시점 `na` 소거 경로를 제거하고, 다음 단계 진입 시 도구가 자동 승인을 수행하도록 배선한다.

## 배경

캡틴이 규정한 사용자 확인 행의 의도는 3조다.

1. 기본적으로 **사용자가 확인하지 않은 상태**로 초기화된다.
2. 해당 단계 진행 중 에스컬레이션이 필요 없고 다음 단계로 넘어가면 **자동 승인된 것으로 마킹**한다.
3. 사용자 확인이 필요한 경우에는 **보고 → 승인 수령**을 거친다.

이 3조는 하네스 문서상 규범이지만, `state-tool` 구현이 규범대로 되어 있지 않다. 특히 2)의 "다음 단계 진입 시 자동 승인"이 구현되어 있지 않고, 그 자리를 agentic 전용 우회(`na` 소거)가 대신하고 있다. 그 결과 모드에 따라 같은 명령이 다르게 실패하고, 같은 행의 최종 상태가 `na`와 `done`으로 혼재한다.

## 배경 분석 (대화에서 도출)

PM이 태스크 092 진행본(현 HEAD)을 직접 실측한 결과다.

### (1) `na`의 정체 — 자동 승인이 아니라 가드 회피용 소거

- init 시 agentic 모드에 한해 `사용자 확인` 행을 `status=na / owner=auto`로 생성한다 (`opal/tools/state-tool/state_tool.py:825-829`, `:917-921`, `:1051-1055` — 빌더 3곳 동일 분기).
- `na`는 완료 상태 집합에 포함되어 단계 건너뛰기 가드를 통과시킨다 (`opal/tools/state-tool/state_tool.py:456`).
- `na`는 todo 미러 집계에서 중립 제외된다 (`opal/tools/state-tool/state_tool.py:481`).
- 결과적으로 `timestamp`가 `null`로 남아 **자동 승인 이력이 기록되지 않는다**. 캡틴 3조의 1)·2) 모두와 어긋난다.

### (2) 조항 2가 구현되어 있지 않음

- 자동 승인은 오직 PM의 명시 호출(`mark --auto-pass`)로만 발생한다 (`opal/tools/state-tool/state_tool.py:1560-1568`).
- 다음 단계 진입 시점에 앞 단계의 미완 사용자 확인 행을 처리하는 훅은 존재하지 않는다.
- `check_stage_transition_guard`는 앞 행이 미완이면 `stage_transition_violation`으로 차단한다 (`opal/tools/state-tool/state_tool.py:492`).
- 따라서 PM이 `--auto-pass` 호출을 누락하면 다음 단계 진입이 막힌다. 이것이 캡틴이 관측한 "가끔 작동이 안 된다"의 직접 원인이다.

### (3) 같은 행에 진입 경로가 3개인데 상호 계약이 없음

| 경로 | 결과 상태 | 현재 상태 전제조건 |
|------|----------|------------------|
| init auto-na (agentic) | `na / auto` | — |
| `mark --auto-pass` | `done / auto` | **없음** |
| `mark --owner user` | `done / user` | **없음** |

- `mark`에는 현재 상태 전제조건이 전혀 없어 `na → done` 덮어쓰기가 무검증 통과한다 (`opal/tools/state-tool/state_tool.py:1474-1524`).
- 반면 `advance`는 `pending`만 허용하고 그 외는 거부한다 (`opal/tools/state-tool/state_tool.py:1420-1423`). agentic에서 사용자 확인 행에 `advance`를 호출하면 항상 실패한다.
- 멱등성이 없어 동일 행 재-mark 시 note 접두가 누적된다 (`opal/tools/state-tool/state_tool.py:1563-1568`). 실측 사례: 태스크 092 `state.json` rows **5·8·11**의 note가 `agentic auto-pass: agentic auto-pass: …`로 이중 접두 — **3건**이다.
  > [PM 정정 2026-08-15 20:14] 최초 작성 시 2건(rows 5·8)으로 기재했으나, ANALYSIS 단계에서 전수 스캔한 결과 row 11(TEST-SCENARIO 사용자 확인)까지 3건임을 확인했다. F-5 회귀 시나리오는 3건 전부를 커버한다.

### (4) CLOSE 게이트가 auto-na와 충돌

- `check_close_gate`는 직전 사용자 확인 행이 `status=done` **AND** `owner=user`여야 통과시킨다 (`opal/tools/state-tool/state_tool.py:716-723`).
- agentic에서 그 행은 `na / auto`이므로, 캡틴 발화 후 `mark --owner user`로 `na`를 덮어써야만 CLOSE 진입이 가능하다.
- 즉 어떤 덮어쓰기(`--owner user`)는 필수이고 어떤 덮어쓰기(`--auto-pass`)는 무의미·유해한데, 코드가 이 둘을 구분하지 않는다.

### (5) semi-agentic도 동일 함정

- `MODE_BOUNDARY_STAGES`에 TEST가 없어 TEST 사용자 확인 행에 `--auto-pass`가 허용된다 (`opal/tools/state-tool/state_tool.py:50-54`, `:1525-1529`).
- 그렇게 `done/auto`가 되면 CLOSE 진입에서 `close_gate_violation`으로 막힌다. PM 관점에서는 "통과시켰는데 왜 막히지"로 보인다.

### (6) 자동 승인 가능 여부의 판정 기준이 흩어져 있음

`MODE_BOUNDARY_STAGES`(`:50`), CLOSE 게이트(`:716`), interactive 검증(`:1718-1730`) 세 곳에 각각 박혀 있어, PM이 사전에 "여기는 승인 필요"를 알 방법이 없고 호출해 보고 에러가 나야 안다.

## 확정된 설계 방향 (대화에서 합의)

캡틴 3조를 그대로 도구 계약으로 옮긴다.

| # | 항목 | 내용 |
|---|------|------|
| R-1 | 조항 1 집행 | 사용자 확인 행은 **전 모드 `pending / owner=PM`**으로 초기화한다. agentic auto-na 분기 3곳을 제거한다 |
| R-2 | 조항 2 집행 | **자동 승인 훅을 신설한다.** 다음 단계 첫 행 advance/mark 시, 앞 단계의 미완 사용자 확인 행을 `done / owner=auto / timestamp` + 자동 승인 사유 note로 마킹한다. PM의 명시 호출 누락에 의존하지 않는다 |
| R-3 | 모드별 경계 유지 | 자동 승인 허용 범위는 기존 규칙 그대로 — agentic 전 구간 / semi-agentic은 `MODE_BOUNDARY_STAGES` 제외 / interactive 불가 / CLOSE 직전은 전 모드 불가 |
| R-4 | 조항 3 집행 | 자동 승인 불가 구간이면 전용 에러로 **어느 행에 무슨 보고가 필요한지** 반환한다. PM은 보고 → 캡틴 발화 → `mark --owner user` |
| R-5 | 멱등성 | note 접두 중첩을 제거한다. 이미 `done`인 행에 대한 재-auto-pass는 no-op으로 성공 반환한다 |
| R-6 | 하위호환 | 기존 `na` 행은 읽기 측에서 계속 완료로 인정한다(`_COMPLETE_STATUSES` 유지). 신규 생성만 `pending`으로 바뀐다 |

**설계 후 불변식**: 사용자 확인 행의 최종 상태는 `done/auto`(자동 승인) 또는 `done/user`(캡틴 승인) 둘뿐이며, 두 경우 모두 `timestamp`가 남는다.

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | 사용자 확인 행의 상태 전이를 `pending → done/auto` 또는 `pending → done/user` 단일 축으로 일원화하고, 자동 승인을 PM 호출이 아닌 도구 훅으로 집행한다 | - | 캡틴 3조 (배경 절) |
| 범위 | **포함** — ①auto-na 분기 3곳 제거 ②자동 승인 훅 신설 ③모드별 자동 승인 경계 단일 판정 함수화 ④승인 필요 시 전용 에러 반환 ⑤mark 멱등성 ⑥기존 `na` 하위호환 ⑦pilot SKILL.md·하네스 문서 정합 ⑧회귀 테스트.<br>**제외** — `na` 상태값 자체의 스키마 제거(하위호환 위해 존치), 모드 체계(3-way) 변경, CLOSE 진입 게이트의 `owner=user` 요구 자체의 완화 | - | R-1~R-6 |
| 제약 | ①기존 `na` 보유 state.json이 계속 동작해야 함 ②CLOSE 진입은 전 모드 캡틴 승인 필수 유지 ③STATE.md 마크다운 직접 편집 금지 ④`~/.opal/` 직접 편집 금지(소스 수정 후 install) ⑤install은 전역 단일 타겟이라 배포 검증이 실행 중 파이프라인에 영향 | - | `opal/core/references/opal-harness.md` §1, `.opal/AGENT.md` 금지사항 |
| 완료기준 | ①신규 init 시 전 모드에서 사용자 확인 행이 `pending/PM` ②`auto-na` 문자열 잔존 0건 ③다음 단계 진입만으로 앞 단계 사용자 확인 행이 `done/auto`+timestamp로 마킹됨(PM 명시 호출 없이) ④자동 승인 불가 구간에서 전용 에러 반환 ⑤동일 행 재-mark 시 note 접두 중첩 0건 ⑥기존 `na` 보유 state.json 회귀 0건 ⑦state-tool 기존 테스트 전량 통과 | - | 아래 요구사항 AC |

## 요구사항

- [ ] **F-1. agentic auto-na 분기 제거 (교체형)**
  - 무엇을: init 시 `사용자 확인` 행을 `na/auto`로 만드는 분기를 제거하고 전 모드 `pending/PM`으로 통일
  - 어디에: `opal/tools/state-tool/state_tool.py` 빌더 3곳 (`:825-829`, `:917-921`, `:1051-1055`)
  - 왜: 확정 방향 R-1 (조항 1 집행)
  - AC: (a) **구형 잔존 0** — `state_tool.py`에서 `agentic auto-na at init` 문자열이 0건이고, `--mode agentic`으로 신규 init한 `state.json`의 모든 `사용자 확인` 행이 `status=pending / owner=PM`이다. (b) **신형 채택** — 동일 init 결과가 interactive·semi-agentic과 행 단위로 동일하다(3모드 diff 0)

- [ ] **F-2. 자동 승인 훅 신설**
  - 무엇을: 다음 단계 첫 행 advance/mark 시 앞 단계의 미완 `사용자 확인` 행을 `done/auto`+timestamp+사유 note로 자동 마킹하는 훅 추가
  - 어디에: `opal/tools/state-tool/state_tool.py` — `cmd_advance`/`cmd_mark`의 가드 구간
  - 왜: 확정 방향 R-2 (조항 2 집행 — 현재 미구현)
  - AC: agentic 모드에서 ANALYSIS 사용자 확인 행을 `pending`으로 둔 채 PLAN 첫 행을 advance하면, 별도 `--auto-pass` 호출 없이 해당 행이 `done/owner=auto/timestamp≠null`로 바뀌고 advance가 성공한다

- [ ] **F-3. 모드별 자동 승인 경계 단일 판정**
  - 무엇을: "이 행을 자동 승인해도 되는가"를 단일 함수로 판정하도록 통합 (agentic 전 구간 / semi-agentic은 `MODE_BOUNDARY_STAGES` 제외 / interactive 불가 / CLOSE 직전 전 모드 불가)
  - 어디에: `opal/tools/state-tool/state_tool.py` — `:50-54`, `:1525-1529`, `:1718-1730`에 분산된 **모드별 경계 판정** 3곳
  > [PM 정정 2026-08-15 20:14] 최초 작성 시 `:716-723`(`check_close_gate`)을 네 번째 판정 지점으로 함께 묶었으나, ANALYSIS 실측 결과 이 함수는 `MODE_BOUNDARY_STAGES`를 **전혀 참조하지 않는** 모드 무관 상수 규칙(CLOSE 첫 행이면 무조건 `owner=user` 요구)이다. 따라서 F-3 단일 판정 함수는 "CLOSE 여부(무조건 거부)"와 "`MODE_BOUNDARY_STAGES` 소속 여부(semi-agentic 한정 거부)"라는 **서로 다른 두 축을 합성**해야 하며, 두 조건은 상호 배타적이다(CLOSE는 `MODE_BOUNDARY_STAGES`에 없음). 근거: `ANALYSIS.md` §4-2 / §5 문서-코드 불일치 보고.
  - 왜: 확정 방향 R-3 + 배경 분석 (6)
  - AC: 판정 로직이 단일 함수에 모이고, 기존 4개 지점이 그 함수를 호출한다. 모드×단계 조합에 대한 판정 결과가 변경 전과 동일함을 테스트로 확인한다(경계 불변)

- [ ] **F-4. 승인 필요 구간 전용 에러**
  - 무엇을: 자동 승인 불가 구간에서 자동 승인이 시도되면, 대상 행 ID·단계·필요 조치를 담은 전용 에러를 반환
  - 어디에: `opal/tools/state-tool/state_tool.py` `ERROR_CODES` + 훅 호출부
  - 왜: 확정 방향 R-4 (조항 3 집행)
  - AC: interactive 모드에서 F-2 훅이 발동하면 자동 마킹하지 않고 전용 에러 코드를 반환하며, 응답에 `row_id`와 대상 단계가 포함된다

- [ ] **F-5. mark 멱등성**
  - 무엇을: note 접두 중첩 제거 + 이미 `done`인 행에 대한 재-auto-pass no-op 처리
  - 어디에: `opal/tools/state-tool/state_tool.py` `:1563-1568`
  - 왜: 확정 방향 R-5 + 배경 분석 (3) 실측(092 rows 5·8 이중 접두)
  - AC: 동일 행에 `mark --auto-pass`를 2회 호출해도 note에 `agentic auto-pass:` 접두가 1회만 존재하고, 2회차 호출이 `ok: true`로 성공한다

- [ ] **F-6. 하위호환 + 문서 정합**
  - 무엇을: 기존 `na` 보유 state.json의 동작 보존 확인, 그리고 pilot SKILL.md·하네스 문서의 auto-pass 지시 문구를 신규 계약에 맞춰 정합화
  - 어디에: `opal/core/references/opal-harness-agentic.md`, `opal/skills/opal-pilot-*/SKILL.md` 중 `--auto-pass`를 지시하는 지점
  - 왜: 확정 방향 R-6 + `.opal/AGENT.md` 금지사항(하네스 SSOT 단일 수정)
  - AC: (a) `na` 행을 가진 기존 state.json으로 advance/mark/validate를 수행해도 에러가 발생하지 않는다. (b) 문서에서 "PM이 `--auto-pass`를 호출한다"는 지시가 신규 훅 계약과 모순되지 않는다

## 제약 조건

- [MUST] `opal/core/references/opal-harness.md` §1 Guards: "**커밋은 사용자가 명시적으로 요청할 때만 수행한다.**"
- [MUST] `opal/core/references/opal-harness.md` §1 Guards: "사용자의 확인된 지시(`승인`, `확인`, `확인완료` 등 명시적 표현)가 없으면 CLOSE 단계 진입 불가."
- [MUST] `.opal/AGENT.md` §금지사항: "**`~/.opal/` 직접 편집 금지** — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
- [MUST] `.opal/AGENT.md` §금지사항: "**STATE.md 마크다운 직접 편집 금지** — `state-tool`만 사용."
- 기존 `na` 상태값은 스키마·읽기 경로에서 제거하지 않는다(in-flight state.json 보호).
- 배포 검증 제약: `scripts/install-mac.sh`는 `$USER_HOME/.opal` 단일 타겟이라 per-run 오버라이드가 없다. TEST는 worktree 소스의 `run.sh` 직접 실행으로 수행하고, 전역 배포는 CLOSE 이후 캡틴이 수동 실행한다.
- 이 태스크는 `--wt`로 격리된 worktree에서 코드를 수정한다. 태스크 문서(`tasks/`)·`.opal/`은 허브에 고정된다.

## 기술 스택

- Python 3.14 (`~/.opal/.venv`) — `state_tool.py` 표준 라이브러리 기반, 외부 의존 없음
- pytest — `opal/tools/state-tool/tests/test_state_tool.py`
- JSON Schema — `opal/tools/state-tool/schema/state.schema.json` (런타임 미강제)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | 변경 대상 본체 — auto-na·가드·mark/advance |
| D-2 | 소스 | test_state_tool.py | `opal/tools/state-tool/tests/test_state_tool.py` | 회귀 기준 테스트 |
| D-3 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | Guards(CLOSE 진입 게이트·커밋 규칙)·모드 축 정의 |
| D-4 | 설계 | opal-harness-agentic.md | `opal/core/references/opal-harness-agentic.md` | agentic auto-pass 지시·CLOSE 진입 절차 SSOT |
| D-5 | 설계 | opal-pilot-dev SKILL.md | `opal/skills/opal-pilot-dev/SKILL.md` | 단계별 사용자 확인 행 mark 지시(P-5) |
| D-6 | 소스 | state.schema.json | `opal/tools/state-tool/schema/state.schema.json` | status enum·`na` 존치 판단 |
| D-7 | 설계 | AGENT.md (프로젝트) | `.opal/AGENT.md` | 금지사항·PM 검토 기준 |
| D-8 | 소스 | 092 state.json | `tasks/092-260815-opd-워크트리-작업공간-분리/state.json` | 결함 실측 증거(na/done 혼재·note 이중 접두) |
