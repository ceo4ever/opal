---
type: concept
title: 동결 spec 시드 제약 — lock 이후 시나리오 추가 불가
tags:
- e2e
- red-first
- ssot
- tool-gated
sources:
- task:127
related:
- e2e-integration-gap-pattern
created: '2026-09-18'
updated: '2026-09-18'
status: draft
---
## 개념 요약

`test-scenario.json`은 RED-first 동결 게이트를 위해 `scenario-lock` 이후 spec존 변경을 막는다. 그런데 **잠금을 풀 수단이 없고**, spec을 고치려면 `scenario-init`을 다시 불러야 하는데 그 도구는 `red_confirmed`를 **항상 false로 초기화**한다(시드 우회 봉쇄, `scenario.py` `_normalize_scenario`).

따라서 시나리오 일부가 이미 GREEN이 된 뒤에는 재시드가 **비가역 차단**을 만든다 — 이미 통과한 시나리오의 RED 실패를 다시 관측할 수 없으므로 `scenario-lock`이 영구히 `red_not_confirmed`로 막힌다.

## 귀결

**태스크 캡슐 안에서는 사후에 E2E 시나리오를 추가할 수 없다.** 태스크 127에서 실제로 부딪힌 지점이다.

- S-26·S-27의 `profile`이 `null`로 시드돼 `executor_contract(None)`이 `KeyError`를 내고 `candidates[]`가 구조적으로 빈 배열이 됐다. 고치려면 재시드가 필요했으나 그 시점에 S-1~S-7이 이미 GREEN이었다.
- S-8·S-9에 실행 스펙(step action·assertion verifier)이 없어 AC-4를 관통할 수 없었다. 같은 이유로 spec을 고칠 수 없었다.
- S-11·S-28의 `handoff.server_policy`가 `"local-only"`로 시드됐는데 §A.9 enum은 `keep`|`terminate`다. 역시 재시드 불가.

## 우회 방법 (태스크 127에서 실제로 쓴 것)

| 문제 | 우회 |
|---|---|
| spec의 `profile`·실행 스펙 부재 | 테스트가 **자기 fixture 시나리오를 임시 폴더에 작성**해 `--task-path`로 넘긴다. 동결 spec은 읽기 전용으로만 소비한다 |
| enum 밖 값이 시드됨 | **발행 시점 정규화** — executor가 발행하는 값을 enum 안으로 떨어뜨리고(보수적 기본값) 선언 원문은 `*_declared` 필드에 보존한다. 조용히 바꾸지 않고 `*_normalized` 플래그로 대체 사실을 남긴다 |

## 설계 함의

시나리오를 **프로젝트 레벨 저장소**에 두어야 한다는 결론이 여기서 나온다. 태스크 캡슐은 동결 의미를 갖는 3-SSOT 파일을 품고 있어 사후 추가에 적합하지 않다. `docs/proposals/e2e-journey-fragment-library.md`가 이 제약을 근거로 `docs/e2e/`·`.opal/e2e/`·`.e2e/` 3층 저장을 제안한다.

**시드 품질이 곧 상한이다.** 손으로 시드한 JSON은 태스크 127에서 4건의 사고를 냈다(profile null · server_policy enum 밖 · 실행 스펙 부재 · 재시드 불가). 사람이 쓰는 문서에서 도구가 시드하는 구조를 유지해야 하는 이유다.

## 관련

[[e2e-integration-gap-pattern]] · [[oppl-3-ssot-tool-gated-separation]]
