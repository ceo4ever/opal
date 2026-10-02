---
template: sdlc-v2
---
# TASK: 이벤트 로더 보안 보강(GC-004·006·011·012) + 절 단위 로딩(P3) 실험

## Problem

태스크 175(이벤트 로딩 경량화 1차)는 머지됐지만, 최종 보안 검사가 권고 4건을 남겼다(`tasks/175-261001-opd-이벤트-로딩-경량화/gc-findings-security-2026-10-02T00-50-00-final2.json`, `docs/proposals/261001_이벤트_문서_로딩_경량화.md` §1.1). 모두 같은 로컬 사용자 권한을 전제로 하지만, 그중 하나는 이미 시작된 호환 종료 관찰의 판단 근거를 흔든다.

- GC-006: 구형 호출 원장의 경로와 시각을 환경변수(`OPAL_EVENT_LOADER_LEDGER`·`OPAL_EVENT_LOADER_NOW`)로 바꿀 수 있고, 원장 쓰기 실패는 경고만 남긴다(`opal/tools/event-loader/event_loader.py:337-364`). 이 원장은 호환 종료(`contract.legacy_accepted=false`)를 판단하는 근거라서 구형 호출이 적게 집계될 수 있다.
- GC-011: verify는 receipt의 매니페스트 경로를 실제 경로로 정규화해 비교하지만, 기본 매니페스트 경로는 정규화하지 않는다(`event_loader.py:332`). `events.json`이 심볼릭 링크인 설치에서는 정상 receipt가 거부되고 모든 워커 디스패치가 막힌다.
- GC-004: `--role-doc`에 임의 경로를 넣을 수 있어(`event_loader.py:412-419`) 파일 존재·해시를 알아내는 데 쓰이거나, FIFO·장치 파일로 멈출 수 있다.
- GC-012: 검증 기준 매니페스트를 `OPAL_DEPLOYED_ROOT`·`--manifest`·`--deployed-root`로 바꿀 수 있고(`event_loader.py:136`, `opal/tools/state-tool/state_tool_parts/gates.py:2666-2668`), 워커 진입 게이트와 디스패치 절차의 성공 조건이 결과 `manifest_path`를 확인하지 않아 사본 매니페스트로 게이트를 통과할 수 있다.

또한 이벤트 문서 중 큰 문서는 매번 전문이 전달된다. `pm.activate`의 PROJECT.md(약 41KB)와 pm-process(약 21KB), 여러 이벤트에 중복으로 실리는 citation-rules(약 23KB: stage.task·stage.design, opd 경로에서는 stage.plan), design-gate(약 16KB), pm-review-gate(약 19KB)다(제안서 §2.1). 제안서 §3.4는 이를 "필수 절 + 목차 + 필요한 절만 로드"로 줄이는 P3를 별도 실험으로 남겼다. 효과는 가장 크지만 필수 규칙이 빠질 위험이 있어, 기본 동작으로 들이기 전에 실험으로 검증해야 한다.

## Proposed outcome

- 보안 권고 4건이 해소된다. 원장 조작·쓰기 실패가 호환 종료 집계에 드러나고, 심볼릭 링크 설치에서도 정상 receipt가 통과하며, `--role-doc`은 허용된 루트 안의 일반 파일만 받고, 게이트는 설치본 기본 매니페스트가 아닌 매니페스트로 만든 검증 결과를 통과시키지 않는다.
- 절 단위 로딩을 명시적으로 켠 호출에서만 동작하는 실험 모드로 쓸 수 있다. 켜면 대상 문서는 필수 절과 목차만 오고 필요한 절은 따로 가져오며, 필수 절(항상 필수·조건부 필수)과 그 의존 절은 항상 함께 온다. 끄면(기본) 지금과 똑같이 동작한다.
- 실험 모드 켬/끔을 같은 조건에서 비교한 측정 결과(품질·로드량·비용·시간)와 채택 권고가 남는다.

## Affected users and systems

- 사용자: 파일럿을 실행하는 캡틴·PM, `worker.dispatch` 게이트를 통과하는 모든 워커.
- 포함: `opal/tools/event-loader/`(원장·매니페스트 경로·`--role-doc`·절 단위 로딩 실험 모드), `opal/core/references/events.json`의 실험 대상 문서 선언, 결과 `manifest_path` 확인이 필요한 게이트 문서(`pm/dispatch-process.md`, `opal/agents/*/AGENT.md` 진입 게이트, 하위 디스패치 에이전트), `state-tool event-verify` 전달 경로, 실험 대상 문서의 절 식별자·의존 선언, 측정 기록, install 배포 확인.
- 제외: 제안서 2차(P2 조건부 문서 분리), 실험 모드의 기본값 전환(측정 후 별도 결정), 호환 종료 플래그(`legacy_accepted`) 변경, 응답 계약 v2의 기존 동작 변경.

## Constraints

- C-1: 실험 모드를 켜지 않은 모든 호출의 응답·receipt·검증 결과는 지금과 같다. 계약 v2의 기존 거부 규칙과 구형 호출 호환은 그대로 유지된다.
- C-2: 필수 규칙은 지연 로딩되지 않는다. `[MUST]` 절, 항상 필수 절, 조건이 성립한 조건부 필수 절, 그 의존 절은 실험 모드에서도 load 응답에 항상 포함된다.
- C-3: 프로젝트 공통 계약을 따른다 — 배포 경계와 플랫폼 분기 금지(`.opal/AGENT.md` §금지사항), 이벤트 문서 집합의 SSOT는 `events.json`.

## Acceptance criteria

- AC-1: 구형 호출 원장의 경로·시각 override가 테스트 전용 조건 밖에서 조용히 적용되지 않고, override 사용과 원장 쓰기 실패가 load 응답과 `legacy-report` 결과에 드러난다.
- AC-2: `events.json`이 내용이 같은 파일로의 심볼릭 링크인 설치에서 정상 receipt가 verify를 통과하고, 실제로 다른 매니페스트를 가리키는 receipt는 계속 거부된다.
- AC-3: `--role-doc`은 프로젝트·소스·설치 루트 안의 일반 파일이고 크기 상한 이하일 때만 받아들여지며, 루트 밖 경로·FIFO·장치 파일·상한 초과는 거부된다.
- AC-4: PM 디스패치·워커 진입·하위 디스패치 게이트가 결과 `manifest_path`가 설치본 기본 매니페스트와 같은지 확인하고, 환경변수나 인자로 다른 매니페스트를 써서 만든 검증 결과로는 통과하지 못한다.
- AC-5: 절 단위 로딩 실험 모드를 켠 호출에서 대상 문서는 필수 절·조건 성립 절·의존 절·목차만 load 응답에 오고 나머지 절은 별도 요청으로 가져올 수 있으며, 추가로 가져온 절도 검증 대상이 된다. 실험 모드를 끈 호출은 C-1대로 지금과 같다.
- AC-6: 실험 모드 켬/끔을 같은 시나리오로 비교한 측정 결과(품질 동등성, 문서 본문·응답 바이트, 비용·시간)와 기본값 채택 여부 권고가 태스크 산출물에 남는다.
