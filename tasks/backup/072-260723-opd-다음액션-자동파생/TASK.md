# TASK: state-tool STATE.md "다음 액션" 자동 파생 (미갱신 결함 해소)

> 작성일: 2026-07-23 | 작업 유형: 수정(결함) | 적용 스킬: opd | 모드: agentic (072-2 재개 시 --agentic 전환)
> 입력: 사용자 요청 (대화)
> 출력: TASK.md

## 작업 목표

STATE.md "## 다음 액션"이 `init` 이후 갱신되지 않아 태스크 내내 stale하게 표시되는 결함을, `advance`/`mark` 시 파이프라인의 **다음 대기 행에서 자동 파생**하도록 고친다.

## 배경

STATE.md의 "## 다음 액션"은 소유자에게 "지금 다음 차례"를 알려주는 칸이다. 그러나 이 값은 태스크 생성(`init`) 때 한 번만 쓰이고 이후 어떤 명령으로도 갱신되지 않아, 태스크가 진행돼도 항상 첫 단계를 가리킨다(예: EXECUTE 단계인데 "PLAN 단계 진입"). 파이프라인 현황판(행 테이블)은 정상 작동하므로, "다음 액션" 한 줄만 신뢰 불가한 상태다.

## 배경 분석 (대화에서 도출)

071·070 태스크에서 실증됨 — 두 태스크 모두 STATE.md "다음 액션"이 init 값에 고정되어 실제 단계와 불일치했다. 코드 근거로 원인을 특정했다:

- `--next-action`은 **`init` 전용 인자**다 (`opal/tools/state-tool/state_tool.py:2086` `p_init.add_argument("--next-action")`). `advance`/`mark` 서브명령엔 이 옵션이 없다.
- 별도 갱신 서브명령(`set-next-action` 등)도 없다.
- `state.json` 스키마에 `next_action` 필드 자체가 없다(071 state.json 최상위 키: task_id/skill/mode/schema_version/created_at/updated_at/current_status/rows — `next_action` 부재).
- "다음 액션" 렌더는 init 경로에서만 값을 받는다 (`state_tool.py:927` `next_action = args.next_action or "PLAN 단계 진입"`, 템플릿 `:1006-1007`). `advance`/`mark`는 마커 영역(현황판)+현재 상태만 재렌더하고 "다음 액션" 섹션은 건드리지 않는다.
- 결론: 파이프라인 현황판(행 상태)은 정상이며, 결함은 "다음 액션" 섹션의 **갱신 경로 부재**다.

## 확정된 설계 방향 (대화에서 합의)

**자동 파생 방식**을 채택한다(캡틴 권고 수용).

- `advance`/`mark` 등 행 상태 전이 시, state-tool이 **파이프라인의 다음 대기 행(현재 진행행 다음의 첫 ⬜/🔄 행)에서 "다음 액션"을 자동 계산**하여 갱신한다 → 구조적으로 stale이 불가능해진다.
- `state.json`에 `next_action` 필드를 추가하고, 이를 SSOT로 렌더한다.
- 기존 `init --next-action`(명시 지정)과 **선택적 `--next-action` 오버라이드**는 유지한다.
- 대안(PM이 매 전이마다 `--next-action` 수동 전달 / `set-next-action` 별도 명령)은 누락 위험이 있어 비채택 — 도구가 자동 파생하는 것이 근본 해결이며 헌법 "enforce, don't advise"에 부합한다 (`~/.opal/PRINCIPLES.md` Core Stance).

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | `advance`/`mark` 후 STATE.md "다음 액션"이 실제 다음 대기 행을 자동으로 가리키게 한다(영구 stale 제거) | - | `state_tool.py:2086,927,1006-1007` |
| 범위 | **포함**: state.json `next_action` 필드 추가 / `advance`·`mark`(및 관련 전이)에서 다음 대기 행 기반 자동 파생 / 렌더 반영 / 선택적 `--next-action` 오버라이드 / 테스트 / README·배포. **제외**: 의사결정로그·블로커 섹션 동작 변경 / 파이프라인 행 구조 변경 / 070 task-step key 체계 변경 | 자동 파생 표현 포맷·완료시 표현·오버라이드 지속성 → ANALYSIS/PLAN | `state.schema.json`, 070 task-step key |
| 제약 | 배포 경계(`~/.opal/` 직접수정 금지, 소스 수정 후 install) / 하위호환(기존 `init --next-action`·기존 state.json 무손상, 마이그레이션 불요) / 070 task-step key 체계 정합 / 변경이력·@header 규칙 | - | `.opal/AGENT.md` 금지사항 |
| 완료기준 | ①`advance`/`mark` 후 "다음 액션"=다음 대기 행 자동 반영 ②`--next-action` 오버라이드 동작 ③모든 행 완료 시 합리적 표현 ④기존 state-tool 테스트 무회귀 + 신규 테스트 통과 ⑤install 배포 | - | - |

## 요구사항

- [ ] **R-1 state.json `next_action` 필드** — 무엇을: state.json 스키마에 `next_action` 추가 + init이 기록 / 어디에: `opal/tools/state-tool/schema/state.schema.json`, `state_tool.py` init / 왜: 렌더 SSOT 확보 / AC: init 후 state.json에 `next_action` 키 존재, schema validation 통과
- [ ] **R-2 자동 파생** — 무엇을: `advance`/`mark`(행 상태 전이) 시 다음 대기 행(현재 진행행 다음 첫 ⬜/🔄)에서 `next_action` 자동 계산·갱신 / 어디에: `state_tool.py` advance/mark 경로 / 왜: 결함 근본 해결 / AC: 여러 행을 순차 advance/mark하면 각 시점의 next_action이 다음 대기 행을 정확히 가리킴
- [ ] **R-3 렌더 반영** — 무엇을: STATE.md "## 다음 액션"이 state.json `next_action`을 반영 / 어디에: `state_tool.py` 렌더 경로(`:927,1006-1007` 부근) / 왜: 사람 열람 미러 정합 / AC: advance/mark 후 STATE.md "다음 액션"이 state.json과 일치
- [ ] **R-4 오버라이드 유지** — 무엇을: `init --next-action` 유지 + (설계 시) 전이 시 오버라이드 옵션 / 어디에: argparse / 왜: 커스텀 안내 필요 시 / AC: 오버라이드 지정 시 그 값이 자동 파생보다 우선(지속성 규칙은 PLAN 확정)
- [ ] **R-5 테스트** — 무엇을: 자동 파생·오버라이드·완료 시 표현·하위호환 회귀 / 어디에: `opal/tools/state-tool/tests/test_state_tool.py` / 왜: 완료=검증된 동작 / AC: 신규 테스트 통과 + 기존 회귀 0
- [ ] **R-6 문서·배포** — 무엇을: README·변경이력·@header 갱신 후 install / 어디에: `state-tool/README.md`, 배포 스크립트 / 왜: 배포 경계 / AC: 배포본이 소스와 일치

## 제약 조건

- **배포 경계**: `~/.opal/` 직접 편집 금지. `opal/` 소스 수정 후 install (`.opal/AGENT.md` 금지사항).
- **하위호환**: 기존 `init --next-action`·기존 state.json(필드 없는 구버전) 무손상. 마이그레이션 불필요(필드 부재 시 안전 처리).
- **070 정합**: task-step key 주소 체계(070)와 정합. 행 식별·전이 로직을 깨지 않는다.
- **추적성**: 변경이력 표 행 추가(KST+태스크 072), 코드 @header 규칙 준수.

## 기술 스택

- Python 3 (state-tool — `opal/tools/state-tool/state_tool.py`)
- JSON Schema (`schema/state.schema.json`)
- pytest (`tests/test_state_tool.py`)
- bash install 스크립트 (배포)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | state_tool.py | `opal/tools/state-tool/state_tool.py` | init/advance/mark/렌더·next_action 대상 (R-1~R-4) |
| D-2 | 소스 | state.schema.json | `opal/tools/state-tool/schema/state.schema.json` | next_action 필드 추가 (R-1) |
| D-3 | 소스 | state-tool tests | `opal/tools/state-tool/tests/test_state_tool.py` | 회귀·신규 테스트 (R-5) |
| D-4 | 소스 | state-tool README | `opal/tools/state-tool/README.md` | 문서 정합 (R-6) |
| D-5 | 설계 | OPAL 헌법 | `~/.opal/PRINCIPLES.md` | enforce-don't-advise 근거 |

## 미확정 사항 (ANALYSIS/PLAN에서 결정)

- **M-1 자동 파생 표현 포맷** — 다음 대기 행 기반 문자열 형식(예: "{다음행 stage} {item} 진입" vs 커스텀 매핑). ANALYSIS에서 현행 렌더·행 구조 확인 후 확정.
- **M-2 모든 행 완료 시 표현** — 마지막 행(CLOSE) 완료 후 "다음 액션" 값(예: "완료" / 공란 / 마지막 행 유지).
- **M-3 오버라이드 지속성** — `--next-action` 오버라이드가 이후 전이에서 유지되는지, 다음 전이 시 자동 파생으로 되돌아가는지.
