# DONE: 워크트리 registry 메타의 태스크별 폴더 분리와 워크트리 세션 쓰기 권한·기동 전 점검

## 결과

워크트리 registry 메타가 태스크마다 전용 폴더 `<hub>/.opal-worktrees/.meta/task_{NNN}/meta.json`에 저장된다. 메타 쓰기의 lock(`meta.json.lock`)과 원자 쓰기 임시 파일(`meta.json.tmp.<pid>`)도 그 폴더 안에만 생긴다. `remove`가 성공하면 태스크 폴더 전체를 회수하고 `.meta/` 루트는 남긴다. 실패하면 폴더를 보존한다. 폴더를 지우는 데 실패하면 성공 판정은 유지한 채 `meta_dir_cleanup_failed` 경고를 보고한다. remove 직후 들어온 writer가 빈 폴더를 남기지도 않는다.

모든 소비자가 도구별 경로 함수 하나를 거쳐 새 구조만 읽는다. 대상은 worktree-tool, ownership-tool 훅 3종, state-tool 부트 이상 검사, launcher, Console, skill-tester다. 구 구조 `.meta/task_{NNN}.json`은 읽지도 옮기지도 않는다. 구 구조 메타 정리는 캡틴 결정에 따라 이번 범위에서 제외했다.

launcher에 치환 토큰 `{meta_dir}`을 추가했다. Codex 기본 명령은 `codex --no-daemon --add-dir "{meta_dir}" "{utterance}"`이며, 워크트리 세션은 자기 태스크 메타 폴더 하나만 추가 쓰기 경로로 받는다. `.meta/` 루트, 다른 태스크 폴더, 공유 `.git`은 받지 않는다. Claude 기본 명령은 바뀌지 않았다.

`launch`는 lease 이관·터미널 기동 전에 기동 전 점검을 한다.
- 태스크 메타 폴더와 `meta.json`의 존재·쓰기 가능 여부를 registry 조회보다 먼저 확인한다.
- `{meta_dir}` 바로 앞 옵션이 에이전트 `--help`에 있는지 확인한다(10초 제한).
- 점검에 실패하면 `launch_preflight_failed`와 `cause` 4종 중 하나로 종료하고 어댑터·lease를 건드리지 않는다.
- 공유 `.git` 쓰기는 부여하지 않으므로 `git_write_requires_escalation` 경고를 싣고, 기동은 막지 않는다.

설치 스크립트(Mac·Windows)는 전역 설정의 Codex 명령이 이전 기본값 2종 중 하나일 때만 새 기본값으로 바꾼다. 사용자 수정값은 보존하고 안내만 출력한다.

git checkpoint·finalize 커밋의 권한 처리는 바꾸지 않았다. 하네스 문서에는 공유 `.git` 쓰기가 거부될 때 권한 상승을 요청하는 기존 절차로 명시했다.

## 변경 파일

- `opal/tools/worktree-tool/worktree_tool.py`, `README.md`, `tests/{conftest.py,test_worktree_tool.py,test_task164_meta_layout.py}`
- `opal/tools/ownership-tool/ownership_tool/{ownership_core.py,heartbeat_hook.py,session_start_hook.py,stop_evaluator.py}`, `README.md`, `tests/{test_heartbeat.py,test_session_start.py,test_stop_evaluator.py,test_pretooluse_guard.py,test_integration.py,test_task164_registry_layout.py}`
- `opal/tools/state-tool/state_tool.py`, `tests/test_state_tool_core_cli.py`
- `opal/skills/opal-skill-tester/scripts/skill_tester.py`, `tests/test_task164_registry_meta.py`
- `opal/tools/worktree-launcher/worktree_launcher/{settings.py,launcher_core.py,cli.py}`, `README.md`, `tests/{conftest.py,test_cli.py,test_settings.py,test_task164_preflight.py}`
- `dashboard/backend/routers/tasks.py`, `dashboard/backend/tests/test_task164_console_registry.py`
- `opal/core/setting.default.json`, `scripts/install-mac.sh`, `scripts/install/windows.ps1`, `scripts/tests/test_agent_adapter_fields.sh`
- `opal/core/references/harness/worktree.md`, `opal/core/references/harness/task-process.md`
- `tasks/164-260928-opds-워크트리-메타-태스크폴더-권한-분리/` — TASK·PLAN·TEST-SCENARIO·AGENTIC-LOG·STATE·state·test-scenario·DONE, 설계 게이트 결과 `run/design-gate-i3.json`, 컨벤션 보고서

## 검증

- 설계 게이트: 결정론 검사가 i1·i2에서 실패했고, 보정 뒤 i3에서 독립 evaluator(design-rubric) pass를 받았다(설계 4축 PASS, 시나리오 2/2/2).
- RED-first: 6건(S-1·2·3·5·7·8)이 구현 전에 assertion 실패로 확인된 뒤 `scenario-lock`됐다. S-7의 조건 1건은 새 구조에서 성립할 수 없는 상태를 가정하고 있어, 구현자가 아닌 테스트 에이전트가 조건만 바로잡았다. 기대 계약은 그대로다.
- 독립 TEST: 필수 시나리오 S-1~S-12 **12/12 PASS**(`test-tool scenario-status`), `scenario-fidelity-check` all_met.
  - S-6 1차 실행은 환경 결함으로 무효 처리했다. 허브 루트를 cwd로 잡았고 허브가 `/tmp` 아래에 있었다.
  - 실제 배치 조건(cwd=워크트리, `.meta/`는 워크트리 밖의 형제 폴더, `/tmp` 제외)에서 codex-cli 0.157.1로 다시 실측했다. 자기 폴더 쓰기·교체는 성공했고, 다른 태스크·`.meta/` 루트·`.git` 쓰기는 거부됐다. 판정은 파일 존재로 했다.
- 소스 회귀: worktree-tool 168, ownership-tool 170, launcher 170(+4 skipped), state-tool 609(+3 skipped) 모두 passed. state-tool은 세션 환경변수를 비운 상태로 실행했다.
  - Console backend 41건, installer 5건의 실패는 태스크 이전 커밋 `86d08d7` 추출본과 실패 목록이 완전히 같다. 신규 회귀는 0건이다. installer 5건은 TS-001/TS-010·TS-025·TS-026과 `test_archive_contents` 1건, `test-install-skill-cleanup` 1건이다.
- 구 구조 경로 조합: 테스트를 제외한 source에서 0건.
- 배포본: 캡틴이 정식 `install-mac.sh`를 실행했다.
  - 설치 로그에서 `setting.json` Codex 기본값 승격을 확인했다.
  - 소스와 배포본의 sha256이 전부 같다.
  - 배포본에서 S-5(argv)·S-6(실제 codex)·S-7(`meta_dir_missing` 조기 종료) 결과가 소스와 같다.
  - 허브 task_164 메타는 새 구조로 옮겼다(해시 불변). 배포본 `worktree-tool status` ok.
- 최종 컨벤션 checker 1회: Critical 0 / High 0. Medium 5·Low 1은 모두 신규 테스트 파일에 태스크 번호를 적은 것으로, 기존 테스트의 관행과 같아 advisory로 수용했다.
- TEST 소요 계측(`test-metrics`): `auto_seconds`·`human_wait_seconds`가 null이다. test-clock이 기록되지 않았으므로 unknown이다.

## 회고적 학습 후보

.opal/brain/pages/entity/worktree-tool.md
.opal/brain/pages/entity/ownership-tool.md
.opal/brain/pages/concept/worktree-session-launch-order-and-ownership.md

## 참고

- 실행 중 사고: 병렬 워커 2명이 금지된 `git stash`를 쓰다가 작업 트리 일부(하네스 문서·태스크 상태)를 HEAD로 되돌렸다. PM이 중지·대조·재적용으로 복구했고, 이후 검증된 단위마다 checkpoint로 고정했다. 경위는 AGENTIC-LOG #13~#14에 있다. 공유 stash 스택을 쓰는 git 명령을 워커 계약에서 막는 것은 회고 후보다.
- 설치 후 허브에 구 구조 메타가 남아 있는 다른 프로젝트의 active 태스크(예: opal-studio task_012)는 새 도구의 registry 조회에서 보이지 않는다. 기존 메타 정리는 캡틴이 직접 하기로 했다.
- 허브 루트에서 Codex를 실행하는 세션은 원래 `.meta/` 전체에 쓸 수 있다. 이번 격리는 워크트리 세션만 대상으로 한다.
- git checkpoint·finalize의 허브 위임은 후속 태스크 범위다(TASK 제외 항목).
- 이 태스크에서는 main merge·push를 수행하지 않았다. 브랜치 `feat/OP-TASK-164`는 merge 대기 상태다.
