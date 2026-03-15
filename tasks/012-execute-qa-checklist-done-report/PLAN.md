# PLAN: EXECUTE 완료 시 QA 체크리스트 갱신 + 완료 리포트 생성 규칙 추가

> 작성일: 2026-03-15 | 모드: Short Task | 참조: TASK.md

## 1. 코드 분석

### 관련 파일
| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `skills/task-flow/SKILL.md` | task-flow 핵심 스킬 정의 (워크플로우 전체) | O |
| `skills/task-flow/references/execute-guide.md` | EXECUTE 단계 상세 가이드 | O |
| `CLAUDE.md` | 프로젝트 컨벤션 + 산출물 저장 구조 | O |

### 현재 구현

**SKILL.md — EXECUTE 관련 구현:**

1. **Full EXECUTE (STEP 5, L591~631)**:
   - 체크리스트 갱신 규칙(L599~602): TODO.md Part A의 실행 체크박스만 갱신
   - 단순 모드(L606~614): Step 완료 → TODO.md 갱신 → 완료 후 "Part B QA 체크리스트를 확인" → QA 에이전트 호출 → 완료 보고
   - 복잡 모드(L616~628): 서브 에이전트 배치 실행 → TODO.md 갱신 → test 에이전트 → QA 에이전트 → 완료 보고
   - **문제**: Part B QA 체크리스트를 "확인"만 하고 체크박스를 갱신하는 규칙이 없음. DONE.md 생성 규칙 없음.

2. **Short EXECUTE (STEP 3, L720~742)**:
   - 체크리스트 갱신 규칙(L729~731): PLAN.md 섹션 3(실행 체크리스트)만 갱신
   - 실행 흐름(L735~741): Step 완료 → PLAN.md 갱신 → "QA 체크리스트(섹션 4)를 확인" → QA 에이전트 → 완료 보고
   - **문제**: 섹션 4 QA 체크리스트를 "확인"만 하고 체크박스를 갱신하는 규칙이 없음. DONE.md 생성 규칙 없음.

3. **산출물 저장 구조(L352~377)**:
   - Full Task: TASK.md, RESEARCH.md, QA-RESEARCH.md, PLAN.md, QA-PLAN.md, TODO.md, QA-EXECUTE.md, TEST-REPORT.md, skills/
   - Short Task: TASK.md, PLAN.md, QA-PLAN.md, QA-EXECUTE.md
   - **문제**: DONE.md가 없음.

4. **게이트 체크포인트(L749~776)**: EXECUTE 완료 보고 형식에 DONE.md 경로가 없음.

**execute-guide.md — EXECUTE 상세 가이드:**

1. **체크리스트 갱신 규칙(L105~116)**: 실행 체크리스트(Part A / 섹션 3)의 체크박스 갱신만 정의. QA 체크리스트 갱신 절차 없음.
2. **단순 모드(L16~36)**: L34 "Part B QA 체크리스트를 인라인으로 검증" — 검증만 언급, 갱신 규칙 없음.
3. **Short Task 모드(L63~73)**: L71 "QA 체크리스트(섹션 4)를 인라인으로 검증" — 검증만 언급, 갱신 규칙 없음.
4. **EXECUTE 최종 보고(L156~168)**: DONE.md 경로 없음.
5. **EXECUTE 품질 체크리스트(L202~211)**: QA 체크리스트 갱신 여부 항목 없음. DONE.md 생성 여부 항목 없음.

**CLAUDE.md — 산출물 저장 구조:**

- Full Task 구조(L36~46): DONE.md 없음.
- Short Task 구조(L48~54): DONE.md 없음.
- 단계 완료 보고 형식(L56~73): DONE.md 경로 없음.

### 영향 범위

- **상위 의존**: 오케스트레이터(SKILL.md)가 EXECUTE 완료 보고 형식을 사용 → 게이트 체크포인트에 DONE.md 경로 추가 필요
- **하위 의존**: 워커가 execute-guide.md를 읽고 실행 → 가이드에 QA 체크리스트 갱신 + DONE.md 생성 절차 추가 필요
- **참조**: CLAUDE.md의 산출물 구조를 외부에서 참조 → 구조에 DONE.md 추가 필요
- **기존 워크플로우 흐름**: QA 에이전트 호출, 게이트 체크포인트 순서는 변경하지 않음

## 2. 구현 계획

### 변경 파일
| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `skills/task-flow/SKILL.md` | (a) Full EXECUTE 단순/복잡 모드에 QA 체크리스트 갱신 규칙 추가, (b) Short EXECUTE에 QA 체크리스트 갱신 규칙 추가, (c) 산출물 저장 구조에 DONE.md 추가, (d) DONE.md 생성 규칙 + 템플릿 추가, (e) 게이트 체크포인트 EXECUTE 완료 보고에 DONE.md 경로 추가 |
| 2 | `skills/task-flow/references/execute-guide.md` | (a) 체크리스트 갱신 규칙에 QA 체크리스트 갱신 절차 추가, (b) 단순/복잡/Short 모드 실행 흐름에 QA 체크리스트 갱신 + DONE.md 생성 단계 추가, (c) DONE.md 템플릿 및 생성 규칙 섹션 추가, (d) EXECUTE 최종 보고 형식에 DONE.md 경로 추가, (e) 품질 체크리스트에 QA 체크리스트 갱신 + DONE.md 생성 항목 추가 |
| 3 | `CLAUDE.md` | (a) Full Task / Short Task 산출물 저장 구조에 DONE.md 추가, (b) 단계 완료 보고 형식에 DONE.md 경로 추가 |

### 핵심 설계

#### DONE.md 템플릿

기존 `tasks/011-short-task-default-mode/DONE.md` 예시를 기반으로 표준 템플릿을 정의한다:

```markdown
# DONE: {태스크 제목}

> 완료일: YYYY-MM-DD | 모드: {Full Task / Short Task} | 작업 유형: {신규/개선/수정/오류}

## 완료 요약
{작업 결과를 1~3문장으로 요약}

## 변경 파일
| # | 파일 | 변경 내용 |
|---|------|----------|

## 핵심 변경 사항
### Before
{변경 전 상태/동작}
### After
{변경 후 상태/동작}

## QA 결과
{QA 단계별 결과 요약: Pass/Fail 수}
{QA 체크리스트 결과 요약}

## 산출물 목록
| 파일 | 설명 |
|------|------|
```

#### QA 체크리스트 갱신 규칙

- **시점**: 모든 실행 Step 완료 후, QA 에이전트 호출 전
- **대상**: Full Task → TODO.md Part B / Short Task → PLAN.md 섹션 4
- **방법**: 각 QA 항목을 실제 검증하고 `- [ ]` → `- [x]`로 갱신. 통과하지 못한 항목은 `- [ ]`로 유지하고 사유를 인라인 주석으로 기록
- **주체**: EXECUTE 워커가 수행 (QA 에이전트와는 별도)

#### DONE.md 생성 규칙

- **시점**: QA 에이전트 호출 완료 후, 최종 완료 보고 직전
- **주체**: 오케스트레이터가 생성 (모든 단계 결과를 알고 있으므로)
- **저장 경로**: `tasks/{NNN}-{태스크명}/DONE.md`

#### 게이트 체크포인트 변경

EXECUTE 완료 보고 형식에 `📎 완료 리포트: tasks/{NNN}-{태스크명}/DONE.md` 추가.

## 3. 실행 체크리스트

- [x] Step 1: SKILL.md — EXECUTE 단계에 QA 체크리스트 갱신 규칙 추가 — Full 단순 모드(L606~614), Full 복잡 모드(L616~628), Short 모드(L735~741) 세 곳의 실행 흐름에 "QA 체크리스트 검증 및 갱신" 단계 삽입. 체크리스트 갱신 규칙 섹션(L599~602)에 QA 체크리스트 갱신 포함.
- [x] Step 2: SKILL.md — DONE.md 생성 규칙 + 템플릿 추가 — 공통 규칙 영역(게이트 체크포인트 앞 또는 뒤)에 "완료 리포트(DONE.md)" 섹션 신설. 템플릿, 생성 시점, 생성 주체 명시. 산출물 저장 구조(Full/Short 모두)에 DONE.md 추가. 게이트 체크포인트 EXECUTE 완료 보고 형식에 DONE.md 경로 추가.
- [x] Step 3: execute-guide.md — QA 체크리스트 갱신 절차 + DONE.md 생성 절차 추가 — 체크리스트 갱신 규칙 섹션에 QA 체크리스트 갱신 절차 추가. 단순/복잡/Short 모드 각 실행 흐름에 QA 체크리스트 갱신 + DONE.md 생성 단계 삽입. DONE.md 생성 규칙 섹션 신설. EXECUTE 최종 보고 형식에 DONE.md 경로 추가. 품질 체크리스트에 2개 항목 추가.
- [x] Step 4: CLAUDE.md — 산출물 저장 구조 + 완료 보고 형식 갱신 — Full Task / Short Task 산출물 구조에 DONE.md 추가. 단계 완료 보고 형식에 DONE.md 경로 추가.

## 4. QA 체크리스트

### 기능 테스트
- [x] SKILL.md Full EXECUTE 단순 모드: QA 체크리스트 갱신 단계가 명시되어 있는가?
- [x] SKILL.md Full EXECUTE 복잡 모드: QA 체크리스트 갱신 단계가 명시되어 있는가?
- [x] SKILL.md Short EXECUTE: QA 체크리스트 갱신 단계가 명시되어 있는가?
- [x] SKILL.md에 DONE.md 생성 규칙과 템플릿이 있는가?
- [x] SKILL.md 산출물 저장 구조(Full/Short)에 DONE.md가 있는가?
- [x] execute-guide.md에 QA 체크리스트 갱신 절차가 있는가?
- [x] execute-guide.md에 DONE.md 생성 규칙이 있는가?
- [x] execute-guide.md 최종 보고 형식에 DONE.md 경로가 있는가?
- [x] CLAUDE.md 산출물 구조에 DONE.md가 있는가?

### 회귀 테스트
- [x] 기존 게이트 체크포인트 흐름(QA 에이전트 호출 순서)이 변경되지 않았는가?
- [x] 기존 체크리스트 갱신 규칙(실행 체크리스트)이 유지되는가?
- [x] DONE.md 템플릿이 기존 예시(tasks/011)와 호환되는가?

### 코드 품질
- [x] SKILL.md 내 Full/Short 양쪽에 일관된 규칙이 적용되었는가?
- [x] execute-guide.md와 SKILL.md 간 내용이 정합성을 유지하는가?
- [x] CLAUDE.md의 산출물 구조가 SKILL.md와 일치하는가?
