# DONE: 코덱스 세션 이관 복구

## 결과

Codex native session ID를 전용 adapter에서 해석하고, OPAL 중립 ID와 기존 Claude 우선순위 및 훅 payload-only 경계를 보존했다. 공개 `session-launch`는 부모 신원을 제거한 뒤 원래 명령을 실행하고, 설치된 Codex bootstrap의 `codex-start`는 실제 새 ID로 등록·claim·heartbeat를 수행한다. registry 등록 실패는 성공으로 숨기지 않는다.

launcher는 시작 신원을 고정하여 handoff와 cancel에 명시 전달한다. 신원 부재·다른 live owner는 변경 전에 거부하고, 실패 cause·adapter·가용 source 이름을 진단한다. 최종 registry는 공개 `ownership-set --owner-from-lease`로 실제 자식 owner를 반영한다. state-tool 상태 전이·run-log actor와 worktree checkpoint도 공통 resolver를 사용한다.

기존 task155 PM 세션의 실제 ID가 허브와 다름을 확인한 뒤 공개 SessionStart·heartbeat·ownership-set으로 이관을 복구했다. 초기 bridge는 복구에만 사용했고 최종 설치본 검증에서는 OPAL export 없이 동작했다. 새 태스크·워크트리·PM을 만들지 않았으며 원 장애 task008, 허브 MEMORY 및 허브의 기존 .claude/skills 변경은 수정하지 않았다.

## 변경 파일

- `docs/ARCHITECTURE.md`
- `opal/bootstrapper/codex-bootstrap.md`
- `opal/core/references/harness/worktree.md`
- `opal/tools/ownership-tool/README.md`
- `opal/tools/ownership-tool/ownership_tool/claude_adapter.py`
- `opal/tools/ownership-tool/ownership_tool/cli.py`
- `opal/tools/ownership-tool/ownership_tool/ownership_core.py`
- `opal/tools/state-tool/state_tool.py`
- `opal/tools/state-tool/tests/test_state_tool_ownership.py`
- `opal/tools/state-tool/tests/test_state_tool_run_log.py`
- `opal/tools/worktree-launcher/README.md`
- `opal/tools/worktree-launcher/tests/test_integration.py`
- `opal/tools/worktree-launcher/tests/test_launcher_core.py`
- `opal/tools/worktree-launcher/worktree_launcher/launcher_core.py`
- `opal/tools/worktree-tool/README.md`
- `opal/tools/worktree-tool/worktree_tool.py`
- `opal/tools/ownership-tool/ownership_tool/codex_adapter.py`
- `opal/tools/ownership-tool/tests/test_codex_identity.py`
- `opal/tools/worktree-launcher/tests/test_codex_handoff.py`

- 태스크의 PLAN·TEST-SCENARIO·AGENTIC-LOG·state-tool 산출물·독립 검증 및 run 증거.

## 검증

- 독립 TEST: 잠긴 시나리오 **9/9 PASS**, FAIL/BLOCKED 0. 원본: `test-scenario.json`.
- 개별 pytest: ownership165, launcher148, worktree147, state ownership9, state 핵심193 통과(핵심93 subtests 포함). launcher의 기존 선택형 live4건 skip은 별도 실제 Orca 검증으로 보완했다.
- 실제 정식 설치본 Orca/Codex: 부모≠자식 native ID, 부모 OPAL 미상속, lease generation1→2, registry/lease owner 일치, 유효 TTL, 1초 이상 간격의 heartbeat 증가·generation 유지, terminal 정확 handle 정리 확인.
- 실제 증거: `run/real-e2e-final/proof.json`, `launch.json`, `terminal-close.json`, `run/independent-e2e-raw-check.json`.
- 정식 `scripts/install-mac.sh` 메뉴1만 사용. 제품7개 source/installed SHA256 및 Codex bootstrap 본문 일치: `run/installed-source-proof.json`, `run/independent-installed-hash-check.json`.
- Ruff 오류군, diff check, secret 패턴/플랫폼 env 경계, code-map changed, 독립 convention PASS. 기존 헤더 경고는 별도로 보존했다.
- 추가 독립 RED: state-tool native 신원 누락 실패 후9pass. 테스트 주석만 JSON header로 변환했으며 AST·실행 본문 동일 증거를 남겼다.
- 초기 환경·설치 경합 실패와 재검증은 `run/independent-test-report.md`에 보존했다.

## 회고적 학습 후보

.opal/brain/pages/entity/ownership-tool.md
.opal/brain/pages/concept/worktree-session-launch-order-and-ownership.md

## 참고

공식 openai/codex commit `53446f90a56692dede3c8f413e8d486a6adb77b5`는 native root-session ID의 도구 환경 주입과 descendant 공유를 설명한다. 설치 standalone0.154.0에는 Rust 소스가 없으므로 공개 commit과 바이너리의 완전 동일성이나 모든 resume 경로 수명은 보증하지 않는다. fresh root 기동의 실제 다른 ID는 두 번 관측했다. 근거·한계: `run/codex-identity-research.json`.

E2E 구조화 profile에 CLI/terminal 종류가 없어 API/browser로 허위 분류하지 않았다. 지원되는 공개 scenario-mark의 real-usage/evidence 경로로 실제 판정을 기록했고 원시 expected/actual도 보존했다.

merge/push와 워크트리 제거는 수행하지 않는다. brain 후보는 워크트리 계약에 따라 선언만 하고 실제 귀속은 후속 허브 절차에 맡긴다.

회고에서 CLI/terminal E2E profile과 정식 설치·검증 경합 방지의 FW 개선 후보2건을 공식 improve-tool로 기록했다(`run/retrospective-*.json`). worktree finalize는 관측 brain/MEMORY 변경0·귀속 commit 없음으로 성공했다(`run/worktree-finalize.json`).
