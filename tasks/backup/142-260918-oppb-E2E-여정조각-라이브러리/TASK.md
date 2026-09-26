---
template: sdlc-v2
---
# TASK: E2E 여정·조각 라이브러리 구축 (oppb 프로젝트 빌드)

## Problem

`docs/proposals/archives/e2e-journey-fragment-library.md`(태스크 142 CLOSE에서 `적용완료`로 보관)가 제안한 것이 하나도 구현되지 않았다. `docs/e2e/`·`.opal/e2e/`·`.e2e/` 세 폴더가 없고 `opal-e2e` 스킬도 없다.

그 결과 태스크 127이 실측한 두 제약이 그대로 살아 있다.

1. `test-scenario.json`은 `scenario-lock` 이후 spec존을 못 고치고 `scenario-init` 재호출이 `red_confirmed`를 전건 초기화하므로, 태스크 캡슐 안에서는 사후에 E2E 시나리오를 추가할 수 없다. 프로젝트 레벨 저장소가 없으면 E2E 시나리오는 태스크마다 버려진다.
2. `e2e run`은 `--scenario <id>`로 id만 받을 뿐 시나리오를 만드는 수단이 없다. 발동층이 없어 작성이 전부 도구 밖 사람 손에 남는다.

여기에 제안서가 스스로 선행 조건으로 지목한 미해소 항목 4건이 붙는다 — Q-1(조각 전개분과 본문 연산의 중복 판정 충돌), Q-6(ops 기반 후보 게이트 부재), driver 적합성 스위트 부재, 증적 마스킹 구멍(`fill`의 `value`가 `actions.jsonl`에 원문으로 남는다).

## Proposed outcome

E2E 여정과 조각이 프로젝트 레벨에 누적되고, 사람이 `//e2e`로 작성·실행·조회하며, 새 브라우저를 JSON 매니페스트 한 장으로 등록할 수 있는 상태.

관찰 지점은 셋이다.

- 한 태스크에서 만든 여정이 다음 태스크에서 재사용된다 — 태스크 캡슐이 아니라 `docs/e2e/`가 소유하므로 태스크가 끝나도 남는다.
- 자격증명이 증적에 원문으로 남지 않는다.
- 조각을 바꾸면 그 조각을 참조하는 여정만 재실행되고, 재실행 생략은 "미실행"이 아니라 "이전 증적 재인용"으로 기록된다.

## Affected users and systems

- 이 프레임워크로 개발하는 사용자와, E2E 검증이 필요한 모든 후속 태스크의 PM·테스트 워커.
- 신규 자산: `docs/e2e/`(여정·조각), `.opal/e2e/`(driver 매니페스트·후보 순서), `.e2e/`(신선도 원장·산출물), `opal-e2e` 스킬.
- 변경 대상: `opal/tools/test-tool/`(증적 마스킹·ops 게이트·`driver-verify`·선언형 driver·중복 판정 범위), `.gitignore`.
- 범위 제외: 기존 pilot(`opd`·`opds`·`oppd`·`oppl`·`opsdd`)의 단계 계약 변경, `test-tool`의 E2E exit 계약(0/6/7/18/19/20) 자체 변경, 실제 서비스 배포.

## Constraints

- C-1: `test-tool`의 E2E exit 계약과 `FIDELITY_ORDER`(`opal/tools/test-tool/lib/scenario.py:119`)를 이 프로젝트가 재정의하지 않는다. 참조만 한다.
- C-2: 판정 주체를 바꾸지 않는다 — `opal-e2e` 스킬은 호출과 해석만 하고 pass/fail을 선언하지 않는다.
- C-3: 동결된 RED 시나리오(`red_confirmed: true`)의 기대 계약을 약화·삭제하지 않는다.
- C-4: `~/.opal/` 배포 파일을 직접 수정하지 않는다. 프로젝트 소스를 고치고 install로 배포한다.
- C-5: 새 driver·후보 순서 변경이 전환 조건을 바꾸지 않는다 — `provider_unavailable`에서만 다음 후보로 넘어가고 `infra_error`·제품 실패에서는 넘어가지 않는다.
- C-6: `.gitignore`는 `.e2e/` 폴더 단위 1줄로 처리한다. 예외 등록(`!` 규칙) 방식을 쓰지 않는다.
- C-7: 프로젝트 문서 갱신은 기존 SSOT에 반영한다. PRD·TRD를 신규 생성하지 않는다.

## Acceptance criteria

- AC-1: 증적 마스킹 보강 — `fill` 계열 action 레코드의 입력값이 `actions.jsonl`에 원문으로 남지 않는다. 실패 시 원문을 남기지 않고 `infra_error`로 끝나는 기존 C-6 계약이 유지된다.
- AC-2: ops 기반 후보 게이트(Q-6) — 시나리오 step이 요구하는 연산을 제공하지 않는 driver 후보가 실행 전에 걸러진다. 실행 도중 `driver_operation_unimplemented`로 `blocked`가 되는 경로가 재현되지 않는다.
- AC-3: `test-tool e2e driver-verify --driver <name>`이 8연산 이행을 실제 실행으로 검사하고, 일부 연산만 구현한 driver를 통과시키지 않는다.
- AC-4: 조각 전개분과 본문 연산의 중복 판정 충돌(Q-1)이 해소된다 — 같은 연산 signature가 조각 전개와 본문에 함께 나타나도 재시도로 오판되지 않으며, 동결 RED S-27의 기대 계약은 그대로다.
- AC-5: 선언형 driver wrapper — `.opal/e2e/drivers/`에 매니페스트 JSON 한 장을 추가하면 파이썬 모듈 없이 driver가 등록되고, `driver-verify`를 통과해야 후보가 된다.
- AC-6: `.opal/e2e/order.json`으로 후보 우선순위를 재정의할 수 있고, 그 값이 `resolve_candidates(candidate_order=...)`에 전달된다.
- AC-7: 조각 계약 — 사후 조건이 없는 조각은 등록이 거부된다. 조각 전개 결과는 `actions.jsonl`에 실제 연산 단위로 남는다.
- AC-8: 신선도 키 — `(여정 해시, 조각 해시 집합, surface_id, 대상 commit, 선택 driver 정체, 달성 충실도)`로 판정하며, 순서 설정만 바꿔 이전 `pass` 증적을 재인용하는 경로가 막힌다.
- AC-9: 재실행 생략이 "이전 증적 재인용"으로 기록되고 DONE.md에서 보인다. 생략이 미실행으로 침묵하지 않는다.
- AC-10: `opal-e2e` 스킬(alias `//e2e`)이 `author`·`import`·`run`·`status` 4모드로 동작하고 스킬 레지스트리에서 매칭된다.
- AC-11: 3폴더가 실제로 생성·동작한다 — `docs/e2e/`와 `.opal/e2e/`는 추적되고 `.e2e/`는 `.gitignore` 1줄로 전량 무시되어 `git status`를 더럽히지 않는다.
- AC-12: 한 태스크에서 만든 여정이 `docs/e2e/`로 승격되고 다음 실행에서 재사용된다. 승격 자격은 도구가 `pass` 증적으로 판정하며 사람 산문 판단만으로 승격되지 않는다.
- AC-13: `.e2e/artifacts/` 보존 정책(최근 N개)이 집행되어 무한 증가하지 않는다.
- AC-14: 기존 회귀 0 — `test-tool` 기존 테스트와 E2E 계약 테스트가 이 프로젝트 전후로 모두 통과한다.
