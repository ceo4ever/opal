# AGENTIC-LOG: run-log 기록 완전성

> 모드: agentic | 시작: 2026-09-16 13:25 | 스킬: //opds

## 요약

| 항목 | 건수 |
|------|------|
| 게이트 판단 | 9회 (Pass: 7 / Fail: 2) |
| 3회 초과 Gate | 0건 (Critical: 0 / Normal: 0 / Minor: 0) |
| 오류 발견 | 3건 |
| 수정 지시 | 3건 |
| 의사결정 | 6건 |
| 에스컬레이션 | 0건 |

## 활동 기록

### 2026-09-16 13:25 — `DECISION` 모드 전환 semi-agentic → agentic

- 내용: 캡틴 지시로 EXECUTE 진입 시점에 mode를 agentic으로 전환. `state-tool resolve-mode --mode agentic` 결과 `effective_mode=agentic`, `source=explicit`, `persisted=true`.
- 근거: 캡틴 발화 "agentic으로 진행해줘". PLAN 사용자 확인 행은 전환 직전 `--owner user`로 이미 승인됨(row 6, 2026-09-16 13:09).
- 영향: EXECUTE~TEST 구간 게이트를 PM이 대행 승인한다. CLOSE 진입 게이트는 agentic에서도 캡틴 승인 필수로 유지된다(`harness/guards.md` §CLOSE 진입 게이트).

### 2026-09-16 13:25 — `DECISION` PLAN 보정 3건 반영 후 EXECUTE 진입

- 내용: PM 검토에서 도출한 3건을 PLAN·TEST-SCENARIO에 반영했다 — (1) W-4 진단에 `last_observed_*` 3필드 추가(AC-7 결정론 판정), (2) `state-tool log-event`·`gate-request`·`gate-resolve`를 "기존 표면"에서 "선언·미구현 → 신규 구현"으로 정정, (3) D-1·D-2 CONTRACT 의미 계약을 W-0(P0)으로 분리해 RED보다 선행시킴.
- 근거: `state_tool.py` `add_parser` 전수 검색에서 세 서브커맨드 0건 확인. `docs/PROJECT.md` 레지스트리가 CONTRACT를 "구현 전 명세 심판의 판정 기준 원천"으로 규정.
- 검증: `state-tool verify --plan-contract-check` pass(W-0~W-6 인식), `--code-scan-citation-check` pass.

### 2026-09-16 13:29 — `GATE` W-0 PM Gate — **Fail** (루핑 1/3, 심각도 Normal)

- 확인 방법: `git diff docs/run-log/CONTRACT.md` 실측 + §1.1 공통 필드 표 직접 Read.
- 통과 항목: 변경 파일 1개(CONTRACT.md, +4줄)로 범위 준수, 신규 event enum 0건, 신규 CLI 표면 0건, 이력 절 미생성, PRD/TRD/surfaces.json 미변경.
- Fail 사유: §1.3 추가 조문이 §1.1 공통 필드 계약과 충돌. 아래 `ERROR` 참조.

### 2026-09-16 13:29 — `ERROR` PM activity 화이트리스트가 최상위 키 축을 폐쇄해 필수 필드를 거부 대상으로 만듦

- 추가된 조문: "`data.kind`, `summary`, `reason`, `refs`만 허용하는 폐쇄 목록 … 폐쇄 목록에 없는 필드가 하나라도 있으면 append 단계에서 구조화 오류로 거부한다."
- 충돌: §1.1 표는 `schema_version`·`event_id`·`ts`·`run_id`·`seq`·`event`·`actor`·`provenance`를 필수, `caused_by_event_id`·`worker_run_id`를 필수(널 허용)로 요구한다. 문자 그대로 적용하면 규격을 지킨 PM activity를 단 1건도 append할 수 없다.
- 부수 결함 2건: (1) `stage`·`task_step`·`work_item`까지 거부 대상이 되어 AC-2의 "근거 참조 조회"를 오히려 약화, (2) §1.1이 이미 소유한 최상위 키 폐쇄를 §1.3이 중복 소유 → PLAN H-5 위반.

### 2026-09-16 13:29 — `FIX` W-0 재지시 — 폐쇄 범위를 사건 고유 payload 축으로 한정

- 선행 `ERROR`: 위 항목.
- 지시 내용: 폐쇄 대상을 (a) `data` 객체 내용(`kind` 1키, 4종 enum)과 (b) 자유 서술 필드 신설 금지 두 축으로 한정하고, §1.1 공통 필드는 §1.1 계약 그대로 적용됨을 명시. 최상위 키 폐쇄 판정은 §1.1 소유로 두고 참조만 하도록 교체.
- §1.2의 D-1 단락은 검증 통과 — 변경 대상에서 제외.

### 2026-09-16 13:34 — `GATE` W-0 재검증 — **Pass**

- 확인 방법: `git diff docs/run-log/CONTRACT.md` 실측 + §1.1 표 상단 필드명 직접 대조.
- 해소 확인: 교체된 §1.3 단락이 폐쇄 범위를 (a) `data` 객체(`kind` 1키, 4종 enum), (b) 자유 서술 필드 신설 금지 두 축으로 한정하고, §1.1 공통 필드는 제한하지 않음을 명시. 최상위 키 폐쇄 판정은 §1.1 소유로 참조만 함 → H-5 중복 소유 해소.
- 필드명 정확성: 단락이 인용한 `timestamp`·`sequence`·`schema_version`·`event_id`·`run_id`·`worker_run_id`·`caused_by_event_id`·`stage`·`task_step`·`work_item`이 §1.1 표의 실제 표기와 전건 일치함을 확인(문서상 표기는 `ts`/`seq`가 아니라 `timestamp`/`sequence`).
- 범위: CONTRACT.md 단일 파일 +4줄, §1.2 D-1 단락 무변경, 신규 enum·CLI 표면 0건.

### 2026-09-16 13:36 — `DECISION` RED 대상 9종 고정 후 W-1 디스패치

- 내용: `test-tool scenario-init`으로 `test-scenario.json`을 생성했다(11 시나리오). `red_required=true`는 S-1~S-9 9건, S-10(회귀)·S-11(문서 정합)은 `false`.
- 근거: TEST-SCENARIO.md의 `시점` 칸이 S-1~S-9는 "구현 전 RED", S-10·S-11은 "구현 후" — `harness/red-first.md` §1.5 조 1의 변환 규칙 그대로 적용.
- 비고: `profile`을 null로 두었다. 최초 시도에서 `profile=api`가 `executor contract mismatch`로 거부됐는데, 본 태스크 시나리오는 브라우저·API executor 축이 아니라 CLI subprocess 검증이므로 profile 축이 성립하지 않는다.

### 2026-09-16 13:44 — `GATE` W-1 1차 — **조건부 Pass + 보강 지시** (루핑 1/3, 심각도 Minor)

- PM 독립 실측: `pytest ... -q` → 9 failed / 20 passed 재현. `git status`로 구현 파일·docs 미변경 확인. mock 계열 실사용 0건. `scenario-status` → locked=true, red_confirmed_required 9/9.
- 보강 사유: 진공 통과 3건(절대경로 refs 거부·orphan resolve 거부·중복 resolve 거부)이 "명령 부재"로 통과해 계약을 하나도 고정하지 못했다. 지금 조이지 않으면 조이는 주체가 W-3 구현자가 되어 계약이 구현을 따라가는 역전이 생긴다(생성자≠평가자 위반).

### 2026-09-16 13:52 — `GATE` W-1 최종 — **Pass**

- PM 독립 실측: `pytest ... -q` → **12 failed / 17 passed**. 이전 대비 정확히 3건 pass→fail 전환, 기존 RED 9건·회귀 17건 기대값 불변(red-first §1.5 조 5 준수).
- 오류 코드 근거 대조: `gate_not_requested`는 CONTRACT.md:381(§2.2 표)·:429(§2.2.1 대응표)·surfaces.json `gate-resolve.err`에, `gate_duplicate`는 CONTRACT.md:382·:430·surfaces.json `gate-request`/`gate-resolve` 양쪽 err에 **이미 선언됨**을 PM이 직접 조회해 확인. 발명 아님.
- 구현 파일 미변경 재확인.

### 2026-09-16 13:52 — `DECISION` `refs` 절대경로 거부 전용 오류 코드 신설 — 캡틴 승인(a)

- 공백 사실: CONTRACT §2.2 표, surfaces.json `state-tool.log-event.err`(6종: actor_not_allowed·run_log_pending·run_log_outbox_full·run_log_write_failed·task_path_not_absolute·task_lock_timeout), `RUN_LOG_STATE_ERROR_CODES` 3원천 모두에 부재 — PM이 실측 확인.
- 결정: W-5가 CONTRACT §2.2와 surfaces.json `log-event.err`에 `refs_invalid`를 신설하고, W-3이 이를 구현한다.
- 근거: 거부 코드가 없으면 호출자가 사유로 분기할 수 없어 `harness/tool-output-contract.md`의 "코드로 분기 가능해야 한다" 계약이 이 표면에서만 깨진다. `schema_invalid` 재사용은 CONTRACT가 그 범위를 §1.1 최상위 키·필드 enum 위반으로 좁혀놔 계약 오독이 된다.
- 범위 영향: PLAN D-7의 "surfaces.json에 신규 표면을 추가하지 않는다"는 유지된다 — 신규 **표면**이 아니라 기존 표면의 err 집합 1칸 확장이며, 캡틴이 이 확대를 명시 승인했다.

### 2026-09-16 14:05 — `GATE` W-2 PM Gate — **Pass**

- PM 독립 실측 (1): `pytest test_state_tool_run_log.py -q` → **11 failed / 18 passed**. 이전 12 failed 대비 정확히 1건(`TestAutoApprovedRowsEachGetIndependentStateChanged`)만 GREEN 전환. 나머지 11건은 W-3·W-4 소유로 실패 유지 — 범위 침범 없음.
- PM 독립 실측 (2) legacy 회귀: `pytest test_state_tool.py -q` → **411 passed, 3 skipped, 116 subtests passed, 0 failed**. C-6(1.0/1.1 무회귀) 충족.
- PM 독립 실측 (3) H-1 원자성: `state_tool.py` `run_log_commit()` 본문을 직접 Read해 검증. `_working_pending` 지역 변수에 누적하고 `run_log_outbox_admit()`에는 `{**block, ...}` 복사본만 전달하며, 실제 `block["pending_events"]` 갱신은 루프 전원 통과 후 단 한 줄에서만 일어난다. 중간 거부 시 호출되는 `err()`가 `sys.exit(exit_code)`로 실제 종료함을 함수 정의에서 확인 — 부분 admission이 코드 구조상 불가함이 성립한다.
- 범위: `state_tool.py` +76줄, 테스트 파일은 W-1 이후 추가 변경 0건(GREEN 구현자가 RED 기대값을 건드리지 않음), `run_log_core.py`·`docs/**` 미변경.
- @header 갱신 확인: "state.changed 1건" 낡은 서술이 "단일 event 또는 event list" + 전부-아니면-전무 서술로 교체됨.

### 2026-09-16 14:30 — `GATE` W-3 1차 — **Fail** (루핑 1/3, 심각도 Normal)

- Fail 사유: `state_tool.py` `@header` JSON 파손. 아래 `ERROR` 참조.
- 통과 항목(되돌리지 않음): 중첩 오류 봉투 `_rl_err()` 도입은 CONTRACT §2.1이 run-log 계열 전용으로 명시 확정한 형태이며 "기존 도구는 이 형태로 이전하지 않는다(C-2)"까지 적혀 있어 계약 근거 있음. `refs` 절대경로 거부(§1.1 "절대 경로·원문 금지"), gate 선행/중복을 조각+미드레인 보관함 양쪽에서 판정(코어 미호출 → TRD D-5 유지)도 타당.

### 2026-09-16 14:30 — `ERROR` `@header` 블록이 유효 JSON이 아니게 파손됨

- 원인: 기존 `description` 값을 `한다.",`로 닫은 뒤 신규 서술을 JSON 객체 안 따옴표 밖 생짜 텍스트로 이어붙임.
- PM 실측: `json.loads()` → `Expecting property name enclosed in double quotes: line 5 column 6251`.
- 영향: `@header`는 `code-scan`이 전 파일에서 파싱하는 SSOT라, 파손 시 이 파일이 코드맵에서 누락된다. 표기 문제가 아니라 기계 판독 계약 위반.

### 2026-09-16 14:30 — `FIX` W-3 재지시 — `@header` 복구 + 서술 3문장 압축

- 선행 `ERROR`: 위 항목.
- 부가 지시: `schema_invalid` 방출 지점 불일치(§1.3 "append 단계에서" vs 구현의 state-tool 사전 검증)에 대해 수정 금지·사실 확인만 요청.

### 2026-09-16 14:42 — `GATE` W-3 최종 — **Pass**

- PM 독립 실측: `@header` JSON `VALID`(description 6,547자). `pytest test_state_tool_run_log.py -q` → **5 failed / 24 passed**(이전 11 failed에서 담당 6건 정확히 전환, 잔여 5건 전부 W-4 소유). `pytest test_state_tool.py -q` → **411 passed / 3 skipped / 0 failed**.
- 코어 공백 확인: `run_log_core.py:801-805`는 `data.get("kind")` enum만 판정하고 키 집합은 보지 않음. 키 집합 검사 grep 0건 — 워커 보고가 사실임을 PM이 직접 확인.

### 2026-09-16 14:42 — `DECISION` `data` 1키 폐쇄를 코어 `append`에도 집행 — 캡틴 승인(a)

- 문제: CONTRACT §1.3은 "`data`에 `kind` 외의 키가 있으면 **append 단계에서** 거부"라고 적었으나 코어 append는 이를 집행하지 않는다. 현재 집행 지점은 `state-tool log-event` 사전 검증 한 곳뿐.
- 결정: W-4가 `run_log_core.append()`에 키 집합 폐쇄 검사를 추가하고 §1.3 문구는 그대로 둔다.
- 근거: `log-event` CLI를 거치지 않는 생산 경로(adapter·importer·향후 표면)가 `data`에 원문 프롬프트를 실어도 현재는 어디서도 걸리지 않는다. C-3이 표면 하나에만 걸린 방어가 되어 계약이 약속한 보장 범위와 실제가 어긋난다.
- 기각한 대안: 문서만 정정(b)은 그 어긋남을 계약에 고착시킨다. 양쪽 집행(c)은 `kind` enum 판정이 이미 두 곳에 중복된 상태에서 중복을 더 늘려 H-5 표면을 넓힌다.
- 유지 결정: state-tool 사전 검증은 제거하지 않는다 — `_run_log_drain()`이 실패 이벤트를 `pending_events`에서 제거하지 않아, 영구 스키마 위반 이벤트가 admission을 통과하면 이후 모든 호출을 오염시키는 poison pill이 된다.

### 2026-09-16 15:40 — `GATE` W-4 PM Gate — **Pass (축 1~3), 축 4는 blocker 수용**

- PM 독립 실측: `test_state_tool_run_log.py` **29 passed / 0 failed**(RED 5건 전부 전환), `test_state_tool.py` **411 passed / 3 skipped**, `test_run_log_tool.py` **53 passed / 4 subtests** — 3개 스위트 기준선 유지.
- 축 3(H-4 경계) 확인: `--profiles` 미지정 `--channel-id`도, 항목 없는 channel도 여전히 `profile_not_found` 거부. 승인 경계 확대 없음.
- `run_log_core.py` diff 0 확인(`git diff --stat opal/tools/run-log-tool/` 빈 출력).

### 2026-09-16 15:40 — `ERROR` 축 4 코어 집행이 기존 테스트 자산과 구조적으로 충돌

- PM 실측: `test_run_log_tool.py:906`이 `--data '{"kind":"progress","x":1}'`, `:951/956/963`이 `{"kind":"progress","a":1,"b":2}`를 PM/direct `activity`로 append한다. 전자는 digest 차이 검증, 후자는 멱등 정규화(키 순서 불변) 검증 fixture다.
- 코어에 키 집합 폐쇄를 넣으면 이 테스트들이 깨진다. 워커가 전체 activity 버전과 PM·direct 한정 버전을 모두 시도해 둘 다 회귀(53→51/43 failed)를 관측한 뒤 전량 되돌렸다. C-2/C-6이 회귀 0을 요구하므로 되돌린 판단이 옳다.
- **PM 귀책**: 직전 (a) 권고 시 이 fixture들의 존재를 확인하지 않았다. "코어에 검사가 없다"는 사실만 보고 "넣으면 된다"고 판단한 것이 근거 부족이었다.

### 2026-09-16 15:40 — `ERROR` `missing_pm_activity`가 항상 빈 배열

- PM 실측: `result["missing_pm_activity"]`에 값을 넣는 코드 0건(grep). 초기화 후 갱신되지 않는다.
- 워커 사유: RED가 이를 검증하지 않고 CONTRACT에 결정론적 트리거 조건이 없어 발명하지 않았다(침묵하지 않고 명시 보고).
- 판정: PLAN W-4가 4종 누락 목록을 명시했고 AC-5가 "누락 범위 식별"을 요구하므로 4분의 1이 비어 있다. 발명하지 않은 것은 옳으나 공백은 남는다.

### 2026-09-16 15:40 — `DECISION` 축 4 종결 방식 (b) — PM 대행 판단

- 결정: 코어 집행을 포기하고, W-5가 CONTRACT §1.3의 "append 단계에서"를 "`state-tool log-event` 입력 검증에서"로 정정해 계약을 실제 집행 지점에 맞춘다.
- 근거: 충돌하는 fixture들이 여분 키를 쓰는 것은 실수가 아니라 의도된 설계다 — 임의 payload로 digest가 달라지는지·키 순서를 바꿔도 멱등인지를 보는 테스트라 "아무 키나 실을 수 있어야" 성립한다.
- 기각한 대안: (d) 기존 테스트 4종 수정은 그 테스트의 목적 자체를 훼손한다. (e) §1.3에 fixture 예외 carve-out 추가는 계약이 구현 사정을 따라가는 역전이며 더 나쁘다.
- **한계 명시**: (b)를 택하면 C-3의 "원본 프롬프트·내부 사고 과정 비저장" 방어가 `state-tool log-event` 표면 하나에만 걸린다. adapter·importer 등 다른 생산 경로는 이 방어를 받지 않는다. 이 사실을 §1.3에 명시해 후속 태스크의 판단 근거로 남긴다.
- 대행 사유: agentic 모드 PM 대행 의무 범위. 심각도 Normal(계약 문구 조정이며 아키텍처 변경 아님). 캡틴이 이 기록을 근거로 뒤집을 수 있다.

### 2026-09-16 15:40 — `DECISION` `missing_pm_activity` 공백 처리

- 결정: 트리거 조건을 발명하지 않고 필드는 유지하되, W-5가 TRD·CONTRACT에 "현재 미집행 공백"임을 명시한다. CLOSE 회고에서 개선 후보로 올린다.
- 근거: `PRINCIPLES.md` §1 "모호하면 침묵하지 말고 드러낸다" + §2 "현재 요구만 해결한다". 결정론 트리거가 계약에 없는 상태에서 구현자가 조건을 만들면 그 조건이 사실상 계약이 되어 역전이 생긴다.

### 2026-09-16 16:05 — `GATE` W-5 PM Gate — **Pass**

- PM 독립 실측: `python3 -m json.tool docs/run-log/surfaces.json` → JSON OK. `state-tool.log-event.err` = 8종으로 확장(`schema_invalid`·`refs_invalid` 추가 확인). 옛 문구 "append 단계에서 구조화 오류로 거부" grep **0건**(완전 교체).
- 변경 범위: CONTRACT +12/-1, TRD +4/-2, surfaces.json +2, state-tool README +21. PRD·run-log-tool README는 미변경(반영할 확정 사실이 없어 surgical-changes 적용) — 타당.
- 구현 파일·테스트 파일 미변경 확인.
- 중복 소유: `refs_invalid` 정의는 CONTRACT §2.2 1곳, `missing_pm_activity` 공백 서술은 CONTRACT 1곳(README는 요약+포인터), completeness-check 필드 정의는 CONTRACT 1곳(TRD는 소유 근거 흐름만) — H-5 대응 성립.

### 2026-09-16 16:05 — `DECISION` `surfaces.json`에 `state-tool.verify` 계열 id 신설하지 않음 — PM 판단

- 열린 결정: W-5가 `verify --run-log-completeness-check`를 surfaces.json에 반영하려면 신규 id가 필요하다며 PM 승인을 요청했다.
- PM 실측: `grep -c '"state-tool.verify' docs/run-log/surfaces.json` → **0**. 기존 6개 verify 라우트(`--red-check`·`--fix-mode`·`--clarification-check`·`--evidence-check`·`--code-scan-citation-check`·`--plan-contract-check`) 중 **어느 것도 surfaces.json에 등재되어 있지 않다**.
- 결정: 추가하지 않는다. CONTRACT §2.5 문단과 state-tool README 사용법 절로 충분하다.
- 근거: surfaces.json은 run-log 계열 공개 CLI 표면 인벤토리이고 `verify` 라우트는 애초에 그 범위에 들어온 적이 없다. 7번째 라우트만 등재하면 같은 서브커맨드의 6개 형제는 빠진 비대칭 인벤토리가 되어, 이 파일을 소비하는 커버리지·적합성 게이트가 잘못된 전수성을 가정하게 된다. PLAN D-7의 "신규 표면 추가 금지"와도 일치한다.
- 이월: `verify` 라우트 전체를 인벤토리에 넣을지는 별도 판단 대상이며 CLOSE 개선 후보로 올린다.
