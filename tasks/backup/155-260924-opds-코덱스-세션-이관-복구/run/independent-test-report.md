# 독립 TEST 결과

판정: **All Pass — 9/9 시나리오**. `test-tool scenario-status`의 failed/blocked=0이며 `state-tool mark --task-step test.run_tests --done --as-worker --worker-stage TEST` 성공. PM Gate는 수행하지 않았다.

## 실행 증거

- ownership 전체: 165 passed (`independent-ownership.txt`).
- launcher 전체: 148 passed, 기존 선택형 live 4 skipped (`independent-launcher.txt`). 실제 Orca/Codex 검증은 별도 실행으로 입증했다.
- worktree 전체: 147 passed (`independent-worktree.txt`).
- state ownership: 9 passed (`independent-state.txt`).
- state core CLI/run-log/mode transition: 193 passed, 93 subtests passed (`independent-state-core-clean.txt`).
- 초기 state 실행 5 fail은 숨기지 않고 `independent-state-core.txt`에 보존했다. 3건은 no-env fixture의 native ambient 제거 누락, 2건은 설치 중 date.js 부재였다. PM의 fixture 환경 정리 후 설치 완료 시점에 native ambient로 동일 5건을 재실행하여 5 passed 확인 (`independent-state-native-recheck.txt`). 기존 assertion은 유지됐다.
- optional ownership dependency 부재는 None + ownership_import_failed 경고로 비차단 처리 (`independent-state-missing-dependency.json`).
- Ruff E9/F63/F7/F82, git diff --check, code-map changed 모두 통과. code-map 기존 uncovered/header_history 경고는 보존 (`independent-lint.txt`, `independent-code-map.json`).
- 변경 파일 secret 패턴 및 core 플랫폼 신원 문자열 AST 검사 발견 0 (`independent-security.json`).

## 실제 Orca/Codex

`real-e2e-final/`의 Codex thread.started, 공개 CLI 응답, 실제 lease/registry 파일, launcher receipt를 독립 대조했다. native child와 parent가 다르고 OPAL 부모 신원이 없으며, lease generation 1→2, heartbeat 시각 엄격 증가, heartbeat 동안 generation 유지, 유효 TTL, registry/lease native owner 일치를 확인했다. 실제 terminal handle과 close 응답이 일치하며 ptyKilled=true다. 증거는 `independent-e2e-raw-check.json`, `independent-real-verdict.json`, `real-e2e-final/terminal-close.json`이다.

7개 제품 source/installed SHA256을 직접 재계산해 일치를 확인했고 Codex bootstrap 코드블록도 설치본과 일치했다 (`independent-installed-hash-check.json`).

## 결과 기록 형식 한계

`scenario-mark --verdict-json`의 E2E profile 계약은 browser/API 계열이며 CLI/terminal profile이 없다. profile=None인 구조화 verdict 제출은 형식 FAIL로 기록되었다. 실제 테스트 실패와 구분하여 원시 expected/actual 및 required/observed evidence JSON을 보존하고, 지원되는 공개 `scenario-mark --result pass --fidelity real-usage --evidence`로 S-5/6/9를 기록했다. API/browser 실행으로 허위 분류하지 않았고 잠긴 명세와 기대 계약은 변경하지 않았다.

제품 수정 없음. 독립 검증 소요 약 9분; state 도구 duration 필드는 정확한 harness duration_ms 부재로 unknown 사용.
