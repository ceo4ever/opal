# DONE: opal-pilot-sdd (opsdd) 오케스트레이터 스킬 설계

> 완료일: 2026-04-06

## 요약

SDD(Spec-Driven Development) 방법론을 OPAL 프레임워크에 통합하는 `opal-pilot-sdd` (opsdd) 오케스트레이터와 4개 단계 스킬을 설계·구현했다.

## 산출물

### 신규 생성 (13개)

| # | 파일 | 역할 |
|---|------|------|
| 1 | `opal/skills/opal-pilot-sdd/SKILL.md` (385줄) | opsdd 오케스트레이터 — 7단계 파이프라인 |
| 2 | `opal/skills/opal-pilot-sdd/references/spec-guide.md` | spec.md 작성 가이드 |
| 3 | `opal/skills/opal-pilot-sdd/references/spec-plan-guide.md` | SPEC-PLAN.md 작성 가이드 |
| 4 | `opal/skills/opal-pilot-sdd/references/execute-loop-guide.md` | EXECUTE-LOOP 상세 가이드 |
| 5 | `opal/skills/opal-pilot-sdd/references/verify-guide.md` | 검증 3계층 + verify.md 구조 |
| 6 | `opal/skills/op-sdd-spec/SKILL.md` (315줄) | SPEC 단계 — spec.md 작성 |
| 7 | `opal/skills/op-sdd-spec/personas/spec-writer.md` | 명세 작성 페르소나 |
| 8 | `opal/skills/op-sdd-verify/SKILL.md` (411줄) | VERIFY 단계 — 3계층 검증 |
| 9 | `opal/skills/op-sdd-verify/personas/spec-verifier.md` | 검증 페르소나 |
| 10 | `opal/skills/op-sdd-plan/SKILL.md` (317줄) | SPEC-PLAN 단계 — 아키텍처 설계 |
| 11 | `opal/skills/op-sdd-plan/personas/system-architect.md` | 시스템 아키텍트 페르소나 |
| 12 | `opal/skills/op-sdd-tasks/SKILL.md` (267줄) | TASKS 단계 — 태스크 분해 |
| 13 | `opal/skills/op-sdd-tasks/personas/task-decomposer.md` | 태스크 분해 페르소나 |

### 수정 (5개)

| # | 파일 | 변경 |
|---|------|------|
| 1 | `docs/PROJECT.md` | opsdd 컴포넌트 5개 등록 |
| 2 | `docs/ARCHITECTURE.md` | 오케스트레이터/스킬 그룹에 opsdd 추가 |
| 3 | `docs/CONVENTIONS.md` | 약어, 네이밍, specs/ 규칙 추가 |
| 4 | `opal/core/references/opal-skills-registry.json` | opsdd + 4개 스킬 등록 |
| 5 | `opal/core/references/skills.md` | SDD 추천 항목 추가 |

## 핵심 설계 결정

| # | 결정 | 근거 |
|---|------|------|
| 1 | C안: TASK=진입점, SPEC=SSOT | SDD 철학 + 하네스 호환 |
| 2 | 두 세계 분리: specs/(SDD) + tasks/(OPAL) | 개념 충돌 해소 |
| 3 | 7단계 파이프라인: SPEC→VERIFY→SPEC-PLAN→TASKS→VERIFY→LOOP→DONE | SDD 3대 도구 패턴 + TDD 통합 |
| 4 | EXECUTE-LOOP A안: 기존 opal-pilot 오케스트레이터 호출 | 재활용 극대화 |
| 5 | QA Gate: VERIFY 단계에만 적용 (수행자 ≠ 리뷰어) | 이중 검증 방지 |
| 6 | 신규 에이전트 불필요: opal-task-agent 재활용 | 기존 범용 워커 패턴 |
| 7 | SKILL.md 500줄 유지: references/ 분리 | oppd 패턴 준수 |

## QA 결과

Pass with Warnings (Fail 0, Warning 4 — 모두 합리적 사유로 허용)

## 후속 작업

- oppd Phase 3 액션 스킬로 opsdd 등록 (별도 태스크)
- 배포: install-mac.sh 갱신 (캡틴 지시 시)
- op-sdd-verify 복잡도 증가 시 mode별 스킬 분리 검토
