# TASK 014 — 파이프라인 간소화 (QA 통합 + 단계 축소 + 경량 트랙)

> 채번: 014 | 일자: 2026-06-07 | 스킬: opp | 모드: semi-agentic (PLAN까지 캡틴 검토)

## 목적
캡틴 #2 문제("작업이 단계 많고 왕복이 길어 느림") 해결. 파이프라인 단계·게이트·왕복을 줄여 속도를 개선하되, 검증 실효성(특히 동작 검증 TEST)은 유지·강화한다.

## 배경 (진단 결과)
- opds(가장 짧은 트랙)조차 STATE 19행 — State Gate가 PM Gate 앞뒤로 중복(단계당 2개)
- QA = 실제로는 "요구사항→설계 문서 검토자"이며, opds엔 QA Gate가 아예 없고 PM이 겸함
- 캡틴 정의: QA 역할(요구사항→설계 누락·오해 검토)이 PM Gate로 충분하면 통합 OK

## 범위 (3축)
- **a (QA 통합)**: 문서 QA를 PM Gate로 통합. QA Gate 단계 제거(opd/opwt). PM Gate를 "요구사항→설계 검토자"로 강화(QA 항목 흡수 + self-check). **동작 검증(TEST)은 독립 유지 — 통합 금지.**
- **L1 (STATE 행 축소)**: 산출물 생성 행을 작업 행에 흡수 + State Gate 중복 제거. opds 19→~11행.
- **L2 (경량 트랙)**: 작은 작업(파일 1~2개·단순 수정)은 풀 파이프라인 우회 (PM 직접·게이트 최소).

## 불변 원칙 (지켜야 할 것)
- TEST-SCENARIO.md 작성은 **유지** (추적 행만 통합, 문서·작업 불변)
- 동작 검증(TEST·state-tool verify)은 독립 유지 — self-confirming 위험 영역
- 헌법(PRINCIPLES.md) §4 준수

## AC
- [ ] QA Gate 단계 제거 + PM Gate가 요구사항 누락·오해 검토 + self-check 흡수
- [ ] opds STATE 행 19→11 (산출물 행 흡수 + State Gate 중복 제거)
- [ ] 모든 pilot 트랙에 일관 적용 (opds/opd/opp/opdw/opwt/oppd/opsdd)
- [ ] interactive 하네스와 opds의 QA Gate 모순 해소
- [ ] L2 경량 트랙 진입 기준 정의
- [ ] TEST-SCENARIO·TEST·verify 불변 확인

## 결정 보류 항목 (PLAN에서 캡틴 확정)
- M-A: State Gate를 별도 행에서 완전 제거(각 행 mark에 흡수)할지 — 더 줄지만 추적 방식 변경
