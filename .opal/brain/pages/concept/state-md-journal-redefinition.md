---
type: concept
title: STATE.md 저널 재정의 — 파생 섹션 제거 + state.json 단일 SSOT
tags:
- state-tool
- ssot
- journal
- architecture
- task-094
sources:
- task:094
related:
- state-tool
- mirror-gate-must-not-hostage-ssot-record
- mark-force-decision-log-scope
- state-tool-next-action-auto-derivation
- state-tool-import-existing-key-reattachment
- dedup-pointer-over-copy
created: '2026-08-16'
updated: '2026-08-16'
status: draft
---
## 개요

`STATE.md`를 "파이프라인 현황판"에서 "의사결정 로그·블로커·자유 기재만 담는 저널"로 재정의한 아키텍처 결정이다. 기계 상태(진행 현황·다음 액션 등)의 SSOT는 `state.json` 단일로 확정하고, 조회는 `state-tool show`로 일원화했다. STATE.md 파일 자체는 삭제하지 않는다 — 삭제되는 것은 `state.json`에서 파생 가능한 표시(현황판 표·마커·"## 현재 상태"·"## 다음 액션" 자동 파생)뿐이다.

## 결정 배경 (WHY)

- STATE.md는 `state.json`이 도입된 이후 이미 표시용 미러로 강등돼 있었다 — 사람이 읽는 표는 `state.json.rows[]`를 렌더한 것에 불과했다. 그런데도 렌더 동기화 코드(`sync_state_md`·`update_state_md_header`·마커 삽입)가 계속 남아 있어, 표만 걷어내면 부분 렌더 상태가 유지되고 코드 정리 효과가 반감됐다(근거: task:094 TASK.md 확정된 설계 방향 ②).
- 경계를 "표"가 아니라 "파생 전체"로 그어야 하는 이유는 `## 다음 액션`처럼 표가 아닌 파생 섹션도 있었기 때문이다. 표만 제거하고 이 섹션을 남기면 `state.json.next_action`(SSOT)과 STATE.md의 자유 기재 값이 같은 이름의 두 값으로 공존해, 이번에 제거하려는 "이중 표현"이 이름만 바꿔 재발한다(근거: task:094 PLAN.md D-1).
- 의사결정 로그·블로커는 `state.json`에 대응 필드가 없다 — 삭제하면 유실되므로 파일 자체는 남기고 이 두 섹션만 저널로 존치한다(근거: task:094 TASK.md 확정된 설계 방향 ①, 제약 ②).

## 결정 내용

- **판별 원리(SSOT/미러 판별의 핵심 질문)**: "`state.json` `rows[]` 스키마에 이 정보를 담을 필드가 있는가?" — 있으면 파생이므로 STATE.md에서 제거하고 `show` 조회로 대체한다. 없으면(도구가 구조화할 수 없는 서술·이력 정보) 저널의 자유 기재 섹션으로 존치한다. 이 질문 하나로 3개 pilot(oppd·opgc·opsdd)의 문서 개정을 일관 판정했다(근거: task:094 DONE.md §8(4)).
  - 실제 적용 사례: oppd 자체 STATE.md 템플릿(`opal-pilot-project-dev/SKILL.md:579-632`)의 4개 표 중 `## 현재 상태`는 `state.json` 파생이므로 삭제, 나머지 `## Phase 진행 현황`·`## WBS 액션`·`## 병렬 실행 현황` 3표는 `state.json`이 담지 못하는 oppd 고유 서술 정보이므로 저널 자유 기재로 존치했다(근거: task:094 PLAN.md §4.2 Step 10 표, line 648). 검증 루프 진행 계층·시도 횟수(`## 현재 상태 - 검증:`)도 같은 이유로 저널의 `## 검증 루프` 자유 기재 섹션으로 옮겼다(PLAN.md line 566).
- **제거 대상**: 파이프라인 현황판 표 + `<!-- pipeline:start/end -->` 마커 + `## 현재 상태` + `## 다음 액션` 자동 파생. 이들을 산출하던 `replace_pipeline_section`·`update_current_status_section`·`update_next_action_section` 함수를 삭제했다(근거: task:094 코드 @header 094 항목).
- **존치 대상**: `## 의사결정 로그`(표, `ensure_journal_skeleton`으로 골격 보증) + `## 블로커` + 자유 기재. `update_state_md_header`(`> 최종 갱신:` 타임스탬프)도 존치 — 표·마커와 무관한 범용 갱신 시각이라 이중 표현 리스크가 없기 때문이다(근거: task:094 PLAN.md D-3).
- **레거시 호환**: 001~093의 기존 STATE.md는 소급 변경하지 않는다. 마커가 남은 레거시 파일을 `show`로 열람하면 "이 표는 동결 텍스트이며 SSOT는 state.json"이라는 배너만 출력에 덧붙이고 파일에는 어떤 바이트도 쓰지 않는다(근거: task:094 PLAN.md D-4).
- **조회 표준 경로 통합**: `show --format md/json/full` 모두 마커 유무와 무관하게 `state.json`에서만 렌더하도록 재설계했다 — 기존에는 레거시 마커가 있으면 STATE.md 본문의 정지된 표를 그대로 반환하는 정확성 결함이 있었다(아래 [[mirror-gate-must-not-hostage-ssot-record]]와 연결).

## 영향 범위

- `opal/tools/state-tool/state_tool.py` — 렌더·마커·파싱 경로 전반, `state-tool/README.md`, 하네스 SSOT 3문서(`opal-harness.md` §3, `harness/state.md`, `harness/state-template.md`), pilot 10종 `SKILL.md`, 전문 에이전트 문서, `docs/CONVENTIONS.md`·`docs/ARCHITECTURE.md`.
- 세션 복원 절차가 "STATE.md를 Read하여 재개"에서 "`state-tool show` 호출"로 전면 교체됐다 — 비Claude 플랫폼에서 표가 소멸해도 조회 수단이 남는다.
- 회귀 테스트 재작성: 파생 검증 테스트 다수 삭제(D-1·D-2·R-3 대응), 저널 무손실·`show` 단일화·import 거부·에러 카탈로그 정합 등 신규 기능 5종에 대응하는 테스트가 신설됐다. 숫자 하한(기존 pass 수 이상)은 padding 테스트를 유도한다는 이유로 소유자 판정으로 폐기하고, 성질 기반 검증(삭제 1:1 대응 + 신규 기능 대응 존재)으로 대체했다.
- **미판정 항목**: 저널 구조의 실사용 수용성(진행 현황 부재가 불편하지 않은가, `show` 조회가 실용적인가)은 자동 검증이 원리적으로 불가능한 영역으로 남아, 소유자 확인 대기 상태다(근거: task:094 DONE.md §4 S-28). FAIL이면 이 설계 결정 자체를 재검토하기로 명문화돼 있다.

## 관련 페이지

- [[state-tool]]
- [[mirror-gate-must-not-hostage-ssot-record]]
- [[mark-force-decision-log-scope]]
- [[state-tool-next-action-auto-derivation]]
- [[state-tool-import-existing-key-reattachment]]
- [[dedup-pointer-over-copy]]
