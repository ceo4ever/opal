# DONE: Codex 워크트리 부팅 소유권 복구

## 결과

Codex 자식 세션의 lease 획득을 기다린 뒤 허브 launcher가 같은 세션 ID를 registry owner로 확정한다. 미확정 상태에서 owner 없는 성공을 기록하지 않고, 실패 시 터미널·lease 확인 결과에 따라 허브 소유로 복귀하거나 `recovery_required`를 남긴다. registry 잠금의 권한 거부는 즉시 `registry_write_denied`로 반환하며, lease를 가진 Codex 자식은 허브 확정 진단과 함께 부팅할 수 있다. Codex 기본 명령에 `--no-daemon`을 추가하고 구 기본값만 이관하도록 설치 스크립트를 갱신했다.

개인 launcher 설정을 보존하면서 변경된 런타임 파일 13개를 선택 설치했다. 태스크 162의 기존 세션 종료를 확인하고 새 Codex 세션을 기동했다. 새 세션의 lease owner와 registry owner가 일치하며, 첫 checkpoint SHA가 registry 기록과 일치한다.

## 변경 파일

- `opal/tools/worktree-tool/worktree_tool.py`, `schema/worktree.schema.json`, `tests/test_worktree_tool.py`, `README.md`
- `opal/tools/ownership-tool/ownership_tool/{ownership_core.py,session_start_hook.py,codex_adapter.py}`, `tests/{test_session_start.py,test_codex_identity.py}`, `README.md`
- `opal/tools/worktree-launcher/worktree_launcher/{launcher_core.py,cli.py,settings.py,adapters/orca.py}`, `tests/{test_launcher_core.py,test_adapter_orca.py,test_cli.py,test_codex_handoff.py,test_integration.py,test_settings.py}`, `README.md`
- `opal/core/setting.default.json`, `opal/core/references/harness/worktree.md`, `opal/bootstrapper/codex-bootstrap.md`
- `scripts/install-mac.sh`, `scripts/install/windows.ps1`, `scripts/tests/test_agent_adapter_fields.sh`
- `docs/ARCHITECTURE.md`
- `tasks/163-260927-opds-코덱스-워크트리-부팅-소유권-복구/`의 TASK·REQUEST·PLAN·TEST-SCENARIO·STATE·AGENTIC-LOG·state·test-scenario, 컨벤션 보고서와 `run/` 검증 증거

## 검증

- 독립 TEST: 잠금 RED 6/6, 필수 시나리오 S-1~S-10 **10/10 PASS** (`test-tool scenario-status`).
- 소스 회귀: launcher 155 passed/4 skipped, ownership-tool 167 passed, Task 163 worktree-tool 집중 테스트 2 passed. 변경 코드의 문법·JSON·`git diff --check` 통과.
- 설치본 실측: 실패 launch는 `session_boot_timeout` 후 확인된 터미널 종료와 `hub_owned` 복귀; 성공 launch는 실제 Codex 자식의 lease·registry owner 동일. 실제 샌드박스 권한 거부는 0.134ms에 `registry_write_denied`; 격리된 설치본 어댑터 검증은 `ok:true`·`registry_owner_deferred_to_hub`를 반환하고 registry·lease 파일 해시는 불변. 태스크 162 첫 checkpoint SHA `48f25a5aac77d320b4f491ddb938992acba50328`가 registry 기록과 일치.
- Codex 명령 이관 `TS-028` 통과. 컨벤션 진단 Critical/High 0, state validate 위반 0, code-scan 인용 검사 통과. 개인 `~/.opal/setting.json` 해시 불변.

## 회고적 학습 후보

.opal/brain/pages/concept/worktree-session-launch-order-and-ownership.md
.opal/brain/pages/entity/ownership-tool.md
.opal/brain/pages/entity/worktree-tool.md

## 참고

- 전체 installer 회귀의 기존 Claude hook 항목 `TS-025`·`TS-026`은 실패했다. Task 163 변경 항목 `TS-028`은 통과했고, 두 실패는 이번 소유권 변경의 판정과 분리해 `run/test-report.md`에 기록했다.
- 태스크 162의 후속 TEST는 별도 브랜치 통합·설치 승인 경계에서 대기 중이다. 이 태스크에서는 merge·push를 수행하지 않았다.
