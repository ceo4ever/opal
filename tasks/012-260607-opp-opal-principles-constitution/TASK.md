# TASK 012 — OPAL Principles 헌법 신설 + 하네스 다이어트

> 채번: 012 | 일자: 2026-06-07 | 스킬: opp | 모드: 경량 PM 직접수행 (캡틴 승인)

## 목적
카파시 스킬 철학을 담은 OPAL 헌법(`opal/core/PRINCIPLES.md`)을 SSOT로 신설하고,
하위 문서(하네스·스킬·에이전트)가 헌법을 **참조로 상속**하도록 전환하여 중복 advisory를 제거(다이어트)한다.

## 배경 — 캡틴 보고 문제점
1. 임의 해석 진행 / 모호함 무시 (카파시 §1)
2. 속도 느림 — Context Rot (Eager 부트스트랩 1,206줄 ≈ 15.7K토큰, 권장의 6배)
3. **목업으로 때우고 완료 선언 → 테스트로 잠재 문제 미발견** (카파시 §4, 가장 심각)
4. TASK/ANALYSIS/PLAN 문서는 완성되나 실제 개발이 안 됨

근본 원인: 원칙(의도)은 4~5개 문서에 흩어져 선언돼 있으나 **강제가 없고 중복·비대**.
→ "완료 = 문서 생성"으로 정의돼 구현·검증이 권고에 그침.

## 산출물
- `opal/core/PRINCIPLES.md` — 영어 헌법, 신규 ✅
- `tasks/012-.../PRINCIPLES.ko.md` — 한국어 참고판 ✅
- 하위 문서 헌법 참조 전환 + 중복 제거 (진행)

## 범위
**포함**: 헌법 신설 / 헌법 always-on 등록 / 중복 advisory 제거·헌법 참조 전환
**별도 후속 태스크**: state-tool 강제 게이트(완료=동작·목업금지·명확화 차단), Eager 부피 D1 다이어트

## 다이어트 대상 (스캔 결과)
- `opal/core/references/harness/coding-principles.md` — 카파시 원칙 전면 중복 (1순위)
- `opal/core/references/opal-harness.md` — §1 Guards 중 Core Stance 중복분
- `opal/skills/op-dev-wireframe/personas/service-planner.md`
- `opal/skills/op-task/personas/service-planner.md`
- `opal/agents/opal-wtm-agent/AGENT.md`

## AC
- [ ] PRINCIPLES.md 신설 + Eager always-on 로드 등록
- [ ] coding-principles 등 중복 문서가 헌법 참조로 전환·슬림화
- [ ] 하위 문서가 원칙을 재서술하지 않음 (참조만)
- [ ] 변경 문서마다 변경이력 행 추가
