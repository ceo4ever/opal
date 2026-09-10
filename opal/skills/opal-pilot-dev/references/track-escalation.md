---
module: track-escalation
role: Short profile에서 Full Task로 승격을 제안하는 규칙 SSOT
load: `//opds` PLAN.md 수신 직후 승격 판정
상속: 하향 강등 규칙은 `opal/core/references/harness/track-routing.md`
---

# 트랙 승격 — opds→opd 제안 규칙

> 이 문서는 `opal-pilot-dev` canonical 구현의 Short profile(`opds`)에서 Full profile(`opd`) 전환을 제안하는 기준만 정의한다.
> 하향 강등(`opd`→`opds`)은 `opal/core/references/harness/track-routing.md`가 소유한다.

## 1. 판정 시점

[MUST] Short→Full 승격은 PLAN.md 수신 직후 1회만 판정한다.

[MUST] PLAN.md 작성 전에는 승격 조건을 판정하거나 Full Task 전환을 제안하지 않는다.

[MUST] PM은 승격 조건이 감지되어도 자동 전환하지 않고 사용자에게 Full Task 전환을 제안한다. 사용자가 `Short로 진행해`라고 응답하면 Short profile을 유지한다.

## 2. PLAN 결과 승격

op-dev-plan 결과에서 아래 조건이 감지되면 Full Task 전환을 제안한다.

| 조건 | 판별 방법 |
|------|----------|
| 예상 변경 파일 >= 10개 | sdlc-v2 Work items 변경 대상의 고유 파일 또는 legacy 변경 계획에서 카운트 |
| 다단계 기술 의사결정 | 아키텍처 선택, 기술 스택 비교가 필요한 수준 |
| 다중 모듈 연쇄 영향 | 변경이 3개 이상 독립 모듈에 연쇄 영향 |

## 3. 제안 문구

```
[에스컬레이션 제안]
이 작업은 Short Task 범위를 초과할 수 있습니다: {해당 조건}
Full Task(opal-pilot-dev)로 전환할까요?
- "Full로 해줘" -> Full Task 전환
- "Short로 진행해" -> Short Task 유지
```

## 4. 강등 규칙과의 관계

[MUST] 하향 강등 판정 시점은 Full profile TASK 완료 직후 1회, 승격 판정 시점은 Short profile PLAN.md 수신 직후 1회다.

[MUST] 강등의 예상 변경 파일 수 임계와 PLAN 결과 승격의 예상 변경 파일 수 임계는 상호배타여야 하며, 두 규칙이 동시에 발동할 수 없어야 한다.

[MUST] Short profile이 승격 제안 후 Full profile로 전환되면 동일 태스크에서 하향 강등을 다시 수행하지 않는다.
