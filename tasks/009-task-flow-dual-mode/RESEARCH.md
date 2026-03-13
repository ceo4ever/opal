# RESEARCH: task-flow Full Task / Short Task 듀얼 모드 분리

> 작성일: 2026-03-13 | 참조: TASK.md

## 1. 기존 코드 분석

### 관련 파일 목록

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `skills/task-flow/SKILL.md` | 메인 스킬 (472줄) — 전체 파이프라인 정의 | 수정 (대폭) |
| `skills/task-flow/references/research-guide.md` | RESEARCH 상세 가이드 (119줄) | 수정 (Short Task 참조 추가) |
| `skills/task-flow/references/plan-guide.md` | PLAN 상세 가이드 (108줄) | 수정 (Short Task 통합 PLAN 가이드 추가) |
| `skills/task-flow/references/todo-guide.md` | TODO 상세 가이드 (173줄) | 수정 (Full Task 전용 명시) |
| `skills/task-flow/references/execute-guide.md` | EXECUTE 상세 가이드 (202줄) | 수정 (체크리스트 갱신 규칙 추가) |
| `skills/task-flow/references/execute-plan-guide.md` | 실행 아키텍처 설계 가이드 (194줄) | 변경 없음 |
| `agents/claude/task-flow-qa/AGENT.md` | QA 에이전트 (263줄) | 수정 (호출 시점 변경, Short Task PLAN 검증 기준 추가) |
| `agents/cursor/task-flow-qa.md` | QA 에이전트 Cursor 버전 | 수정 (동기화) |
| `agents/antigravity/task-flow-qa/SKILL.md` | QA 에이전트 Antigravity 버전 | 수정 (동기화) |
| `agents/claude/task-flow-planner/AGENT.md` | Planner 에이전트 (223줄) | 변경 없음 |
| `agents/claude/task-flow-test/AGENT.md` | Test 에이전트 (176줄) | 변경 없음 |
| `CLAUDE.md` | 프로젝트 설정 — Core Workflow 섹션 | 수정 (워크플로우 개요) |

### 현재 구현 패턴

**SKILL.md 구조:**
```
frontmatter → 구현 금지 원칙 → 워크플로우 개요 → QA/Planner/Test 호출 규칙
→ 작업 유형 판별 → 산출물 구조 → 컨텍스트 로딩 → Git 점검
→ STEP 1~5 (각 단계 정의) → 게이트 체크포인트 → 실행 모드
```

현재 SKILL.md는 **단일 파이프라인**만 지원. 모드 분기 개념이 없음.

**QA 에이전트 호출 현황:**
- TASK → QA (호출)
- RESEARCH → QA (호출)
- PLAN → QA (호출)
- TODO → QA (호출)
- EXECUTE → QA (호출)

**변경 후 호출 맵:**

| 단계 | Full Task | Short Task |
|------|-----------|------------|
| TASK | QA 생략, 사용자 검토 | QA 생략, 사용자 검토 |
| RESEARCH | QA 호출 + 사용자 검토 | (PLAN에 통합) |
| PLAN | QA 호출 + 사용자 검토 | QA 호출 + 사용자 검토 |
| TODO | QA 생략, 사용자 검토 | (PLAN에 통합) |
| EXECUTE | QA 호출 + 사용자 보고 | QA 호출 + 사용자 보고 |

### 의존성 맵

```
SKILL.md ──references──→ research-guide.md
                       → plan-guide.md
                       → todo-guide.md
                       → execute-guide.md
                       → execute-plan-guide.md

SKILL.md ──호출──→ task-flow-qa (3개 플랫폼)
                → task-flow-planner (3개 플랫폼, Full Task 복잡 모드)
                → task-flow-test (3개 플랫폼, Full Task 복잡 모드)

CLAUDE.md ──참조──→ SKILL.md (워크플로우 개요 요약)
```

## 2. 영향 범위

### 직접 영향

1. **SKILL.md**: 워크플로우 개요, STEP 정의, 게이트 체크포인트, 실행 모드 — 전면 재구성
2. **QA 에이전트 (3개 플랫폼)**: 호출 시점 테이블 변경, Short Task PLAN 전용 검증 기준 추가
3. **references/ 가이드 4개**: 모드 분기 안내 추가, 체크리스트 갱신 규칙 추가
4. **CLAUDE.md**: Core Workflow 섹션 워크플로우 다이어그램 업데이트

### 간접 영향

- **task-flow-planner**: Full Task 복잡 모드에서만 호출 — 변경 불필요 (기존과 동일)
- **task-flow-test**: Full Task 복잡 모드에서만 호출 — 변경 불필요 (기존과 동일)
- **opal/core/references/skills.md**: task-flow 스킬 설명 업데이트 (트리거 키워드 동일)

## 3. 핵심 설계 결정사항

### 3.1 SKILL.md 구조 설계 방향

**선택지 A**: 하나의 SKILL.md에서 분기
- 장점: 단일 파일, 공통 로직 중복 없음
- 단점: 파일이 길어짐, 읽기 복잡

**선택지 B**: SKILL.md(공통) + short-task-guide.md(Short 전용) + full-task-guide.md(Full 전용)
- 장점: 관심사 분리
- 단점: 파일 3개로 분산, 공통 로직 동기화 필요

**결정: 선택지 A** — 하나의 SKILL.md에서 분기. 이유:
- 공통 부분(구현 금지 원칙, Git 점검, 작업 유형 판별, 모드 판별, 게이트 체크포인트)이 많음
- 모드별 차이는 STEP 정의와 QA 호출 여부 뿐
- 기존 references/ 가이드 파일이 상세 내용을 담당하므로 SKILL.md 자체는 길이 관리 가능

### 3.2 Short Task 통합 PLAN 설계

Short Task의 PLAN.md는 RESEARCH + PLAN + TODO를 하나로 통합한다. 새 references 가이드가 필요할 수 있으나, plan-guide.md를 확장하는 것이 적합하다.

**Short Task PLAN.md 구조:**
```markdown
# PLAN: {태스크 제목}
> 작성일: YYYY-MM-DD | 모드: Short Task | 참조: TASK.md

## 1. 코드 분석 (RESEARCH 요약)
### 관련 파일
### 현재 구현
### 영향 범위

## 2. 구현 계획
### 변경 파일
### 핵심 설계

## 3. 실행 체크리스트 (TODO)
- [ ] Step 1: ...
- [ ] Step 2: ...

## 4. QA 체크리스트
- [ ] 기능 테스트 항목
- [ ] 회귀 테스트 항목
```

### 3.3 모드 판별 위치

TASK 단계 완료 후, 사용자에게 TASK를 보고할 때 모드 제안도 함께 보고.
사용자가 오버라이드 가능 ("Full로 해줘" / "Short로 해줘").

### 3.4 체크리스트 갱신 규칙

EXECUTE 단계에서:
- **Full Task**: TODO.md Part A의 각 Step 체크박스 `[ ]` → `[x]` 갱신
- **Short Task**: PLAN.md 실행 체크리스트 `[ ]` → `[x]` 갱신
- 두 모드 모두 **각 Step 완료 즉시** 파일 업데이트
- 기존 상태 표시(`⬜→🔄→✅/🚫`)는 폐지하고, 마크다운 체크박스로 통일

### 3.5 에스컬레이션 규칙

Short Task 진행 중 PLAN 작성 시 복잡도가 높아진 경우:
- Step 수 > 5 또는 변경 파일 > 3 → 에스컬레이션 제안
- 사용자 승인 시 Full Task로 전환 (TASK.md 유지, RESEARCH부터 재시작)

### 3.6 QA 에이전트 변경 포인트

QA 에이전트(3개 플랫폼)에서 변경해야 할 부분:
1. **호출 시점 다이어그램** — Full/Short 모드별 분기 표시
2. **입력 필드** — `mode` 필드 추가 (`full` / `short`)
3. **PLAN 검증 기준** — Short Task용 추가 (통합 PLAN에 맞는 검증 항목)
4. **TASK/TODO 검증 기준** — "호출되지 않음" 명시 (Full/Short 모두)

## 4. 핵심 발견 사항

1. **SKILL.md 변경이 핵심** — 워크플로우 개요, STEP 정의, 게이트 체크포인트 전면 재구성 필요
2. **QA 에이전트 3개 플랫폼 동기화 필수** — claude/cursor/antigravity 모두 동일 변경
3. **references/ 가이드는 경미한 수정** — 모드 명시 + 체크리스트 갱신 규칙 추가 수준
4. **task-flow-planner, task-flow-test는 변경 불필요** — Full Task 복잡 모드에서만 호출, 기존 로직 유지
5. **CLAUDE.md의 Core Workflow 섹션** — 듀얼 모드 다이어그램으로 업데이트 필요

## 5. 제약/리스크

| 리스크 | 영향 | 대응 |
|--------|------|------|
| SKILL.md 대폭 변경으로 기존 동작 회귀 | 높음 | QA 에이전트의 검증 기준을 먼저 업데이트하여 기존 Full Task 호환 보장 |
| 3개 플랫폼 에이전트 파일 동기화 누락 | 중간 | cursor, antigravity 에이전트 파일을 claude 버전 기반으로 일괄 생성 |
| Short Task 모드 판별 오류 (복잡한 작업을 Short로 진입) | 중간 | 에스컬레이션 규칙으로 방어, PLAN 단계에서 QA가 복잡도 재검증 |
