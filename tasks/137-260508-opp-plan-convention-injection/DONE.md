# DONE: PLAN 워커 컨벤션 [MUST] 인용 강제 — 사전 주입 강화

> 완료일: 2026-05-08 22:56 KST | 적용 스킬: opp | 모드: interactive

## 작업 결과 요약

PLAN 워커가 PLAN.md를 작성할 때 `docs/CONVENTIONS.md`의 강제 규칙을 [MUST] 원문 인용 포맷으로 반드시 박도록 하네스(dispatch-process.md) + 에이전트(opal-plan-agent) + 스킬(op-task-plan / plan-guide.md / op-dev-plan)에 의무 규약을 신설했다. 사전 차단(A) + 136 사후 검출(B)의 이중 안전망이 완성됨.

## 4개 잠재 적용 지점 채택 결정 (PLAN.md §2.1)

| # | 적용 지점 | 결정 |
|---|---------|------|
| #1 | dispatch-process.md §Step 3 (SSOT) | **채택** — 4개 오케스트레이터 PM 디스패치 흐름에 자동 전파 |
| #2 | opal-plan-agent AGENT.md 행동 규칙 | **부분 채택** (M-5 보조 강화) — opd/opds dev 라인 대비 |
| #3 | op-task-plan + plan-guide + op-dev-plan 품질 체크리스트 | **채택** (M-2/M-3/M-4) — QA Gate 자동 검출 |
| #4 | citation-rules.md §2.5 [MUST] 토큰 대상 | **비채택** — §2.5 헤더 "**개발 트랙** [MUST]" 한정 → 컨벤션(비개발 포함)과 트랙 매트릭스(§1.5) 충돌. §2.4 [MUST] 일반 포맷이 충분 |

## 요구사항 충족 (R-1 ~ R-6)

| # | 요구사항 | 결과 |
|---|---------|------|
| R-1 | PM 디스패치 측 강제 | ✅ M-1: dispatch-process.md §Step 3 카탈로그 + 워커 컨텍스트 주입 템플릿 갱신 |
| R-2 | PLAN 에이전트 측 강제 | ✅ M-5: opal-plan-agent AGENT.md §행동 규칙에 [MUST] 컨벤션 인용 의무 1행 |
| R-3 | PLAN.md 산출물 측 검증 | ✅ M-2/M-3/M-4: op-task-plan SKILL.md + plan-guide.md + op-dev-plan SKILL.md 품질 체크리스트 항목 추가 |
| R-4 | 인용 규약 측 토큰 확장 결정 | ✅ #4 비채택 + 근거 PLAN.md §2.1 명시 |
| R-5 | 하위 호환 명문화 | ✅ 5개 변경 지점 모두 "CONVENTIONS.md 부재 시 자동 스킵" 명시 |
| R-6 | 적용 지점 결정 근거 PLAN.md 기재 | ✅ §2.1에 4개 지점 채택/비채택 표 |

## 산출물

| # | 파일 | 크기 | 비고 |
|---|------|------|------|
| 1 | `tasks/137-260508-opp-plan-convention-injection/TASK.md` | 11KB | 요구사항 R-1~R-6 + 잠재 적용 지점 4종 |
| 2 | `tasks/137-260508-opp-plan-convention-injection/PLAN.md` | 411줄 | 잠재 적용 지점 정밀 분석 + 6 Step (M-1~M-5 + 통합 검증) |
| 3 | `tasks/137-260508-opp-plan-convention-injection/QA-PLAN.md` | 14.8KB | PLAN 검증 보고서 (R-1~R-6 1:1 매핑) |
| 4 | `tasks/137-260508-opp-plan-convention-injection/QA-EXECUTE.md` | 8.7KB | EXECUTE 검증 보고서 (5개 파일 grep + 일관성 + 문서 품질 모두 Pass) |
| 5 | `tasks/137-260508-opp-plan-convention-injection/DONE.md` | (이 파일) | 완료 보고 |

## 변경 파일 (changed_files)

| # | 파일 (진본) | 버전 | 변경 요약 |
|---|------------|------|----------|
| 1 | `opal/core/references/pm/dispatch-process.md` | v1.1 | §Step 3 인용 의무 카탈로그에 컨벤션 [MUST] 명시 (4건: 카탈로그·예시·템플릿·하위 호환) |
| 2 | `opal/skills/op-task-plan/SKILL.md` | v1.4 | §품질 체크리스트에 컨벤션 [MUST] 검증 항목 추가 |
| 3 | `opal/skills/op-task-plan/references/plan-guide.md` | v1.2 | SKILL.md와 동일 항목 동기화 |
| 4 | `opal/skills/op-dev-plan/SKILL.md` | v2.5 | §품질 체크리스트에 동일 항목 추가 |
| 5 | `opal/agents/opal-plan-agent/AGENT.md` | v1.1 | §행동 규칙에 [MUST] 컨벤션 인용 의무 + 변경이력 섹션 신설 |

## 136 (사후 검증 B)와 책임 분리 + 시너지

| 차원 | 137 (사전 주입 A) | 136 (사후 검증 B) |
|------|-----------------|-------------------|
| 검사 시점 | PLAN 단계 (워커 작성 시) | EXECUTE / TEST PM Gate (워커 완료 후) |
| 검사 대상 | PLAN.md (코드 예시 포함) | changed_files (소스 파일) |
| 메커니즘 | PLAN 워커의 자체 [MUST] 인용 의무 | opal-convention-checker 자동 디스패치 |
| 효과 | 사전 차단 — 잘못된 예시가 PLAN.md에 박히지 않음 | 사후 검출 — 코드 변경 후 위반 자동 진단 |

→ **이중 안전망**: 사전에 [MUST] 인용으로 워커 인지 강화 + 사후에 컨벤션 체커가 한 번 더 검증.

## 검증 결과

- **PLAN PM Gate**: state validate Pass (violations 0건)
- **EXECUTE QA Gate**: Pass — grep 6/6 / R-1~R-6 / 일관성 5 / 문서 품질 5 모두 Pass
- **EXECUTE PM Gate**: Pass — 자가 진단 4/4 (산출물 / 체크리스트 / `~/.opal/` 미편집 / state validate)
- **CLOSE 진입 게이트**: 통과 (캡틴 "확인" 발화 → row 18 owner=user mark)
- **136 §13 충돌 검토**: 0건 (검사 시점·대상·메커니즘 분리)

## 후속 작업

- **136 사후 검증 시스템**과 함께 사전·사후 이중 안전망 정착 완료. 추가 후속 태스크 불필요.
- **검증 시기**: 다음 PLAN 단계 작업 시(opp/opd/opds/opdw 어느 오케스트레이터든) PLAN.md에 컨벤션 [MUST] 인용이 자동 적용되는지 운영 중 관찰.

## 변경이력

| 버전 | 일시 (KST) | 변경 |
|------|-----------|------|
| v1.0 | 2026-05-08 22:56 | 태스크 완료 보고 |
