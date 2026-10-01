# DONE: @header 이력 누적 코드 차단 + state-tool 동작 보존 분할

## 결과

- `code-scan validate`가 `header_history`(description·note의 서로 다른 태스크 번호 2개 이상, 미정의 필드)를 경고가 아니라 차단(exit 2)으로 판정한다. 전체·`--changed` 두 모드 모두 같다. PM Gate는 CLOSE 전 `validate --changed`의 exit 0을 이미 요구하므로 이 판정이 곧 게이트 실패가 된다.
- 머리말이 읽기 범위(24,576바이트) 안에서 닫히지 않는 파일은 `uncovered:pre_existing`으로 숨지 않고 새 차단 코드 `header_overflow`로 드러난다. 읽기 범위 상수는 유지했다.
- 저장소의 `header_history` 10건(9개 파일)과 `uncovered:incomplete` 1건, 읽기 범위를 넘은 `state_tool.py` 머리말을 정리했다. 저장소 전체 `validate`가 exit 0, `header_history`·`header_overflow` 0건이다.
- `state_tool.py`(8,256줄)를 37줄 진입점으로 줄이고 코드를 `state_tool_parts/` 아래 9개 모듈(`codes`·`base`·`run_log`·`journal`·`guards`·`gates`·`commands_core`·`commands_run`·`cli`)로 나눴다. 기존 CLI 경로·서브커맨드·stdout JSON·종료 코드·오류 코드·산출물은 기준 트리와 비교해 차이가 없다.
- 유지한 것: state-tool의 외부 계약, `~/.opal` 배포본(이 태스크에서 install 미실행), 읽기 범위 24,576바이트.
- 적용한 경계: 코드는 원문 그대로 이동하고 `get_kst_datetime`·`_import_ownership_lease`·`_import_run_log_core` 3개 이름만 `base.<이름>` 한정 호출로 바꿨다. 분할 후 줄 번호 인용이 깨지는 증거 검사 테스트와 098 기록 TASK.md의 인용은 같은 코드의 분할 후 위치로 옮겼다.

## 변경 파일

- `docs/CONVENTIONS.md`
- `opal/core/references/harness/header-rules.md`
- `opal/core/references/harness/pm-review-gate.md`
- `opal/core/references/header-standard.md`
- `opal/skills/opal-skill-tester/scripts/skill_tester.py`
- `opal/tools/code-scan/README.md`
- `opal/tools/code-scan/code-scan.js`
- `opal/tools/code-scan/tests/test-header-history.js`
- `opal/tools/code-scan/tests/test-validate.js`
- `opal/tools/git-sync-tool/tests/conftest.py`
- `opal/tools/git-sync-tool/tests/test_git_sync_tool.py`
- `opal/tools/oppb-runtime-tool/tests/test_pilot_isolation.py`
- `opal/tools/oppb-runtime-tool/tests/test_product_flow.py`
- `opal/tools/ownership-tool/ownership_tool/session_start_hook.py`
- `opal/tools/run-log-tool/tests/test_run_log_tool.py`
- `opal/tools/state-tool/README.md`
- `opal/tools/state-tool/state_tool.py`
- `opal/tools/state-tool/state_tool_parts/__init__.py`
- `opal/tools/state-tool/state_tool_parts/base.py`
- `opal/tools/state-tool/state_tool_parts/cli.py`
- `opal/tools/state-tool/state_tool_parts/codes.py`
- `opal/tools/state-tool/state_tool_parts/commands_core.py`
- `opal/tools/state-tool/state_tool_parts/commands_run.py`
- `opal/tools/state-tool/state_tool_parts/gates.py`
- `opal/tools/state-tool/state_tool_parts/guards.py`
- `opal/tools/state-tool/state_tool_parts/journal.py`
- `opal/tools/state-tool/state_tool_parts/run_log.py`
- `opal/tools/state-tool/tests/fixtures/state_tool_surface.json`
- `opal/tools/state-tool/tests/state_tool_test_support.py`
- `opal/tools/state-tool/tests/test_pilot_shared_contract.py`
- `opal/tools/state-tool/tests/test_split_surface.py`
- `opal/tools/state-tool/tests/test_state_tool_core_cli.py`
- `opal/tools/state-tool/tests/test_state_tool_extended_contracts.py`
- `opal/tools/state-tool/tests/test_state_tool_mode_contracts.py`
- `opal/tools/state-tool/tests/test_state_tool_ownership.py`
- `opal/tools/state-tool/tests/test_state_tool_verification_gates.py`
- `opal/tools/test-tool/tests/test_e2e_action_value_redaction.py`
- `opal/tools/tool-scan/tests/test_tool_scan.py`
- `opal/tools/worktree-tool/tests/test_worktree_tool.py`
- `opal/tools/worktree-tool/worktree_tool.py`
- `opal/skills/opal-pilot-dev2/references/lifecycle.md`
- `tasks/backup/098-260821-opds-근거등급-확정판정-트랙강등/TASK.md`

## 검증

- TEST-SCENARIO S-1~S-12 12건 전부 pass(`opal-test-agent` 독립 실행, 대상 SHA `3c77f33`). RED-first 대상 S-1·S-2·S-3·S-5는 구현 전 실패를 기록하고 잠근 뒤 GREEN.
- `node --test opal/tools/code-scan/tests/test-header-history.js` 29/29, `test-validate.js` 46/46. code-scan 전체 테스트는 기준 트리와 실패 9건의 이름이 같다(신규 테스트 12건 추가).
- `opal/tools/state-tool/run-tests.sh` 세션 환경변수 제거 시 640 passed / 0 failed(기준 631, 차이 9건은 `test_split_surface`). 세션 환경변수가 있으면 기준과 같은 2건이 실패한다. `test_pilot_isolation.py` 11 passed / 2 failed로 기준과 같다.
- 기준 트리(`git archive dee405ca opal`)와 분할본의 대표 명령 19회 호출(오류 경로 3종 포함) 정규화 출력·종료 코드·산출물 차이 0건.
- 저장소 전체 `code-scan validate --json` exit 0, `header_history`=0, `header_overflow`=0.
- 최종 게이트: 보안 Critical 0/High 0(Low 2건 advisory), 컨벤션 Critical 0/High 0(Medium 10건은 `state_tool_parts` 패키지명이 kebab-case가 아니라는 동일 advisory). `state-tool validate` violations 0, `--code-scan-citation-check` pass.

## 회고적 학습 후보

.opal/brain/pages/entity/code-scan-tool.md
.opal/brain/pages/entity/header-standard-doc.md
.opal/brain/pages/entity/state-tool.md
.opal/brain/pages/concept/behavior-preserving-split-and-block-conversion-lessons.md

## 참고

- `~/.opal` 배포본은 분할 전 단일 파일 그대로이며 install은 main 병합 뒤 별도로 실행해야 한다. 그 전에는 소스 트리의 `state_tool.py`와 배포본이 다르다.
- 보안 advisory GC-001: `skill_tester.py`의 `_framework_fingerprint`가 파일 내용을 구분자 없이 이어 붙여 해시한다. 파일 경계가 이동해도 같은 지문이 나올 수 있어 상대경로·길이를 해시에 포함하는 후속 개선을 권고한다.
- `.opal/brain/pages/entity/code-scan-tool.md:44`와 `header-standard-doc.md:40`은 `header_history`를 비차단으로 서술한다. 이번 CLOSE의 brain ingest로 갱신했다.
- `opal/tools/state-tool/README.md`·code-scan `README.md`는 이 태스크 안에서 갱신했다.
