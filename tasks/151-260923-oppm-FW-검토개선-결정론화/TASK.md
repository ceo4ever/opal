---
template: self-pm-task
actor: PM
---

# TASK: FW 검토 개선의 결정론화

## Problem

태스크 149 검토 과정에서 프레임워크 개선 후보 6건을 대조한 결과, 다음 네 문제가 확인됐다.

1. `scenario-coverage-build`의 Markdown 표 파서는 셀 안의 escape 파이프(`\|`)도 구분자로
   처리하고, 열 수가 달라진 행을 오류 없이 버린다. 이 때문에 시나리오가 누락돼도 부분
   입력으로 coverage 판정이 계속될 수 있다
   (`opal/tools/test-tool/lib/scenario.py:816-835`).
2. `task_root`와 `allocator_root`의 결정 방법은 구분돼 있지만, 바로 이어지는 추론 금지
   문장이 `allocator_root`에만 적용된다는 대칭 진술이 없어 실제 태스크에서 적용 범위를
   잘못 확장했다(`opal/core/references/harness/worktree.md:32-43`).
3. 코드 설명이 특정 테스트의 집행을 주장하면서 실제 테스트 경로와 심볼을 정확히
   지목하지 않아, 존재하지 않는 테스트가 근거로 소비된 사례가 있었다
   (`opal/core/references/harness/header-rules.md §기존 파일 수정`).
4. PM Gate는 참조 문서 전달·반영 여부를 검사하지만, 인용한 `[MUST]` 조항의 적용 대상이
   현재 변경 대상과 같은지는 명시적으로 검사하지 않는다
   (`opal/core/references/harness/pm-review-gate.md:55-66`).

## Proposed outcome

- Markdown 표의 escape 파이프를 셀 내용으로 처리하고, 열 수가 맞지 않는 행은 조용히
  버리지 않고 `coverage_input_invalid`로 거부한다.
- `task_root` 조상 탐색과 `allocator_root` 추론 금지의 적용 범위를 문서에서 대칭적으로
  명시한다.
- 코드 설명의 집행 주장은 정확한 테스트 경로와 심볼을 근거로 사용하도록 제한한다.
- PM Gate가 강제 조항의 적용 대상을 명시적으로 대조한다.

## Affected users and systems

- 사용자: TEST-SCENARIO 목표-커버 게이트를 수행하는 PM과 워커
- 시스템: test-tool `scenario-coverage-build`, worktree 루트 계약, @header 규칙, PM Gate

## Constraints

- C-1: 태스크 149 워크트리의 기존 미커밋 변경은 수정하거나 되돌리지 않는다.
- C-2: 검토에서 기각한 Stop guard 대기 상태와 state-tool unblock/log-event 계약은 변경하지
  않는다.
- C-3: 외부 Markdown 파서나 새 범용 검증 계층을 추가하지 않는다.
- C-4: 정상 표와 기존 공개 CLI 성공 응답 계약은 유지한다.
- C-5: Markdown 문서에는 수기 변경이력 절을 추가하지 않는다.

## Acceptance criteria

- AC-1: `\|`가 포함된 시나리오 표 행이 누락되지 않고 S-ID와 커버 토큰이 모두 변환된다.
- AC-2: 헤더와 열 수가 다른 시나리오 표 행은 exit 17,
  `coverage_input_invalid`로 거부되며 문제 행을 식별할 수 있다.
- AC-3: `worktree.md`가 `task_root`의 조상 탐색은 정의된 해석이고 allocator 금지를 적용하지
  않는다고 명시한다.
- AC-4: `header-rules.md`가 집행 주장의 정확한 테스트 경로·심볼 근거를 요구한다.
- AC-5: `pm-review-gate.md`가 인용 강제 조항의 적용 대상·조건 일치 검사를 포함한다.
- AC-6: 신규 테스트와 기존 test-tool scenario 테스트가 모두 통과하고 code-scan 변경 파일
  검증이 성공한다.

## Analysis

### 원인

`_parse_markdown_table_rows()`는 각 행을 `line.strip("|").split("|")`로 나눈다. 이 방식은
Markdown escape를 해석하지 않으며, 분리된 셀 수가 헤더와 다르면 `continue`로 행을 버린다.
따라서 구문 문제와 의도된 비시나리오 행을 구분할 수 없다
(`opal/tools/test-tool/lib/scenario.py:816-835`).

루트 계약 자체는 `task_root`와 `allocator_root`를 서로 대체하지 않는다고 선언하고 각 결정
방법도 분리한다. 문제는 표 다음의 강한 금지문만 눈에 띌 때 범위를 잘못 옮길 수 있다는
실사용 위험이다. state-tool은 이미 조상 탐색을 task-root 전용으로 한정하고 allocator write에
사용하지 않는 선례를 갖는다(`opal/tools/state-tool/state_tool.py:2696-2710`).

PM Gate에는 “요구사항 오해”와 “참조 문서 반영” 검사가 있으므로 새 게이트를 만들 필요는
없다. 기존 참조 반영 항목에 적용 대상·조건 검사를 추가하는 것이 최소 변경이다
(`opal/core/references/harness/pm-review-gate.md:42-65`).

## Design

### D-1. Escape-aware 표 행 분리

`scenario.py`에 한 행을 문자 단위로 분리하는 작은 helper를 둔다. `\|`는 현재 셀의 literal
파이프로 변환하고, escape되지 않은 `|`만 셀 경계로 처리한다. 그 밖의 backslash는 보존한다.
Markdown 문법상 선택적인 선두·후미 테두리 파이프의 유무로 S 행이 누락되지 않게 한다.

### D-2. Malformed 행 fail-closed

표 헤더를 얻은 뒤 데이터 행의 셀 수가 다르면 건너뛰지 않고 `ValueError`로 문제 행 번호와
내용을 올린다. builder 경계에서 이를 `coverage_input_invalid` exit 17로 변환한다. 정상 행의
payload와 성공 응답은 바꾸지 않는다.

### D-3. 문서 계약 최소 보강

- `worktree.md`: task-root 조상 탐색 허용과 allocator-root 금지 비전이를 한 문장으로 명시.
- `header-rules.md`: “테스트가 집행한다”는 주장은 실제 경로와 심볼을 정확히 지목하도록 명시.
- `pm-review-gate.md`: 기존 참조 문서 반영 검사 아래 적용 대상·발동 조건 일치 검사를 추가.

## Implementation and verification

1. 공개 CLI 테스트 2건을 먼저 추가해 기존 구현에서 RED를 확인한다.
2. D-1·D-2를 구현하고 테스트를 GREEN으로 만든다.
3. D-3의 owner 문서 3개를 수정한다.
4. 관련 scenario 테스트 전체와 code-scan 변경 파일 검증을 수행한다.
5. 표준 CLOSE 산출물 `DONE.md`에 결과와 검증 증거를 기록한다.
