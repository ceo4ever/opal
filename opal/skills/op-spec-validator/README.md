# op-spec-validator

> 이 스킬은 사용자가 직접 호출하지 않습니다. `opal-pilot-project-dev`가 SDD 명세 검증 단계에서 디스패치합니다.

PRD/TRD 문서를 읽고 체크리스트 기반으로 명세 완성도를 판정하는 SDD 명세 검증 워커 스킬입니다.

## 역할

오케스트레이터가 워커 에이전트로 디스패치하면, 서브에이전트를 추가로 만들지 않고 직접 입력을 파싱하고 대상 문서를 Read하여 체크리스트를 판정합니다. alias나 trigger가 없어 사용자가 직접 호출할 수 없으며, 오케스트레이터가 경로로 직접 로드합니다.

PRD는 P1~P6(비목표 섹션·타깃 유저 시나리오·Must/Should 분류·Acceptance Criteria·모호한 표현 여부·Open Questions), TRD는 T1~T5(기술 스택 버전·성능 요구사항 수치화·보안 요구사항·PRD Must 기능 커버리지·Open Questions) 항목을 각각 검증합니다. 두 체크리스트 모두 전 항목 Pass여야 해당 문서가 Pass이며, 1개라도 Fail이면 그 문서는 Fail입니다. 각 항목은 Pass/Fail 판정 근거(`reason`)와 Fail 시 구체적 수정 제안(`suggestion`)을 함께 기록합니다.

## 입력

```
검증 요청:
- PRD 경로: {path} (검증 대상이 PRD 또는 ALL일 때)
- TRD 경로: {path} (검증 대상이 TRD 또는 ALL일 때)
- 검증 대상: PRD | TRD | ALL
- (선택) 참조 문서: {추가 참조 경로 목록}
```

경로가 누락되면 해당 항목 판정을 건너뛰고 결과에 명시합니다.

## 출력

항목별 `{item, result, reason, suggestion}` 구조화 판정 결과를 마크다운 표로 반환합니다. 종합 판정(PRD/TRD/종합 Pass 또는 Fail), 상세 결과 표, Fail 항목 요약을 포함하며, 검증 대상에 포함되지 않는 항목은 표에서 생략합니다.

## 호출 시점

오케스트레이터(예: opsdd 1-1b)가 PRD/TRD 또는 spec.md 같은 명세 문서의 완성도를 검증해야 할 때 디스패치합니다. opsdd SPEC 단계에서는 spec.md 경로를 PRD/TRD 경로 대신 전달해 동일 워커를 재사용할 수 있으며, 이 경우 검증 대상에 `SPEC`을 추가 지원하거나 커스텀 체크리스트를 입력받는 확장은 opsdd 스킬 구현 시점에 이 SKILL.md에 추가됩니다. 현재는 PRD/TRD 체크리스트(P1~P6, T1~T5)만 구현되어 있습니다.
