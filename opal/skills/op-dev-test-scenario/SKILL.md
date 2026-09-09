---
name: op-dev-test-scenario
description: |
  개발 태스크의 실행 전 검증 기준을 TEST-SCENARIO.md로 작성한다.
  opal-pilot-dev가 TEST-SCENARIO 단계에서 호출하며 TASK.md와 PLAN.md가 필요하다.
---

# op-dev-test-scenario

## 입력과 출력

- 입력: `{task_folder}/TASK.md`, `{task_folder}/PLAN.md`, PM이 선별한 프로젝트 문서와 실행 capability
- 출력: `{task_folder}/TEST-SCENARIO.md`
- 작성자: PM. PLAN 작성자와 분리한다.

사용자 검토 시점은 pilot의 진행 모드가 정한다. 이 스킬은 승인이나 pipeline 상태를 변경하지 않는다.

## 작성

TASK 첫 frontmatter가 `template: sdlc-v2`이면
`references/test-scenario-guide.md`를 읽고 `Setup / Scenarios` 형식으로 작성한다.

legacy 태스크에 기존 TEST-SCENARIO.md가 있으면 재작성하지 않는다. legacy 산출물이 없으면
호출한 pilot의 legacy 계약을 따른다. 신규 형식을 legacy 문서에 소급 적용하지 않는다.

## 실행 계약

- TASK의 AC/C와 PLAN Risks에 실제 H가 있을 때의 H만 검증 대상에 연결한다.
- 한 시나리오가 여러 토큰을 검증할 수 있다. 요구사항별 시나리오 수 하한을 만들지 않는다.
- 단계·승인은 `state.json`, 실행 결과·증거와 RED 대상 여부는 `test-tool`이 관리하는 `test-scenario.json`이 소유한다.
- PM이 `## 실행 capability`에 주입한 항목만 사용한다. 고정 도구·스킬 목록을 추정하지 않는다.
- 목표 커버 판정과 반복은 다음 단계인 `op-scenario-gate`가 소유한다.

## 완료

- sdlc-v2 문서는 `Setup / Scenarios` 두 절만 가진다.
- 각 행의 조건·행동·기대 결과가 관찰 가능하다.
- 결과표, 승인 상태, 별도 매핑표, 고정 capability 카탈로그를 만들지 않는다.

반환:

```text
TEST-SCENARIO 완료: {task_folder}/TEST-SCENARIO.md
```

## 변경이력

| 버전 | 날짜 | 변경내용 |
|---|---|---|
| v1.2 | 2026-04-15 | 실행 주체에 전문 에이전트 체계 안내 + PLAN 통합 비고 추가 (117) |
| v1.3 | 2026-05-12 11:16 | 시나리오 작성 체크리스트에 AC↔verify check 매핑 표 의무 룰 + 형식 예시 추가 (001) |
| v1.4 | 2026-05-15 16:40 | 통일 형식 7섹션 재편 — 리스크 가설·데이터·L1/L2/L3·매핑 표 추가 (004) |
| v1.5 | 2026-05-19 17:05 | 실행 방식 M1/M2/M3 필드 추가 (004 추가작업) |
| v1.6 | 2026-06-10 10:13 | RED 작성 주체와 테스트 파일 연결 추가 (016) |
| v1.7 | 2026-06-24 | FE 변경 E2E 검사 보강 (041) |
| v1.8 | 2026-07-23 | scenario-gate SSOT와 목표 커버 검사 연결 (073) |
| v1.9 | 2026-09-02 | 소유자 호칭을 런타임 플레이스홀더로 전환 (L2 직접 수정) |
| v2.0 | 2026-09-09 14:18 KST | sdlc-v2 출력을 `Setup / Scenarios`로 축소하고 상태·증거 소유권 분리 (task 111/W-5) |
| v2.1 | 2026-09-09 14:58 KST | test substitute의 경계와 실제 연동 증거 계약 반영 (task 111/W-5 보완) |
| v2.2 | 2026-09-09 15:02 KST | 고정 활용 카탈로그를 런타임 capability 주입 계약으로 교체 (task 111/W-5 보완) |
| v2.3 | 2026-09-09 15:07 KST | PLAN Risks H를 optional로 변경 (task 111/W-5 보완) |
| v2.4 | 2026-09-09 15:33 KST | SKILL을 입력 분기·작성 계약·완료 조건으로 축소하고 템플릿·체크리스트를 guide로 일원화. 미사용 persona와 요구사항별 시나리오 수 하한 제거 (task 111/W-13) |
