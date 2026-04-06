# DONE: Artifact Gate 설계 및 적용

> 완료일: 2026-04-06 | 스킬: opp | 태스크: 090-opp-artifact-gate

## 완료 요약

QA Gate 완료의 증거(산출물 파일)가 없으면 다음 단계 진입을 구조적으로 차단하는 Artifact Gate를 하네스와 opwt에 적용했다.

## 변경 파일

| 파일 | 변경 내용 |
|------|---------|
| `opal/core/references/opal-harness-interactive.md` | §2.5 Artifact Gate 신설 — QA Gate 후 PM Gate 전 산출물 존재 강제 확인 |
| `opal/core/references/opal-harness-agentic.md` | §4 강화 검토 기준에 Artifact Gate 항목 추가 |
| `opal/core/references/opal-harness.md` | §2 QA 산출물 표준 파일명 공통 명세 추가 (QA-PLAN.md / QA-EXECUTE.md / QA-ANALYSIS.md) |
| `opal/skills/opal-pilot-write-tech/SKILL.md` | ANALYSIS PM Gate(자가 체크) 추가 + EXECUTE 배치 "PM 검토" → "PM Gate" 명확화 |

## 설계 결정

- Artifact Gate는 각 SKILL.md 인라인이 아닌 **하네스 공통 규칙**으로 적용 — 모든 opal-pilot 자동 적용
- opwt ANALYSIS는 PM 직접 수행 단계이므로 외부 QA 에이전트 없이 **자가 체크(Self-check)** 방식
- opwt EXECUTE 배치 게이트는 구조 변경 없이 **표기만 명확화** (배치 단위 간이 검토 + QA 단계 최종 판정이 전체 PM Gate 역할)

## 후속 과제

- 추가작업 프로세스(§3) Artifact Gate 적용 — 별도 태스크로 분리 예정
