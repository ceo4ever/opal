# ANALYSIS: STATE.md 파생 섹션 제거 — 저널로 재정의

> 작성일: 2026-08-15
> 입력: TASK.md
> 출력: ANALYSIS.md

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | 렌더·마커·파싱·의사결정로그 함수 전수 + 서브명령 구현 (2,611줄) |
| D-2 | 설계 | state-tool README | `opal/tools/state-tool/README.md` | 서브명령 명세·에러 카탈로그 |
| D-3 | 소스 | state.schema.json | `opal/tools/state-tool/schema/state.schema.json` | state.json 필드 SSOT (변경 대상 아님) |
| D-4 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | §3 State 정의 — 개정 대상 SSOT |
| D-5 | 설계 | state.md | `opal/core/references/harness/state.md` | STATE.md 이벤트 표·todo 미러·세션 복원 |
| D-6 | 설계 | state-template.md | `opal/core/references/harness/state-template.md` | STATE.md 템플릿·마커 명세 |
| D-7 | 설계 | header-rules.md | `opal/core/references/harness/header-rules.md` | code-scan 폴백 STATE 기록 규약 서술 |
| D-8 | 설계 | verification-loop-guide.md | `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | 세션 복원 절차(:520) — STATE.md Read 소비 지점 |
| D-9 | 소스 | test_state_tool.py | `opal/tools/state-tool/tests/test_state_tool.py` | 회귀 테스트 291개 함수 (6,084줄) |
| D-10 | 소스 | test_todo_mirror_hook.py | `opal/tools/state-tool/tests/test_todo_mirror_hook.py` | todo 미러 훅 테스트 |
| D-11 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | §227 State 규칙 — 표 전제/도구 규율 혼재 판정 대상 |
| D-12 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | STATE.md 위치 서술 |
| D-13 | 소스 | 093 STATE.md 실물 | `tasks/093-260815-opd-사용자확인행-자동승인-일원화/STATE.md` | 현행(마커·표 有) 포맷 실측 샘플 — 레거시 공존 시나리오 근거 |
| D-14 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | ANALYSIS 인용 규칙 §4 — 본 문서 작성 기준 |

> §7 영역 간 용어 일관성 검토: FE/BE/ERD/IA 영역 쌍 해당 없음 — 내부 CLI+문서 리팩터, `decision_required` 0건.

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/tools/state-tool/state_tool.py` | 9서브명령 구현체(2,611줄) | Yes — 함수 삭제 3 / 재작성 3 / 존치 5 / R-4 결정종속 1 | `state_tool.py:219-1350` |
| `opal/tools/state-tool/README.md` | 서브명령 명세+에러 카탈로그 | Yes — `--import-existing` 절, `marker_missing` 트리거 오기재 수정, 에러 총수 정정 | `README.md:58,157,279,284` |
| `opal/tools/state-tool/schema/state.schema.json` | state.json 필드 SSOT | No (제약① — 스키마 불변) | - |
| `opal/tools/state-tool/tests/test_state_tool.py` | 회귀 테스트(291 함수) | Yes — 마커/표/import 의존 테스트 재작성 | §1.4 |
| `opal/core/references/opal-harness.md` | 하네스 SSOT §3 | Yes — 파생 서술·에러종수(23종, stale) 정정 | `opal-harness.md:167,169,181` |
| `opal/core/references/harness/state.md` | STATE.md 이벤트표·todo미러·세션복원 | Yes — SSOT 서술 자기모순 해소 + 표 전제 서술 6건 | `state.md:15,21,27,57,66` |
| `opal/core/references/harness/state-template.md` | STATE.md 템플릿·마커 명세 | Yes — 템플릿 전면 교체(저널 구조로) | `state-template.md:5,24,26-40,63-72` |
| `opal/core/references/harness/header-rules.md` | code-scan 폴백 STATE 기록 규약 | 경미 — "현황판 표 행 아님" 어구 정리 | `header-rules.md:139,141` |
| `opal/skills/opal-pilot-*/SKILL.md`(10종) | pilot별 State Gate 호출 규율 | Yes — 표 전제 어구만 정정, 도구규율 문장은 존치·재작성 | §3.2 |
| `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | 세션 복원 절차 | Yes — "STATE.md Read" → `state-tool show` 호출로 교체 | `verification-loop-guide.md:520` |
| `docs/CONVENTIONS.md` | §227 State 규칙 | Yes — "마크다운 표 직접 편집 금지" 문장 분리(B/C 혼재) | `CONVENTIONS.md` §227 |
| `docs/ARCHITECTURE.md` | STATE.md 위치 서술 | 확인 필요(참조 1건, 표 전제 여부 PLAN에서 재확인) | grep 1건 |
| `.opal/brain/pages/**` | 브레인 이력 페이지 | No — (D) 과거 이력, 소급 개정 대상 아님 | §3.2 (D) 분류 |
| `opal/tools/memory-tool/tests/**` | 074 히스토리 텍스트 fixture | No — (D) 과거 이력 문자열, 동작과 무관 | grep 2건 |
| `opal/agents/*/AGENT.md`(일부) | STATE.md 언급 에이전트 문서 | 확인 필요(11건 중 표 전제분만) | §3.2 |

### 1.2 아키텍처 패턴

- **SSOT/미러 분리 패턴(기존)** — `state.json`이 SSOT, STATE.md 표는 `state-tool`이 자동 렌더하는 미러라는 설계가 이미 `state-tool/README.md:13`("SSOT: state.json (마크다운 표는 도구가 자동 렌더한 미러)")에 명문화되어 있다. 이번 태스크는 "미러 렌더 자체를 제거"하는 다음 단계다.
- **단일 후처리 관문(chokepoint) 패턴** — `advance`/`mark`/`block`/`add-row`/`status`/`gate-pass` 6개 서브명령이 모두 `sync_state_md()`(`state_tool.py:365-392`) 한 함수로 STATE.md 갱신을 위임한다(호출 지점: `:1453,1636,1683,1853,1900,1979`). 이 관문 내부에서 **마커 게이트 → 표 갱신 → 헤더 갱신 → 현재상태 갱신 → 다음액션 갱신 → 의사결정로그 기재**가 순차 결합되어 있다(`:375-390`).
- **HTML 주석 마커 경계 치환 패턴** — `<!-- pipeline:start/end -->`(`:135-136`)로 감싼 영역만 정규식 교체(`replace_pipeline_section:288-298`), 마커 부재 시 `None` 반환(호출자 책임 위임).
- **fail-safe 폴백 패턴(재사용 가능)** — `cmd_show`의 md 포맷 분기(`:1376-1393`)는 마커가 없어도 죽지 않고 `state.json.rows[]`에서 표를 즉석 재구성해 반환한다. 이 폴백 경로는 **R-5("현황 조회는 show로 일원화")가 그대로 재사용할 수 있는 이미 존재하는 구현**이다.

### 1.3 의존성 맵 (Q1 — state_tool.py 렌더 경로 의존 그래프)

#### 1.3.1 8개 대상 함수 정의·호출자·생사 판정

| 함수 | 정의 줄 | 호출자(파일:줄번호) | 판정 |
|------|--------|---------------------|------|
| `load_state_md` | `:219` | `sync_state_md:375` / `cmd_init(import):1269,1300` / `cmd_show:1357` / `cmd_validate:1735` | **존치** — `sync_state_md` 외에도 3개 명령이 독립 호출하는 순수 파일 I/O 유틸 |
| `save_state_md` | `:227` | `sync_state_md:392` / `cmd_init(import):1296,1306` | **존치** — 순수 쓰기 I/O, `append_decision_log` 결과를 파일에 쓰는 데 계속 필요 |
| `render_pipeline_table` | `:270` | `sync_state_md:380` / `cmd_init(import):1265` / `cmd_show:1380` | **사멸** — 표 자체가 없어지므로 3개 호출부 전부 제거 대상 |
| `replace_pipeline_section` | `:288` | `sync_state_md:381` / `cmd_init(import):1270` | **사멸** — 마커 영역 자체가 없어지므로 무의미 |
| `update_state_md_header` | `:300` | `sync_state_md:385` / `cmd_init(import):1285` | **재검토 대상(미확정)** — "> 최종 갱신:" 라인은 표/마커와 무관한 범용 타임스탬프. TASK.md R-1 AC는 표·마커·`## 현재 상태`·`## 다음 액션` 파생만 제거 대상으로 명시하고 이 헤더 라인은 언급 안 함 → **PLAN에서 존치/삭제 결정 필요** |
| `sync_state_md` | `:365` | `cmd_advance:1453` / `cmd_mark:1636` / `cmd_block:1683` / `cmd_add_row:1853` / `cmd_status:1900` / `cmd_gate_pass:1979` | **재작성(완전 삭제 아님)** — 6개 명령의 공유 관문이므로 완전 삭제 불가. 마커게이트·표갱신·현재상태갱신·(다음액션갱신은 미확정 종속) 로직만 제거하고 "헤더(존치 여부 별도 결정)+의사결정로그 기재"만 남긴 축소판으로 재작성 |
| `parse_existing_state_md` | `:1064` | `cmd_init(import):1183` | **R-4 결정 종속** — §1.3.6 참조 |
| `_build_new_state_md` | `:1317` | `cmd_init(new):1291` | **재작성(완전 삭제 아님)** — `cmd_init`은 신규 STATE.md를 여전히 생성해야 하므로, 표·마커 없이 제목+헤더(재검토)+의사결정로그 빈 표+블로커 "없음"만 담은 저널 템플릿으로 재작성 |

> `opal/tools/state-tool/tests/test_state_tool.py`에서는 8개 함수명이 주석/docstring 서술로만 언급되고(예 `:1492,1537`) 실제 import·직접 호출은 없다 — 테스트는 CLI subprocess 실행 방식이라 함수 삭제가 테스트 실행 자체를 깨뜨리지 않는다(대신 stdout/파일 내용 assert가 깨진다, §1.4 참조). `opal/` 전체(state_tool.py 제외)에서 8개 함수명을 참조하는 곳은 grep 결과 0건 — 프레임워크 다른 컴포넌트가 이 함수들을 직접 import하지 않는다.

#### 1.3.2 PM 사전 목록 밖에서 추가로 발견된 동일 클러스터 함수

| 함수 | 정의 줄 | 판정 | 근거 |
|------|--------|------|------|
| `update_current_status_section` | `:308` | **사멸** — `## 현재 상태` 섹션 자체가 R-1 AC(a) 제거 대상 | `sync_state_md:385` 호출 |
| `update_next_action_section` | `:324` | **R-1 §다음 액션 미확정 항목에 종속** | `sync_state_md:387` 호출, docstring `:326` |
| `append_decision_log` | `:340-357` | **완전 존치, 무변경** — `"## 의사결정 로그\n\|..."` 정규식 매칭만 사용, 마커·표·`render_pipeline_table` 어디에도 의존하지 않음 | `:344-345` |
| `_derive_next_action` | `:497` | **완전 존치** — `state["rows"]`만 순회, STATE.md 텍스트 무관 | `:501` |
| `build_todo_mirror` | `:459` | **완전 존치** — `state["rows"]`만 사용 | `:476-493` |

#### 1.3.3 의사결정 로그·블로커 보존 경로 실측 — 핵심 리스크

> **[MUST] 확인된 리스크**: 현재 코드 구조에서 의사결정 로그 기재는 마커 게이트 통과에 종속되어 있다.

- `sync_state_md:375-378` — `load_state_md`가 `None`(파일 부재)이면 `err(command, "marker_missing")`로 **즉시 종료**(`sys.exit`, `:155-169` `err()` 정의).
- `sync_state_md:380-383` — `replace_pipeline_section`이 `None`(마커 부재)이어도 동일하게 `err(..., "marker_missing")`로 **즉시 종료**.
- `append_decision_log` 호출은 그 **뒤**인 `:389-390`에 위치한다. 즉 **마커가 없으면 의사결정 로그 기재 자체가 차단된다** — TASK.md 배경분석(3) "미러가 SSOT를 인질로 잡는 구조"가 코드 레벨로 정확히 확인된다.
- **추가로 확인된 순서 문제**: `save_state_json()`(state.json 갱신)이 `sync_state_md()` 호출보다 **먼저** 커밋된다(예: `cmd_mark:1601` vs `sync_state_md` 호출 `:1636`). 마커 누락 시 **state.json은 이미 갱신되었으나 STATE.md·의사결정로그는 갱신되지 않은 채 exit 1** — SSOT/미러 순간 불일치 윈도우가 실제로 존재한다.
- **블로커 섹션은 애초에 코드가 본문을 쓰지 않는다** — `cmd_block:1683`은 `sync_state_md(..., status_text="블로커")`만 호출하며, 이는 `## 현재 상태`의 `- 상태:` 한 줄만 변경한다(`update_current_status_section:308-322`). `## 블로커` 섹션 **본문**은 어떤 함수도 갱신하지 않는다(`state-template.md:39` "PM이 수동 갱신"과 일치). → **R-2 AC 중 블로커 보존은 이미 구조적으로 안전하며, 위험은 의사결정 로그 쪽에 집중된다.**
- **결론**: R-2를 충족하려면 `append_decision_log`(+`save_state_md`) 호출을 `sync_state_md`의 마커 게이트 앞단 또는 완전히 독립된 경로로 재배선해야 한다. 재배선 자체는 안전하다 — `append_decision_log`(`:340-357`)와 `_derive_next_action`(`:497`)이 이미 표/마커와 무관하게 동작하기 때문이다.

#### 1.3.4 `next_action` 파생과 렌더 경로 결합

- `_derive_next_action`(`:497`)·`update_next_action_section`(`:324`, 072 태스크 도입)은 `sync_state_md`의 `next_action=` 파라미터로 전달되어 `:387`에서 호출된다.
- `cmd_advance`(`:1453` 부근)·`cmd_mark`(`:1639` `next_action=state["next_action"]`)만 값을 넘기고, `cmd_block`/`cmd_add_row`/`cmd_status`/`cmd_gate_pass`는 `next_action` 인자를 넘기지 않는다(`None` 유지 계약, docstring `:326` "block/add-row/status 등 미접촉").
- `_build_new_state_md`(`:1317`)는 `next_action` 파라미터가 없어 처음부터 무관(072 이후로도 무변경).
- 결론: `next_action` **파생 값 계산**(`state.json` 필드)은 STATE.md 렌더와 독립적으로 이미 성립한다. STATE.md 쪽 "다음 액션" **섹션 표시**만 파생 렌더에 묶여 있으므로, TASK.md 미확정 항목("완전 제거 vs 자유기재 존치")의 영향 범위는 `update_next_action_section` 1개 함수로 국한된다.

### 1.3.5 마커 게이트(`marker_missing`) 차단 지점 (Q2)

| # | 위치 | 트리거 조건 | 차단 성격 |
|---|------|-----------|----------|
| 1 | `state_tool.py:377-378`(`sync_state_md`) | STATE.md 파일 자체 부재 | **하드 차단**(`sys.exit(1)`) |
| 2 | `state_tool.py:382-383`(`sync_state_md`) | 마커 없음 | **하드 차단**(`sys.exit(1)`) |
| 3 | `state_tool.py:1359-1363`(`cmd_show --format json`) | 마커 부재 | **비차단** — `marker_present:false`, `ok:true` |
| 4 | `state_tool.py:1369-1374`(`cmd_show --format full`) | 마커 부재 | **비차단** — 경고 배너 prepend |
| 5 | `state_tool.py:1376-1393`(`cmd_show --format md`) | 마커 부재 | **비차단** — `state.json.rows[]` 즉석 재구성 폴백 |
| 6 | `state_tool.py:1734-1740`(`cmd_validate`) | 마커 부재 | **간접 차단** — `violations[]`에 반영되어 `validate` 자체가 exit 1 |

**서브명령별 실제 분기 (하드 차단만)**:

| 서브명령 | 마커 하드 차단 여부 | 근거 |
|---------|---------------------|------|
| `init`(비-import) | 아니오 — `_build_new_state_md`가 항상 새 마커 포함 생성 | `cmd_init:1289-1296` |
| `init --import-existing` | 아니오 — `None`이면 자체 삽입 폴백(`:1271-1284`)으로 복구, `err()` 없음 | `cmd_init:1267-1284` |
| `advance`/`mark`/`block`/`add-row`/`status`/`gate-pass` | 예 — `sync_state_md` 경유(`:1453/1636/1683/1853/1900/1979`) | 상동 |
| `show` | 아니오(비차단 폴백) | `cmd_show:1350-1405` |

**ERROR_CODES 실측**: 총 **44종**(dict 키 실측, `state_tool.py:81-133`). 마커 전용 에러 코드는 `marker_missing` **1종뿐**(관련 코드 추가 없음).

> **문서/코드 불일치 발견 (PM 보고 필요)**:
> 1. `README.md:284`는 `marker_missing` 발생 명령을 `"init(--import-existing 외)/advance/mark/block/add-row"`로 기재하나, 실측 코드에는 (a) `init`이 어떤 경로로도 마커 하드 차단을 일으키지 않고(자동 삽입으로 대체) (b) `status`·`gate-pass` 2개 명령이 표에서 누락되어 있다(둘 다 실제로는 차단 대상).
> 2. 에러 카탈로그 종수가 **3중 불일치** — 코드 실측 44종(`state_tool.py:81`) vs README 헤더 "39종"(`README.md:279`) vs 하네스 문서 "23종"(`opal-harness.md:181`, `harness/state.md:21` 등). 이는 이번 태스크와 무관한 **선재 결함**(091 태스크에서 5종 추가 후 문서 갱신 누락 추정, 39+5=44로 정합)이나, 이번 태스크가 `marker_missing`을 제거하면 종수가 다시 바뀌므로 **함께 정정할지 별도 태스크로 분리할지 PLAN에서 결정 필요**.
> 3. 하네스 SSOT 자체 모순 — `opal/core/references/harness/state.md:66` "[SSOT 불변] STATE.md/state-tool이... 유일한 SSOT"라는 서술이 `opal/tools/state-tool/README.md:13` "SSOT: state.json(마크다운 표는 도구가 자동 렌더한 미러)"과 정면 배치된다. R-6(하네스 SSOT 개정)에서 반드시 해소해야 한다.

### 1.3.6 `--import-existing` 및 하위호환 경계 (Q4)

- **의존 체인**: `cmd_init`(`:1177` `import_mode` 분기) → `load_state_md`(`:1180`) → `parse_existing_state_md`(`:1064`, 정규식 표 파싱, 호출 `:1183`) → 성공 시 `_key_source_index`/`_reattach_import_keys`(`:1102-1130`, 호출 `:1189-1206`)로 074 key 재접합.
- **재접합 로직은 표 파싱에 구조적으로 종속되지 않는다** — `_key_source_index`(`:1102-1112`)·`_reattach_import_keys`(`:1115-1130`)는 **이미 만들어진 rows(dict 리스트)**만 입력받고, 그 출처(표 파싱 결과/`state.json`/`pipeline.json`)를 구분하지 않는다. 현재 코드도 표 파싱 결과에 `state.json`(`:1192-1198`, 우선)·`pipeline.json`(`:1199-1202`, 폴백) 순으로 재접합한다. **표 파싱(`parse_existing_state_md`) 한 단계만 표에 종속되며, 나머지 재접합 로직은 표가 사라져도 무손상 재사용 가능하다.**
- `tests/test_state_tool.py:1535-1557`(`_write_state_md_table` 헬퍼)가 **마커 없이** 표만으로 STATE.md를 구성해 `parse_existing_state_md`를 호출하는 테스트가 통과한다는 점도, 표 파싱 정규식(`:1066-1069`)이 마커 토큰과 무관함을 방증한다.
- **레거시(001~093) STATE.md + 신형 state-tool 호출 시나리오**: 소급 미변경 태스크(예 D-13 `tasks/093-.../STATE.md:11-35`)는 마커+표 포함 STATE.md를 그대로 보유한다. R-3 적용 후 신형 `sync_state_md`는 마커를 찾거나 표를 교체하려 시도하지 않으므로, **레거시 표는 "더 이상 갱신되지 않는 동결 텍스트"로 남을 뿐 크래시·파싱 실패는 발생하지 않는다** — 오히려 마커 게이트 제거가 하위호환성을 개선하는 방향이다. `append_decision_log`(정규식 기반, 마커 무관)는 레거시 템플릿에서도 정상 동작한다. 유일한 잔여 리스크는 `show`가 레거시 표를 노출할 때 사용자에게 "이 표는 갱신되지 않는다"는 안내가 필요한지(§5 리스크 R-I, PLAN 결정 필요).

### 1.4 테스트 현황 (Q5)

- **실행 명령**: `cd /Volumes/Data/AiStudio/workspace/opal/opal/tools/state-tool && python3 -m pytest tests/ -v` (2026-08-15 실행)
- **결과**: **308 passed, 32 subtests passed**, 실패 0건, 3.92초. 파일: `tests/test_state_tool.py`(6,084줄, `def test_` 291개) + `tests/test_todo_mirror_hook.py`(374줄). 클래스 46개.
- 이 수치가 **R-8 AC(b)의 회귀 기준선**이다 — "기존 pass 수 이상"은 308 passed + 32 subtests를 의미한다.

**STATE.md 렌더 의존 테스트 (제거 시 영향권)**:

| 테스트(클래스.메서드) | 파일:줄번호 | 깨지는 이유 | 수정 방향 |
|---|---|---|---|
| `TestInit.test_init_creates_state_md` | `:271-278` | 마커·`## 현재 상태` assert | 수정 — 저널 산출물(의사결정 로그/블로커 존재)로 assert 교체 |
| `TestAdvance`/`TestMark` 헤더 테스트 4건 | `:403-410`,`:428-431` | `update_state_md_header` 삭제 시 헤더 4줄 소멸 | `update_state_md_header` 존치/삭제 결정(§1.3.1)에 종속 |
| `TestShow.test_show_*_marker_missing_*` 3건 | `:356-383` | `marker_present`/마커 fallback 개념 소멸 | 삭제 — `show` 자체가 R-5로 재설계 |
| `TestBlock.test_block_g6_status_blocker` | `:510` | `## 현재 상태` 섹션 제거 시 영향 | 수정 필요 |
| `TestErrorCodes.test_marker_missing` | `:711-722` | R-3으로 `marker_missing` 코드 제거 | 삭제 |
| `TestErrorCodes.test_import_failed` | `:746-757` | `parse_existing_state_md` 거취(R-4)에 종속 | R-4 결정 종속 |
| `TestErrorCodesCompleteness.*` 2건 | `:2273,:2328-2337` | `marker_missing` 제거 시 44→43종, 목록/카운트 불일치 | 수정 — `EXPECTED_CODES` 목록 갱신 + 카운트 43 |
| `TestBasicScenarios.test_scenario_marker_missing_*` | `:1391-1402` | 마커 게이트 제거 | 삭제 |
| `TestBasicScenarios.test_scenario_import_existing_*` 2건 | `:1425-1483` | R-4 결정 종속 | R-4 결정 종속 |
| `TestImportPreservesKeys`(S-a~S-e, 9건) | `:1487-1710` | `parse_existing_state_md` 제거 시 전멸 | R-4 확정("제거" 시) 삭제, "no-op 유지" 시 유지+동작 재정의 |
| `TestFreeTextPreservation` 2건 | `:1743-1779` | `## 다음 액션` 자동 파생 제거 | R-1 미확정 항목("다음 액션" 거취)에 종속 |
| `TestNextActionAutoDerive`(9건 중 5건) | `:1964-2069` | STATE.md `## 다음 액션` 렌더 제거 | 동상 — 파생 값 자체(`_derive_next_action`) 테스트 4건(`:1854-1897`)은 state.json 필드 검증이라 **생존 가능** |
| `TestG14G15DecisionLog`(트리거 1~7) | `:1285-1364` | 검사 대상이 `## 의사결정 로그`/`row.note`이지 마커/현황판이 아님 | **대부분 생존** — fixture만 표 없는 STATE.md로 조정, R-2 AC의 실측 검증 기준선 |
| `TestWorktreeFlag.test_s2_state_md_identical_*` | `:6027` | STATE.md 포맷 변경으로 베이스라인 파일 재생성 필요 | 베이스라인 갱신 |

- 총 **약 26~30건**(전체 308건 중 약 9%)이 직접 영향권. R-4(`--import-existing` 거취)·R-1(`## 다음 액션` 거취) 미확정 2건이 이 범위를 최대 ±13건 흔든다.

## 2. 외부 조사 결과

해당 없음 — 순수 내부 CLI/문서 리팩터링. 외부 라이브러리·API 의존 없음(`state_tool.py`는 `re`/`json`/`pathlib`/`argparse`/`subprocess` 등 표준 라이브러리만 사용, 코드 내 import 구문 확인).

## 3. 영향 범위

### 3.1 직접 영향

`state_tool.py` 함수: 삭제 3(`render_pipeline_table`/`replace_pipeline_section`/`update_current_status_section`), 재작성 3(`sync_state_md`/`_build_new_state_md`/`update_state_md_header`-재검토), 완전 존치 5(`load_state_md`/`save_state_md`/`append_decision_log`/`_derive_next_action`/`build_todo_mirror`), R-4 결정 종속 1(`parse_existing_state_md`군 — `_key_source_index`/`_reattach_import_keys` 포함). + `README.md` 에러 카탈로그·`--import-existing` 절. + 하네스 SSOT 3문서(`opal-harness.md`/`state.md`/`state-template.md`).

### 3.2 간접 영향 — STATE.md 참조 성격 분류 (Q3)

**참조 건수 실측 (범위: `tasks/`·`backup/`·`docs/backup/` 제외)**:

> **PM 사전 정보(754건/40+파일)와의 괴리 — PM 보고 필요**: 동일 스코프 조건(`tasks/`·`backup/` 제외)으로 두 차례 독립 실측한 결과 각각 **387건/84파일**, **385건**으로 서로 근접(약 0.5% 오차 — grep 파일 확장자 필터 차이)했으나 사전 정보 754건과는 **약 49% 괴리**한다. `tasks/`(과거 태스크 아카이브)를 포함해 재실측하면 **804건**으로 754에 근접했다 — 즉 사전 정보는 `tasks/` 아카이브를 포함한 수치였을 가능성이 높다. 이번 태스크가 실제로 개정해야 할 모집단은 **약 385~387건 / 84개 파일**로 확정한다.

| 그룹 | 건수(대략) | 성격 |
|------|------|------|
| `opal/tools/state-tool/`(코드+테스트+README+schema) | ~105 | R-1~R-4로 직접 재작성되는 구현 본체 |
| `opal/core/references/` + `opal/skills/`(하네스·pilot 문서) | ~220 | **R-6/R-7 실제 개정 대상 모집단** |
| `.opal/brain/pages/**` | ~28 | (D) 변경이력 — 소급 개정 대상 아님 |
| `opal/tools/memory-tool/tests/**` | 2 | (D) 074 히스토리 fixture |
| `opal/agents/*/AGENT.md` | ~11 | 확인 필요(표 전제 여부 개별 판정) |
| 기타(루트 문서 등) | ~19 | 개별 검토 |

**하네스·pilot 문서(~220건) 내부 4분류** — 표/마커/현황판/현재상태/다음액션 키워드 매칭 약 52건 중 changelog 행 25건 제외, **약 27건이 (B) 현재시제 개정 대상**으로 확정:

| 분류 | 건수(대략) | 정의 | 대표 사례 |
|------|------|------|-----------|
| (A) 실제 소비 | 1건 확정 + 코드 내부 I/O 다수 | STATE.md 파일을 Read/파싱/편집하는 지시·코드 | `verification-loop-guide.md:520` "새 세션에서 STATE.md를 Read하여 중단된 지점을 파악한다" — 사전 확보된 유일 소비 지점. 추가로 `opal-pilot-project-dev/SKILL.md:138` "존재하면: STATE.md Read → 현재 Phase와 상태를 파악 → 재개"도 동일 성격으로 확인(사전 정보 "1건뿐"에 대한 보정 — 최소 2건) |
| (B) 표 전제 서술 | ~27건 | 표/마커/현황판/`## 현재 상태` 존재를 전제하는 문장 → 개정 대상 | 아래 표 참조 |
| (C) 도구 규율 서술 | ~7건(하이브리드 MUST) + 별도 순수 C 소수 | 표 유무와 무관하게 유지되어야 할 도구 사용 규율 | `harness/state.md:15` `[MUST]` "파이프라인 행 상태 변경은 `state-tool`로만 수행한다" (순수 C) |
| (D) 변경이력·brain 기록 | ~55건(changelog 25 + brain 28 + memory-tool 2) | 과거 이력 서술 | changelog 표 행, `.opal/brain/pages/**` |

**파일별 (B) 표 전제 서술 상위 15개**:

| # | 파일 | (B) 건수 | 대표 사례(파일:줄번호) |
|---|------|-----|----------|
| 1 | `opal/core/references/harness/state.md` | 6 | `:27` "STATE.md 초기 생성 + 파이프라인 현황판 행 구성", `:66` "[SSOT 불변]..." |
| 2 | `opal/core/references/harness/state-template.md` | 2(+템플릿 본문 전체) | `:24` "마커 형식(T-6)... 파이프라인 현황판 표 영역을 HTML 주석 마커로 감쌈" — 템플릿 자체가 표 구조 |
| 3 | `opal/core/references/opal-harness.md` | 3 | `:167` "PM Gate 검증: 파이프라인 현황판 행 상태 정합성", `:180` `marker_missing` |
| 4 | `opal/skills/opal-pilot-project-dev/SKILL.md` | ~8(템플릿 포함) | `:579-632` 자체 STATE.md 템플릿 — `## 현재 상태`·`## Phase 진행 현황`·`## WBS 액션`·`## 병렬 실행 현황` 표 4종 |
| 5 | `opal/skills/opal-pilot-sdd/SKILL.md` | ~2 | `:216` "state-tool로 STATE.md ACT 행 갱신", `:353` "STATE.md 구조" ACT/TS 요약 템플릿 |
| 6 | `opal/skills/opal-pilot-gc/SKILL.md` | ~2 | `:287,:435` "실행 요약 테이블" 템플릿 |
| 7 | `opal/skills/opal-pilot-project-loop/SKILL.md` | 2 | `:49` "파이프라인 진행 현황판 \| STATE.md" |
| 8 | `opal/core/references/tools.md` | 2 | `:71` |
| 9 | `opal/core/references/harness/header-rules.md` | 2 | `:139,:141` |
| 10 | `opal/skills/opal-pilot-sdd/references/verify-guide.md` | 1 | `:154` |
| 11 | `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md` | 1 | `:305` |
| 12 | `opal/skills/opal-pilot-project/SKILL.md` | 1 | `:32` |
| 13 | `opal/skills/opal-pilot-project-loop/references/journey-flow.md` | 1 | `:33` |
| 14 | `opal/skills/opal-pilot-dev/SKILL.md` | 1 | `:27`(B+C 혼재, 아래 참조) |
| 15 | `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | 1 | `:46`(B+C 혼재) |

> 동일한 "마크다운 표 직접 편집 금지" 계열 문구가 `opal-harness.md:169`, `harness/state.md:15`, `opal-pilot-dev/SKILL.md:27`, `opal-pilot-dev-wireframe/SKILL.md:46`, `opal-pilot-dev-short/SKILL.md:32`, `verification-loop-guide.md:482`, `parallel-execution-guide.md:356`, `opal-pilot-project-loop/SKILL.md:52` 등 **8회 이상 반복**된다. R-6/R-7 개정 시 이 보일러플레이트 문구를 새 표준 문구로 일괄 치환하는 것이 효율적이다.

**`docs/CONVENTIONS.md` §227 판정(B/C 혼재 대표 사례)**:

원문: "파이프라인 STATE.md 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다. 마크다운 표 직접 편집 금지." 이 한 문장은 **B와 C가 융합**되어 있다.
- 주어부("파이프라인 STATE.md 행 상태(⬜/🔄/✅) 변경")는 STATE.md 안에 행 상태 아이콘 표가 존재함을 전제하므로 **(B)** — 개정 대상.
- 술어부("~로만 수행/직접편집 금지")는 표 유무와 무관하게 유지되어야 할 도구 규율 원칙이므로 **(C)** — 존치 대상.
- 저널화 후에는 편집 대상 자체(STATE.md 표)가 사라지므로 이 문장을 단순 삭제(C 상실)하거나 단순 존치(B 잔존)할 수 없고, "파이프라인 상태(rows) 변경은 `state-tool`로만 수행한다. `state.json` 직접 편집 금지 — 조회는 `state-tool show`로 확인한다" 식으로 **재작성**이 필요하다. 이는 §5 리스크로 별도 기재한다.

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경 — 없음
- [x] API 인터페이스 변경 — CLI 서브명령 옵션(`--import-existing` R-4 미확정, `marker_missing`/관련 에러코드 카탈로그 정리)
- [ ] 설정/환경변수 변경 — 없음
- [ ] 빌드/배포 파이프라인 변경 — 없음(통상 install 재배포 절차만 적용)

## 4. 핵심 발견 사항

1. **마커 게이트가 의사결정 로그를 인질로 잡는 정확한 코드 경로를 확인했다** — `sync_state_md:375-392` 안에서 마커 체크(`:377-383`)가 `append_decision_log` 호출(`:389`)보다 먼저 실행되고 `err()`가 즉시 `sys.exit()`한다. 게다가 `save_state_json()`(state.json 갱신)이 이 함수 호출 이전에 커밋되어(`cmd_mark:1601` vs `:1636`), 마커 누락 시 **state.json은 갱신됐지만 STATE.md·의사결정로그는 미갱신인 채 exit 1**되는 SSOT/미러 불일치 윈도우가 실재한다.
2. **8개 대상 함수 중 완전 삭제는 실제로 3개뿐**(`render_pipeline_table`/`replace_pipeline_section`/`update_current_status_section`) — 나머지는 재작성(`sync_state_md`/`_build_new_state_md`/`update_state_md_header`) 또는 완전 존치(`load_state_md`/`save_state_md`)다. 여기에 PM 사전 목록 밖의 5개 함수(`append_decision_log`/`_derive_next_action`/`build_todo_mirror`/`update_next_action_section`/`update_current_status_section`)가 동일 클러스터에 존재하며, 이 중 3개(`append_decision_log`/`_derive_next_action`/`build_todo_mirror`)는 이미 `state.json`만 사용해 STATE.md 렌더와 완전히 독립적이다 — 리스크가 최초 예상보다 낮다.
3. **074 key 재접합 로직(`_key_source_index`/`_reattach_import_keys`)은 표 파싱에 종속되지 않는다** — rows(dict) 출처를 구분하지 않으므로 표가 사라져도 무손상 재사용 가능하다. 표에 종속되는 것은 `parse_existing_state_md` 한 단계뿐이며, R-4 결정(제거 vs no-op)의 실제 영향 반경은 이 함수와 `TestImportPreservesKeys` 테스트군(9건)으로 국한된다.
4. **레거시(001~093) STATE.md 공존은 예상보다 안전하다** — 마커 하드 차단 경로 자체가 삭제되므로 크래시·파싱 실패 없이 표만 "동결 텍스트"로 남는다. 오히려 마커 게이트 제거가 하위호환성을 개선하는 방향이다.
5. **STATE.md 참조 754건이라는 사전 추정치는 실측(385~387건, `tasks/`·`backup/` 제외)과 약 49% 괴리한다** — `tasks/` 아카이브 포함 시 804건으로 근접, 즉 사전 추정은 아카이브 포함 수치였을 가능성이 높다. 실제 개정 작업량은 하네스·pilot 문서 220건 중 (B) 27건이며, 이 중 7건은 도구규율(C)과 한 문장에 융합된 하이브리드 `[MUST]` 절이라 문장 분리 작업이 필요하다.
6. **에러 카탈로그 종수가 이번 태스크와 무관하게 이미 3중 불일치 상태다**(선재 결함) — 코드 실측 44종(`state_tool.py:81`) vs README "39종"(`:279`) vs 하네스 문서 "23종"(`opal-harness.md:181`, `state.md:21`). PLAN에서 이번 태스크 범위 포함 여부를 결정해야 한다.
7. **하네스 SSOT 문서 자체가 이번 태스크의 전제와 모순된다** — `harness/state.md:66` "STATE.md/state-tool이 유일한 SSOT"가 `state-tool/README.md:13` "SSOT: state.json"과 정면 배치된다. R-6에서 반드시 해소해야 할 최우선 항목이다.
8. **README의 `marker_missing` 트리거 목록 자체가 코드와 다르다** — `init`이 잘못 포함되어 있고 `status`/`gate-pass`가 누락되어 있다. R-3 작업 시 정확한 트리거 목록으로 재작성해야 한다.

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| R-A 마커게이트-의사결정로그 결합 | 마커 체크가 decision log 기재보다 먼저 실행되어 하드 exit — R-2 재배선 필수 | High | `state_tool.py:375-392` |
| R-B SSOT/미러 순간 불일치 윈도우 | `save_state_json`이 `sync_state_md`보다 먼저 커밋되어 마커 누락 시 state.json↔STATE.md 불일치 발생 | Medium | `state_tool.py:1601` vs `:1636` |
| R-C README `marker_missing` 트리거 목록 오류 | `init` 오기재 + `status`/`gate-pass` 누락 | Medium | `README.md:284` vs `state_tool.py:1289-1296,1900,1979` |
| R-D 에러 카탈로그 3중 불일치(선재 결함) | 코드 44 / README 39 / 하네스 23 | Medium | `state_tool.py:81` vs `README.md:279` vs `state.md:21`/`opal-harness.md:181` |
| R-E 하네스 SSOT 자기모순(선재 결함) | `state.md:66`(STATE.md가 SSOT) vs `README.md:13`(state.json이 SSOT) | Medium | 상동 |
| R-F PM 추정 대비 참조건수 괴리 | 754건 추정 vs 385~387건 실측(`tasks/`·`backup/` 제외) | Low~Medium | §3.2 |
| R-G `--import-existing` 회귀테스트 대량 영향 | `TestImportPreservesKeys`(9건) 등이 R-4 미확정 결정에 종속 | Medium | `tests/test_state_tool.py:1487-1710,1425-1483` |
| R-H `update_state_md_header`/`update_next_action_section` 존치 여부 미검토 | TASK.md R-1 AC가 명시적으로 언급하지 않음 — PLAN 신규 결정 필요 | Low | `state_tool.py:300-306,324-334` |
| R-I 마커 제거로 레거시(001~093) 표 영구 동결 | 크래시 없으나 `show`가 레거시 표를 노출할 때 "갱신 안 됨" 안내 필요 여부 검토 | Low | §1.3.6, `tasks/093-.../STATE.md:11-35` |
| R-J CONVENTIONS §227 등 B/C 혼재 문장 8회+ 반복 | 단순 삭제/존치 불가, 표준 문구로 일괄 재작성 필요 | Low~Medium | §3.2 CONVENTIONS 판정 |

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| 언어 | Python 3 | 표준 라이브러리만 사용(`re`/`json`/`pathlib`/`argparse`/`subprocess`) |
| 테스트 | pytest(+ subtests) | 실측 308 passed + 32 subtests, 0 fail |
| 문서 | Markdown | 하네스·스킬·에이전트 문서(프레임워크 산출물 본체) |
| 스키마 | JSON Schema | `schema/state.schema.json`(이번 태스크에서 불변) |
| 배포 | Bash | `run.sh` 래퍼(무변경 예상) |

### 6.2 추천 스킬

해당 없음 — 순수 내부 리팩터링(하네스/도구/문서), 외부 프레임워크 스킬 불필요.

### 6.3 추천 MCP

해당 없음 — 외부 라이브러리·API 조사 불필요.
