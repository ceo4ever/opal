---
module: capability
role: 디스패치 시점 런타임 capability 주입 계약의 단일 SSOT
load: pilot.start
---

# Runtime Capability

고정된 도구·MCP·스킬 목록은 런타임에서 실제 호출 가능함을 보장하지 못하므로 참조
문서에 정적 카탈로그로 보존하지 않는다.

## 주입 계약

- PM은 워커 디스패치 직전에 `pm/dispatch-process.md` Step 6의 `## 실행 capability` 블록으로 현재 세션에서 실제 호출 가능한 capability만 주입한다.
- 워커는 주입 블록에 없는 스킬·MCP·외부 도구가 있다고 가정하지 않는다.
- 필요한 capability가 없고 기본 파일 편집·검색·셸 실행으로도 배정된 완료 기준을 검증할 수 없으면 추정 통과하지 않고 blocker를 반환한다.
- capability 이름과 호출 방식은 플랫폼 중립적으로 기술한다. 플랫폼별 차이는 부트스트래퍼·설치 어댑터가 소유한다.

구조상 필수인 `state-tool`과 `test-tool` 호출은 선택 capability 목록이 아니라 각 단계
workflow의 일부다. 상태 전이는 `harness/state.md`와 `harness/task-process.md`, 시나리오
커버리지는 `harness/scenario-gate.md`와 테스트 단계 스킬이 명령과 판정을 소유한다.

모델 레벨·설정 오버라이드·플랫폼별 실모델 치환의 원문은
`opal-model-mapping.md`가 소유한다.

## PM 직접 수행 시 capability 선택

PM 직접 수행에서도 capability는 실행 시점에 실제 호출 가능한 것만 사용하며, 다음 순서를 따른다.

1. 현재 workflow 또는 문제에 맞는 기존 OPAL skill·tool을 먼저 확인한다.
2. 기본 도구로 충분하면 새 skill을 만들지 않는다.
3. 공식 문서나 외부 자료가 필요하면 최신성과 출처를 확인한다.
4. 외부 skill 설치가 필요하면 출처·권한·license·실행 위험을 제시하고 별도 승인을 받는다.
5. 반복 가능한 공백이고 기존 skill과 중복되지 않을 때만 skill 생성을 제안한다.

설치·생성은 원래 작업 승인에 포함되지 않는다. 승인 후 생성하더라도 registry 검증과 실제 호출 검증을 통과해야 사용 가능 상태로 본다.
