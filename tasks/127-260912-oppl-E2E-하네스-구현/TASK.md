---
template: sdlc-v2
---
# TASK: OPAL 범용 E2E 하네스 구현 (제안서 태스크 3~9)

## Problem

`docs/proposals/opal-e2e-harness.md`가 정의한 9개 구현 태스크 중 **2개가 완료됐고 7개가 남았다**. 태스크 1(E2E profile·verdict 계약)은 태스크 125가, 태스크 2(Console 실행·프로세스 소유권)는 이 태스크의 앞선 수행(`archive/README.md`)이 끝냈다.

그 결과 **판정 계약과 최소 실행 환경은 있으나 그것을 집행할 실행 주체가 없다.**

- `opal/tools/test-tool/lib/e2e/`에 포트 bind·프로세스 그룹 기동·health gate 골격이 있으나, **allocator lock·lease record·stale 회수가 없어** 여러 작업본이 동시에 검증할 수 없다. 대상 소스 증명(`run.json`)도 없다.
- Browser·API·Human 실행 주체가 전무해 `e2e_contract.py`가 정의한 5개 profile 중 어느 것도 실제로 돌지 않는다. `e2e_adapter.py:217-225`는 `assertion_results: []`로 `build_verdict`를 호출하므로 **구조적으로 `pass`를 낼 수 없다** — 계약은 있는데 집행자가 없다는 코드 근거다.
- Playwright가 기본 설치에 남아 설치 비용과 "무엇이 진짜 검증인가"의 경쟁 정의가 유지된다.

추가로 **앞선 수행이 남긴 안전 결함 1건**이 이미 브랜치에 들어가 있다. PID 레코드는 `stop` 실행 시에만 삭제되므로 크래시·리부팅 시 무기한 잔존하고, 리부팅 후 PID 재할당 시 기록된 pid가 무관한 사용자 프로세스를 가리킨다. 이때 `app_dir`은 레코드 자기 필드라 당연히 일치하고 `kill -0`도 성공해 종료 분기로 직행한다. `scripts/install-mac.sh`가 이 경로를 무인 호출하므로 **리부팅 후 첫 설치가 임의 사용자 프로세스를 종료할 수 있다**(`archive/README.md` §미해결 안전 결함).

## Proposed outcome

main과 여러 작업본을 각각 격리 실행하면서 Browser·API·Hybrid·Collaborative·Manual E2E를 하나의 판정·증적 계약으로 수행하는 하네스가 동작한다.

- 실행자가 대상(`source-main`/`source-worktree`/`installed`)을 지정하면 하네스가 포트를 임대하고 그 소스 트리에서 SUT를 기동한 뒤 health 통과 후 시나리오를 실행한다.
- 동시에 실행되는 run끼리, 그리고 사용자의 `127.0.0.1:7823` Console과 서로 간섭하지 않는다.
- assertion과 필수 증적이 확인된 실행만 `pass`·`real-usage`로 기록된다.
- Orca가 없는 환경에서도 standalone agent-browser로 같은 시나리오가 실행된다.
- Playwright는 기본 설치에서 빠지고, 남은 소비자는 이전되거나 명시적 opt-in으로만 남는다.
- 오염된 PID 레코드가 사용자 프로세스를 죽이지 못한다.

## Affected users and systems

- **포함**: `opal/tools/test-tool/`(E2E orchestrator·runtime·drivers·executors·evidence), `opal/tools/opal-cli/lib/console.sh`(PID 레코드 stale 판정 보강), `scripts/install-mac.sh`·`scripts/install/windows.ps1`·`opal/tools/requirements.txt`(Playwright 기본 설치 제거), `opal/tools/playwright-tool/`, `opal/agents/opal-wtm-agent/`, `opal/core/mcps/playwright.json`, `opal/tools/doctor/`, `opal/tools/tool-scan/tests/`, `opal/templates/test-tools.yaml`, oppl·oppd·opsdd의 L3b·`real-usage` 문구, `opal/core/references/tools.md`·`agents.md`·`mcps.md`, `.gitignore`.
- **제외**: 태스크 125가 확정한 profile·verdict·exit code 계약의 재설계(소비만 한다), 앞선 수행이 완료한 Console 소유권 모델과 FE 주소 주입의 재작업, Playwright·브라우저 제품 기능의 자체 재구현, `test-scenario.json` 스키마 교체, community skill catalog의 Playwright 항목, 격리 `OPAL_HOME` 배포본 **생성** 절차.
- **사용자**: OPAL로 E2E를 돌리는 개발자(로컬 macOS·CI), Console을 상시 띄워 쓰는 사용자.

## Constraints

- C-1: 태스크 125가 확정한 profile·final status 5종·`awaiting_human`·exit code(0/6/7/18/19/20) 계약을 재정의하지 않고 소비한다. `opal/tools/test-tool/lib/e2e_contract.py`와 `lib/scenario.py`는 변경 0이다.
- C-2: 사용자 소유 자원(`127.0.0.1:7823` Console daemon, 사용자 브라우저 탭·cmux surface·Orca worktree, 사용자 `~/.opal`)을 종료·삭제·재설치하지 않는다. 검증은 격리 `OPAL_HOME`·별도 포트에서만 수행한다.
- C-3: 다음 실행 후보로의 전환은 `provider_unavailable`에만 허용한다. 제품 실패·assertion 실패·인증 실패를 다른 mode 성공으로 덮지 않으며, `infra_error`에서 다음 후보로 넘어가지 않는다.
- C-4: 구현 순서는 제안서 §14를 유지한다 — Runtime Manager(3)·Browser driver 계약(4)이 executor(5~8)보다 앞서고, Playwright 기본 설치 제거(9)가 마지막이다.
- C-5: 산출물은 OS 임시 디렉터리 또는 `OPAL_E2E_ARTIFACT_DIR`에만 쓴다. 저장소 `dist/`·추적 파일·설치본을 변경하지 않는다.
- C-6: 증적 저장 전 `Authorization`·`Cookie`·`Set-Cookie`·query secret을 redaction하며, 실패 시 원문을 남기지 않고 `infra_error`로 판정한다.
- C-7: 프로젝트 기존 규칙을 유지한다 — `~/.opal/` 직접 편집 금지(프로젝트 소스 수정 후 install 배포), 플랫폼 분기는 어댑터 계층에만, @header·Citation·state-tool 규칙 준수.
- C-8: 캡슐 루트의 `CONTRACT.md`·`surfaces.json`을 계약 근거로 소비한다. 계약 변경이 필요하면 `contract.md` §4 오너십 계층으로 분류해 PM 반영을 거치며, 워커가 직접 수정하지 않는다.
- C-9: 앞선 수행이 세운 기준선을 회귀시키지 않는다 — `test-tool` 88 passed, `scripts/tests/test_console_ownership.sh` 20/20, vitest 161 passed, `console.sh`·`install-mac.sh`의 `pkill|pgrep|killall` 0건.

## Acceptance criteria

- AC-1: main 1개와 서로 다른 worktree 2개에서 E2E run을 동시에 실행했을 때 backend/frontend 포트, browser page/profile, 서버 프로세스가 충돌하지 않고 세 run 모두 독립적으로 종료된다.
- AC-2: 각 run의 `run.json`에 `profile`·`actors`·`target`·`project_root`·`worktree_root`·commit·dirty 여부·실제 `urls`·`executors`·`candidates`·driver version이 기록된다.
- AC-3: **(충족)** E2E 실행 중 `opal-cli console stop`을 실행해도 E2E backend가 살아 있고, E2E 종료 후에도 사용자 `127.0.0.1:7823` Console이 계속 동작한다. 근거: `scripts/tests/test_console_ownership.sh` 20/20, `archive/tasks/T02-Console-프로세스-소유권/DONE.md`.
- AC-4: Orca가 설치된 macOS에서 `orca-managed` mode로 실제 UI 행동 + semantic assertion을 포함한 E2E 시나리오가 `pass`하며, 소유한 `browserPageId`와 profile id만 정리되고 같은 worktree의 다른 탭은 남는다.
- AC-5: Orca runtime을 제거한 환경에서 같은 시나리오가 `provider_unavailable`을 거쳐 standalone agent-browser로 전환되어 `pass`한다.
- AC-6: assertion 또는 필수 증적이 누락된 실행은 어떤 경로로도 `pass`·`real-usage`가 되지 않고, 누락 항목이 결과에 명시된다.
- AC-7: 공개 HTTP API 요구사항이 Browser 없이 `api` profile로 request/response와 후속 상태까지 실제 SUT에서 검증된다.
- AC-8: `hybrid` profile 시나리오에서 핵심 UI 행동을 API 호출로 대체하면 surface fidelity gate가 이를 거부한다.
- AC-9: `collaborative` 시나리오가 `awaiting_human`(exit 20)으로 일시 정지한 뒤 동일 run-id와 resume token으로 재개되고, 사용자 제출만으로는 `pass`가 되지 않으며 verifier 통과 후에만 최종 판정이 난다.
- AC-10: 실패한 run만 보고도 공통 필수 증적(metadata·server log·action log·assertion expected/actual·cleanup)과 해당 session이 지원하는 진단 증적으로 원인을 추적할 수 있다.
- AC-11: `docs/proposals/opal-e2e-harness.md` §8.4의 9개 migration area와 `TRD.md` §6.8이 추가 발견한 7건에서 Playwright 소비자가 0이거나 명시적 opt-in으로만 남고, 소비자별 이전 결과가 문서화된다.
- AC-12: Playwright/Chromium 기본 설치를 제거한 뒤 clean install → update → doctor 경로에서 web-to-markdown과 MCP 등록을 포함한 회귀가 0건이다.
- AC-13: source E2E 실행 후 `git status`가 저장소에 새로운 추적/미추적 산출물을 남기지 않고, 설치본 `~/.opal/dashboard-server/`가 변경되지 않는다.
- AC-14: oppl·oppd 문서에 남아 있던 `real-usage`·L3b 정의 문구가 `test-tool` fidelity 계약 참조로 대체되어, 경쟁 SSOT 문장이 0건이다.
- AC-15: 레코드의 `started_at`이 시스템 부팅 시각보다 이르면 `console stop`이 종료 대상으로 삼지 않고 stale로 판정해 레코드만 정리한다. 리부팅을 모사한 조건(격리 `OPAL_HOME`에 `started_at`을 부팅 이전으로 둔 레코드)에서 센티넬 프로세스가 죽지 않음을 실관측한다.
- AC-16: `.gitignore`에 `.oppl-run/`이 추가되어 에이전트 전송 산출물이 `git status`에 나타나지 않는다.

## Open questions

- Orca-managed session에 agent-browser launch-scope `--config`·`--allowed-domains`를 적용할 수 있는지(Q-2)와 `console`·`errors`·`network_har` 증적을 실제로 수집할 수 있는 실행 경로가 무엇인지(Q-3)는 E3 단계의 비파괴 probe 실측에 의존한다. 미확정 상태에서도 설계는 성립한다 — `CONTRACT.md` §A.8이 형태를 확정하고 `probed=false`를 보수적으로 `available=false`로 처리한다. 이 둘은 착수 판단을 바꾸지 않으므로 실행 중 해소한다.
