# DONE: Harness Observability — 행위 주체 표시 + Gate 상태 추적

> 완료일: 2026-04-08 | 태스크: 096 | 스킬: opp

## 완료 요약

Harness에 Observability 체계를 구축했다. PM 행위 주체 표시 3종 선언 형식 신설, Gate 상태값 세분화(`대기 중` → `QA Gate 대기 / PM Gate 대기 / 사용자 확인 대기`), State Gate 이전 단계 차단 규칙 추가.

## 변경 파일

| 파일 | 변경 내용 |
|------|---------|
| `opal/core/references/opal-harness.md` | §5 행위 주체 표시 신설, §3 상태값 확장 + State Gate 강화 (v3.1) |
| `opal/core/references/opal-harness-interactive.md` | §3 State Gate 상태값 전이 표 신설 (v2.1) |
| `opal/core/references/opal-pm.md` | §3 디스패치 전 선언, §4 워커 완료 선언 추가 |
| `opal/core/AGENT.md` | 보고 형식 Observability 선언 참조 추가 |

## QA 결과

- QA-PLAN.md: Pass
- QA-EXECUTE.md: Pass (조건부 — 선언 형식 예시 미포함, Minor)

## 특이 사항

- `대기 중` 레거시 호환 노트 추가 — 기존 STATE.md 소급 변경 불필요
- 선언 형식 구체 예시는 추후 AGENT.md 또는 harness 개선 시 보완 가능
