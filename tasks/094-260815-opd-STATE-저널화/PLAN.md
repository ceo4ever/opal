# PLAN: STATE.md 파생 섹션 제거 — 저널로 재정의

> 작성일: 2026-08-16 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature (기능 5개)
> 문서 루트: `/Volumes/Data/AiStudio/workspace/opal/tasks/094-260815-opd-STATE-저널화/`
> 코드 루트(EXECUTE): `/Volumes/Data/AiStudio/workspace/opal/.opal-worktrees/task_094/`

---

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

STATE.md에서 `state.json` 파생 산출물(파이프라인 현황판 표 · HTML 주석 마커 · `## 현재 상태` · `## 다음 액션` 자동 파생)을 전부 제거하고, STATE.md를 **의사결정 로그 + 블로커 + 자유 기재로 구성된 저널**로 재정의한다. 기계 상태(rows/current_status/next_action)의 SSOT는 `state.json` 단일로 확정하고, 현황 조회는 `state-tool show`로 일원화한다.

부수적으로 미러가 SSOT를 인질로 잡던 역방향 의존(`marker_missing` 하드 게이트)을 제거하고, ANALYSIS가 검출한 선재 결함 3건(에러 카탈로그 3중 불일치 · 하네스 SSOT 자기모순 · `marker_missing` 트리거 목록 오기재)을 동반 정정한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | STATE.md 저널 산출 전환 + 의사결정 로그 무손실 재배선 | R-1, R-2 | P0 | 없음 |
| F-002 | 마커 게이트·import 경로 제거 + 에러 카탈로그 정합 | R-3, R-4 | P0 | F-001 |
| F-003 | 현황 조회 표준 경로(`show`) 재설계 + 소비 지점 교체 | R-5 | P0 | F-002 |
| F-004 | 하네스 SSOT·pilot·프로젝트 문서 개정 (선재 결함 3건 포함) | R-6, R-7, R-9 | P0 | F-003 |
| F-005 | 회귀 테스트 재작성 + 신형 구조 실동작 실증 | R-8 | P0 | F-004 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 ─ F-002 ─ F-003 ─ F-004 ─ F-005
 (코드)  (코드)  (코드+문서) (문서)  (테스트+실증)
```

> 전 기능이 **단일 사슬(순차)**이다. `state_tool.py` 하나를 F-001·F-002·F-003이 연속 편집하므로 병렬화가 불가능하며(파일 충돌), F-004 문서 개정은 코드 실측값(에러 종수)에 종속되고, F-005는 코드·문서 확정 후에만 의미 있는 검증이 된다.

### 1.4 [MUST] 상위 제약 원문 인용

- [MUST] `.opal/AGENT.md` §금지사항: "**`~/.opal/` 직접 편집 금지** — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
- [MUST] `.opal/AGENT.md` §금지사항: "**하드코딩된 플랫폼 분기 추가 금지** — Claude/Cursor/Gemini 분기는 어댑터 계층(install·plugin)에서만 수행한다."
- [MUST] `docs/CONVENTIONS.md` §State 관리: "파이프라인 STATE.md 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다. 마크다운 표 직접 편집 금지." → 본 태스크에서 **표 전제(B)를 걷어내고 도구 규율(C)만 남긴 표준 문구 A**(§3.4.2)로 교체한다.
- [MUST] `docs/CONVENTIONS.md` §State 관리: "행 주소는 `--task-step <key>`(예: `plan.pm_gate`) 우선 사용, `--task-step-id <N>`은 숫자 폴백 — `--row`는 deprecated 별칭(신규 문서·프롬프트에 사용 금지)." → 본 PLAN이 신설·개정하는 모든 예시 명령은 `--task-step`을 사용한다.
- [MUST] `docs/CONVENTIONS.md` §Citation: "`[MUST]` 토큰이 붙은 항목은 인용 누락 시 산출물 부적합 처리."
- [MUST] `TASK.md` §제약 조건: "의사결정 로그·블로커 데이터는 어떤 경로에서도 유실되어서는 안 된다"
- [MUST] `TASK.md` §제약 조건: "`state.json` 스키마와 `rows[]` 구조는 변경하지 않는다 — 이번 작업은 파생 제거이며 SSOT 교체가 아니다"

---

## 1.5 미확정 5건 결정 (PM 위임 사항 — 본 PLAN에서 확정)

### D-1. `## 다음 액션` 섹션 거취 → **완전 제거**

| 항목 | 내용 |
|------|------|
| 선택지 | (a) 완전 제거 / (b) 자동 파생만 끊고 자유 기재 섹션으로 존치 |
| 판단 근거 | `update_next_action_section` 정의 `state_tool.py:324-334`, 유일 호출 `state_tool.py:387`. 값 계산(`_derive_next_action:497`)은 `state["rows"]`만 순회해 STATE.md와 무관 (→ D-2 §1.3.4). 템플릿 생성부 `_build_new_state_md:1344-1345` |
| **결정** | **(a) 완전 제거** — `## 다음 액션` 섹션을 신규 템플릿에서 삭제하고 `update_next_action_section()` 함수를 삭제한다. `state.json` `next_action` 필드·`_derive_next_action()`·`--next-action` 플래그는 **전부 존치**(스키마 불변 제약). 조회는 `show`가 담당한다(§3.3.2) |
| 근거 | (b)를 택하면 `state.json.next_action`(SSOT)과 `STATE.md ## 다음 액션`(자유 기재)이 **같은 이름의 두 값**으로 공존한다 — 본 태스크가 제거하려는 이중 표현이 이름만 바꿔 재발한다. 확정 방향 §2 "경계는 표가 아니라 파생 전체로 긋는다"(→ D-10 §확정된 설계 방향)와도 정합. 자유 기재 자체는 STATE.md가 평문 마크다운이므로 PM이 임의 섹션을 추가하면 되고, 템플릿이 `state.json` 필드명과 동일한 섹션을 선점할 이유가 없다 |
| 영향 | `TestFreeTextPreservation` 2건(`test_state_tool.py:1743-1779`)·`TestNextActionAutoDerive` 중 렌더 검증 5건(`:1964-2069`) 삭제. 파생 값 검증 4건(`:1854-1897`)은 `state.json` 필드 검증이므로 **생존** |

### D-2. `--import-existing` 거취 → **제거(명시적 에러 반환)**

| 항목 | 내용 |
|------|------|
| 선택지 | (a) 제거 / (b) no-op 유지 |
| 판단 근거 | `cmd_init` import 분기 `state_tool.py:1177-1206`, 표 파싱 `parse_existing_state_md:1064-1096`, 마커 재삽입 폴백 `:1267-1288`, key 재접합 `_key_source_index:1102`/`_reattach_import_keys:1115` (→ D-2 §1.3.6) |
| **결정** | **(a) 제거** — argparse 인자 `--import-existing`은 **존치하되 `help=argparse.SUPPRESS`**, `cmd_init` 진입 즉시 신규 에러 코드 `import_existing_removed`로 거부(exit 1). `parse_existing_state_md`·`_key_source_index`·`_reattach_import_keys`·마커 재삽입 폴백(`:1267-1288`) 전부 삭제. 에러 코드 `import_failed` 삭제(유일 발생점 `:1072` 소멸) |
| 근거 | ① **(b)는 물리적으로 불가능하다** — 현행 import 분기는 마커를 STATE.md에 **재삽입**한다(`:1271-1284`). no-op으로 남기려 해도 이 코드는 R-1/R-3과 정면 충돌해 반드시 제거되어야 하므로, "유지"의 실체는 껍데기뿐이다. ② 표가 사라지면 파싱 입력원이 소멸하므로 no-op은 "성공했으나 rows가 비어 있음"을 반환해 **호출자를 조용히 오도**한다(silent no-op은 최악의 계약). ③ argparse 인자를 남기는 이유는 삭제 시 `unrecognized arguments`(exit 2, 비JSON)가 되어 R-4 AC "명확한 에러 반환"과 stdout JSON 계약(제약 ③)을 동시에 깨기 때문이다. ④ 신규 태스크는 전량 `--rows-from pipeline.json` 경로다 — [MUST] `docs/CONVENTIONS.md` §State 관리: "`state-tool init --rows-from`은 pilot `references/pipeline.json`을 지정한다. … **10/10 pilot 전환 완료(090)**" |
| 영향 | `TestImportPreservesKeys` 9건(`:1487-1710`) · `TestBasicScenarios.test_scenario_import_existing_*` 2건(`:1425-1483`) · `TestErrorCodes.test_import_failed` 1건(`:746-757`) 삭제 = **-12건**. 대체 신규 테스트로 회귀 기준선을 보전한다(§3.5.5 TS-009, F-005) |

### D-3. `update_state_md_header`(`> 최종 갱신:`) 존치 여부 → **존치**

| 항목 | 내용 |
|------|------|
| 선택지 | (a) 존치 / (b) 삭제 |
| 판단 근거 | 정의 `state_tool.py:300-306`(정규식 1회 치환, 6줄), 호출 `:385`(sync) / `:1285`(import — D-2로 소멸). 대상 라인은 `_build_new_state_md:1325`가 생성 |
| **결정** | **(a) 존치** — `sync_state_md`의 축소판에서도 계속 호출한다. 대상 라인 부재 시 `re.sub` count=1이 no-op이므로 레거시·비정형 STATE.md에서도 안전하다 |
| 근거 | ① `> 최종 갱신:`은 **표·마커와 완전 무관한 범용 타임스탬프**로, 제거해도 렌더 동기화 코드 정리 효과가 늘지 않는다(정규식 1회, 의존 0). ② 저널은 사람이 여는 파일이며 "이 저널이 마지막으로 기재된 시점"을 파일 안에서 확인할 수 있어야 한다 — 제거하면 파일만 보고는 최신성을 판단할 수 없다. ③ **이중 표현 리스크 없음** — 이 값은 상태(rows/current_status)가 아니라 *파일 갱신 시각*이므로 `state.json.updated_at`과 SSOT 경쟁 관계가 아니다(파일이 갱신되지 않으면 값도 갱신되지 않는 것이 정상). ④ `TASK.md` R-1 AC(a)의 제거 대상 열거(`pipeline:start` 마커 / 현황판 표 헤더 / `## 현재 상태`)에 포함되지 않는다. ⑤ 기존 헤더 테스트 4건(`:403-410`, `:428-431`) 보존 → 회귀 기준선 방어에 기여 |

### D-4. 레거시(001~093) STATE.md 안내 문구 → **`show` 출력 시점 배너로 삽입(파일 삽입 없음)**

| 항목 | 내용 |
|------|------|
| 선택지 | (a) 안내 없음 / (b) `show` 출력 배너 / (c) 파일 삽입 — **(c)는 소급 변경 금지 제약으로 원천 배제** |
| 판단 근거 | `cmd_show` md 분기 `state_tool.py:1376-1405`(마커 있으면 **STATE.md 본문에서 표를 추출**), full 분기 `:1365-1374`, json 분기 `:1359-1363`. 레거시 실물 `tasks/093-260815-opd-사용자확인행-자동승인-일원화/STATE.md:11-35` (→ D-2 §1.3.6) |
| **결정** | **(b) 배너 — 단, 배너보다 우선하는 구조 교정을 함께 수행한다.** ① `show --format md`는 **마커 유무와 무관하게 항상 `state.json.rows[]`에서 렌더**한다(현행 폴백 `:1376-1393`을 유일 경로로 승격, STATE.md 본문 추출 경로 `:1395-1405` 삭제). ② `show --format md`/`--format full`에서 STATE.md에 마커가 **잔존**하면 출력 상단에 1줄 배너를 prepend: `> [레거시] 이 STATE.md의 파이프라인 표는 더 이상 갱신되지 않는 동결 텍스트입니다. 현황의 SSOT는 state.json이며 위 렌더가 최신입니다.` ③ 파일에는 어떤 바이트도 쓰지 않는다 |
| 근거 | 단순 배너만으로는 **부족하며 실제로는 결함**이다 — 현행 `md` 분기는 마커가 있으면 STATE.md 본문의 표를 그대로 추출해 반환하므로(`:1396-1398`), 저널화 이후 레거시 태스크에서 `show`가 **정지된 옛 표를 최신 현황인 양 반환**한다. 이는 R-5(조회 표준 경로)의 전제를 무너뜨리는 정확성 버그이므로, 배너 이전에 렌더 원천을 `state.json`으로 단일화하는 것이 필수다. 배너는 그 위에 "파일 안의 표는 무시하라"는 사람 대상 안내를 얹는다 |
| 하위호환 | `marker_present` 응답 필드는 **키·타입 그대로 존치**(제약 ③). 의미는 문자 그대로 "STATE.md에 마커가 존재하는가"로 불변이며, README에 "저널화 이후 이 값이 true인 것은 레거시 동결 표 잔존을 뜻한다"고 재해석만 명시한다. 신규 키를 추가하지 않는다(이중 표현 재발 방지) |

### D-5. R-9 선재 결함 3건 정정 방식·순서 → **코드 실측 선행 → SSOT 단일화 → 숫자 중복 제거**

| # | 결함 | 정정 방식 | 순서 |
|---|------|----------|------|
| ① | 에러 카탈로그 3중 불일치 (코드 44 / `README.md:279` 39 / `opal-harness.md:181`·`harness/state.md:21` 23) | **코드가 SSOT**. F-002 코드 변경 완료 후 `len(ERROR_CODES)`를 실측하여 README 카탈로그를 그 수치로 갱신. **하네스 2문서에서는 종수 숫자 자체를 삭제**하고 `opal/tools/state-tool/README.md §에러 코드 카탈로그` 포인터로 대체 | Step 1·2 → Step 5(README) → Step 6(하네스) |
| ② | 하네스 SSOT 자기모순 (`harness/state.md:66` "STATE.md/state-tool이 진행 현황의 유일한 SSOT" ↔ `README.md:13` "SSOT: state.json") | `harness/state.md:66` `[SSOT 불변]` 블록을 "**`state.json`(state-tool)이 진행 현황의 유일한 SSOT다. STATE.md는 의사결정 로그·블로커를 담는 저널이며 진행 현황의 SSOT가 아니다. todo 패널은 읽기 전용 거울이며, 충돌 시 `state-tool show`가 이긴다.**"로 재작성 | Step 6 |
| ③ | `README.md:284` `marker_missing` 트리거 목록 오류(`init` 오기재 · `status`/`gate-pass` 누락) | R-3으로 `marker_missing` 에러 코드 자체가 소멸하므로 **카탈로그 행 전체 삭제**로 자동 해소. 잔존 서술(`README.md:164` validate 응답 예시, `harness/state.md:21`, `opal-harness.md:180`, `state-template.md:31`)도 동시 삭제 | Step 1(코드) → Step 5·6(문서) |

**에러 종수 산식 (설계 목표값 — EXECUTE에서 실측 재확인 [MUST])**:

| 구분 | 종수 | 근거 |
|------|------|------|
| 현행 실측(093 머지 후 base) | **45** | 093이 `user_confirmation_required` 1종 추가. `python3 -c "import state_tool; print(len(state_tool.ERROR_CODES))"` 로 매번 재실측한다 — **이 리터럴을 base로 삼지 말 것** |
| 제거 | -2 | `marker_missing`(R-3) · `import_failed`(D-2로 유일 발생점 `:1072` 소멸) |
| 추가 | +1 | `import_existing_removed`(D-2) |
| **목표값** | ~~43~~ → **44** | **093 머지(2026-08-16)로 재산정** — 093이 `user_confirmation_required` 1종을 추가해 머지 시점 base가 45종이 되었다. 45 − 2 + 1 = **44**. 머지 후 실측으로 확인 완료. 문서 기입 시 이 값을 사용한다 |

> [MUST] 문서에 종수를 기입하기 전 **반드시 코드 실측을 선행**한다. 실측값이 43이 아니면 PLAN의 산식이 아니라 **실측값을 채택**하고 차이를 DONE.md에 기록한다.

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 된다.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-001 `sync_state_md` 재배선 (`state_tool.py:365-392`) | **의사결정 로그 유실** — 마커 게이트 제거 후에도 STATE.md 부재/표 부재 시 `append_decision_log`가 조용히 no-op(`:349-350` "표 없으면 조용히 패스")하여 `--force --note` 기재가 증발 | **P0** | L1(단위) + L2(CLI 통합, 실파일) 의무 | S-1: STATE.md 삭제 상태에서 `mark --force --note` → 저널 자동 복구 + 로그 1행 / S-2: `## 의사결정 로그` 표 헤더만 손상시킨 STATE.md에서 동일 호출 |
| H-2 | F-001 저널 쓰기 예외 흡수 | **파이프라인 차단 vs 로그 유실의 이중 실패** — try/except가 너무 넓으면 진짜 I/O 오류가 은폐되고, 너무 좁으면 `sys.exit`로 파이프라인이 멈춤 | **P0** | L2(권한 제거 디렉토리로 강제 실패 주입) | S-3: STATE.md를 읽기전용(0444)으로 만든 뒤 `mark` → `ok:true` + stdout `journal_warning`에 decision 원문 포함 |
| H-3 | F-001/F-002 `save_state_json` → 저널 순서 (`cmd_mark:1601` vs `:1636`) | **SSOT/미러 순간 불일치** — state.json은 커밋됐는데 저널만 실패하면 "일어난 일이 기록되지 않음", 역순이면 "일어나지 않은 일이 기록됨" | P1 | L2(순서 강제 실패 주입) | S-3과 동일 시나리오에서 `state.json`이 정상 갱신되었는지 동시 확인 |
| H-4 | F-002 `marker_missing` 제거 + **레거시(001~093) STATE.md 공존** | 레거시 파일(마커+표+`## 현재 상태` 보유)에 신형 `sync_state_md`/`append_decision_log` 적용 시 예외·중복 삽입·정규식 오매칭 | P1 | L2(레거시 실물 복사본으로 통합) | S-4: `tasks/093-.../STATE.md` 사본에 `advance`/`mark`/`block` 연속 호출 → 무예외 + 의사결정 로그 정상 추가 + 레거시 표 **무변경(바이트 동결)** |
| H-5 | F-003 `cmd_show` 렌더 원천 단일화 | **`show`가 R-5 조회 표준으로 실동작하지 않음** — 레거시 마커 잔존 시 옛 표를 최신인 양 반환(현행 `:1395-1405` 경로) | **P0** | L2(신형·레거시 2케이스 대조) | S-5: 레거시 표와 `state.json.rows[]`를 **의도적으로 불일치**시킨 뒤 `show --format md` → state.json 값이 반환되고 배너가 붙는지 |
| H-6 | F-003 `show` 응답 계약 | `marker_present` 필드 제거/의미 변경이 기존 소비자를 깨뜨림 (제약 ③) | P1 | L1(응답 키 스냅샷) | S-6: `show --format json/md/full` 3종 응답 키 집합이 기존과 동일(추가만 허용, 삭제 0)임을 assert |
| H-7 | F-002 `--import-existing` 제거 | 미발견 호출부(pilot SKILL.md·훅·스크립트)가 있으면 파이프라인이 즉시 실패 | P1 | L2(전역 grep 0건 + CLI 실행) | S-7: `opal/`·`docs/`·`.opal/` 전역에서 `--import-existing` 호출 지시 0건 확인 + 실제 호출 시 `import_existing_removed` exit 1 |
| H-8 | F-005 테스트 재작성 | **커버리지 공백** — D-1·D-2·R-3으로 25건이 정당 삭제되는데, 삭제분에 가려 신규 기능이 미검증인 채 남거나 숫자 보전용 padding 테스트가 유입 | P1 | L1(pytest 전건) + L3(삭제·신규 대응 감사) | S-8: `pytest tests/ -v` → fail 0 AND 삭제 25건이 D-1/D-2/R-3에 1:1 대응 AND 신규 기능 5종 각각에 대응 테스트 존재 (소유자 판정 2026-08-16 — 숫자 하한 폐기) |
| H-9 | F-004 문서 개정 (약 29파일) | **구형 잔존 0 미달** — 교체형 목표 AC(a). 산문 치환은 누락이 필연적이며 changelog(D분류) 오삭제 위험도 공존 | P1 | L3(결정론 grep 스윕) | S-9: 금지 패턴 grep(§5.2 스윕 명세)이 **현재시제 본문에서 0건**, changelog 행은 **보존됨**을 동시 검증 |
| H-10 | F-004 `docs/CONVENTIONS.md` §State 관리 표준 문구 치환 | 표 전제(B) 제거 시 도구 규율(C)까지 함께 소실 → LLM의 `state.json` 직접 편집 방지선이 무너짐 | P1 | L3(문구 존재 검증) | S-10: 8회+ 반복 지점 전부에 표준 문구 A가 들어갔고 "`state-tool`로만 수행" 규율 문장이 파일당 >=1건 존재 |
| H-11 | F-005 install 재배포 | 프로젝트 소스만 고치고 `~/.opal/` 미배포 시 실증이 구버전으로 수행되어 **거짓 통과** | P1 | L2(배포 후 해시/동작 대조) | S-11: `~/.opal/tools/state-tool/state_tool.py`가 프로젝트 소스와 동일(diff 0)한 뒤 실증 수행 |
| H-12 | F-003 oppd 검증 루프 상태 | `## 현재 상태`의 `- 진행:`/`- 검증:` 필드 소멸로 **검증 루프 재개 정보가 유실** (`verification-loop-guide.md:505-520`) | P1 | L3(문서 정합) | S-12: 검증 루프 진행률의 새 보관처(§3.3.2 (4))가 문서에 명시되고, 세션 복원 절차가 `show` 호출로 기술됨 |

---

## 2. 기능별 분석

### F-001: STATE.md 저널 산출 전환 + 의사결정 로그 무손실 재배선

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/state-tool/state_tool.py` | 렌더·동기화·템플릿 생성 | 수정 |
| 환경 | `opal/tools/state-tool/schema/state.schema.json` | 필드 description 문구 | 수정(문구만) |

#### 2.1.2 현재 구현

`sync_state_md(task_path, state, now_str, command, progress, status_text, decision, reason, next_action)` (`state_tool.py:365-392`)가 6개 갱신 명령의 **단일 후처리 관문**이다(호출: `:1453` advance / `:1636` mark / `:1683` block / `:1853` add-row / `:1900` status / `:1979` gate-pass). 내부 순서:

1. `load_state_md()` → `None`이면 `err(command,"marker_missing")` **즉시 종료** (`:375-378`)
2. `render_pipeline_table()` → `replace_pipeline_section()` → `None`이면 `err(...,"marker_missing")` **즉시 종료** (`:380-383`)
3. `update_state_md_header()` (`:385`)
4. `update_current_status_section()` (`:386`)
5. `update_next_action_section()` (`:387`)
6. `append_decision_log()` — `decision is not None`일 때만 (`:389-390`)
7. `save_state_md()` (`:392`)

즉 **의사결정 로그 기재(6)가 마커 게이트(1·2) 뒤에 있어, 마커가 없으면 로그가 기록되지 않는다** (→ D-2 §1.3.3). 게다가 `save_state_json()`이 이 함수보다 먼저 커밋된다(`cmd_mark:1601` vs `:1636`) — state.json은 갱신됐는데 저널은 미갱신인 채 exit 1 되는 창이 실재한다.

`append_decision_log(md_content, now_str, decision, reason)` (`:340-359`)는 `## 의사결정 로그` 표 헤더 정규식만 사용하며 마커·표·렌더에 **전혀 의존하지 않는다**(`:344-347`). 다만 헤더를 못 찾으면 **조용히 원문 반환**(`:349-350`)한다 — 이 침묵이 H-1의 근원이다.

`_build_new_state_md(task_title, now_str, mode, first_stage, rows, table_str, next_action)` (`:1317-1346`)가 생성하는 템플릿은 제목 / `> 최종 갱신:` / `## 현재 상태`(4줄) / 마커+표 / `## 의사결정 로그` 빈 표 / `## 블로커` / `## 다음 액션` 7블록이다.

블로커 섹션 본문은 **어떤 함수도 쓰지 않는다** — `cmd_block:1683`은 `status_text="블로커"`만 넘겨 `## 현재 상태`의 `- 상태:` 한 줄을 바꿀 뿐이다(`:308-322`). 즉 블로커 보존은 이미 구조적으로 안전하고, 위험은 의사결정 로그 쪽에 집중된다 (→ D-2 §1.3.3).

#### 2.1.3 영향 범위

- **상위 의존(호출자)**: `cmd_advance` / `cmd_mark` / `cmd_block` / `cmd_add_row` / `cmd_status` / `cmd_gate_pass` 6개 — 시그니처 축소 시 6곳 전부 인자 정리 필요
- **하위 의존(피호출)**: `load_state_md:219`(존치) / `save_state_md:227`(존치) / `update_state_md_header:300`(존치·D-3) / `append_decision_log:340`(존치·보강)
- **사멸 유발**: `cmd_mark`의 지역 변수 `progress_text`(`:1582,1596`) · `status_text`(`:1583,1592`), `cmd_status`의 `status_text_map`(`:1887-1894`), `cmd_add_row`의 `status_text=` 인자(`:1854`), `cmd_block`의 `status_text="블로커"`(`:1683`) — 모두 `## 현재 상태` 전용이므로 함께 정리
- **관련 테스트**: `TestInit.test_init_creates_state_md`(`:271-278`), `TestAdvance`/`TestMark` 헤더 4건(`:403-410,428-431` — D-3으로 **생존**), `TestBlock.test_block_g6_status_blocker`(`:510`), `TestG14G15DecisionLog` 트리거 1~7(`:1285-1364` — R-2 검증 기준선, fixture만 조정), `TestWorktreeFlag.test_s2_state_md_identical_*`(`:6027` — 베이스라인 재생성)

---

### F-002: 마커 게이트·import 경로 제거 + 에러 카탈로그 정합

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/state-tool/state_tool.py` | `ERROR_CODES` · `cmd_init` import 분기 · `cmd_validate` 마커 검사 | 수정 |
| 문서 | `opal/tools/state-tool/README.md` | 에러 카탈로그 · `--import-existing` 절 · validate 검증 항목 | 수정 |

#### 2.2.2 현재 구현

`ERROR_CODES` (`:81-133`) **실측 44종**. 마커 전용은 `marker_missing` 1종(`:83`). 마커 차단 지점 6곳 중 **하드 차단은 2곳**(`sync_state_md:377-378`, `:382-383`)이고, `cmd_validate:1734-1740`은 `violations[]`에 담아 간접 차단, `cmd_show` 3분기(`:1359-1393`)는 비차단이다 (→ D-2 §1.3.5).

`cmd_init` import 분기(`:1177-1206`): `load_state_md` → `parse_existing_state_md`(정규식 표 파싱, `:1064-1096`) → 실패 시 `import_failed` → 성공 시 `_reattach_import_keys`로 기존 `state.json`(`:1192-1198`) 또는 `pipeline.json`(`:1199-1202`) 원천에서 074 key 재접합. 이어 `:1267-1288`이 마커 영역을 교체하거나 **없으면 새 마커를 삽입**한다.

#### 2.2.3 영향 범위

- `--import-existing` 호출 지시 전역 검색 결과: `opal/tools/state-tool/README.md`(`:51,58,284,287`) 및 `state_tool.py` 외 **0건** — pilot SKILL.md·훅·스크립트에 호출부 없음(H-7 완화)
- `LABEL_STATUS_MAP`(`:63`)은 `parse_existing_state_md:1079` 외에 `:904`(`build_rows_from_skill_md`)에서도 사용 → **존치**
- `marker_present` 응답 필드 소비자: `state_tool.py` 자신과 `tests/` 뿐. `opal/tools/backlog-tool/backlog_tool.py:572-584`의 동명 필드는 **BACKLOG.md 자체 마커**로 본 태스크와 무관(범위 밖)
- 관련 테스트: `TestErrorCodes.test_marker_missing`(`:711-722`, 삭제), `TestErrorCodes.test_import_failed`(`:746-757`, 삭제), `TestErrorCodesCompleteness.*` 2건(`:2273,:2328-2337`, 목록·카운트 갱신), `TestBasicScenarios.test_scenario_marker_missing_*`(`:1391-1402`, 삭제)

---

### F-003: 현황 조회 표준 경로(`show`) 재설계 + 소비 지점 교체

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/state-tool/state_tool.py` | `cmd_show` 3분기 | 수정 |
| 가이드 | `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | 세션 복원·루프 진행률 추적 | 수정 |
| 스킬 | `opal/skills/opal-pilot-project-dev/SKILL.md` | 재개 절차(`:138`) | 수정 |
| 가이드 | `opal/core/references/harness/state.md` | §세션 복원 | 수정(F-004 Step 6에서 동시 처리) |

#### 2.3.2 현재 구현

`cmd_show` (`:1350-1405`) 3분기:

- `json`(`:1359-1363`): `marker_present` + `data=state` 반환. **마커와 무관하게 이미 state.json 기반** — 정상
- `full`(`:1365-1374`): STATE.md 원문 반환. 마커 **누락 시** 복구 권고 경고를 prepend(`:1371`) — 저널화 후에는 의미가 뒤집힌다
- `md`(`:1376-1405`): 마커 **있으면 STATE.md 본문에서 표 추출**(`:1396-1398`) + `## 현재 상태` 추출(`:1401-1402`) / 마커 없으면 `state.json.rows[]`로 재구성(`:1379-1393`, stdout·stderr 이중 출력)

#### 2.3.3 영향 범위

- 저널화 후 신규 태스크는 마커가 없으므로 항상 폴백 경로를 타지만, **레거시 태스크는 마커가 있어 동결된 옛 표를 반환**한다 → H-5
- `## 현재 상태` 제거로 `show --format md`가 모드·상태를 잃는다 → **state.json에서 재구성해 보전**해야 정보 손실이 없다
- `verification-loop-guide.md:505-520`은 STATE.md `## 현재 상태`의 `- 진행:`/`- 검증:`/`- 상태:` 필드로 검증 루프 재개를 기술한다 → 대체 보관처 지정 필요(H-12)
- STATE.md Read 소비 지점 실측 **2건**: `verification-loop-guide.md:520`, `opal-pilot-project-dev/SKILL.md:138` (→ D-2 §3.2 (A))

---

### F-004: 하네스 SSOT·pilot·프로젝트 문서 개정 (선재 결함 3건 포함)

#### 2.4.1 관련 파일 맵 (개정 대상 확정 목록)

| # | 영역 | 경로 | 성격 | 변경 유형 |
|---|------|------|------|----------|
| 1 | 문서 | `opal/tools/state-tool/README.md` | 에러 카탈로그·import 절·SSOT 서술 | 수정 |
| 2 | 환경 | `opal/tools/state-tool/schema/state.schema.json` | description 문구 3곳(`:4,:43,:129`) — **필드 구조 불변** | 수정(문구만) |
| 3 | 가이드 | `opal/core/references/opal-harness.md` | §3 State — 표 전제·에러 종수 23종·marker_missing | 수정 |
| 4 | 가이드 | `opal/core/references/harness/state.md` | 이벤트 표·SSOT 자기모순(`:66`)·세션 복원 | 수정 |
| 5 | 가이드 | `opal/core/references/harness/state-template.md` | 템플릿 전면 교체(저널 구조) | 수정 |
| 6 | 가이드 | `opal/core/references/harness/header-rules.md` | "현황판 표 행 아님" 어구(`:139,:141`) | 수정 |
| 7 | 가이드 | `opal/core/references/harness/pm-review-gate.md` | `:120` "파이프라인 현황판 행 상태가 state-tool로만 갱신" | 수정 |
| 8 | 가이드 | `opal/core/references/harness/task-process.md` | `:65` `--next-action`이 `## 다음 액션` 초기값이라는 서술 | 수정 |
| 9 | 가이드 | `opal/core/references/harness/qa-standards.md` | `:34` "파이프라인 현황판 산출물 행" | 수정 |
| 10 | 가이드 | `opal/core/references/opal-harness-interactive.md` | `:87,:130` 현황판 테이블 전제 (changelog `:177,:179`는 **보존**) | 수정 |
| 11 | 가이드 | `opal/core/references/tools.md` | `:71` | 수정 |
| 12 | 스킬 | `opal/skills/op-task/SKILL.md` | `:222` `--next-action` = `## 다음 액션` 초기값 | 수정 |
| 13~21 | 스킬 | pilot 9종 SKILL.md + references 5종 (§4.2 Step 9~13 목록) | 표 전제 서술 | 수정 |
| 22 | 문서 | `docs/CONVENTIONS.md` | §State 관리 B/C 융합 문장 | 수정 |
| 23 | 문서 | `docs/ARCHITECTURE.md` | `:207` "State \| STATE.md 상태 관리, 세션 복원" | 수정 |
| 24 | 문서 | `.opal/AGENT.md` | `:44` "마크다운 표 직접 편집 금지" | 수정 |

**개정 제외 확정 (오탐·(D) 분류 — 실측 근거 명시)**:

| 경로 | 제외 사유 |
|------|----------|
| `opal/agents/*/AGENT.md` 10종 | 전건이 순수 (C) 도구 규율(`"STATE.md 갱신은 run.sh 호출로만 수행"` — 예 `opal-be-agent/AGENT.md:71`)이며 표/마커/현황판 키워드 **0건**(grep 실측). 저널화 후에도 문장이 참이므로 개정 불필요 |
| `opal/tools/backlog-tool/**` | BACKLOG.md 자체 마커 — STATE.md와 무관 |
| `opal/tools/opal-action-monitor/**` | `.oppl-run/` 파싱 "현황판" — 별개 개념 |
| `opal/tools/memory-tool/tests/fixtures/**` | (D) 074 히스토리 문자열 fixture |
| `opal/skills/op-task-plan/SKILL.md:136` | `### 현재 상태`는 PLAN 문서 섹션명 — STATE.md 무관(오탐) |
| `opal/skills/opal-brain/SKILL.md:360` | "마크다운 표(GFM)" 일반 서술(오탐) |
| `opal/skills/opal-pilot-write-tech/SKILL.md:532` | changelog 행 — (D) |
| `opal/skills/opal-pilot-project-loop/references/contract.md:58` | surfaces.json 파서 서술 — 무관(오탐) |
| `docs/PROJECT.md:162,245` | `opal-action-monitor` 설명 — 무관(오탐) |
| `.opal/brain/pages/**` · `tasks/**` · `backup/**` · `docs/backup/**` | (D) 과거 이력 — 소급 개정 대상 아님 |
| `docs/architecture-diagram/opal_framework_architecture.html` | "현황판" 2건 — Step 14 스윕에서 STATE.md 표 전제 여부 개별 판정 후 결정 |

#### 2.4.2 현재 구현 / 2.4.3 영향 범위

ANALYSIS 실측 기준 모집단은 **385~387건 / 84파일**(`tasks/`·`backup/`·`docs/backup/` 제외)이며, 이 중 실제 현재시제 개정 대상 (B)는 **약 27건**, (C) 도구 규율 하이브리드가 **7건**, (D) 변경이력·brain이 **약 55건**이다 (→ D-2 §3.2). 동일 계열 "마크다운 표 직접 편집 금지" 보일러플레이트가 **8회 이상** 반복되므로 표준 문구 일괄 치환(§3.4.2)이 필수다.

---

### F-005: 회귀 테스트 재작성 + 신형 구조 실동작 실증

#### 2.5.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/state-tool/tests/test_state_tool.py` | 회귀 테스트 291 함수(6,084줄) | 수정 |
| 배치 | `install-mac.sh` 실행(변경 없음) | `~/.opal/` 재배포 | 실행만 |

#### 2.5.2 현재 구현

기준선 실측: **308 passed + 32 subtests passed, 실패 0, 3.92초** (`cd opal/tools/state-tool && python3 -m pytest tests/ -v`) (→ D-2 §1.4). 테스트는 CLI subprocess 실행 방식이라 함수 삭제가 import 에러를 일으키지 않고 **stdout/파일 내용 assert가 깨진다**.

#### 2.5.3 영향 범위 (증감 회계)

| 구분 | 건수 | 내역 |
|------|------|------|
| 삭제 | -12 | D-2: `TestImportPreservesKeys` 9 + `test_scenario_import_existing_*` 2 + `test_import_failed` 1 |
| 삭제 | -7 | D-1: `TestFreeTextPreservation` 2 + `TestNextActionAutoDerive` 렌더 검증 5 |
| 삭제 | -6 | R-3: `TestShow.test_show_*_marker_missing_*` 3 + `TestErrorCodes.test_marker_missing` 1 + `TestBasicScenarios.test_scenario_marker_missing_*` 2 |
| 수정 | ~8 | `test_init_creates_state_md` · `test_block_g6_status_blocker` · `TestErrorCodesCompleteness` 2 · `TestG14G15DecisionLog` fixture · `TestWorktreeFlag` 베이스라인 등 |
| **신규** | **기능 커버 기준** | §3.5.5 TS-001~TS-020 대응 신규 케이스 — 신규 기능 5종을 전부 커버하는 데 필요한 만큼 작성한다. **숫자 보전 목적의 추가 작성 금지**(H-8) |

---

## 3. 기능별 설계

### F-001: STATE.md 저널 산출 전환 + 의사결정 로그 무손실 재배선

#### 3.1.1 파일 변경 계획

**신규 생성**: 없음

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | BE | `sync_state_md` 재작성 / `_build_new_state_md` 재작성 / `ensure_journal_skeleton` 신설 / `append_decision_log` 보강 / `replace_pipeline_section`·`update_current_status_section`·`update_next_action_section` 삭제 / 6개 호출부 인자 정리 | `state_tool.py:288-334,365-392,1317-1346` |
| 2 | `opal/tools/state-tool/schema/state.schema.json` | 환경 | `:129` `next_action` description을 "STATE.md '## 다음 액션' 렌더 SSOT"에서 "파이프라인 다음 액션 파생값(조회: `state-tool show`)"으로 교체. `:4,:43` 문구 정합 | `state.schema.json:4,43,129` |

> [MUST] `TASK.md` §제약: "`state.json`은 기존 스키마·`rows[]` 구조를 유지한다" — schema 변경은 **`description` 문자열에 한정**하며 `properties`/`required`/`additionalProperties`는 손대지 않는다.

#### 3.1.2 API·데이터 모델 설계

**(1) 신규 STATE.md 저널 템플릿** — `_build_new_state_md(task_title: str, now_str: str) -> str`

기존 7블록 시그니처(`mode`, `first_stage`, `rows`, `table_str`, `next_action`)를 **2인자로 축소**한다 (`state_tool.py:1317-1318` 대비).

```markdown
# STATE: {task_title}

> 최종 갱신: {now_str}
> 파이프라인 현황(rows/상태/다음 액션)의 SSOT는 `state.json`입니다.
> 조회: `~/.opal/tools/state-tool/run.sh show <task-path>`

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|

## 블로커
없음
```

- 제거 블록: `## 현재 상태`(4줄) / `<!-- pipeline:start -->`~`<!-- pipeline:end -->` + 표 / `## 다음 액션` (→ D-1)
- 존치: 제목 · `> 최종 갱신:`(D-3) · `## 의사결정 로그` 빈 표 · `## 블로커` "없음"
- 신설 2줄은 **정적 안내 텍스트**이며 어떤 값도 파생하지 않는다(재렌더 대상 아님) — R-5 조회 경로를 파일 안에서도 안내한다

**(2) 저널 골격 보증** — `ensure_journal_skeleton(md: str | None, task_title: str, now_str: str) -> str` **[신설]**

```python
def ensure_journal_skeleton(md, task_title, now_str):
    """저널 필수 골격(## 의사결정 로그 표 헤더)을 보증한다.
    - md is None            → _build_new_state_md(task_title, now_str) 반환
    - 표 헤더 정규식 미매칭 → md 끝에 '## 의사결정 로그' 빈 표 블록을 append
    - 이미 존재            → md 원문 그대로 반환 (멱등)
    레거시 STATE.md(마커·표 보유)는 본문을 일절 건드리지 않는다 — append만 수행."""
```

> [MUST] 이 함수는 **기존 본문을 삭제·치환하지 않는다.** 레거시 표는 동결 텍스트로 보존되어야 한다(`TASK.md` §제약: "기존 태스크(001~093)의 STATE.md는 소급 변경하지 않는다").

**(3) `sync_state_md` 재작성** — 시그니처 축소 + fail-open

```python
def sync_state_md(task_path, state, now_str, command, decision=None, reason=None):
    """저널 후처리 (구 '미러 동기화'에서 개칭 없이 의미 재정의).
    반환: dict | None — 실패 시 {"journal_warning": {...}}, 성공 시 None.
    [MUST] 어떤 경로에서도 err()/sys.exit()를 호출하지 않는다 (fail-open).
    """
    try:
        md = load_state_md(task_path)
        if decision is not None:
            md = ensure_journal_skeleton(md, state.get("task_id", "task"), now_str)
        if md is None:
            return None                      # 갱신할 저널 없음 + 기재할 결정 없음 → no-op
        md = update_state_md_header(md, now_str)          # D-3 존치
        if decision is not None:
            md = append_decision_log(md, now_str, decision, reason or "(none)")
        save_state_md(task_path, md)
        return None
    except Exception as e:                    # 디스크/권한 등 I/O 오류만 도달
        return {"journal_warning": {
            "reason": f"{type(e).__name__}: {e}",
            "decision": decision, "note": reason,     # 유실 방지 — stdout으로 원문 회수
        }}
```

**제거 파라미터**: `progress` / `status_text` / `next_action` — 전량 `## 현재 상태`·`## 다음 액션` 전용이었다(`:386-387`). 6개 호출부에서 인자와 지역 변수를 함께 정리한다:

| 호출부 | 정리 대상 |
|--------|----------|
| `cmd_advance:1453-1454` | `progress` 지역변수 + `next_action=` 인자 (단 `state["next_action"]` 계산 `:1449`는 **존치**) |
| `cmd_mark:1582-1596,1637-1639` | `progress_text` · `status_text` 지역변수 + 두 인자 + `next_action=` 인자 (`decision`/`reason_text` 계산 `:1615-1634`는 **전량 존치**) |
| `cmd_block:1683` | `status_text="블로커"` 인자 |
| `cmd_add_row:1853-1855` | `status_text=(...)` 인자 (`decision`/`reason` `:1850-1851` 존치) |
| `cmd_status:1887-1901` | `status_text_map` 딕셔너리 + `status_text=` 인자 (`decision`/`reason` `:1897-1898` 존치) |
| `cmd_gate_pass:1979-1980` | 인자 변경 없음(이미 `decision`/`reason`만 전달) |

**(4) `journal_warning` 표면화** — 6개 명령의 `ok()` 페이로드에 **조건부** 추가

```python
_jw = sync_state_md(task_path, state, now_str, command, decision=..., reason=...)
ok(command, ..., **(_jw or {}))
```

> [MUST] `journal_warning`은 **키가 없을 수도 있는 선택 필드**로만 추가한다 — 기존 `ok`/`command`/`todo_mirror`/`gate_checklist` 필드 집합은 삭제·개명 없이 그대로 유지한다(`TASK.md` §제약 ③ stdout 응답 계약 호환).

**(5) [MUST] SSOT/미러 순서와 유실 방지의 긴장 해소** (R-B / H-3)

| 결정 | 내용 |
|------|------|
| 순서 | **`save_state_json()` → `sync_state_md()` 순서를 유지한다** (현행 `cmd_mark:1601` → `:1636`) |
| 근거 | 역순(저널 먼저)은 "저널에는 기록됐으나 state.json 커밋이 실패한" 상태를 만든다 — **일어나지 않은 일이 기록된 저널**은 일어난 일이 누락된 저널보다 나쁘다. SSOT 확정이 선행되어야 저널이 사실을 기술한다 |
| 유실 방지 1 | 마커 게이트 소멸 + `ensure_journal_skeleton`으로 **논리적 실패 경로가 0**이 된다. 남는 실패는 순수 I/O 오류뿐이며, 이는 `save_state_json`이 이미 성공한 동일 디렉토리에서 발생 확률이 극히 낮다 |
| 유실 방지 2 | 그럼에도 실패하면 `journal_warning.decision`/`.note`에 **원문 그대로** stdout JSON으로 반환한다 — 파일에 못 써도 세션 로그·PM 응답에 남으므로 "어떤 경로에서도 유실 금지"를 실질 충족한다 |
| 파이프라인 비차단 | 저널 실패는 `exit 0` + `ok: true`를 유지한다 — 미러(저널) 실패가 SSOT 진행을 막지 않는다. 이는 `marker_missing`이 만들던 역방향 의존의 정확한 반대편이다 |

**(6) `append_decision_log` 보강** (`:340-359`)

행 번호 계산 `row_count = existing_rows.count("\n| ")` (`:354`)는 첫 행이 `\n`으로 시작하지 않는 경계에서 오프바이원 위험이 있다. **정규식 캡처 그룹의 실제 행 수를 세는 방식**으로 교체한다: `row_count = len([l for l in existing_rows.splitlines() if l.strip().startswith("|")])`. 동작 계약(1행 append, 표 부재 시 무해)은 불변.

#### 3.1.3 환경 변경
해당 없음 — 표준 라이브러리만 사용(`re`/`json`/`pathlib`/`argparse`/`subprocess`) (→ D-2 §2).

#### 3.1.4 배치/마이그레이션
**마이그레이션 없음** — 기존 태스크 001~093의 STATE.md는 소급 변경하지 않는다. 신형 코드는 레거시 파일을 만나도 표를 건드리지 않고 헤더 갱신 + 의사결정 로그 append만 수행한다(H-4).

#### 3.1.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC(a) | 산출물 검사 | 신규 `state init` 산출 STATE.md에 `pipeline:start` / `\| # \| 단계 \| 항목 \|` / `## 현재 상태` / `## 다음 액션` 이 각각 **0건** |
| TS-002 | R-1 AC(b) | 기능 테스트 | 신규 STATE.md가 `## 의사결정 로그` 표 헤더와 `## 블로커`를 포함하고, `advance`→`mark`→`block` 연속 호출 후에도 두 섹션이 보존됨 |
| TS-003 | R-2 AC | 기능 테스트 | `mark --force --note '...'` 후 `## 의사결정 로그` 표에 1행 추가 + 기존 행 전건 보존 + `#` 컬럼이 1부터 연속 |
| TS-004 | R-2 AC | 통합 테스트 | STATE.md **삭제** 상태에서 `mark --task-step <key> --done --force --note 'x'` → `ok:true` + STATE.md 자동 생성 + 의사결정 로그 1행 |
| TS-005 | R-2 AC | 통합 테스트 | STATE.md 권한 0444(쓰기 불가)에서 `status --set blocked --note 'x'` → `ok:true`, `exit 0`, stdout에 `journal_warning.decision` 원문 포함, `state.json`은 정상 갱신 |
| TS-021 | R-1 AC(b) | 회귀 테스트 | `> 최종 갱신:` 라인이 `advance`/`mark` 후 갱신됨 (D-3 존치 검증, 기존 4건 유지) |

---

### F-002: 마커 게이트·import 경로 제거 + 에러 카탈로그 정합

#### 3.2.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | BE | `ERROR_CODES`에서 `marker_missing`·`import_failed` 삭제 + `import_existing_removed` 추가 / `cmd_init` import 분기 삭제 / `parse_existing_state_md`·`_key_source_index`·`_reattach_import_keys` 삭제 / `cmd_validate` 마커 검사 삭제 | `state_tool.py:83,86,1064-1130,1177-1206,1267-1288,1734-1740` |
| 2 | `opal/tools/state-tool/README.md` | 문서 | 카탈로그 종수·행 정정, `--import-existing` 절 교체, validate 검증 항목에서 마커 삭제, §개요 마커 서술 삭제 | `README.md:13,14,51,58,157,164,279,284,287` |

#### 3.2.2 API 설계

**(1) `ERROR_CODES` 변경** (`:81-133`)

```python
# 삭제
"marker_missing":  "...",     # :83  — R-3
"import_failed":   "...",     # :86  — 유일 발생점 parse_existing_state_md:1072 소멸
# 추가
"import_existing_removed":
    "--import-existing은 094(STATE.md 저널화)에서 제거되었습니다 — "
    "STATE.md 파이프라인 표가 더 이상 존재하지 않습니다. "
    "행 구성은 --rows-from <pipeline.json> 또는 --rows-spec을 사용하세요.",
```

> [MUST] `err()`는 `ERROR_CODES` 키만 받는다(`state_tool.py:155-158`: "code는 ERROR_CODES 키 중 하나여야 한다 (§2.18 SSOT). 추가/임의 변형 금지."). 신규 코드는 반드시 이 dict에 등록한 뒤 사용한다.

**(2) `cmd_init` import 분기 제거**

```python
# cmd_init 진입부 (--rows-acts 가드 :1153 직후)
if getattr(args, "import_existing", False):
    err(command, "import_existing_removed")
```

argparse 정의는 유지하되 `help=argparse.SUPPRESS`로 문서에서 감춘다(D-2 근거 ③). `:1176-1206`(import 분기)·`:1263-1288`(마커 교체/삽입 분기) 전체 삭제, `:1289-1296`의 신규 생성 경로만 남긴다:

```python
    save_state_json(task_path, state)
    new_md = _build_new_state_md(task_title, now_str)   # 시그니처 축소(§3.1.2 (1))
    save_state_md(task_path, new_md)
    if args.force:                                       # :1299-1306 존치
        updated = append_decision_log(load_state_md(task_path), now_str,
                                      "force flag used at init",
                                      resolve_owner_placeholder(args.note))
        save_state_md(task_path, updated)
```

> `ok()` 응답의 `import_existing=import_mode` 필드(`:1313`)는 **키를 유지하고 항상 `False`를 반환**한다 — 응답 키 삭제는 제약 ③ 위반이 되므로 값만 고정한다.

**(3) `cmd_validate` 마커 검사 제거** (`:1734-1740`)

`violations[]`에 `marker_missing`을 넣던 블록을 통째로 삭제한다. `PIPELINE_MARKER_START/END` 상수(`:135-136`)는 **`cmd_show`의 레거시 감지 전용으로 용도를 재정의하여 존치**한다(§3.3.2).

**(4) 함수 생사 판정 — ANALYSIS §1.3.1 대비 정정 2건**

| 함수 | ANALYSIS 판정 | **PLAN 확정 판정** | 사유 |
|------|--------------|------------------|------|
| `render_pipeline_table:270` | 사멸 | **존치 (용도 격하)** | `cmd_show --format md`가 `state.json.rows[]`에서 표를 렌더하는 **유일 경로**가 되므로 계속 필요하다(§3.3.2). 파일에 고정 저장하는 "미러"가 아니라 요청 시 생성하는 "뷰"이므로 저널화 취지와 충돌하지 않는다 |
| `PIPELINE_MARKER_START/END:135-136` | (미판정) | **존치 (용도 재정의)** | 레거시 동결 표 감지에만 사용. 신규 STATE.md에는 어디에도 기록되지 않는다 |
| `replace_pipeline_section:288` | 사멸 | 삭제 (동일) | - |
| `update_current_status_section:308` | 사멸 | 삭제 (동일) | - |
| `update_next_action_section:324` | 미확정 | **삭제** (D-1) | - |
| `parse_existing_state_md:1064` | R-4 종속 | **삭제** (D-2) | - |
| `_key_source_index:1102` / `_reattach_import_keys:1115` | R-4 종속 | **삭제** (D-2) | 유일 호출부가 import 분기(`:1198,1202`)이며 타 참조 0건(grep 실측) |
| `update_state_md_header:300` | 재검토 | **존치** (D-3) | - |
| `load_state_md` / `save_state_md` / `append_decision_log` / `_derive_next_action` / `build_todo_mirror` | 존치 | 존치 (동일) | `append_decision_log`만 §3.1.2 (6) 보강 |

#### 3.2.3 환경 변경 / 3.2.4 배치
해당 없음.

#### 3.2.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-006 | R-3 AC(a) | 통합 테스트 | STATE.md를 (i) 삭제 (ii) 마커만 제거 (iii) 임의 텍스트로 덮어쓴 3케이스에서 `advance`/`mark` 모두 `ok:true`, exit 0 |
| TS-007 | R-3 AC(b) | 기능 테스트 | `ERROR_CODES`에 `marker_missing`·`import_failed` 부재, `import_existing_removed` 존재, `len(ERROR_CODES)`가 README 기재 종수와 **일치** |
| TS-008 | R-3 AC(a) | 기능 테스트 | 마커 없는 STATE.md에서 `validate` 실행 시 `violations[]`에 `marker_missing` 0건 |
| TS-009 | R-4 AC | 기능 테스트 | `init <path> --skill opd --mode agentic --import-existing` → `{"ok":false,"error":"import_existing_removed",...}` 단일 라인 JSON + exit 1 |
| TS-022 | R-4 AC | 회귀 테스트 | `init --rows-from <pipeline.json>` 정상 경로가 `key` 영속화 포함 기존과 동일 동작(074 key 재접합 삭제가 정상 경로를 훼손하지 않음) |
| TS-023 | R-3 | 회귀 테스트 | `advance`/`mark`/`block`/`add-row`/`status` 응답 키 집합이 기존과 동일(삭제 0건, `journal_warning`만 조건부 추가) |

---

### F-003: 현황 조회 표준 경로(`show`) 재설계 + 소비 지점 교체

#### 3.3.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/state-tool/state_tool.py` | BE | `cmd_show` 3분기 재설계 | `state_tool.py:1350-1405` |
| 2 | `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | 가이드 | 세션 복원(`:517-524`) + 루프 진행률 추적(`:505-515`) 교체 | `verification-loop-guide.md:505-524` |
| 3 | `opal/skills/opal-pilot-project-dev/SKILL.md` | 스킬 | `:138` "STATE.md Read → 현재 Phase 파악 → 재개" 교체 | `opal-pilot-project-dev/SKILL.md:138` |

#### 3.3.2 API 설계

**(1) `cmd_show --format md` — state.json 단일 파생으로 승격**

```python
else:  # md (기본)
    legacy = bool(md) and (PIPELINE_MARKER_START in md and PIPELINE_MARKER_END in md)
    head = [
        f"## 현재 상태",
        f"- 모드: {state.get('mode')}",
        f"- 상태: {STATUS_TEXT.get(state.get('current_status'), state.get('current_status'))}",
        f"- 다음 액션: {state.get('next_action') or '-'}",
        "",
    ]
    body = render_pipeline_table(state["rows"])          # 존치 함수 재사용
    banner = (LEGACY_FROZEN_BANNER + "\n\n") if legacy else ""
    ok(command, format="md", marker_present=legacy,
       content=banner + "\n".join(head) + body)
```

- **STATE.md 본문 추출 경로(`:1395-1405`) 삭제** — 레거시 동결 표가 최신 현황으로 반환되는 결함 제거(H-5)
- **stderr 중복 출력(`:1382-1386`) 삭제** — stdout 단일 출력으로 통일
- `## 현재 상태` 정보는 **사라지지 않고 조회 경로로 이동**한다 — STATE.md에서 뺀 4줄을 `show` 응답이 그대로 제공하므로 정보 손실이 0이다 (R-5 AC(b) 근거)
- `LEGACY_FROZEN_BANNER` 상수 신설:
  `> [레거시] 이 태스크의 STATE.md에는 파이프라인 표가 남아 있으나 더 이상 갱신되지 않는 동결 텍스트입니다. 현황의 SSOT는 state.json이며 아래 렌더가 최신입니다.`

**(2) `--format full`** — 배너 극성 반전

마커 **누락 시 복구 권고**(`:1370-1372`)를 삭제하고, 마커 **잔존 시 동결 배너**를 prepend한다. STATE.md 부재 시 응답(`:1367` `content="(STATE.md 없음)"`)은 불변.

**(3) `--format json`** — 변경 없음. `marker_present`·`data` 키 그대로 유지(제약 ③). README에 의미 재해석만 명시(D-4 하위호환 행).

> [MUST] `TASK.md` §제약: "`state-tool` 서브명령의 stdout 응답 계약(`ok`/`command`/`todo_mirror`/`gate_checklist` 등)은 기존 소비자와 호환을 유지한다." → `show` 3분기 모두 **기존 키를 하나도 삭제하지 않는다**. 변경은 `content` 값의 출처뿐이다.

**(4) 세션 복원·루프 진행률 대체 경로 명문화** (H-12)

| 잃는 것 | 대체 |
|---------|------|
| STATE.md `## 현재 상태` `- 진행:` (Step N/M) | `show --format json` → `data.rows[].note`(`Step N/M 완료`가 이미 `row["note"]`에 기록됨) + `data.current_status` |
| STATE.md `## 현재 상태` `- 상태:` | `show --format json` → `data.current_status` / `show --format md` → `- 상태:` 라인 |
| STATE.md `## 다음 액션` | `show --format json` → `data.next_action` / `show --format md` → `- 다음 액션:` 라인 |
| STATE.md `## 현재 상태` `- 검증:` (oppd 검증 루프 계층·시도) | **STATE.md 저널의 자유 기재 섹션 `## 검증 루프`(PM 수동 기재)** — 파생값이 아니라 도구가 담지 못하는 서술 정보이므로 저널 정의(TASK 확정 방향 §3)에 정확히 부합한다 |

**세션 복원 표준 절차** (`harness/state.md` §세션 복원 · `verification-loop-guide.md:517-524` · `opal-pilot-project-dev/SKILL.md:138` 공통 교체 문구):

```
새 세션에서 태스크를 재개할 때는 아래 순서로 상태를 복원한다.
1. `~/.opal/tools/state-tool/run.sh show <task-path> --format json` 을 호출해
   현재 단계·행 상태·current_status·next_action을 파악한다 (SSOT: state.json).
2. `tasks/{NNN}-{name}/STATE.md`(저널)를 Read하여 의사결정 로그·블로커·검증 루프
   기재 등 도구가 담지 못하는 서술 맥락을 보완한다.
```

> [MUST] 1단계(`show`)가 **기계 상태의 유일 근거**이며, 2단계(STATE.md Read)는 서술 맥락 보완 전용이다. STATE.md에서 행 상태·진행률을 읽어 판단하지 않는다.
> 이 절차는 플랫폼 분기가 아니라 **모든 플랫폼 공통 경로**다 — [MUST] `.opal/AGENT.md` §금지사항: "하드코딩된 플랫폼 분기 추가 금지". `show`는 CLI이므로 Cursor/Gemini/Codex에서도 동일하게 동작하며, 이것이 배경분석 (5)의 비Claude 가시성 문제에 대한 해답이다.

#### 3.3.3 환경 변경 / 3.3.4 배치
해당 없음.

#### 3.3.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-010 | R-5 AC(b) | 기능 테스트 | 신규 태스크에서 `show --format md` → `state.json.rows[]` 파생 표 + `- 모드:`/`- 상태:`/`- 다음 액션:` 3줄 포함, `marker_present:false` |
| TS-011 | R-5 AC(b) / D-4 | 통합 테스트 | 레거시 STATE.md(마커+표, 표 내용을 state.json과 **의도적 불일치**)에서 `show --format md` → 반환 표가 **state.json 값**과 일치 + 배너 1줄 prepend + `marker_present:true` |
| TS-012 | R-5 AC(a) | 산출물 검사 | `opal/`·`docs/` 현재시제 본문에서 "STATE.md를 Read하여 …재개/파악" 계열 서술 **0건**(changelog 제외) |
| TS-024 | R-5 AC(b) | 기능 테스트 | `show --format full`이 레거시 파일에 배너를 붙이고, 신규 파일에는 붙이지 않으며 STATE.md 원문을 손상 없이 반환 |
| TS-025 | H-6 | 회귀 테스트 | `show` 3포맷 응답 키 집합 = 기존(`ok`,`command`,`format`,`marker_present`,`content`/`data`) 동일 |

---

### F-004: 하네스 SSOT·pilot·프로젝트 문서 개정

#### 3.4.1 파일 변경 계획

§2.4.1 표의 24개 항목(파일 기준 약 29개)을 §4.2 Step 5~14로 분할 수행한다. 신규 생성 파일 없음.

#### 3.4.2 [MUST] 표준 대체 문구 및 일괄 치환 규격

동일 계열 보일러플레이트가 8회 이상 반복되므로(→ D-2 §3.2 각주: `opal-harness.md:169`, `harness/state.md:15`, `opal-pilot-dev/SKILL.md:27`, `opal-pilot-dev-wireframe/SKILL.md:46`, `opal-pilot-dev-short/SKILL.md:32`, `verification-loop-guide.md:482`, `parallel-execution-guide.md:356`, `opal-pilot-project-loop/SKILL.md:52`, `docs/CONVENTIONS.md` §State 관리, `.opal/AGENT.md:44`) 아래 **표준 문구를 SSOT로 확정**하고 전 지점에 동일 문자열을 적용한다.

**표준 문구 A — 도구 규율 (구 B/C 융합 문장의 대체)**

> **[MUST] 파이프라인 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다. `state.json` 직접 편집 금지 — 현황 조회는 `state-tool show <task-path>`로 한다.**

**표준 문구 B — STATE.md 역할 정의**

> STATE.md는 **의사결정 로그·블로커·자유 기재를 담는 저널**이다. 파이프라인 현황(행 상태·진행·다음 액션)의 SSOT는 `state.json`이며, 조회는 `state-tool show`로 한다.

**치환 규격 (패턴 → 조치)**

| # | 매칭 패턴(현재시제 본문 한정) | 조치 |
|---|------------------------------|------|
| 1 | "LLM이 STATE.md 마크다운 표를 직접 편집하는 것은 금지된다" / "마크다운 표 직접 편집 금지" | **표준 문구 A**로 치환 |
| 2 | "파이프라인 현황판 행 상태 변경은 `state-tool`로만" / "파이프라인 STATE.md 행 상태(⬜/🔄/✅) 변경은 …로만 수행한다" | **표준 문구 A**로 치환 |
| 3 | "파이프라인 현황판 테이블" / "파이프라인 현황판 표" / "현황판 표 행" (STATE.md 내부를 가리키는 경우) | "파이프라인 행"(state.json `rows[]`)으로 치환하고 필요 시 `show` 조회 안내 부가 |
| 4 | `<!-- pipeline:start -->` / `pipeline:end` / "마커 형식(T-6)" / "마커가 손실되면 …거부된다" | **삭제** |
| 5 | "`marker_missing`(STATE.md 마커 누락)" (에러 나열 문맥) | **삭제**. 남는 나열은 `worker_scope_violation` / `state_not_initialized` |
| 6 | "전체 에러 카탈로그 23종: `tasks/134-260501-opp-pipeline-state-tool/PLAN.md` §2.18" | "전체 에러 카탈로그: `opal/tools/state-tool/README.md` §에러 코드 카탈로그" — **종수 숫자 삭제**(중복 SSOT 재발 방지, D-5 ①) |
| 7 | "`## 다음 액션` 초기값" / "`## 다음 액션` 렌더" | "`state.json` `next_action` 필드 초기값 (조회: `state-tool show`)"로 치환 |
| 8 | "`## 현재 상태`" 섹션 전제 서술 | 삭제 또는 `show --format md` 조회 안내로 치환 |
| 9 | "새 세션에서 …STATE.md…Read하여 …재개/파악" | §3.3.2 (4) **세션 복원 표준 절차** 2단계 문구로 치환 |
| 10 | "STATE.md/state-tool이 …유일한 SSOT" | D-5 ② 재작성 문구로 치환 |
| 11 | `--import-existing` 서술 | 삭제(README는 "094에서 제거됨" 1줄 + `import_existing_removed` 안내로 대체) |
| 12 | **changelog / 변경이력 표 행, `.opal/brain/pages/**`, `tasks/**`, `backup/**`** | **무변경** — (D) 과거 이력 (→ D-2 §3.2 (D)) |

> [MUST] 치환 #12는 절대 위반하지 않는다. 변경이력은 "그때 그랬다"는 사실 기록이며 소급 수정은 이력 위조다 (`harness/citation-rules.md` §5 레거시 호환: "기존 산출물 소급 변경 불필요").

#### 3.4.3 문서별 핵심 개정 내용

| 파일 | 개정 요지 |
|------|----------|
| `state-tool/README.md` | §개요 `:13-14`에서 마커 행 삭제 + "STATE.md는 저널"(문구 B) 추가 / `:51,58` `--import-existing` 절 → 제거 안내 / `:157,164` validate 검증 항목·응답 예시에서 마커 삭제 / `:279` 카탈로그 헤더 종수를 **실측값**으로 / `:284,287` `marker_missing`·`import_failed` 행 삭제 + `import_existing_removed` 행 추가 + 전 행 번호 재부여 / `--next-action` 설명에서 "`## 다음 액션` 첫 줄로 렌더" 삭제 |
| `opal-harness.md` §3 | 표 전제 문장 → 문구 A/B / `:180` marker_missing 삭제 / `:181` 종수 삭제 후 README 포인터 / 예시 명령의 `--row <N>`을 `--task-step <key>`로 교체([MUST] CONVENTIONS §State 관리 "`--row`는 deprecated 별칭(신규 문서·프롬프트에 사용 금지)") |
| `harness/state.md` | `:15` [MUST] 블록 → 문구 A / `:21` 에러 나열·종수 정정 / `:27` 이벤트 표 "파이프라인 현황판 행 갱신" 컬럼명 → "파이프라인 행 갱신" / `:66` [SSOT 불변] → D-5 ② 문구 / §세션 복원 → §3.3.2 (4) 절차 / 이벤트 표 명령의 `--row` → `--task-step` |
| `harness/state-template.md` | **템플릿 전면 교체** — §3.1.2 (1) 저널 템플릿으로. 마커 명세 블록(`:24-31`) 삭제, 자유 텍스트 3섹션 표(`:33-40`)를 2섹션(의사결정 로그·블로커) + "PM 자유 기재 허용"으로 재작성. **파이프라인 행 구성 규칙·산출물 행 규칙은 존치**(state.json `rows[]` 구성 규칙이므로 표와 무관) |
| `harness/header-rules.md` | `:139,141` "현황판 표 행 아님" 어구 정리 |
| `harness/pm-review-gate.md` | `:120` "파이프라인 현황판 행 상태가 state-tool로만 갱신되었는가" → "파이프라인 행 상태가 `state-tool`로만 갱신되었는가 (`state.json` 직접 편집 0건)" |
| `harness/task-process.md` | `:65` `--next-action` 설명 → 치환 #7 |
| `harness/qa-standards.md` | `:34` "파이프라인 현황판 산출물 행" → "파이프라인 산출물 행" |
| `opal-harness-interactive.md` | `:87,:130` 현황판 테이블 전제 → 문구 A 계열 (changelog `:177,:179` **보존**) |
| `core/references/tools.md` | `:71` 표 전제 정리 |
| `op-task/SKILL.md` | `:222` 치환 #7 |
| pilot 9종 + references 5종 | 치환 #1~#9 일괄 적용. **`opal-pilot-project-dev/SKILL.md:579-632`의 자체 STATE.md 템플릿**(`## 현재 상태`·`## Phase 진행 현황`·`## WBS 액션`·`## 병렬 실행 현황` 표 4종)은 개별 판정: `## 현재 상태`는 삭제, 나머지 3표는 **state.json 파생이 아닌 oppd 고유 서술 정보이므로 저널 자유 기재로 존치** |
| `docs/CONVENTIONS.md` | §State 관리 첫 항목 → 표준 문구 A. 나머지 항목(행 주소·`--rows-from`·PM Gate SSOT)은 표 무관이므로 **존치** |
| `docs/ARCHITECTURE.md` | `:207` "State \| STATE.md 상태 관리, 세션 복원" → "State \| `state.json` 파이프라인 SSOT(state-tool) + STATE.md 저널, 세션 복원" |
| `.opal/AGENT.md` | `:44` → 표준 문구 A |

#### 3.4.4 배치/마이그레이션
`install-mac.sh` 재배포(Step 15)로 `~/.opal/`에 반영. 문서 파일 자체의 마이그레이션은 없다.

#### 3.4.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-013 | R-6 AC(a)(b) | 산출물 검사 | 하네스 3문서에서 현황판 표 템플릿·마커 명세·`## 현재 상태` 템플릿 **0건**, 저널 구조(의사결정 로그·블로커)와 `show` 조회 경로 **명시됨** |
| TS-014 | R-7 AC(a)(b) | 산출물 검사 | pilot·가이드에서 표 존재 전제 문구 0건 **AND** 표준 문구 A(도구 규율)가 각 파일에 >=1건 존재 |
| TS-015 | R-9 AC(a) | 산출물 검사 | `README.md` 카탈로그 종수 == `len(ERROR_CODES)` 실측값, 하네스 2문서에는 **종수 숫자 자체가 부재**(포인터만) |
| TS-016 | R-9 AC(b) | 산출물 검사 | "STATE.md…유일한 SSOT" 계열 서술 0건, `state.json` 단일 SSOT 서술로 통일 |
| TS-017 | R-9 AC(c) | 산출물 검사 | 현재시제 본문에서 `marker_missing` 서술 0건 |
| TS-026 | H-9 | 회귀 테스트 | changelog·변경이력 표 행과 `.opal/brain/pages/**`가 **무변경**임을 `git diff --stat`로 확인 |

---

### F-005: 회귀 테스트 재작성 + 신형 구조 실동작 실증

#### 3.5.1 파일 변경 계획

**수정**: `opal/tools/state-tool/tests/test_state_tool.py` (§2.5.3 증감 회계대로)

#### 3.5.2 설계

- **삭제**: 마커 게이트 6건 / import 12건 / 다음 액션 렌더 7건
- **수정**: `test_init_creates_state_md`(저널 산출물 assert로 교체) / `test_block_g6_status_blocker`(`## 현재 상태` → `state.json.current_status` assert) / `TestErrorCodesCompleteness` 2건(`EXPECTED_CODES` 목록 갱신 + 카운트 실측값) / `TestG14G15DecisionLog` 7건(fixture를 저널 STATE.md로) / `TestWorktreeFlag.test_s2_state_md_identical_*`(베이스라인 재생성)
- **신규 25건 이상**: TS-001~TS-026 대응. 특히 아래 3개 클래스를 신설한다.

| 신설 클래스 | 대상 | 대응 TS |
|-----------|------|--------|
| `TestJournalResilience` | STATE.md 삭제/손상/읽기전용 3케이스에서 의사결정 로그 무손실 | TS-004, TS-005 |
| `TestLegacyCoexistence` | `tasks/093-...` STATE.md 사본 기반 레거시 공존 | TS-011, H-4 |
| `TestShowAsQueryStandard` | `show` 3포맷 응답 계약·렌더 원천·배너 | TS-010, TS-024, TS-025 |

> [MUST] 신규 테스트는 **실제 CLI subprocess 실행 + 실제 파일 검증**으로 작성한다 — mock 금지(헌법 §4 "Don't fake it"; `state_tool.py:1607-1613`의 `mock_in_scenario` 가드가 TEST-SCENARIO에 동일 원칙을 강제한다).

#### 3.5.3 환경 변경
해당 없음 (pytest + pytest-subtests 기존 환경).

#### 3.5.4 배치/마이그레이션
`bash install-mac.sh` 실행으로 `~/.opal/tools/state-tool/`·`~/.opal/core/`·`~/.opal/skills/`·`~/.opal/agents/` 재배포. **[MUST] `~/.opal/`을 직접 편집하지 않는다** (`.opal/AGENT.md` §금지사항).

#### 3.5.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-018 | R-8 AC(a) | 통합 테스트 | 임시 태스크 폴더에서 `init`→`advance`→`mark`→`block`→`add-row` 5개 명령이 전부 `ok:true`, exit 0 |
| TS-019 | R-8 AC(b) | 회귀 테스트 | `python3 -m pytest tests/ -v` → **fail 0** AND 삭제 테스트 D-1/D-2/R-3 1:1 대응 AND 신규 기능 5종 대응 테스트 존재 (숫자 하한 없음) |
| TS-020 | R-8 AC(c) | 기능 테스트 | 위 실증 태스크에서 `show --format md`/`--format json` 모두 현황 정상 반환 |
| TS-027 | H-11 | 통합 테스트 | `diff ~/.opal/tools/state-tool/state_tool.py <프로젝트 소스>` 0 확인 후 실증 수행 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| **0** | **F-001, F-002, F-003** | **0** | **opal-test-agent (mode: red)** | **순차(최선행)** | **RED 테스트 작성 — 구현 선행 금지. 작성자≠구현자** |
| **0-b** | **F-006 (R-11)** | **0-b** | **opal-test-agent (mode: red)** | **순차** | **R-11 RED — Step 3 이후, Step 3-b 이전. `verify --red-check` 게이트** |
| 1 | F-001, F-002 | 1 | opal-be-agent | 순차 | `state_tool.py` 단일 파일 — 병렬 불가. **RED 게이트 통과 후 진입** |
| 2 | F-003 | 2 | opal-be-agent | 순차 | 동일 파일 후속 편집 (Step 1 의존) |
| 3 | F-005 | 3 | opal-be-agent | 순차 | 테스트 재작성 — 코드 확정 후 |
| **3-b** | **F-006** | **3-b** | **opal-be-agent** | **순차** | **R-11 GREEN(G-1·G-2·G-3) — `state_tool.py` 직렬 연장. RED 게이트 통과 후 진입** |
| **3-c** | **F-005** | **3-c** | **opal-test-agent** | **순차** | **S-6 시퀀스 교정(093 머지 여파) — 3-b 의존** |
| **3-d** | **F-006** | **3-d** | **opal-task-agent** | **순차** | **R-11 문서(G-4·G-5) — R-7 스윕(Phase 6·7) 앞에 배치. G-1 상수 확정 후** |
| 4 | F-004 | 4 | opal-task-agent | 순차 | README — 에러 종수 실측 종속 |
| 5 | F-004 | 5 | opal-task-agent | 순차 | 하네스 SSOT 3종 — 규칙 원천, 하위 전파 선행 |
| 6 | F-003, F-004 | 6, 7, 8, 9, 10 | opal-task-agent | **병렬 가능(5-way)** | 하네스 보조 + dev/wireframe/gc/project-dev 문서군 — 파일 상호 배타 |
| 7 | F-004 | 11, 12, 13 | opal-task-agent(11·12) / PM 직접(13) | **병렬 가능(3-way)** | sdd·project-loop pilot + `docs/` 갱신 |
| 8 | F-004, F-005 | 14, 15 | opal-task-agent | 순차 | 스윕 검증 → 재배포·실증 |

> Phase 6·7의 병렬 배치는 §7 C-1 Batch 4·5와 1:1 대응한다. Step 6·7은 Step 4(README) 완료만으로 착수 가능하나, 표준 문구 원천(Step 5) 확정 후 일괄 착수하여 문구 분기(리스크 #11)를 차단한다.

### 4.2 실행 체크리스트

> 총 **20개 Step**(Step 0·0-b·1~3·3-b·3-c·3-d·4~15) | Phase **13개**(0·0-b·1~3·3-b·3-c·3-d·4~8) | 실행 모드: **복잡**
>
> **[정합 이력 2026-08-16]** TEST-SCENARIO 단계에서 F-001·F-002·F-003이 **RED-first 강제** 트랙으로 판정되었으나(`TEST-SCENARIO.md` §0 — 비즈니스 로직/API 계약/버그 수정), 최초 PLAN은 Step 1~2(구현) → Step 3(테스트) 순서로 **구현 선행** 구조였다. `harness/red-first.md` §1(RED 증거 없이 GREEN 진입 금지)·§2(작성자≠구현자) 위반이므로 **Step 0(RED, opal-test-agent)을 최선행으로 신설**하고 Step 3의 역할을 기존 테스트 정리로 축소했다. PM 판정.

#### Step 0: RED 테스트 작성 (RED-first 트랙 — 구현 선행 금지)
- [x] 완료
- **소속 기능**: F-001, F-002, F-003 (RED-first 강제 3기능)
- **영역**: 테스트
- **agent**: `opal-test-agent` (mode: red) — **[MUST] 구현 워커(`opal-be-agent`)와 분리** (`harness/red-first.md` §2 작성자≠구현자)
- **파일**: `.opal-worktrees/task_094/opal/tools/state-tool/tests/test_state_tool.py`
- **작업 내용**:
  1. `TEST-SCENARIO.md` §3의 신규 기능 대응 시나리오를 **실패 테스트 코드로 변환**한다. 최소 대상: S-1·S-2·S-3·S-4·S-5(저널 전환·로그 무손실) / S-6·S-7·S-8·S-9(마커·import 제거) / S-10·S-11·S-24·S-25(show 재설계) / **S-29(레거시 쓰기)·S-30(append 분기·멱등)·S-32(note 표 파괴 입력)**
  2. 3클래스 신설: `TestJournalResilience` · `TestLegacyCoexistence` · `TestShowAsQueryStandard` (§3.5.2)
  3. 작성 후 `pytest` 실행하여 **실패(exit≠0)를 증거로 기록**한다
- **완료 기준**: 신규 테스트가 **전건 FAIL**(미구현이므로 정상) + RED 증거(실행 출력) 기록 + **기존 308 passed 영향 0** + `python3 -m pytest tests/ -v` 실행 로그 보존
- **[MUST] 제약**: ① 이 Step에서 `state_tool.py`를 **수정하지 않는다**(테스트 파일만) ② 공개 인터페이스(CLI subprocess·반환값·exit code·파일 내용)로만 검증하고 내부 private 결합 금지 (`red-first.md` §4) ③ mock 금지 — 실 파일 I/O + 실 CLI 실행 (`PLAN §3.5.2` [MUST])
- **테스트**: TS-001~TS-011, TS-021~TS-025 + 신규 S-29/S-30/S-32
- **실행 방법**: sub-agent
- **의존**: 없음 (최선행)

> **[MUST] RED 게이트**: Step 0 완료 후 Step 1(GREEN) 진입 전 `state-tool verify --red-check`를 호출하여 RED 증거를 확인한다. 증거 없이 GREEN 진입 금지 (`harness/red-first.md` §1).
> **[MUST] 테스트 불변성**: Step 1~3의 GREEN/fix 루핑 중 Step 0이 작성한 RED 테스트 파일을 **수정 금지**. 위반 시 블로커 (`red-first.md` §3 — 테스트 약화·삭제·조건 완화로 통과를 유도하는 reward hacking 방어).

#### Step 1: `state_tool.py` 저널 코어 전환 — 파생 제거·재배선·마커/import 삭제
- [x] 완료
- **소속 기능**: F-001, F-002
- **영역**: BE
- **agent**: `opal-be-agent`
- **파일**: `.opal-worktrees/task_094/opal/tools/state-tool/state_tool.py`
- **작업 내용**:
  1. `_build_new_state_md`를 §3.1.2 (1) 저널 템플릿으로 재작성(시그니처 2인자 축소)
  2. `ensure_journal_skeleton()` 신설 (§3.1.2 (2))
  3. `sync_state_md`를 §3.1.2 (3) fail-open 축소판으로 재작성 + 6개 호출부 인자·지역변수 정리(§3.1.2 표)
  4. `ok()` 페이로드에 `journal_warning` 조건부 추가 (§3.1.2 (4))
  5. `append_decision_log` 행 수 계산 보강 (§3.1.2 (6))
  6. `replace_pipeline_section` / `update_current_status_section` / `update_next_action_section` 삭제
  7. `ERROR_CODES`에서 `marker_missing`·`import_failed` 삭제, `import_existing_removed` 추가 (§3.2.2 (1))
  8. `cmd_init` import 분기·마커 삽입 폴백 삭제 + `import_existing_removed` 가드 추가, `--import-existing`을 `help=SUPPRESS`로 (§3.2.2 (2))
  9. `parse_existing_state_md` / `_key_source_index` / `_reattach_import_keys` 삭제
  10. `cmd_validate` 마커 검사 블록(`:1734-1740`) 삭제 (§3.2.2 (3))
  11. 파일 상단 `@header` description에 094 변경 요약 1문장 추가 ([MUST] `docs/CONVENTIONS.md` @header 규칙)
- **완료 기준**: `python3 -c "import state_tool"` 무오류 + `len(ERROR_CODES)` 실측값 기록 + 삭제 대상 6심볼 grep 0건 + `render_pipeline_table`·`PIPELINE_MARKER_*`·`update_state_md_header`는 **존치** 확인
- **테스트**: TS-001, TS-002, TS-003, TS-004, TS-005, TS-006, TS-007, TS-008, TS-009, TS-021, TS-022, TS-023
- **실행 방법**: sub-agent
- **의존**: **Step 0 (RED 증거 확보 + `verify --red-check` 통과 필수)**

#### Step 2: `cmd_show` 재설계 + schema description 정합
- [x] 완료
- **소속 기능**: F-003
- **영역**: BE
- **agent**: `opal-be-agent`
- **파일**: `.opal-worktrees/task_094/opal/tools/state-tool/state_tool.py`, `.opal-worktrees/task_094/opal/tools/state-tool/schema/state.schema.json`
- **작업 내용**: `cmd_show` md/full 분기 재설계(§3.3.2 (1)(2)) + `LEGACY_FROZEN_BANNER` 상수 신설 + stderr 중복 출력 삭제 + json 분기 무변경 확인 / `state.schema.json` description 3곳(`:4,:43,:129`) 문구 교체 — **`properties`/`required`/`additionalProperties` 무변경 [MUST]**
- **완료 기준**: `show --format md`가 마커 유무와 무관하게 `state.json` 파생 표를 반환 + `marker_present` 키 존치 + `python3 -m json.tool state.schema.json` 통과 + `git diff` 상 schema 변경이 description 문자열 3줄로 국한
- **테스트**: TS-010, TS-011, TS-024, TS-025
- **실행 방법**: sub-agent
- **의존**: Step 1 (동일 파일 순차 편집)

#### Step 3: 회귀 테스트 재작성
- [x] 완료
- **소속 기능**: F-005
- **영역**: BE
- **agent**: `opal-be-agent`
- **파일**: `.opal-worktrees/task_094/opal/tools/state-tool/tests/test_state_tool.py`
- **작업 내용**: §2.5.3 증감 회계대로 **삭제 25건 / 수정 약 8건**만 수행한다. **신규 테스트 작성은 Step 0(RED)이 이미 완료**했으므로 이 Step에서 신규 작성하지 않는다(3클래스 신설도 Step 0 소관). **[MUST] Step 0이 작성한 RED 테스트 파일 수정 금지**(`red-first.md` §3) — 삭제·수정 대상은 D-1/D-2/R-3으로 기능이 소멸한 **기존** 테스트에 한한다
- **완료 기준**: `cd opal/tools/state-tool && python3 -m pytest tests/ -v` → **fail 0** AND 잔존 테스트 전건 통과(fail 0) AND 삭제 테스트가 D-1/D-2/R-3 결정에 1:1 대응함이 증명됨 AND 신규 기능 5종(저널 템플릿·의사결정 로그 무손실·show 렌더 단일화·import 거부·에러 카탈로그 정합) 각각에 대응하는 신규 테스트 존재. **[MUST] passed 수를 채우기 위한 padding 테스트 작성 금지** — 삭제된 25건은 기능이 제거되었으므로 삭제가 정상이다. 최종 passed 수와 삭감 내역은 DONE.md에 보고한다 (소유자 판정 2026-08-16 — 숫자 하한 폐기)
- **테스트**: TS-019 (자체), TS-001~TS-027 전건 커버
- **실행 방법**: sub-agent
- **의존**: Step 2

#### Step 0-b: R-11 RED 테스트 작성 (F-006 RED-first)
- [x] 완료
- **소속 기능**: F-006 (R-11)
- **영역**: 테스트
- **agent**: `opal-test-agent` (mode: red) — **[MUST] 구현 워커(`opal-be-agent`)와 분리** (`harness/red-first.md` §2)
- **파일**: `.opal-worktrees/task_094/opal/tools/state-tool/tests/test_state_tool.py`
- **작업 내용**: `TEST-SCENARIO.md` §3의 **S-34·S-35·S-36·S-37·S-40**을 실패 테스트로 변환한다. `TestR11ModeBoundary`(S-34, 3 stage 개별 판정 + 통과 경로 + QA 대조군) · `TestR11CloseGateFallback`(S-35, `--owner user` 유/무 2케이스 + opd 대조군) · `TestR11DerivedSignals`(S-36 전 구간 순회 + interactive 대조군, S-37 중립 처리 + semi-agentic 경계 내부 대조군) · `TestR11Invariants`(S-40 diff 역검증) 4클래스 신설
- **완료 기준**: 신규 테스트 **전건 FAIL**(R-11 미구현이므로 정상) + RED 증거 기록 + **기존 통과 테스트 무영향** + `state_tool.py` **무변경**(`git diff --stat`으로 확인)
- **[MUST] 제약**: ① 구현 파일 수정 금지 ② mock 금지(실 `pipeline.json` + 실 CLI subprocess) ③ 공개 인터페이스로만 검증 ④ **S-34는 3 stage를 개별 판정**한다 — 단일 호출은 DICT만 노출하여 `"DICT"`만 추가한 부분 구현을 통과시킨다(`SCENARIO-GATE-3.md` ① 하향 주사유)
- **테스트**: S-34, S-35, S-36, S-37, S-40
- **실행 방법**: sub-agent
- **의존**: Step 3 (테스트 파일 직렬 — Step 3의 정리 작업과 충돌 차단)

> **[MUST] RED 게이트**: Step 0-b 완료 후 Step 3-b(GREEN) 진입 전 `state-tool verify --red-check`를 호출한다. RED 증거 없이 GREEN 진입 금지 (`red-first.md` §1).
> **[정합 이력 2026-08-16]** 최초 PLAN은 R-11(F-006)을 Step 3-b/3-d에서 **RED 없이 바로 구현**하는 GREEN-first 구조였다. G-1(모드 판정 변경)·G-2(게이트 분기 신설)·G-3(파생 계산식 변경)은 전부 `red-first.md` §1.5의 "비즈니스 로직 / 버그 수정" 트랙이다. **AGENTIC-LOG #21에서 PM이 직접 검출해 Step 0을 신설한 것과 동일 유형의 위반이 R-11 편입 시 재발**하여, 별도 세션 검토 지적으로 교정한다. 착수 후에는 구현이 존재해 RED 증거를 만들 수 없으므로 Step 3-b 착수 **전에** 처리한다.

#### Step 3-b: R-11 코드 3건 (G-1·G-2·G-3) — `state_tool.py` 직렬 연장
- [x] 완료
- **소속 기능**: F-006 (R-11 신설)
- **영역**: BE
- **agent**: `opal-be-agent`
- **파일**: `.opal-worktrees/task_094/opal/tools/state-tool/state_tool.py`
- **작업 내용**:
  1. **G-1** `MODE_BOUNDARY_STAGES`에 `"DICT"`, `"MODEL"`, `"DDL/MIGRATION"` 3원소 추가 — `can_auto_approve_user_confirmation()` 단일 판정만 참조하므로 상수 추가로 전 경로 반영, **새 분기 불요**
  2. **G-2** `check_close_gate`의 `prev_user_row is None` 분기를 폴백으로 교체 — 확인 행 0개 파이프라인(opgc)을 정상 형태로 인정하고 CLOSE 첫 행 자체에 `--owner user`를 요구. `--force` 우회 경로는 현행 유지
  3. **G-3-a** `_derive_next_action`에 자동 승인 예정 사용자 확인 행 스킵 추가 (`can_auto_approve_user_confirmation` 재사용)
  4. **G-3-b** `build_todo_mirror`의 단계 집계에서 자동 승인 예정 사용자 확인 행을 **중립 처리**(`na`와 동일 취급)
  5. `@header` description에 R-11 요약 1문장 추가
- **완료 기준 (기능 달성)**: Step 0-b의 RED 테스트가 **GREEN 전환** — 즉 **AC(a)** agentic 전 구간에서 `next_action`이 사용자 확인을 미지목(CLOSE 예외) / **AC(b)** semi-agentic opdd의 `DICT`·`MODEL`·`DDL/MIGRATION` **3행 각각**이 `user_confirmation_required`로 거부되고 소유자 승인 시 통과 / **AC(c)** opgc가 `--force` 없이 CLOSE 진입, `--owner user` 없으면 거부 / **AC(d)** 자동 승인 예정 행 중립 처리로 해당 단계 todo가 `completed`. **실행 증거(테스트 출력)를 보고에 포함한다**
- **완료 기준 (비회귀)**: **R-11 diff가 `ERROR_CODES`를 접촉하지 않음**(항목 추가·삭제 0건 — 종수 리터럴을 완료 기준에 두면 S-7·S-15의 실측 판정과 충돌해 거짓 FAIL을 유발한다, `SCENARIO-GATE-3.md` 확정 결함) + `state.json` 스키마·`next_action` 필드 불변 + `build_todo_mirror` 시그니처·반환 구조 불변 + 신규 상수·신규 판정 함수 **0건**(`git diff`로 확인)
- **[MUST]** 명세 SSOT는 `R-11-요청서.md` §2 G-1·G-2·G-3. 요청서의 코드 스니펫을 그대로 따르되, 093 함수 시그니처가 다르면 **요청서가 아니라 실제 코드**를 기준으로 한다
- **테스트**: **S-34·S-35·S-36·S-37·S-40** (TEST-SCENARIO 증분 — 시나리오 ID는 `TEST-SCENARIO.md` §3 기준. PLAN 초안의 TS-028~031 표기는 실제 부여된 S-33~S-41과 불일치하므로 폐기)
- **실행 방법**: sub-agent
- **의존**: **Step 0-b (RED 증거 확보 + `verify --red-check` 통과 필수)** + Step 3 (동일 파일 직렬 — 파일 충돌 차단)

#### Step 3-c: S-6 시퀀스 교정 (093 머지 여파)
- [x] 완료
- **소속 기능**: F-005
- **영역**: 테스트
- **agent**: `opal-test-agent`
- **파일**: `.opal-worktrees/task_094/opal/tools/state-tool/tests/test_state_tool.py`
- **작업 내용**: `test_s6_marker_gate_removed_three_corruption_cases` 3 subtests가 093 auto-na 제거로 사용자 확인 행이 `pending` 유지되어 `stage_transition_violation`에 걸린다. **마커 게이트와 무관한 실패**이므로 유효한 행 순서로 호출 시퀀스를 교정한다. S-6의 검증 목적(마커 부재 3케이스에서 `advance`/`mark` 성공)은 불변
- **완료 기준**: S-6 3 subtests GREEN + 다른 테스트 무영향
- **[MUST]** 구현을 바꿔 통과시키지 않는다 — 시퀀스만 교정
- **테스트**: S-6
- **실행 방법**: sub-agent
- **의존**: Step 3-b

#### Step 3-d: R-11 문서 2건 (G-4·G-5)
- [x] 완료
- **소속 기능**: F-006
- **영역**: 가이드
- **agent**: `opal-task-agent`
- **파일**: `opal/skills/opal-pilot-dev/SKILL.md`, `opal/skills/opal-pilot-dev-short/SKILL.md`, `opal/skills/opal-pilot-dev-wireframe/SKILL.md`, `opal/skills/opal-pilot-project/SKILL.md`, `opal/core/references/opal-harness-semi-agentic.md`
- **작업 내용**: **G-4** 모드 무분기 `사용자 확인 (P-5)` 명령형 주석 7건을 모드 분기 문안으로 교체(표준형: `opal-pilot-project-dev/SKILL.md:779`) / **G-5** 하네스 §3 모드 경계 표에 opdd·oppl·opgc 3종 추가 — opdd 행은 G-1 상수와, opgc 행은 G-2 폴백과 **반드시 일치**
- **완료 기준**: 무분기 P-5 주석 잔존 0건 + 경계 표 10종 등재 + 상수·pipeline.json과 모순 0
- **[MUST]** 파일 5개로 산출량 상한(3) 초과 — R-7 스윕(Step 7~12)과 대상이 겹치므로 **R-7 스윕 전에 수행**하고, 스윕의 grep 패턴에 무분기 P-5 패턴을 추가한다
- **테스트**: **S-38·S-39**
- **실행 방법**: sub-agent
- **의존**: Step 3-b (G-1 상수 확정 후 G-5 표 작성)

#### Step 4: `state-tool/README.md` 개정 (R-4 문서 + R-9 ①③)
- [x] 완료
- **소속 기능**: F-004
- **영역**: 문서
- **agent**: `opal-task-agent`
- **파일**: `.opal-worktrees/task_094/opal/tools/state-tool/README.md`
- **작업 내용**: §3.4.3 README 행 전건. **에러 종수는 Step 1에서 실측한 `len(ERROR_CODES)` 값을 사용**하고 카탈로그 행 번호를 재부여한다. `marker_present` 의미 재해석 1줄 추가(D-4). 변경이력 표에 v1.x 행 1건 추가(과거 행 무변경)
- **완료 기준**: 카탈로그 종수 == 실측값, `marker_missing`·`import_failed` 행 부재, `import_existing_removed` 행 존재, `--import-existing` 사용 안내 0건
- **테스트**: TS-015, TS-017
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 2

#### Step 5: 하네스 SSOT 3문서 개정 (R-6 + R-9 ②)
- [x] 완료
- **소속 기능**: F-004
- **영역**: 가이드
- **agent**: `opal-task-agent`
- **파일**: `opal/core/references/opal-harness.md`, `opal/core/references/harness/state.md`, `opal/core/references/harness/state-template.md` (worktree 경로 기준)
- **작업 내용**: §3.4.3 해당 3행. 치환 규격 #1~#10 적용. `state-template.md`는 템플릿 전면 교체(파이프라인 행 구성 규칙·산출물 행 규칙은 존치). `state.md:66` [SSOT 불변] D-5 ② 재작성. 세션 복원 §3.3.2 (4) 문구 삽입. 각 파일 변경이력 1행 추가
- **완료 기준**: 3문서에서 현황판 표 템플릿·마커 명세·`## 현재 상태` 템플릿 0건 + 저널 구조 + `show` 조회 경로 명시 + 에러 종수 숫자 부재(포인터만)
- **테스트**: TS-013, TS-016, TS-017
- **실행 방법**: sub-agent
- **의존**: Step 4

#### Step 6: 하네스 보조 문서 3종 개정
- [x] 완료
- **소속 기능**: F-004
- **영역**: 가이드
- **agent**: `opal-task-agent`
- **파일**: `opal/core/references/harness/header-rules.md`, `opal/core/references/harness/pm-review-gate.md`, `opal/core/references/harness/task-process.md`
- **작업 내용**: 치환 규격 #3, #7, #8 적용 (§3.4.3 해당 3행)
- **완료 기준**: 표 전제 어구 0건, 도구 규율 문장 보존
- **테스트**: TS-014
- **실행 방법**: sub-agent
- **의존**: Step 5 (표준 문구 원천 확정 후 착수 — 리스크 #11 차단)

#### Step 7: 하네스 잔여 3종 개정
- [x] 완료
- **소속 기능**: F-004
- **영역**: 가이드
- **agent**: `opal-task-agent`
- **파일**: `opal/core/references/harness/qa-standards.md`, `opal/core/references/opal-harness-interactive.md`, `opal/core/references/tools.md`
- **작업 내용**: 치환 #1~#3 적용. **`opal-harness-interactive.md:177,179` changelog 행은 무변경 [MUST]**
- **완료 기준**: 현재시제 본문 표 전제 0건 + changelog 무변경(`git diff`로 확인)
- **테스트**: TS-014, TS-026
- **실행 방법**: sub-agent
- **의존**: Step 5 (표준 문구 원천 확정 후 착수 — 리스크 #11 차단)

#### Step 8: `op-task` + dev 계열 pilot 2종 개정
- [x] 완료
- **소속 기능**: F-004
- **영역**: 스킬
- **agent**: `opal-task-agent`
- **파일**: `opal/skills/op-task/SKILL.md`, `opal/skills/opal-pilot-dev/SKILL.md`, `opal/skills/opal-pilot-dev-short/SKILL.md`
- **작업 내용**: 치환 #1, #2, #7 적용 (`op-task/SKILL.md:222`, `opal-pilot-dev/SKILL.md:27`, `opal-pilot-dev-short/SKILL.md:32`)
- **완료 기준**: 표 전제 0건 + 표준 문구 A 각 1건 이상
- **테스트**: TS-014
- **실행 방법**: sub-agent
- **의존**: Step 5

#### Step 9: pilot 3종 개정 (wireframe / gc / project)
- [x] 완료
- **소속 기능**: F-004
- **영역**: 스킬
- **agent**: `opal-task-agent`
- **파일**: `opal/skills/opal-pilot-dev-wireframe/SKILL.md`, `opal/skills/opal-pilot-gc/SKILL.md`, `opal/skills/opal-pilot-project/SKILL.md`
- **작업 내용**: 치환 #1~#3 적용 (`:46` / `:287,:435` 실행 요약 테이블 / `:32`)
- **완료 기준**: 표 전제 0건 + 도구 규율 보존
- **테스트**: TS-014
- **실행 방법**: sub-agent
- **의존**: Step 5

#### Step 10: `opal-pilot-project-dev` 3종 개정 (R-5 소비 지점 포함)
- [x] 완료
- **소속 기능**: F-003, F-004
- **영역**: 스킬
- **agent**: `opal-task-agent`
- **파일**: `opal/skills/opal-pilot-project-dev/SKILL.md`, `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md`, `opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md`
- **작업 내용**: `SKILL.md:138` 재개 절차 → §3.3.2 (4) 표준 절차 / `SKILL.md:579-632` 자체 STATE.md 템플릿에서 `## 현재 상태` 삭제(나머지 3표 존치, §3.4.3) / `verification-loop-guide.md:482` 치환 #1, `:505-515` 루프 진행률 → `## 검증 루프` 자유 기재 + `show` 조회(§3.3.2 (4)), `:517-524` 세션 복원 교체 / `parallel-execution-guide.md:356` 치환 #1
- **완료 기준**: "STATE.md를 Read하여 …재개" 0건 + `show` 호출 절차 명시 + 검증 루프 상태 보관처 명시
- **테스트**: TS-012, TS-014
- **실행 방법**: sub-agent
- **의존**: Step 5

#### Step 11: `opal-pilot-sdd` 3종 개정
- [x] 완료
- **소속 기능**: F-004
- **영역**: 스킬
- **agent**: `opal-task-agent`
- **파일**: `opal/skills/opal-pilot-sdd/SKILL.md`, `opal/skills/opal-pilot-sdd/references/verify-guide.md`, `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md`
- **작업 내용**: 치환 #1~#3 적용 (`SKILL.md:216,:353` / `verify-guide.md:154` / `execute-loop-guide.md:305`)
- **완료 기준**: 표 전제 0건
- **테스트**: TS-014
- **실행 방법**: sub-agent
- **의존**: Step 5

#### Step 12: `opal-pilot-project-loop` 2종 + `.opal/AGENT.md` 개정
- [x] 완료 (부분 완료 — oppl 2종 완료 / `.opal/AGENT.md`는 worktree sparse-checkout 대상 밖이라 **Step 14에서 허브 처리**)
- **소속 기능**: F-004
- **영역**: 스킬
- **agent**: `opal-task-agent`
- **파일**: `opal/skills/opal-pilot-project-loop/SKILL.md`, `opal/skills/opal-pilot-project-loop/references/journey-flow.md`, `.opal/AGENT.md`
- **작업 내용**: 치환 #1~#3 적용 (`SKILL.md:49,:52` / `journey-flow.md:33` / `.opal/AGENT.md:44`)
- **완료 기준**: 표 전제 0건 + 표준 문구 A 적용
- **테스트**: TS-014
- **실행 방법**: sub-agent
- **의존**: Step 5

#### Step 13: `docs/` 갱신 (CONVENTIONS·ARCHITECTURE)
- [x] 완료
- **소속 기능**: F-004
- **영역**: 문서
- **agent**: **PM 직접**
- **파일**: `docs/CONVENTIONS.md`, `docs/ARCHITECTURE.md`
- **작업 내용**: `CONVENTIONS.md` §State 관리 첫 항목을 표준 문구 A로 교체(나머지 항목 존치) + `## 변경이력` 1행 추가 / `ARCHITECTURE.md:207` State 행 서술 교체 + 변경이력 1행 추가
- **완료 기준**: §State 관리에서 "마크다운 표 직접 편집 금지" 0건 **AND** "`state-tool`로만 수행" 규율 문장 존재(H-10)
- **테스트**: TS-014, TS-016
- **실행 방법**: direct
- **의존**: Step 5

#### Step 14: 구형 잔존 0 전역 스윕 검증 + 잔여 판정
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 공통
- **agent**: `opal-task-agent`
- **파일**: (검증 전용 — 잔여 수정 발생 시 최대 3파일, 초과 시 PM에 분할 보고)
- **작업 내용**: §5.2 스윕 명세의 금지 패턴 grep을 `opal/`·`docs/`·`.opal/AGENT.md` 대상으로 실행하여 현재시제 본문 0건 확인. `docs/architecture-diagram/opal_framework_architecture.html`의 "현황판" 2건이 STATE.md 표 전제인지 개별 판정 후 필요 시 수정. `--import-existing` 호출 지시 0건 확인(H-7). changelog·brain 무변경 확인(TS-026)
- **완료 기준**: 스윕 grep 전 패턴 0건 + `git diff --stat`에 `.opal/brain/`·`tasks/`·`backup/` 변경 0
- **테스트**: TS-012, TS-013, TS-014, TS-016, TS-017, TS-026
- **실행 방법**: sub-agent
- **의존**: Step 3, 6, 7, 8, 9, 10, 11, 12, 13

#### Step 15: install 재배포 + 신형 구조 실동작 실증
- [ ] 완료
- **소속 기능**: F-005
- **영역**: 배치
- **agent**: `opal-task-agent`
- **파일**: (배포 실행 + 실증 로그 — 소스 변경 없음)
- **작업 내용**: `bash install-mac.sh` 실행 → `diff ~/.opal/tools/state-tool/state_tool.py <프로젝트 소스>` 0 확인(H-11) → 임시 태스크 폴더에서 `init --skill opd --mode agentic --rows-from <pilot pipeline.json>` → `advance --task-step <key>` → `mark --task-step <key> --done` → `block --task-step <key> --reason x` → `add-row --after-task-step <key> --stage EXECUTE --item 추가작업` → `show --format md` / `--format json` 순차 실행, 각 응답 JSON을 실행 증거로 수집. **[MUST] `~/.opal/`을 직접 편집하지 않는다**
- **완료 기준**: 5개 서브명령 전부 `ok:true` + `show` 2포맷 정상 + 산출 STATE.md에 구형 잔존 0 + `## 의사결정 로그` 행 존재
- **테스트**: TS-018, TS-020, TS-027, TS-001, TS-002
- **실행 방법**: sub-agent
- **의존**: Step 14

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 → Step 3 | **동일 파일(`state_tool.py`) 순차 편집** — 후행 저장이 선행 편집을 덮어쓰는 충돌 방지 (Step 3은 코드 확정 후에만 assert 작성 가능) |
| Step 1·2 → Step 4 | README 에러 종수가 코드 실측값에 종속 (D-5 ①) |
| Step 4 → Step 5 | 하네스가 README를 에러 카탈로그 SSOT 포인터로 참조하므로 README 확정 선행 |
| Step 5 → Step 8~13 | 하네스가 규칙 SSOT이며 pilot·docs가 이를 상속 — 표준 문구 확정 후 하위 전파 |
| Step 6 ∥ 7 ∥ 8 ∥ 9 ∥ 10 | 상호 배타적 파일 집합, 동일 치환 규격 적용 (Batch 4) |
| Step 11 ∥ 12 ∥ 13 | 상호 배타적 파일 집합 — pilot 2군 + `docs/` (Batch 5) |
| Step 3, 6~13 → Step 14 | 스윕은 전 문서 개정 완료 후에만 의미 있음 |
| Step 14 → Step 15 | 배포 대상이 확정된 뒤 배포·실증 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 신규 STATE.md에 파생 4종(마커/표/현재 상태/다음 액션) 잔존 0 | TS-001 | grep 4패턴 전부 0건 |
| F-001 | 저널 2섹션 생성·보존 | TS-002 | `advance`/`mark`/`block` 후에도 `## 의사결정 로그`·`## 블로커` 존재 |
| F-001 | 의사결정 로그 무손실 (정상 경로) | TS-003 | 표에 1행 추가 + 기존 행 보존 + `#` 연속 |
| F-001 | 의사결정 로그 무손실 (STATE.md 부재) | TS-004 | 저널 자동 복구 + 1행 기재 + `ok:true` |
| F-001 | 저널 쓰기 실패 시 비차단 + stdout 회수 | TS-005 | `ok:true`/exit 0 + `journal_warning.decision` 원문 |
| F-001 | `> 최종 갱신:` 존치 동작 (D-3) | TS-021 | `advance`/`mark` 후 타임스탬프 갱신 |
| F-002 | 마커 부재/손상 상태에서 갱신 명령 성공 | TS-006 | 3케이스 전부 exit 0 |
| F-002 | 에러 카탈로그 코드·문서 정합 | TS-007, TS-015 | `len(ERROR_CODES)` == README 종수, `marker_missing`/`import_failed` 부재 |
| F-002 | `validate`가 마커를 위반으로 보지 않음 | TS-008 | `violations[]`에 `marker_missing` 0건 |
| F-002 | `--import-existing` 명시적 거부 | TS-009 | `import_existing_removed` + exit 1 + 단일 라인 JSON |
| F-002 | `--rows-from` 정상 경로 무손상 | TS-022 | `key` 영속화 포함 기존 동작 동일 |
| F-002 | 응답 계약 호환 | TS-023 | 갱신 5명령 응답 키 삭제 0건 |
| F-003 | `show --format md`가 state.json 단일 파생 | TS-010 | 표 + 상태 3줄 포함, `marker_present:false` |
| F-003 | 레거시 동결 표 미노출 + 배너 | TS-011 | state.json 값 반환 + 배너 1줄 + `marker_present:true` |
| F-003 | 세션 복원 서술 교체 | TS-012 | "STATE.md를 Read하여 재개" 0건 |
| F-003 | `--format full` 배너 극성 | TS-024 | 레거시만 배너, 원문 무손상 |
| F-003 | `show` 응답 계약 | TS-025 | 3포맷 키 집합 동일 |
| F-004 | 하네스 3문서 구형 0 / 신형 채택 | TS-013 | 표 템플릿·마커 명세·`## 현재 상태` 0건 + 저널·`show` 명시 |
| F-004 | pilot·가이드 표 전제 0 + 규율 존치 | TS-014 | 표 전제 0건 AND 표준 문구 A >=1건/파일 |
| F-004 | SSOT 자기모순 해소 | TS-016 | "STATE.md…유일 SSOT" 0건 |
| F-004 | `marker_missing` 서술 0 | TS-017 | 현재시제 본문 0건 |
| F-004 | changelog·brain 무변경 | TS-026 | `git diff --stat` 해당 경로 0 |
| F-005 | 5개 서브명령 실동작 | TS-018 | 전부 `ok:true` |
| F-005 | 회귀 커버리지 유지 | TS-019 | fail 0 AND 삭제 1:1 대응 AND 신규 기능 5종 커버 |
| F-005 | `show` 2포맷 실동작 | TS-020 | 정상 현황 반환 |
| F-005 | 배포 정합 | TS-027 | 소스 ↔ `~/.opal/` diff 0 |

### 5.2 회귀 테스트

- [ ] `cd opal/tools/state-tool && python3 -m pytest tests/ -v` → **fail 0** + 삭제/신규 대응 감사 통과 (변경 전 기준선 308 passed + 32 subtests는 → D-2 §1.4, 참고값이며 하한이 아님)
- [ ] `test_todo_mirror_hook.py` 전건 통과 — `build_todo_mirror`는 `state["rows"]`만 사용하므로 무영향이어야 한다
- [ ] `spec-validate` / `verify` 서브명령 무영향 확인 (본 태스크 미접촉 경로)
- [ ] 레거시 태스크(001~093) STATE.md 바이트 무변경 — `git status`에 `tasks/` 변경 0
- [ ] **구형 잔존 0 스윕 명세** (Step 14 — 교체형 목표 AC (a) 검증 방법):

```bash
cd /Volumes/Data/AiStudio/workspace/opal
# (1) 현재시제 본문 대상: changelog/변경이력 행·brain·tasks·backup 제외
grep -rn -e 'pipeline:start' -e 'pipeline:end' -e 'marker_missing' \
         -e '마크다운 표 직접 편집' -e '## 다음 액션' -e 'import-existing' \
         opal/ docs/ .opal/AGENT.md \
  | grep -v '^opal/tools/state-tool/tests/' \
  | grep -v -E '^\S+:[0-9]+:\| v[0-9]' \
  | grep -v '변경이력'
# 기대: 0건
# (2) 표 헤더 잔존
grep -rn '| # | 단계 | 항목 | 상태 | 시점 |' opal/ docs/ | grep -v '^opal/tools/state-tool/tests/'
# 기대: 0건 (render_pipeline_table 내부 리터럴은 state_tool.py 1건만 허용)
# (3) 도구 규율 보존 (H-10 역검증 — 0이면 안 됨)
grep -rln 'state-tool.*로만 수행' opal/ docs/ .opal/AGENT.md | wc -l
# 기대: 8 이상
```

### 5.3 코드/문서 품질

- [ ] `state_tool.py` 상단 `@header` description에 094 변경 요약 반영 ([MUST] `docs/CONVENTIONS.md` @header 규칙)
- [ ] 표준 라이브러리만 사용 — 신규 패키지 도입 0 (→ D-2 §2)
- [ ] 변경한 모든 문서에 변경이력 1행 추가(버전·KST 일시·변경내용·태스크 번호 094)
- [ ] 신규 예시 명령이 `--task-step` 사용 ([MUST] `docs/CONVENTIONS.md` §State 관리: "`--row`는 deprecated 별칭(신규 문서·프롬프트에 사용 금지)")
- [ ] `state.schema.json` 변경이 `description` 문자열로만 국한 (`git diff` 확인)
- [ ] 배포 경계 준수 — `~/.opal/` 직접 편집 0건, `install-mac.sh` 경유 ([MUST] `.opal/AGENT.md` §금지사항)
- [ ] 플랫폼 분기 하드코딩 0건 — R-5는 공통 CLI(`show`)로만 해결 ([MUST] `.opal/AGENT.md` §금지사항)

### 5.4 보안

- [ ] `.env`·인증 파일이 `.gitignore`에 포함되어 있는가 (변경 없음 확인)
- [ ] 코드에 하드코딩된 토큰/시크릿이 없는가
- [ ] `ensure_journal_skeleton`이 태스크 폴더 밖에 파일을 생성하지 않는가 — 경로는 `task_path / "STATE.md"` 고정(`save_state_md:229`), 경로 조립에 사용자 입력 미개입
- [ ] `journal_warning` 페이로드에 절대 경로·사용자 홈 경로가 노출되지 않는가 — 예외 메시지에 경로가 포함되면 파일명만 남기고 절삭
- [ ] `resolve_owner_placeholder`(`:237-264`) fail-safe 동작 무변경 — note 경로 6곳 유지

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 15개 | 복잡 |
| 변경 파일 수 | 약 29개 | 복잡 |
| 모듈 범위 | 다중 (도구 코드 + 테스트 + 하네스 + pilot 10종 + 프로젝트 docs) | 복잡 |
| 작업 유형 | 대규모 개선(구조 재정의 + 선재 결함 정정) | 복잡 |
| 외부 의존성 | 없음 (표준 라이브러리 전용) | 단순 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1 (순차, 단일 에이전트 — 파일 충돌 방지)
  A1: opal-be-agent  ── Step 1 → Step 2 → Step 3   [state_tool.py, schema, tests]

Batch 2 (순차)
  A2: opal-task-agent ── Step 4                     [README.md — 실측 종속]

Batch 3 (순차)
  A3: opal-task-agent ── Step 5                     [하네스 SSOT 3종 — 규칙 원천]

Batch 4 (병렬 5-way)
  A4: opal-task-agent ── Step 6   [harness 보조 3]
  A5: opal-task-agent ── Step 7   [harness 잔여 3]
  A6: opal-task-agent ── Step 8   [op-task + dev 2]
  A7: opal-task-agent ── Step 9   [wireframe/gc/project]
  A8: opal-task-agent ── Step 10  [project-dev 3]

Batch 5 (병렬 3-way)
  A9:  opal-task-agent ── Step 11 [sdd 3]
  A10: opal-task-agent ── Step 12 [project-loop 2 + .opal/AGENT.md]
  A11: PM 직접        ── Step 13 [docs/ 2]

Batch 6 (순차)
  A12: opal-task-agent ── Step 14 [전역 스윕 검증]
  A13: opal-task-agent ── Step 15 [배포 + 실증]
```

**그룹핑 근거**: (1) `state_tool.py`를 건드리는 Step 1·2·3은 **반드시 동일 에이전트에 직렬 배치**한다 — 동시 편집 시 후행 저장이 선행 편집을 덮어쓴다. (2) Batch 4·5의 병렬 에이전트는 파일 집합이 상호 배타적이며 동일 치환 규격(§3.4.2)을 공유하므로 결과 일관성이 보장된다. (3) `docs/` 갱신은 PM 직접 수행(영역 규칙).

> [MUST] 병렬 에이전트에게 디스패치할 때 §3.4.2 **표준 문구 A/B 원문과 치환 규격 12행을 그대로 주입**한다 — 에이전트가 각자 문구를 창작하면 8회+ 반복 지점의 문구가 갈라져 H-10이 현실화된다.

### C-2. 스킬 요구사항

| 필요 역량 | 매칭 | 갭 |
|----------|------|-----|
| Python CLI 리팩터링 | 기존 역량(`opal-be-agent` 페르소나) | 없음 |
| pytest 회귀 테스트 재작성 | 기존 역량 | 없음 |
| 프레임워크 문서 일괄 치환 | §3.4.2 치환 규격이 인라인 지침으로 충분 | **스킬 신설 불필요** — 본 태스크 1회성 |
| 기술 스택 추천 스킬 | `trailofbits/modern-python` 검토 → **미적용**. 본 태스크는 표준 라이브러리 전용 유지가 제약이며 uv/ruff/async 패턴 도입은 범위 밖 | - |

### C-3. 도구 요구사항

| 도구 | 용도 | 신규 설치 |
|------|------|----------|
| `python3` + `pytest`(+`pytest-subtests`) | 회귀 테스트 | 기존 |
| `bash install-mac.sh` | `~/.opal/` 재배포 | 기존 |
| `~/.opal/tools/state-tool/run.sh` | 실동작 실증 | 기존 |
| `grep`/`git diff` | 구형 잔존 0 스윕 (§5.2) | 기존 |
| MCP | **불필요** — 외부 라이브러리·API 조사 없음 (→ D-2 §6.3) |

### C-4. 테스트 전략

| 계층 | 내용 | 명령 |
|------|------|------|
| L1 단위/CLI | `state_tool.py` 서브명령 계약 | `cd opal/tools/state-tool && python3 -m pytest tests/test_state_tool.py -v` |
| L2 통합 | 실파일 기반 저널 복원력·레거시 공존·실패 주입 | `TestJournalResilience` / `TestLegacyCoexistence` (subprocess + 실제 파일) |
| L2 통합 | todo 미러 훅 무영향 | `python3 -m pytest tests/test_todo_mirror_hook.py -v` |
| L3 산출물 | 구형 잔존 0 / 표준 문구 존재 스윕 | §5.2 grep 명세 (결정론 검증) |
| L3b 실동작 | 신형 구조 5명령 완주 + `show` 2포맷 | Step 15 실증 로그 |

> TEST 단계는 `opal-test-agent`가 TEST-SCENARIO.md 기반으로 별도 수행한다 — EXECUTE 체크리스트에는 배정하지 않는다.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| BE | Python 3 (표준 라이브러리 전용: `re`/`json`/`pathlib`/`argparse`/`subprocess`/`os`) | `opal-be-agent` (`trailofbits/modern-python` 검토 후 미적용 — §C-2) |
| 테스트 | pytest + pytest-subtests | `opal-be-agent` |
| 문서 | Markdown (프레임워크 산출물 본체) | `opal-task-agent` |
| 스키마 | JSON Schema (`state.schema.json` — description만 변경) | - |
| 배포 | Bash (`install-mac.sh`, `run.sh`) | - |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 순수 내부 CLI/문서 리팩터링 — 외부 라이브러리·API 문서 조회 불필요 (→ D-2 §6.3) |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | 렌더·마커·파싱·의사결정로그 함수 + 9서브명령 구현 (2,611줄) — 변경 본체 |
| D-2 | 기획 | ANALYSIS.md | `tasks/094-260815-opd-STATE-저널화/ANALYSIS.md` | 함수 생사 판정·마커 차단 지점·참조 4분류·테스트 영향권 실측 |
| D-3 | 설계 | state-tool README | `opal/tools/state-tool/README.md` | 서브명령 명세·에러 카탈로그(39종 stale)·SSOT 서술(`:13`) |
| D-4 | 소스 | state.schema.json | `opal/tools/state-tool/schema/state.schema.json` | state.json 필드 SSOT — description 3곳(`:4,43,129`) 외 불변 |
| D-5 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | §3 State(`:160-183`) — 개정 대상 SSOT, 에러 종수 23종 stale |
| D-6 | 설계 | harness/state.md | `opal/core/references/harness/state.md` | 이벤트 표·todo 미러·세션 복원·SSOT 자기모순(`:66`) |
| D-7 | 설계 | harness/state-template.md | `opal/core/references/harness/state-template.md` | 템플릿·마커 명세(`:24-40`) — 전면 교체 대상 |
| D-8 | 설계 | verification-loop-guide.md | `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | 세션 복원(`:517-524`)·루프 진행률(`:505-515`) — R-5 소비 지점 |
| D-9 | 소스 | test_state_tool.py | `opal/tools/state-tool/tests/test_state_tool.py` | 회귀 291 함수 / 308 passed 기준선 |
| D-10 | 기획 | TASK.md | `tasks/094-260815-opd-STATE-저널화/TASK.md` | 요구사항 R-1~R-9·확정 설계 방향·제약 |
| D-11 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | §State 관리·§Citation·@header — [MUST] 인용 원천 |
| D-12 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | `:207` State 서술 |
| D-13 | 설계 | PROJECT.md | `docs/PROJECT.md` | §프로젝트 구성(`:210,212`) — 에이전트 라우팅 근거 |
| D-14 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | §4 PLAN 인용 의무 / §5 레거시 호환 원칙 |
| D-15 | 설계 | .opal/AGENT.md | `.opal/AGENT.md` | §금지사항 — 배포 경계·플랫폼 분기 [MUST] |
| D-16 | 소스 | 093 STATE.md | `tasks/093-260815-opd-사용자확인행-자동승인-일원화/STATE.md` | 레거시 포맷 실측 샘플(`:11-35`) — H-4 픽스처 원본 |

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| 1 | 의사결정 로그 유실 (H-1) — `append_decision_log`의 조용한 no-op(`:349-350`) | F-001 | **High** | `ensure_journal_skeleton`으로 표 헤더를 **선행 보증** + 실패 시 `journal_warning.decision`로 stdout 회수. TS-003~TS-005로 3중 검증 |
| 2 | SSOT/미러 순간 불일치 (H-3, → D-2 §5 R-B) | F-001 | Medium | `save_state_json` 선행 순서 **유지** + 저널 fail-open. 근거·트레이드오프 §3.1.2 (5)에 명문화 |
| 3 | 레거시 STATE.md 공존 예외 (H-4, R-I) | F-002 | Medium | 마커 하드 차단 경로 삭제로 크래시 소멸 + `ensure_journal_skeleton`은 append만 수행(본문 무손상). `TestLegacyCoexistence`로 실물 사본 검증 |
| 4 | `show`가 레거시 동결 표를 최신인 양 반환 (H-5) | F-003 | **High** | 렌더 원천을 `state.json` 단일로 승격 + STATE.md 본문 추출 경로 삭제 + 배너. TS-011은 표와 state.json을 **의도적으로 불일치**시켜 검증 |
| 5 | 응답 계약 파손 (H-6, 제약 ③) | F-002, F-003 | Medium | 기존 키 삭제 0 원칙 — `marker_present`·`import_existing` 키 존치(값만 변경), `journal_warning`은 조건부 **추가**만. TS-023·TS-025 키 스냅샷 |
| 6 | 커버리지 공백 / padding 유입 (H-8) | F-005 | Medium | 삭제 25건을 D-1/D-2/R-3에 1:1 매핑해 정당성을 증명하고, 신규 기능 5종 커버를 완료 기준으로 삼는다. 숫자 하한은 두지 않는다 |
| 7 | 구형 잔존 0 미달 / changelog 오삭제 (H-9) | F-004 | Medium | §5.2 결정론 grep 스윕(3종) + Step 14 전용 검증 Step + 치환 규격 #12 [MUST] |
| 8 | 도구 규율(C) 동반 소실 (H-10, R-J) | F-004 | Medium | 표준 문구 A를 SSOT로 확정하고 병렬 에이전트에 **원문 주입**. §5.2 (3) 역검증 grep(8건 이상)으로 확인 |
| 9 | 미배포 상태 실증에 의한 거짓 통과 (H-11) | F-005 | Medium | Step 15에서 `install-mac.sh` 실행 후 `diff` 0 확인을 실증 **선행 조건**으로 고정 |
| 10 | oppd 검증 루프 상태 유실 (H-12) | F-003 | Low~Medium | 대체 보관처를 §3.3.2 (4)에서 지정(`## 검증 루프` 자유 기재 + `show`) 후 Step 10에서 문서 반영 |
| 11 | 병렬 문서 에이전트 간 문구 분기 | F-004 | Low~Medium | C-1 [MUST] — 표준 문구 원문 + 치환 규격 12행 주입 |
| 12 | `--import-existing` 미발견 호출부 (H-7) | F-002 | Low | 전역 grep 실측 결과 pilot·훅·스크립트 호출 0건 확인 완료. Step 14에서 재확인 |
| 13 | 에러 종수 산식 실측 불일치 | F-002, F-004 | Low | [MUST] 문서 기입 전 코드 실측 선행 — 불일치 시 실측값 채택 + DONE.md 기록 (§1.5 D-5). **093 머지로 43→44 재산정 완료**. 완료 기준·시나리오에 종수 리터럴을 중복 고정하지 않는다 |

---

## 부록 A. 문서/코드 불일치 기록 (코드 기준 설계 원칙 적용)

> `.opal/AGENT.md` 및 PM 지시: "문서와 실제 코드가 다르면 코드(실질적 문서) 기준으로 설계하고, 불일치를 PLAN.md에 기재한다."

| # | 문서 서술 | 코드 실측 | 본 PLAN의 채택 |
|---|----------|----------|--------------|
| 1 | `README.md:279` "에러 코드 카탈로그 (39종 SSOT)" | `len(ERROR_CODES)` = **44** (`state_tool.py:81-133`) | 코드 채택 — 변경 후 실측값으로 재기입 (D-5 ①) |
| 2 | `opal-harness.md:181`·`harness/state.md:21` "전체 에러 카탈로그 23종" | 44종 | 코드 채택 + 하네스에서 **숫자 삭제**(포인터화) |
| 3 | `README.md:284` `marker_missing` 발생 명령 = "init(--import-existing 외)/advance/mark/block/add-row" | `init`은 어느 경로로도 마커 하드 차단을 일으키지 않음(`cmd_init:1289-1296` 자동 삽입). `status`(`:1900`)·`gate-pass`(`:1979`)가 누락 | 코드 채택 — R-3으로 행 자체 삭제하여 자동 해소 |
| 4 | `harness/state.md:66` "STATE.md/state-tool이 진행 현황의 유일한 SSOT" | `README.md:13` "SSOT: `state.json`" + `cmd_show`가 state.json 기반 | 코드 채택 — `state.json` 단일 SSOT로 통일 (D-5 ②) |
| 5 | ANALYSIS §1.3.1 `render_pipeline_table` = "사멸" | `cmd_show:1380` 폴백이 유일 경로로 승격되면 계속 필요 | **PLAN에서 존치로 정정** (§3.2.2 (4)) |
| 6 | `state-template.md:31` "마커가 손실되면 갱신 명령이 `marker_missing`으로 거부된다. `show` 명령만 fallback 출력으로 우회" | R-3 적용 후 전 명령 미차단 | 삭제 (치환 #4) |
| 7 | ANALYSIS §3.2 "`opal/agents/*/AGENT.md` ~11건 확인 필요" | 표/마커/현황판 키워드 **0건** — 전건 순수 (C) 도구 규율 | **개정 제외** 확정 (§2.4.1) |
