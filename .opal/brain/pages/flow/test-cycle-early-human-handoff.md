---
type: flow
title: TEST 단계 선요청 흐름 — 사람 협업 선요청과 자동 검사 병행
tags:
- testing
- test-cycle
- opd
- opds
- flow
sources:
- task:162
related: [state-tool, worktree-tool, op-dev-test-scenario, op-dev-execute]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

opd/opds TEST 단계 진입 시 사람이 해야 할 조치(human step/handoff)를 모두 모아 한 번에 요청하고, 그 응답을 기다리는 동안 자동 검사를 병행 실행해 TEST 전체 소요시간을 줄이는 흐름이다. 기존 TEST의 최종 PASS 기준과 독립 검증 주체는 그대로 유지한다.

## 흐름

```
TEST 진입
  ↓
분기 선확인 — worktree-tool divergence로 base_ref 대비 ahead/behind 확인
  (behind>0 → 통합 요청 후 재개, 자동 실행은 시작하지 않는다)
  ↓
사람 handoff 전량 추출 → 한 번에 요청 (human-wait clock start)
  ↓ (병행)                                ↓
자동 검사 실행 (auto clock start/stop)     사람 제출 대기 (verifier 판정)
  ↓                                        ↓
                   합류
  ↓
fix 발생 시 영향 범위 재검증
  (실패 S-ID + 변경 파일 영향 S-ID만 재실행, 관계 불명확하면 해당 묶음 전체)
  ↓
최종 Gate — 필수 시나리오 전부 PASS + 전체 회귀 1회 + 보안 1회 + 최종 수정 기준 컨벤션 1회
```

## 핵심 계약

| 구분 | 계약 |
|------|------|
| 변경 분류 | `state-tool add-row --stage TEST --test-change-kind fix\|requirement_change`로 TEST 행에 유형을 명시한다. 현재 수용 기준을 충족시키는 피드백은 `fix`, 수용 기준 자체의 변경은 `requirement_change`로 분류하며 `requirement_change`는 횟수 제한 없이 계측만 한다(소유자 피드백: 정상적인 수용 사항을 횟수로 차단하면 TEST 단축 목표에 역행한다). 옵션 없는 기존 호출·행은 신규 카운터에서 제외한다. |
| 소요시간 계측 | `state-tool test-clock start\|stop <task> --kind auto\|human --id <식별자>`가 행 mark 시각이 아니라 실제 실행·대기의 시작/종료 호출 시각(UTC ISO 8601)을 상태 파일에 원자 기록한다. `(kind,id)` 열린 interval은 하나만 허용한다. 여러 사람 항목이 동시에 열려도 `human_wait_seconds`는 interval 합산이 아니라 시간축 합집합 길이로 계산한다. `state-tool test-metrics <task>`가 `auto_seconds`·`human_wait_seconds`·`fix_count`·`requirement_change_count`·`open_intervals`를 읽기 전용으로 반환한다. |
| 증거 재사용 | 동일 commit SHA, 동일 명령·환경 서명, PASS 증거 경로가 있는 EXECUTE lint/type/unit 결과만 TEST에서 재사용하고 TEST 보고에 원천을 남긴다. 변경되었거나 증거가 없으면 재실행한다. |
| 분기 선확인 | `worktree-tool divergence --project-root <허브 절대경로> --task <NNN>`이 registry에 동결된 repo별 `base_ref`와 worktree HEAD의 ahead/behind를 읽기 전용으로 반환한다(fetch/merge/reset 없음). `behind>0`이 하나라도 있으면 `integration_required=true`이며, 통합 승인 이후 같은 명령으로 `behind=0`을 재확인하고서만 진행한다. |
| 반복 재검증 범위 | 실패 S-ID와 변경 파일 영향 S-ID만 재실행한다. 영향 관계가 불명확하면 해당 묶음 전체를 재실행한다. 최종 Gate에서는 필수 시나리오 전부 PASS와 전체 회귀 1회를 요구한다. |
| legacy 호환 | 계측을 시작하지 않은 과거 태스크는 `unknown`을 반환하며, 행 mark 시각으로 실행 시간을 추정하지 않는다(`legacy_unclassified_rows`로 미분류 가능성을 명시). |
| 디스패치 경량화 미채택 | receipt 재사용은 채택하지 않았다. manifest가 같아도 선별 프로젝트 문서·capability·권한 경계가 달라질 수 있고 워커별 verify가 보안 게이트이기 때문에, 검증 비용 절감보다 stale 입력 위험이 크다고 판단했다. |

## 설계 배경 (WHY)

- 기존 TEST는 사람 협업 요청과 자동 검사가 순차 실행돼 사람 대기 시간이 그대로 전체 소요시간에 더해졌다(근거: task:162 PLAN Approach, REQUEST §3.1).
- 반복 재검증이 항상 전체 회귀였던 관행이 수정 1건당 회귀 비용을 키웠다 — 실패·영향 S-ID만 좁혀 재검증하되 최종 1회는 전체 회귀로 수렴시켜 누락을 막는다(근거: task:162 PLAN Decisions "반복 재검증").
- 사후 행 mark 시각으로 소요시간을 추정하면 실제 실행·대기 구간과 어긋난다. 실제 사건 시각(시작/종료 호출)을 도구가 직접 찍어야 정확한 자동 실행·사람 대기 시간과 fix/요구 변경 횟수를 조회할 수 있다(근거: task:162 PLAN Decisions "소요시간", TASK.md AC-7).
- 병행 계측의 상태 갱신 유실(16개 동시 기록이 수정 전 2개만 보존)을 재현하고, 태스크 단위 쓰기 잠금으로 16개 보존을 확인했다(근거: task:162 DONE.md 결과 2문단).

## 관련 페이지

- [[state-tool]]
- [[worktree-tool]]
- [[op-dev-test-scenario]]
- [[op-dev-execute]]
