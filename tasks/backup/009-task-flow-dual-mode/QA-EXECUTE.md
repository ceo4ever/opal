# QA: EXECUTE — task-flow Full Task / Short Task 듀얼 모드 분리

> 검토일: 2026-03-13 | 판정: ✅ Pass

## 1. 요약

task-flow 스킬을 Full Task(5단계)와 Short Task(3단계) 듀얼 모드로 분리하는 작업이 완료되었다. SKILL.md를 전면 재구성하여 모드 판별 규칙, Short Task 경로, QA 호출 맵을 추가했고, references/ 가이드 4개(plan-guide, research-guide, todo-guide, execute-guide)를 모드별로 정리했다. QA 에이전트는 3개 플랫폼(claude, cursor, antigravity) 모두 동일한 내용으로 동기화되었으며, CLAUDE.md의 Core Workflow 섹션도 듀얼 모드 다이어그램으로 업데이트되었다. TODO.md의 9개 Step 전부 체크박스가 완료([x]) 상태로 갱신되었다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| E-1 | 체크리스트 갱신 완료 | ✅ | TODO.md Part A의 Step 1~9 모두 `- [x] 완료` 상태 |
| E-2 | 완료 기준 충족 | ✅ | 각 Step의 완료 기준을 아래 상세 검증에서 확인 (후술) |
| E-3 | 파일 변경 정합성 | ✅ | PLAN.md 수정 파일 9개와 changed_files 9개가 정확히 일치. 예상 외 파일 변경 없음 |
| E-4 | 코드 컨벤션 준수 | ✅ | 모든 파일이 마크다운 형식 올바름. 한국어 본문 + 영어 기술 용어 규칙 준수 |
| E-5 | 테스트 결과 확인 | ✅ | 단순 모드 실행. 마크다운 문서 수정이므로 동적 테스트 대신 문서 정합성 검증으로 대체 (PLAN.md 5절 테스트 전략과 일치) |
| E-6 | 블로커 해결 여부 | ✅ | 블로커 보고 없음 |
| E-7 | QA 체크리스트 충족 | ⚠️ | Part B 체크리스트가 미체크([ ]) 상태로 남아 있음 (후술) |

### E-2 상세: Step별 완료 기준 충족 확인

| Step | 완료 기준 | 충족 여부 |
|------|----------|----------|
| 1 | SKILL.md가 Full/Short 두 경로를 명확히 분기, QA 호출 맵이 TASK.md R1/R2와 일치 | ✅ Full Task 경로(STEP 2~5)와 Short Task 경로(STEP 2~3) 명확히 분리. QA 호출 맵: TASK 생략, RESEARCH QA, PLAN QA, TODO 생략, EXECUTE QA — R1/R2와 일치 |
| 2 | Short Task 통합 PLAN 템플릿과 가이드가 포함 | ✅ plan-guide.md에 "Short Task 통합 PLAN" 섹션, 출력 형식 템플릿, 품질 체크리스트 포함 |
| 3 | Full Task 전용임이 명확히 표시 | ✅ research-guide.md 상단에 "Full Task 전용" 명시 + Short Task 참조 안내 |
| 4 | 체크박스 형식 통일, Full Task 전용 명시 | ✅ todo-guide.md 상단 "Full Task 전용" 명시, Step 항목이 `- [ ] 완료` 체크박스로 통일, 상태 표시 규칙이 체크박스 기반으로 변경 |
| 5 | Full/Short 모두의 체크리스트 갱신 규칙이 명확 | ✅ execute-guide.md에 "체크리스트 갱신 규칙" 섹션: Full(`- [ ] 완료` → `- [x] 완료`) + Short(`- [ ] Step N` → `- [x] Step N`) + Short Task 모드 실행 규칙 |
| 6 | Full/Short 모드별 검증 기준이 명확히 분리 | ✅ AGENT.md에 mode 입력 추가, 호출 시점 Full/Short 분기, SP-1~SP-5 추가, TASK/TODO "호출되지 않음" 명시, E-1 체크박스 갱신 구분 |
| 7 | claude 버전과 내용 동일 | ✅ cursor 버전(task-flow-qa.md)이 claude 버전과 구조/내용 동일 (frontmatter 포함 완전 동기화) |
| 8 | claude 버전과 내용 동일 | ✅ antigravity 버전(SKILL.md)이 claude 버전과 구조/내용 동일 (frontmatter 포함 완전 동기화) |
| 9 | CLAUDE.md가 SKILL.md의 듀얼 모드를 정확히 반영 | ✅ Full/Short 별도 다이어그램, 모드 판별 조건, QA 호출 규칙, 산출물 구조 반영 |

## 3. 지적 사항

### 🔵 Info: Part B QA 체크리스트 미체크 상태

TODO.md Part B의 체크박스가 모두 `[ ]`(미체크) 상태로 남아 있다. execute-guide.md의 규칙에 따르면 "Part B QA 체크리스트를 인라인으로 검증"한 후 QA 에이전트를 호출하도록 되어 있으며, 체크리스트 항목의 체크박스 갱신은 Part A에만 적용되는 것이 일반적이다. Part B는 검증 항목이지 실행 항목이 아니므로, 미체크 상태가 반드시 문제인 것은 아니다. 다만, 이 QA 리뷰에서 Part B 항목을 직접 검증한다.

**Part B 인라인 검증 결과:**

B-1. 기능 테스트:
- Full Task 파이프라인 일관성: ✅ SKILL.md에 TASK(검토) → RESEARCH(QA+검토) → PLAN(QA+검토) → TODO(검토) → EXECUTE(QA+보고) 흐름 명확
- Short Task 파이프라인 일관성: ✅ SKILL.md에 TASK(검토) → PLAN(QA+검토) → EXECUTE(QA+보고) 흐름 명확
- 모드 판별 조건 5개: ✅ SKILL.md "모드 판별 규칙" 섹션에 5개 조건 정확 기술
- 에스컬레이션 규칙: ✅ SKILL.md에 포함 (Step > 5 또는 파일 > 3)
- Short Task 통합 PLAN 템플릿: ✅ plan-guide.md에 출력 형식 포함
- 체크박스 갱신 규칙: ✅ execute-guide.md에 Full/Short 모두 기술

B-2. 회귀 테스트:
- Full Task RESEARCH/PLAN QA 호출: ✅ 기존과 동일 (STEP 2, 3에 "QA 에이전트 호출 (필수)" 유지)
- Planner/Test 에이전트 호출 경로: ✅ SKILL.md에 "Full Task 복잡 모드 전용"으로 기존 호출 규칙 보존
- 기존 에이전트(planner, test) 파일 미수정: ✅ git diff 결과 변경 없음 확인
- execute-plan-guide.md 미수정: ✅ git diff 결과 변경 없음 확인

B-3. 코드 품질:
- 마크다운 형식: ✅ 모든 파일 올바른 형식
- QA 에이전트 3플랫폼 동기화: ✅ claude/cursor/antigravity 3개 파일 핵심 내용 완전 동일
- CLAUDE.md 다이어그램 일치: ✅ SKILL.md와 CLAUDE.md의 Full/Short 다이어그램 흐름 일치
- references/ QA 호출 안내 일치: ✅ research-guide, plan-guide, todo-guide, execute-guide 모두 SKILL.md와 정합

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md | R1.1~R1.7 Full Task 요구사항이 SKILL.md에 반영되었는가 | ✅ 5단계 파이프라인, QA 호출 맵, 체크리스트 갱신 규칙 모두 반영 |
| TASK.md | R2.1~R2.6 Short Task 요구사항이 SKILL.md에 반영되었는가 | ✅ 3단계 파이프라인, 통합 PLAN, QA 호출, 체크리스트 갱신 모두 반영 |
| TASK.md | R3.1~R3.4 모드 판별 요구사항 반영 | ✅ 자동 판별 5조건, 오버라이드, 에스컬레이션 모두 SKILL.md에 포함 |
| TASK.md | R4.1~R4.3 산출물 구조 반영 | ✅ Full/Short 산출물 구조가 SKILL.md와 CLAUDE.md에 정확히 기술 |
| TASK.md | R5.1~R5.5 파일 변경 범위 | ✅ SKILL.md, references/ 4개, QA 에이전트 3개, CLAUDE.md — 9개 파일 모두 변경 완료 |
| PLAN.md | 수정 파일 9개와 실제 changed_files 일치 | ✅ 완전 일치, 예상 외 파일 없음 |
| PLAN.md | 영향 확인 파일(planner, test, execute-plan-guide) 미변경 | ✅ git diff로 확인, 변경 없음 |
| PLAN.md | 3.2 워크플로우 다이어그램이 SKILL.md와 일치 | ✅ SKILL.md 워크플로우 개요와 동일 구조 |
| PLAN.md | 3.3 모드 판별 로직이 SKILL.md와 일치 | ✅ 5개 조건, 오버라이드, 에스컬레이션 일치 |
| PLAN.md | 3.4 Short Task PLAN 템플릿이 plan-guide.md/SKILL.md와 일치 | ✅ 동일 템플릿 구조 |
| PLAN.md | 3.5 체크박스 형식 변경이 todo-guide.md에 반영 | ✅ 이모지 상태 폐지, 체크박스 통일 |
| PLAN.md | 3.6 QA 에이전트 변경 설계(SP-1~SP-5, mode 입력)가 반영 | ✅ 3개 플랫폼 에이전트 파일 모두 반영 |

## 5. 판정

**✅ Pass**

9개 Step 모두 완료, TASK.md의 모든 요구사항(R1~R5)이 SKILL.md와 관련 파일에 빠짐없이 반영되었다. PLAN.md의 파일 목록과 실제 변경 파일이 정확히 일치하고, 기존 에이전트(planner, test)에 대한 회귀 영향도 없다. Part B QA 체크리스트를 인라인 검증한 결과 전 항목 통과.
