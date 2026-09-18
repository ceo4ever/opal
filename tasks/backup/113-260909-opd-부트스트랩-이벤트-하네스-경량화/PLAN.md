---
template: sdlc-v2
---
# PLAN: 부트스트랩 이벤트 하네스 경량화

> 입력: [TASK.md](TASK.md), [ANALYSIS.md](ANALYSIS.md)

## Approach

세션 부트는 marker/setting 해석과 최소 비서 커널만 남기고, PM·파일럿·단계·워커 규칙은 이벤트 manifest와 loader receipt를 통해 필요한 시점에만 읽는다. `opal-harness.md`는 호환 인덱스로 축소하고, 원문 규칙은 실행 소유 문서로 이동한다. 검증은 소스 worktree 기준 정적 검사, loader 단위 테스트, marker 우선순위 테스트, 설치 후 `~/.opal` parity, cold-start payload/time 측정으로 나눈다.

code-scan 결과는 이번 PLAN의 소스 판정 근거로 사용하지 않는다. task_113 worktree에서 code-scan이 허브 루트로 수렴한다는 사전 제약이 있어, 변경 대상 확정은 ANALYSIS의 worktree `rg` 근거와 파일별 직접 확인을 따른다.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| 이벤트 SSOT를 `opal/core/references/events.json`로 둔다 | 모든 표준 이벤트는 `id`, `required_docs`, `optional_docs`, `predecessors`, `receipt_required`, `consumer`를 manifest에서 선언한다. 소비자 문서는 이벤트 ID만 참조하고 필수 파일 목록을 복제하지 않는다. | AC-3~AC-5, C-3, C-4를 동시에 만족하려면 산문 대신 결정론 parser가 읽을 수 있는 레지스트리가 필요하다. |
| 로더는 `opal/tools/event-loader`의 플랫폼 독립 CLI로 구현한다 | `load --event`는 필수 문서 전문, sha256, bytes, manifest hash, receipt를 JSON으로 반환한다. `verify --receipt`는 누락·stale·wrong-event를 구조화 오류로 거부한다. `static-check`는 이벤트 소비자 누락과 금지된 구형 harness fallback을 탐지한다. | 부트스트래퍼는 텍스트 어댑터이고 실제 gate는 도구 실행 가능한 pilot/stage/worker 경계에 있어야 한다. |
| 세션 상태는 `session.disabled → session.worker → session.assistant → session.project` 우선순위로 해석한다 | `[WORKER]` 첫 줄은 전역 부트 전체 스킵을 유지한다. `[ASSISTANT]`는 PM 승격만 억제한다. 무마커 + 프로젝트 감지는 PM 활성화가 아니라 project-aware assistant 상태까지만 허용한다. `bootstrap: off`는 OPAL 없는 순수 동작으로 남긴다. | C-1, C-2, AC-1~AC-3의 기존 안전 의미를 보존한다. |
| PM은 `pm.activate`, pilot은 `pilot.start`, 단계는 `stage.*`, 워커는 `worker.dispatch` 이벤트에서 로드한다 | `docs/PROJECT.md`, 전체 `opal-pm.md`, 공통 하네스 본문은 세션 부트에서 제외한다. PM·파일럿·단계·워커 소비자는 loader receipt를 받거나 직접 loader를 실행한 뒤 진행한다. | Eager 지연을 줄이면서 필요한 지점의 MUST read를 명시적으로 강제한다. |
| memory boot brief는 기존 `show --brief`와 별도 계약으로 둔다 | `memory-tool show --boot-brief --max-bytes 1024 --memories 3 --history 0`를 추가하고, 프로젝트 인지 비서 부트는 이 출력만 사용할 수 있다. | 기존 `--brief` 하위호환을 깨지 않고 AC-2의 byte/개수 상한을 만족한다. |
| 배포본 직접 수정은 금지하고 install로 검증한다 | source worktree 변경 후 `scripts/install-mac.sh`로 배포하고, `events.json`, loader, 하네스 문서 parity를 검사한다. | C-7과 AC-9를 충족한다. |
| Markdown 이력은 git과 태스크 기록이 소유한다 | 이번 태스크에서 수정하는 SKILL·AGENT·harness·reference·프로젝트 Markdown은 수기 누적 이력 절 전체를 제거한다. `docs/CONVENTIONS.md`와 관련 생성·검증 경로의 과거 이력 추가 의무도 `opal-doc-standard.md` §5로 정합화한다. | 사용자 확정과 문서 표준 §5를 전 작업 공통 계약으로 적용한다. |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 이벤트 manifest와 loader 추가 | EXECUTE | `opal/core/references/events.json`, `opal/tools/event-loader/`, `opal/tools/event-loader/tests/` | 표준 이벤트 manifest를 추가하고 `load`, `verify`, `static-check`, `measure` CLI를 구현한다. loader는 tokenized path를 source/deployed/project root로 해석하고, 전문 content와 sha256 receipt를 반환하며, missing/stale/wrong-event를 non-zero 구조화 JSON으로 반환한다. | 없음 | P1 | AC-3, AC-5, AC-8, C-3, C-5 |
| W-2. memory boot brief 상한 추가 | EXECUTE | `opal/tools/memory-tool/memory_tool.py`, `opal/tools/memory-tool/README.md`, `opal/tools/memory-tool/tests/` | `show --boot-brief`, `--max-bytes`, `--memories`, `--history` 옵션을 추가한다. boot brief는 본문·긴 결과를 제외하고 최대 3개 active memory와 1KB 이하 JSON/텍스트 출력을 보장한다. | 없음 | P1 | AC-2, C-6 |
| W-3. 하네스 산문 owner 문서 분리 | EXECUTE | `opal/core/references/opal-harness.md`, `opal/core/references/harness/guards.md`, `opal/core/references/harness/modes.md`, `opal/core/references/harness/worktree.md`, `opal/core/references/harness/capability.md`, 기존 `opal/core/references/harness/*.md`, `opal/core/references/pm/activation.md` | `opal-harness.md` 원문 산문을 제거하고 event/owner 문서 인덱스로 축소한다. Guards·mode routing·worktree·capability·PM activation 원문은 owner 문서 한 곳으로 이동하고, 기존 owner 문서가 있는 규칙은 해당 문서로 연결한다. 수정하는 Markdown의 수기 누적 이력 절은 전체 제거한다. | W-1 | P2 | AC-1, AC-4, AC-6, C-4 |
| W-4. 세션 부트와 플랫폼 bootstrapper 경량화 | EXECUTE | `opal/core/AGENT.md`, `opal/bootstrapper/claude-bootstrap.md`, `opal/bootstrapper/codex-bootstrap.md`, `opal/bootstrapper/cursor-bootstrap.mdc`, `opal/bootstrapper/gemini-bootstrap.md`, `opal/tools/opal-agent/opal_agent.py`, `opal/tools/opal-agent/tests/test_opal_agent.py` | Phase B 즉시 PM 로드를 제거하고 session event 계약으로 재작성한다. boot Eager 목록은 identity, principles, 선택적 boot brief만 허용한다. marker precedence와 `opal-agent --opal-bootstrap` mapping 테스트를 추가하고, 수정하는 Markdown의 수기 누적 이력 절은 전체 제거한다. | W-1, W-2, W-3 | P3 | AC-1, AC-2, AC-3, C-1, C-2, C-5 |
| W-5. PM·pilot·stage·worker 소비자 전환 | EXECUTE | `opal/core/references/opal-pm.md`, `opal/skills/opal-pilot-*/SKILL.md`, `opal/agents/opal-task-agent/AGENT.md`, `opal/agents/opal-plan-agent/AGENT.md`, `opal/agents/*/AGENT.md`, `opal/tools/state-tool/`, 관련 stage/pilot tests | PM 시작은 `pm.activate`, pilot 시작은 `pilot.start`, 단계 진입은 `stage.*`, 워커 디스패치는 `worker.dispatch` receipt를 요구하도록 소비자 문서를 수정한다. `[WORKER]` 전역 skip은 유지하되 receipt 없는 worker는 blocked로 반환하게 한다. `state-tool`에는 단계 mark/advance 시 receipt 검증 hook 또는 명시 검증 명령을 붙인다. 수정하는 Markdown의 수기 누적 이력 절은 전체 제거한다. | W-1, W-3, W-4 | P4 | AC-4, AC-7, AC-8, C-3, C-4 |
| W-6. 문서 레지스트리와 아키텍처 설명 갱신 | EXECUTE | `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`, `.opal/AGENT.md`, `opal/tools/opal-agent/README.md`, `opal/skills/opal-skill-creator/SKILL.md`, `opal/skills/opal-pilot-gc/references/base-convention-checklist.md` | PROJECT 레지스트리와 opal-agent 사용 설명의 boot 시점을 project-aware assistant와 `pm.activate`로 분리한다. 아키텍처 2-tier 설명을 assistant/project-aware/PM JIT 구조로 갱신한다. 하네스 포인터를 새 owner 문서로 전환한다. 프로젝트 프로필·컨벤션·skill 생성기·컨벤션 검사기의 과거 변경이력 추가 의무를 `opal-doc-standard.md` §5로 교체하고, 수정한 Markdown의 수기 누적 이력 절은 전체 제거한다. | W-3, W-4, W-5 | P5 | AC-1, AC-4, AC-6, C-4, C-7 |
| W-7. 결정론 회귀·실측·설치 검증 추가 | EXECUTE | `scripts/tests/`, `opal/tools/event-loader/tests/`, `tasks/113-260909-opd-부트스트랩-이벤트-하네스-경량화/TEST-SCENARIO.md`, `tasks/113-260909-opd-부트스트랩-이벤트-하네스-경량화/TEST.md` | TEST-SCENARIO 단계에서 marker precedence, loader missing/stale/wrong-event, pilot/worker static-check, mac/windows bootstrapper parity, cold-start payload/time 측정 시나리오를 정의한다. EXECUTE 후 테스트는 소스 worktree, 가능 시 `pwsh`, install-mac 후 `~/.opal` parity 순서로 수행하고 결과를 기록한다. 이번 태스크에서 수정된 Markdown의 수기 누적 이력 절 0건과 이력 생성·검증 규칙의 문서 표준 정합도 정적으로 검사한다. | W-1~W-6 | P6 | AC-1, AC-3, AC-5, AC-8, AC-9, AC-10, C-7, C-8 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. LLM 내부 Read 적재 여부는 외부 도구가 직접 관측하지 못한다 | AC-5의 "전문 로드"를 플랫폼 내부 상태로 증명할 수 없다. | MUST read가 산문처럼 보일 수 있다. | W-1에서 loader가 전문 content+hash receipt를 반환하고, W-5/W-7에서 receipt 없이는 진행을 거부하는 계약으로 정의한다. |
| H-2. Windows 실행 환경이 없을 수 있다 | `scripts/install/windows.ps1` 실행 회귀를 현 macOS에서 완전 수행하지 못할 수 있다. | AC-8의 지원 플랫폼 회귀가 정적 parity로 제한될 수 있다. | W-7에서 `pwsh` 존재 시 실행, 부재 시 PowerShell syntax/static parity와 명시 한계 기록으로 분리한다. |
| H-3. 실제 install은 사용자 전역 `~/.opal` 배포본을 갱신한다 | 설치 후 현재 세션의 OPAL 동작이 새 bootstrap 계약으로 바뀐다. | 전역 배포본 복구가 필요할 수 있다. | W-7에서 설치 전 `~/.opal` 핵심 파일 해시를 기록하고, 실패 시 같은 install 스크립트로 직전 source 또는 백업에서 복구 가능한 절차를 TEST에 남긴다. |

## Release and recovery

- 적용 순서: P1 loader/memory 기반 → P2 하네스 owner 분리 → P3 세션/bootstrapper → P4 PM·pilot·worker 소비자 → P5 프로젝트 문서 → P6 회귀·실측·설치 검증.
- 검증 범위: loader 단위 테스트, memory-tool 단위 테스트, opal-agent marker 테스트, static-check, state-tool plan/test 계약, mac install parity, 가능 시 Windows PowerShell 정적/실행 검사.
- 실측 경계: 변경 전 payload는 TASK 선측정값과 재현 명령으로 기록하고, 변경 후는 event-loader `measure` 및 `wc -c` 기반으로 일반 비서와 프로젝트 인지 비서 declared Eager payload가 30KB 이하·70% 이상 감소인지 확인한다. 실행 시간은 동일 명령을 3회 반복해 평균과 최대값을 TEST에 기록한다.
- 실패 시: source worktree 변경은 커밋하지 않으므로 revert 후보는 변경 파일 목록 기준으로 분리한다. install 실패 또는 배포 parity 실패 시 `~/.opal` 핵심 파일 해시와 installer 로그를 TEST에 남기고, CLOSE·merge 없이 사용자 확인을 요청한다.
