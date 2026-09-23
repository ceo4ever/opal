# DONE: FW 검토 개선의 결정론화

## 결과

태스크 149에서 제기된 프레임워크 개선 후보 6건을 실제 계약과 코드에 대조해 4건을 채택하고
구현했다. Stop guard의 `continue` 차단과 state-tool의 unblock/log-event 제안 2건은 현행 의도된
계약이거나 이미 제공되는 표면이 있어 범위에서 제외했다.

- `scenario-coverage-build`가 셀 안의 escaped pipe(`\|`)를 내용으로 보존한다.
- Markdown에서 선택 사항인 선두·후미 테두리 파이프가 없어도 S 행을 인식한다.
- 인식한 S 행의 열 수가 헤더와 다르면 조용히 버리지 않고 문제 행을 포함한
  `coverage_input_invalid`(exit 17)로 거부한다.
- `task_root`의 조상 탐색과 `allocator_root`의 추론 금지가 서로 다른 계약임을 대칭적으로
  명시했다.
- 테스트 집행 주장은 레포 상대 테스트 경로와 정확한 심볼을 근거로 요구하게 했다.
- PM Gate가 인용한 `[MUST]`의 적용 대상·발동 조건을 현재 변경과 대조하게 했다.

## 변경 파일

- `.opal/MEMORY.json` — 태스크 번호 151 할당
- `opal/tools/test-tool/lib/scenario.py`
- `opal/tools/test-tool/tests/test_scenario.py`
- `opal/core/references/harness/worktree.md`
- `opal/core/references/harness/header-rules.md`
- `opal/core/references/harness/pm-review-gate.md`
- `tasks/151-260923-oppm-FW-검토개선-결정론화/TASK.md`
- `tasks/151-260923-oppm-FW-검토개선-결정론화/DONE.md`

기존 미추적 `.claude/skills/`와 태스크 149 워크트리의 WIP는 수정하지 않았다.

## 검증

- RED: 신규 T151/S-1·S-2 2건이 기존 구현에서 실패했다. escaped pipe 행은 누락됐고,
  malformed 행은 누락된 채 성공으로 오판됐다.
- 1차 GREEN 뒤 독립 검증자는 선두 또는 후미 테두리 파이프가 없는 S 행이 여전히 누락되는
  공백을 찾아 FAIL 판정했다.
- 보완 후 독립 재검증: **PASS**, findings/blockers 0건.
  - 관련 coverage builder 테스트 **12/12 PASS**
  - `test_scenario.py` **59 passed, 45 subtests passed**
  - 공개 CLI 경계 실측: bordered mismatch, 선두 누락, 후미 누락은 모두 exit 17;
    정상 borderless 표와 escaped `\|` 표는 exit 0
- 관련 회귀 `test_test_tool.py + test_scenario.py`:
  **76 passed, 58 subtests passed**
- `py_compile`, `git diff --check`: 통과
- 변경 파일 code-scan: exit 0, `newly_uncovered: 0`. harness Markdown 3건은 기존
  `pre_existing` 진단이며 비차단이다.

확장 `opal/tools/test-tool/tests` 실행에서는 최종 경계 보완 전 기준
`435 passed, 299 subtests passed, 46 failed, 3 errors`가 나왔다. 실패는 archived task 127
fixture 부재, 기존 frontend/dist 상태, E2E 실행 환경, 변경 파일을 고정한다고 가정한 dirty guard에
집중됐고 이번 parser·문서 변경의 관련 스위트는 위와 같이 전건 통과했다.

## 회고

Markdown 표의 바깥 테두리 파이프가 선택 사항이라는 경계를 최초 구현과 내부 검토가 함께
놓쳤다. 독립 검증자가 성공 행 뒤에 불완전 행을 섞는 방식으로 “조용한 누락인데 전체 coverage는
성공”하는 조건을 다시 만들면서 발견했다. 표 파서는 구분자 escape뿐 아니라 문법상 선택적인
경계 표기까지 공개 CLI 수준에서 검증해야 한다.

## 회고적 학습 후보

없음. 재사용할 규칙은 이번 변경에서 각각의 owner 문서와 공개 CLI 회귀 테스트에 직접
반영했다.

## 종료 경계

소스·태스크 산출물 작성과 독립 검증을 마친 뒤 사용자 명시 요청으로 태스크 커밋을 생성한다.
push, 배포, 태스크 149 수정은 수행하지 않는다.
