# ANALYSIS: state-tool STATE.md "다음 액션" 자동 파생 (미갱신 결함 해소)

> 작성일: 2026-07-23
> 입력: TASK.md
> 출력: ANALYSIS.md

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| 1 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | init/advance/mark/렌더·next_action 전체 데이터 흐름 확인 (R-1~R-4) |
| 2 | 소스 | state.schema.json | `opal/tools/state-tool/schema/state.schema.json` | 현재 스키마 구조 — next_action 부재 확인 (R-1) |
| 3 | 소스 | test_state_tool.py | `opal/tools/state-tool/tests/test_state_tool.py` | 기존 테스트 구조·픽스처·`TestFreeTextPreservation` 충돌 확인 (R-5) |
| 4 | 소스 | state-tool README.md | `opal/tools/state-tool/README.md` | 문서 정합 대상 확인 (R-6) |
| 5 | 설계 | state-template.md | `opal/core/references/harness/state-template.md` | "다음 액션 = PM 수동 갱신, state-tool 범위 밖" 원 설계 SSOT — 본 태스크가 뒤집는 대상 |
| 6 | 설계 | task-process.md | `opal/core/references/harness/task-process.md:42` | `--next-action` 계약 재인용 지점 (R-6 정합 대상) |
| 7 | 소스 | op-task/SKILL.md | `opal/skills/op-task/SKILL.md:219` | `--next-action` 계약 재인용 지점 (R-6 정합 대상) |
| 8 | 소스 | header-rules.md | `opal/core/references/harness/header-rules.md:91` | "다음 액션"을 자유 텍스트 영역으로 전제하는 간접 소비처 |
| 9 | 소스 | parallel-execution.md | `opal/core/references/harness/parallel-execution.md:74` | 상동 |
| 10 | 소스 | install-mac.sh | `scripts/install-mac.sh:1111` | `opal/tools/` → `~/.opal/tools/` 배포 경로 확인 (R-6 배포 경계) |
| 11 | 설계 | OPAL 헌법 | `~/.opal/PRINCIPLES.md` | enforce-don't-advise 근거 (TASK D-5) |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §2 참조.

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/tools/state-tool/state_tool.py` | init/advance/mark/렌더 전체 로직 | Y | `927`, `979-1008`, `1071-1114`, `1131-1286`, `346-371`, `2078-2140` |
| `opal/tools/state-tool/schema/state.schema.json` | state.json JSON Schema (참조용) | Y | `6`(required), `8-113`(properties) |
| `opal/tools/state-tool/tests/test_state_tool.py` | 단위 테스트 | Y | `1484-1554`(TestFreeTextPreservation 직접 충돌), `257-317`(TestInit) |
| `opal/tools/state-tool/README.md` | 도구 사용법 문서 | Y | `40-52`(init), `85-98`(advance), `101-121`(mark) |
| `opal/core/references/harness/state-template.md` | STATE.md 템플릿 SSOT — "다음 액션=PM 수동" 명문화 | Y | `33-40`(자유 텍스트 3섹션 표), `81-82`(템플릿 본문) |
| `opal/core/references/harness/task-process.md` | `--next-action` 계약 재인용 | Y(경미) | `42` |
| `opal/skills/op-task/SKILL.md` | `--next-action` 계약 재인용 | Y(경미) | `219` |
| `opal/core/references/harness/header-rules.md` | "다음 액션"을 자유 텍스트 영역으로 전제 | 검토 필요 | `91` |
| `opal/core/references/harness/parallel-execution.md` | 상동 | 검토 필요 | `74` |

> 근거: `파일:N-M` 포맷. 없으면 `-`.

### 1.2 아키텍처 패턴

- **SSOT 분리 패턴**: `state.json`이 단일 진실 공급원, `STATE.md`는 도구가 자동 렌더하는 미러. 사람의 직접 편집은 금지되고 10개 서브 명령을 통해서만 갱신 (`README.md:9,13`).
- **공통 후처리 패턴**: `advance`/`mark`/`block` 등 상태 전이 명령은 각자 로직 실행 후 `sync_state_md()` 한 곳으로 STATE.md 갱신을 위임한다 (`state_tool.py:346-371`). 이 함수가 갱신하는 범위는 **① 파이프라인 표(마커 영역) ② `> 최종 갱신:` 헤더 ③ `## 현재 상태`의 `- 진행:`/`- 상태:` 라인 ④ (옵션) 의사결정 로그**뿐이며, `## 다음 액션` 섹션은 이 함수의 책임 범위에 전혀 포함되지 않는다.
- **자유 텍스트 영역 보존 원칙**: `## 블로커`/`## 다음 액션`은 "자유 텍스트 영역"으로 설계되어 있고, 이는 우연한 누락이 아니라 `state-template.md:34`에 **"이후 갱신 명령은 `## 의사결정 로그`에만 자동 추가, `## 블로커`와 `## 다음 액션`은 PM이 수동 갱신 (state-tool 범위 밖)"**로 명문화된 **의도적 설계**다. TASK.md가 이를 "결함"으로 규정하고 자동 파생으로 전환하는 것은 이 설계 문서 자체를 뒤집는 결정이며, PLAN 단계에서 이 문서(D-5, 참조 #5)도 함께 갱신해야 한다.
- **행 주소 3원 체계(070)**: `resolve_row_index()`(`state_tool.py:392-428`)가 `--task-step`(key)/`--task-step-id`(숫자)/`--row`(deprecated) 3주소를 `row_index`(int)로 통일 해석한다. advance/mark는 이 `row_index`만으로 동작하므로, 신규 "다음 대기 행" 파생 로직도 동일하게 `row_index` 기반으로 구현하면 070 체계와 자연히 정합한다(신규 주소 체계 불필요).
- **행 완료 판정 상수**: `_COMPLETE_STATUSES = {"done", "additional_work_done", "na"}` (`state_tool.py:435`)가 이미 존재하며 `check_stage_transition_guard()`에서 "앞 행이 완료됐는가"를 판정하는 데 재사용된다. "다음 대기 행"(= 완료가 아닌 첫 행) 탐색도 이 상수의 여집합으로 표현 가능하다.

### 1.3 의존성 맵

```
cmd_init (827-976)
 └─ next_action = args.next_action or "PLAN 단계 진입"   (927, 로컬 변수 — state.json 미저장)
     └─ _build_new_state_md(...) → STATE.md "## 다음 액션" 1회 렌더 (979-1008)
         (import_mode 경로는 "## 다음 액션" 자체를 생성/치환하지 않음 — 930-951)

cmd_advance (1071-1114) ─┐
cmd_mark    (1131-1286) ─┼─► sync_state_md() (346-371)
cmd_block   (1290-1318) ─┘      ├─ render_pipeline_table() → replace_pipeline_section()  (마커 영역만)
                                 ├─ update_state_md_header()                              (헤더만)
                                 ├─ update_current_status_section()                       (현재 상태만)
                                 └─ append_decision_log()  (옵션)                         (의사결정 로그만)
                                 ※ "## 다음 액션" 미접촉 — 결함의 정확한 코드 지점
```

- `state.json`은 `cmd_init`이 구성하는 딕셔너리(`state_tool.py:903-912`)에 `next_action` 키를 포함하지 않는다. 즉 `next_action`은 **state.json에 영속화되지 않고 init 실행 중 로컬 변수로만 존재**하다가 STATE.md 텍스트에 1회 굽혀 들어간다. R-1(스키마 필드 추가)이 필요한 이유가 바로 이 지점이다.
- `cmd_show(format=json)`(`state_tool.py:1021-1025`)은 `state` 딕셔너리를 그대로 반환하므로, `next_action`을 state.json에 추가하면 별도 코드 변경 없이 `show --format json` 응답에도 자동 노출된다.
- `cmd_validate`(`state_tool.py:1320-1377`)의 필수 필드 검증은 `state.schema.json`을 프로그램적으로 로드하지 않고 **하드코딩된 `required_fields` 리스트**(`state_tool.py:1329-1330`)로 수행한다 — 즉 `state.schema.json`은 런타임 검증에 관여하지 않는 "참조용" 문서다(`README.md:326` "JSON Schema Draft-07 참조용"; 드리프트 회귀 테스트만 `test_state_tool.py:3616-3680`, `4025-4104`에서 파일 내용을 직접 파싱해 CLI enum과 비교). 따라서 `next_action`을 스키마에 추가해도 `cmd_validate`의 동작에는 영향이 없다(단, `required_fields`에 넣지 않으면 하위호환 리스크 없음 — §3.3 참조).

### 1.4 테스트 현황

- 프레임워크: `unittest`(표준 라이브러리만, `TASK T-11`). `_TOOL_DIR`을 `sys.path`에 넣어 `state_tool.py`를 직접 import(`test_state_tool.py:38-41`).
- 현재 241개 테스트, 로컬 실행 결과 **240 pass / 1 fail**(베이스라인). 실패 1건은 본 태스크와 무관한 기존 결함: `TestVerify.test_verify_passes_own_test_scenario_md`가 `tasks/034-260621-.../TEST-SCENARIO.md`를 하드코딩 참조하는데(`test_state_tool.py:2177`) 해당 태스크 폴더가 `tasks/backup/034-.../`로 이동되어 경로가 깨져 있다(034 태스크 자체 정리 시점의 잔존 드리프트). R-5 "기존 회귀 0"의 기준선은 **이 1건을 제외한 240 pass 유지**로 잡아야 한다.
- STATE.md 렌더 검증 방식: 문자열 `assertIn`/`find` 위치 슬라이싱 기반(예: `test_state_tool.py:286-287`, `1499-1514`). jsonschema 라이브러리나 마크다운 파서를 쓰지 않고 순수 문자열 비교다.
- **[MUST] 정면 충돌 발견** — `TestFreeTextPreservation`(`test_state_tool.py:1484-1554`)은 `mark`/`advance`/`block`/`add-row` 호출 전후로 `## 다음 액션` 섹션 전체(`_free_text_sections()`, `1499-1507`)가 **문자 그대로 동일**해야 한다고 단언한다(`_assert_free_text_preserved`, `1509-1514`; `test_mark_preserves_free_text`/`test_advance_preserves_free_text` 등 `1516-1528`). 이 테스트는 PLAN §3 Step 2("자유 텍스트 영역 보존")을 근거로 명시하며, 현재의 "다음 액션 미갱신"을 **의도된 불변성**으로 락인하고 있다. R-2(자동 파생)를 구현하면 이 테스트들은 **반드시 실패하게 되며, 이는 회귀가 아니라 설계 반전에 따른 의도된 테스트 갱신 대상**이다 — PLAN 단계에서 이 클래스를 "다음 액션은 파생 갱신, 블로커는 보존"으로 분리 개정해야 한다(테스트명·docstring·근거 인용(§3 Step 2) 함께 갱신 필요).
- 신규 테스트 추가 위치: 기존 클래스 배치 패턴(`# ═══` 구분 주석 + 알파벳/도메인 섹션 라벨, 예: `# E. 자유 텍스트 영역 보존`, `line 1480`)을 따라, R-1~R-4 검증용 신규 클래스(예: `TestNextActionAutoDerive`)를 `TestFreeTextPreservation` 인접 위치(또는 `TestG7StatusTransitions` 류의 G-계열 시나리오 섹션)에 추가하고, `TestFreeTextPreservation`은 "블로커만 보존" 범위로 축소 개정하는 두 갈래 작업이 필요하다.

## 2. 외부 조사 결과 (해당 시)

해당 없음 — 표준 라이브러리(`json`/`argparse`/`re`/`pathlib`)만 사용하는 내부 CLI 도구 수정이며, 외부 라이브러리/API 조사 대상이 아니다(`TASK.md` 기술 스택: Python 3, JSON Schema, pytest 표기이나 실제로는 `unittest` — README 의존성 섹션 `opal/tools/state-tool/README.md:322-325`도 표준 라이브러리만 명시).

## 3. 영향 범위

### 3.1 직접 영향

- `opal/tools/state-tool/state_tool.py`
  - **R-1**: `cmd_init`의 `state` 딕셔너리 구성(`903-912`)에 `next_action` 키 추가, 저장.
  - **R-2**: `cmd_advance`(`1071-1114`)·`cmd_mark`(`1131-1286`) 각각에 "다음 대기 행" 탐색 헬퍼(신설, 예: `_derive_next_action(state, row_index)`) 호출 추가 → `state["next_action"]` 갱신 → `save_state_json`.
  - **R-3**: `sync_state_md()`(`346-371`) 또는 별도 헬퍼에 `## 다음 액션` 섹션 치환 로직 추가(현재 `update_current_status_section`과 동일 패턴의 정규식 치환 함수 신설 필요 — 다만 `TestFreeTextPreservation`이 이 섹션에 사용자가 추가한 멀티라인 텍스트(`- 세부 액션 1` 등, `1496`)를 허용해온 이력이 있어, 치환 범위(1줄만 vs 섹션 전체)를 PLAN에서 확정해야 함 — M-1 관련).
  - **R-4**: `build_parser()`의 `p_adv`(`2104-2114`)·`p_mark`(`2116-2139`)에 `--next-action` 선택 인자 추가, `cmd_advance`/`cmd_mark`에서 우선순위 처리(오버라이드 > 자동 파생).
- `opal/tools/state-tool/schema/state.schema.json`: 최상위 `properties`(`8`)에 `next_action` 필드 추가(oneOf string/null 패턴, `note`/`key` 필드와 동일한 optional 관례 — `102-106` 참조). **`required` 배열(`6`)에는 추가하지 않아야** 하위호환 원칙(§3.3)과 정합.
- `opal/tools/state-tool/tests/test_state_tool.py`: R-5 신규 테스트 + `TestFreeTextPreservation` 개정(위 §1.4 참조).
- `opal/tools/state-tool/README.md`: `init`/`advance`/`mark` 서브 명령 섹션(`40-52`, `85-98`, `101-121`)에 `next_action` 필드·자동 파생 동작·오버라이드 옵션 반영, 변경이력 표(`338-347`)에 태스크 072 행 추가.
- `opal/core/references/harness/state-template.md`: §1.2에서 확인된 원 설계 문언(`33-40`, `81-82`) 갱신 — "다음 액션은 자동 파생, 오버라이드만 수동" 으로 정정. 이 문서를 갱신하지 않으면 §제약조건의 "추적성"·"문서 정합" 요구가 미충족.

### 3.2 간접 영향

- `opal/core/references/harness/task-process.md:42`, `opal/skills/op-task/SKILL.md:219` — `--next-action` 계약 설명 문구("생략 시 PLAN 단계 진입") 자체는 init 한정이라 큰 변경은 없으나, 자동 파생 도입 시 "이후 advance/mark에서도 자동 갱신됨"을 보강 서술할지 PLAN에서 결정 필요(경미).
- `opal/core/references/harness/header-rules.md:91`, `opal/core/references/harness/parallel-execution.md:74` — code-scan 폴백 기록 대상으로 "다음 액션"을 자유 텍스트 영역으로 전제한다. 자동 파생 후에도 이 두 문서가 기술하는 "폴백 사유 1줄 기록" 관행 자체는 섹션이 여전히 존재하는 한 깨지지 않으나(값이 자동 갱신되어도 그 아래/위에 자유 기록을 허용하는 설계라면), R-3의 치환 범위 설계(1줄 vs 섹션 전체)에 따라 이 관행과 충돌 가능성이 있음 — PLAN에서 교차 확인 필요.
- Console(대시보드) 백엔드: `dashboard/` 내 "다음 액션"/`next_action` 참조 0건 확인(Grep) — 영향 없음.
- opal-pilot-* 각 SKILL.md의 `state init --next-action` 호출부(예: `opal-pilot-project-dev`, `opal-pilot-sdd` 등, §0 참조 문서에서 다수 발견됨)는 init 시 `--next-action` 인자를 그대로 넘기는 관례라 R-4(오버라이드 유지)가 충족되면 무변경으로 동작 — 단, PLAN 단계에서 표본 확인 권장.
- 기존 태스크 폴더 다수의 STATE.md(예: `tasks/070-.../STATE.md` 등, Grep 결과 60여 건)는 이미 생성된 산출물이라 소급 변경 대상이 아니다(레거시 호환 원칙, `state-template.md:102` "레거시 호환" 조항과 동일 정신).

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경 — 해당 없음
- [x] API 인터페이스 변경 — `state-tool` CLI에 `advance`/`mark` `--next-action` 옵션 신설(하위호환 추가, breaking 아님) + `state.json` 필드 추가(optional, `required` 미포함이면 breaking 아님)
- [ ] 설정/환경변수 변경 — 해당 없음
- [x] 빌드/배포 파이프라인 변경 — 없음(`opal/tools/` → `~/.opal/tools/` 일괄 동기화 기존 메커니즘으로 흡수, `scripts/install-mac.sh:1111`. 별도 배포 스크립트 수정 불요, `./scripts/install-mac.sh` 재실행만 필요)

## 4. 핵심 발견 사항

1. **결함이 아니라 설계 반전 대상이다.** `state-template.md:34`가 "다음 액션은 PM이 수동 갱신 (state-tool 범위 밖)"이라고 명문화하고 있으므로, 코드는 설계대로 동작 중이다. 본 태스크는 이 설계 문서 자체를 갱신 대상에 포함해야 하며(§3.1 직접 영향에 반영), 단순 버그 픽스보다 넓은 "문서 SSOT 개정 + 회귀 테스트 반전"을 포함한다.
2. **`next_action`은 현재 state.json에 전혀 저장되지 않는 휘발성 로컬 변수다**(`state_tool.py:927`). SSOT 원칙(`README.md:13` "state.json이 단일 진실 공급원") 관점에서 보면 오히려 이 부분이 원칙 위반에 가깝다 — R-1이 이 원칙 정합화이기도 하다.
3. **`sync_state_md()`가 갱신 범위의 유일한 진입점**(`state_tool.py:346-371`)이므로, R-2/R-3 구현의 최소 변경 지점은 이 함수(또는 이를 호출하는 `cmd_advance`/`cmd_mark`) 한 곳에 집중된다 — 파급 지점이 명확하고 좁다.
4. **070 task-step 체계와 자연 정합**: "다음 대기 행" 탐색은 `row_index`(정수) 기반으로 구현 가능하며, key 주소 체계를 건드릴 필요가 없다. `_COMPLETE_STATUSES` 상수(`435`)를 재사용하면 "완료 아닌 첫 행" 탐색 로직을 기존 관례에서 크게 벗어나지 않게 구현할 수 있다.
5. **기존 테스트 `TestFreeTextPreservation`이 정면 충돌한다.** 이 클래스의 4개 테스트(mark/advance/block/add-row)는 "다음 액션 불변"을 assert하므로 R-2 구현 즉시 RED가 된다 — PLAN에서 "의도된 반전"으로 명시하고 테스트를 "블로커만 보존, 다음 액션은 파생 갱신 확인"으로 재정의해야 한다(§1.4 상세).
6. **M-1(파생 포맷)/M-3(오버라이드 지속성)은 `TestFreeTextPreservation`이 허용해온 "섹션 내 사용자 자유 기재"(`- 세부 액션 1` 등, `1496`)와 충돌 여지가 있다.** 자동 파생이 섹션 전체를 덮어쓰는 방식이면 이런 부기 텍스트가 매 전이마다 사라진다 — PLAN에서 "1줄 치환(정규식으로 첫 줄만) vs 섹션 전체 치환" 결정이 필요하며, 이는 `update_current_status_section()`(정규식 1줄 치환 패턴, `301-315`)을 모델로 삼는 편이 기존 관례와 더 정합적이다.

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| 기존 회귀 테스트 충돌 | `TestFreeTextPreservation` 4개 테스트가 "다음 액션 불변"을 assert — R-2 구현 시 필연적 RED, 의도된 테스트 개정 필요(회귀 아님을 QA 단계에서 구분해야) | 높음 | `opal/tools/state-tool/tests/test_state_tool.py:1484-1554` |
| 설계 문서 SSOT 미갱신 리스크 | `state-template.md`를 갱신하지 않으면 신규 태스크 온보딩 시 "다음 액션은 수동"이라는 낡은 문언이 재확산 | 중간 | `opal/core/references/harness/state-template.md:34` |
| 스키마 `required` 오추가 시 하위호환 파괴 | `next_action`을 `state.schema.json`의 최상위 `required`(`6`)에 넣으면, 향후 이 스키마로 실제 jsonschema validate를 수행하는 코드가 생길 경우 구버전 state.json이 즉시 위반 처리됨 — 현재는 런타임 미검증이라 당장 영향 없으나 잠재 리스크 | 낮음(현재) / 중간(향후) | `opal/tools/state-tool/schema/state.schema.json:6`, `state_tool.py:1328-1334`(런타임은 하드코딩 리스트, 스키마 파일 비의존) |
| 섹션 치환 범위 미확정(M-1/M-3) | 자동 파생이 "## 다음 액션" 섹션 전체를 덮어쓸지 첫 줄만 치환할지에 따라 PM의 자유 기재 텍스트 보존 여부가 달라짐 | 중간 | `test_state_tool.py:1496,1506` (섹션 전체를 자유 텍스트로 다뤄온 기존 관례) |
| 사전 존재하는 무관 실패 1건 | `TestVerify.test_verify_passes_own_test_scenario_md`가 이동된 태스크 폴더 경로를 참조해 실패 — 본 태스크의 회귀 판정 시 오인 가능 | 낮음 | `test_state_tool.py:2177` (`tasks/034-.../` → 실제로는 `tasks/backup/034-.../`로 이동됨, 로컬 실행 확인) |
| pending 대비 in_progress 다중 매치 | "다음 대기 행"을 "현재 진행행 다음 첫 pending/in_progress"로 정의할 때, 동일 stage 내 이미 in_progress인 행이 여러 개 존재할 수 있는 편집(`add-row`) 이후 시나리오에서 어떤 행을 우선할지 모호할 수 있음(스텝 N/M 진행 중인 행 등) | 낮음 | `state_tool.py:1190-1209`(다중 Step in_progress 유지 로직) |

> 근거: `경로 §N` 또는 `경로:줄번호` 또는 `[사이트명](URL)` 또는 `-`. (citation-rules.md §2)

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| 언어 | Python 3 | (프로젝트 지정 버전 없음 — `~/.opal/.venv/bin/python`, `README.md:324`) |
| 표준 라이브러리만 | `json`/`argparse`/`pathlib`/`re`/`subprocess`/`sys`/`datetime`/`os` | - (`state_tool.py:16-24`) |
| 테스트 | `unittest`(표준 라이브러리) | - (`test_state_tool.py:35`, TASK.md에는 pytest로 기재되어 있으나 실제 사용은 unittest) |
| 스키마 문서 | JSON Schema Draft-07(참조용, 런타임 미검증) | `state.schema.json:2` |
| 외부 도구 연동 | `~/.opal/tools/date/date.js`(Node.js, KST 시각 취득) | - (`state_tool.py:172`) |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| (해당 프로젝트 자체 파이프라인) op-dev-plan | 다음 단계(PLAN)에서 §1.4/§4/§5의 미확정 항목(M-1~M-3) 확정 |

> 외부 프레임워크/라이브러리 도입이 없는 순수 내부 CLI 수정 태스크라 특정 커뮤니티 스킬 매핑 대상 없음.

### 6.3 추천 MCP

| MCP | 용도 |
|-----|------|
| (해당 없음) | 표준 라이브러리 기반 내부 도구 수정이라 외부 라이브러리 문서 조회 불요 |
