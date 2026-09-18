---
template: sdlc-v2
---
# TASK: run-log 계약 완성 — PM 활동 누락 판정과 payload 키 폐쇄

## Problem

태스크 135는 run-log 기록 완전성을 구현하면서 계약의 빈 곳 2개를 의도적으로 남겼다(`tasks/135-260915-opds-run-log-기록완전성/DONE.md` §참고). 둘 다 `docs/run-log/CONTRACT.md`가 소유해야 할 조문이 아직 없어서 생긴 공백이다.

1. **완전성 진단이 "PM 활동 누락"을 영영 보고하지 못한다.** 진단이 반환하는 누락 4종 중 이 한 종만 값을 채우는 조건이 계약에 정의되어 있지 않아 항상 빈 배열을 반환한다(`docs/run-log/CONTRACT.md:478`, `opal/tools/state-tool/state_tool.py:1371`). 운영자는 결과를 보고 "실제로 누락이 없다"와 "판정이 아직 구현되지 않았다"를 구분할 수 없고, 완료 판정의 근거 4종 중 1종이 사실상 없는 상태로 진단을 신뢰하게 된다.

2. **PM 활동 payload의 키 폐쇄가 실제로는 폐쇄가 아니다.** 폐쇄 목록은 CLI 표면 하나(`state-tool log-event`)의 입력 검증에서만 집행되고, 이 표면을 거치지 않는 생산 경로(adapter·importer)는 검사를 받지 않는다(`docs/run-log/CONTRACT.md` §1.3 말미). 계약이 금지한 형태의 사건이 조각에 그대로 기록될 수 있으므로, 폐쇄 목록을 읽은 소비자가 기대하는 보장이 성립하지 않는다.

두 공백은 같은 계약 문서가 소유하고, 같은 구현 파일 집합을 건드리며, "계약 조문을 먼저 확정하고 구현이 그것을 따른다"는 동일한 순서를 요구한다.

## Proposed outcome

- 완전성 진단을 실행하면 PM 활동 누락이 계약에 적힌 결정론적 조건에 따라 채워진다. 빈 배열이 "누락 없음"을 뜻하고, 같은 입력에는 항상 같은 판정이 나온다.
- 어떤 생산 경로로 기록하든 PM 활동 사건의 의미 payload 키 폐쇄가 동일하게 집행된다. 계약이 금지한 형태의 사건은 조각에 남지 않는다.
- CONTRACT에서 두 공백을 명시하던 유보 문장이 사라지고, 그 자리에 집행 가능한 조문이 들어간다.

## Affected users and systems

- **소유 계약 문서**: `docs/run-log/CONTRACT.md` — 두 조문의 SSOT. 필요 시 `docs/run-log/TRD.md`의 설계 근거 흐름.
- **기록 코어**: `opal/tools/run-log-tool/run_log_core.py` — payload 키 폐쇄의 집행 지점 이동 대상.
- **상태 도구**: `opal/tools/state-tool/state_tool.py` — 완전성 진단(`verify --run-log-completeness-check`)과 `log-event` 입력 검증.
- **테스트**: `opal/tools/run-log-tool/tests/test_run_log_tool.py`, `opal/tools/state-tool/tests/test_state_tool_run_log.py`.
- **문서 미러**: `opal/tools/state-tool/README.md`(요약+포인터).
- **범위 제외**: `~/.opal` 배포(install) 실행, `docs/run-log/surfaces.json` 신규 표면 id 신설, 미구현 상태로 선언만 남은 `state-tool.restart-run` 구현.

## Constraints

- C-1: 계약 조문 확정이 구현보다 앞선다. 구현자가 편의로 만든 조건을 사후에 계약으로 승격하지 않는다.
- C-2: PM 활동 누락의 트리거 조건은 같은 상태·사건 입력에 대해 같은 결과를 내는 결정론적 규칙이어야 한다.
- C-3: 완전성 진단은 read-only·비차단을 유지한다 — 상태 파일을 변경하지 않고 exit 0으로 끝난다.
- C-4: `run_log_core`는 상태 원천 파일을 읽지 않는 단방향 의존을 유지한다(`docs/run-log/TRD.md` D-5). 상태 대조는 `state-tool`이 전담한다.
- C-5: 임의 `data` 키를 전제로 설계된 기존 fixture(`opal/tools/run-log-tool/tests/test_run_log_tool.py:901` S-16, `:951` S-17)는 각 시나리오의 본래 검증 축(요청 재사용 충돌 판정, 멱등 정규화 불변성)을 보존한 채로만 수정한다. 축을 약화시키거나 시나리오를 삭제하지 않는다.
- C-6: 스키마 1.0/1.1 태스크와 run_log 블록이 없는 태스크의 응답 키 집합·산출물은 종전과 동일하게 유지한다.
- C-7: run-log 계열 오류 코드 테이블과 기존 평면 오류 코드 테이블의 물리 분리를 유지한다(`opal/tools/state-tool/state_tool.py` `RUN_LOG_STATE_ERROR_CODES` ↔ `ERROR_CODES`).
- C-8: `~/.opal` 배포본을 직접 수정하지 않는다. 프로젝트 소스만 수정한다.

## Acceptance criteria

- AC-1: `docs/run-log/CONTRACT.md`가 PM 활동 누락의 트리거 조건을 정의하고, 그 조문만 읽고 임의 입력에 대해 누락 여부를 판정할 수 있다.
- AC-2: "현재 트리거 조건을 정의하지 않아 항상 빈 배열을 반환한다"는 유보 서술이 CONTRACT와 README에서 0건이다.
- AC-3: 트리거 조건을 만족하는 fixture에서 완전성 진단이 PM 활동 누락을 비어 있지 않게 반환하고, 만족하지 않는 fixture에서 빈 배열을 반환한다 — 두 방향 모두 테스트로 관찰된다.
- AC-4: PM 활동 payload의 키 폐쇄가 기록 코어의 append 경로에서 집행되어, `state-tool log-event` CLI를 거치지 않는 직접 호출도 계약 위반 payload를 거부한다.
- AC-5: "이 표면을 거치지 않는 다른 생산 경로는 이 폐쇄 검사를 받지 않는다"는 범위 한정 서술이 CONTRACT에서 0건이다.
- AC-6: `test_run_log_tool.py`·`test_state_tool_run_log.py`·`test_state_tool.py` 세 스위트가 전건 통과하고, 135 시점 대비 신규 실패 0건이다.
- AC-7: `state-tool validate`가 violations 0으로 통과한다.
