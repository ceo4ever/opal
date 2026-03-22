# Full Task 파이프라인

> 참조: SKILL.md (오케스트레이터 라우터)
> 워커 에이전트: `dtp-dev-agent`
> QA 에이전트: `dtp-qa-dev-agent`

## 파이프라인 개요

```
TASK → ANALYSIS → PLAN → TODO → TEST-SCENARIO → EXECUTE
```

```
[워커: ANALYSIS] → [QA] → 검토
        │
[워커: PLAN] → [QA] → 검토
        │
[워커: TODO] → 검토
        │
[워커: TEST-SCENARIO 작성] → 검토/승인
        │
[워커: EXECUTE]
        │
[dtp-dev-test-agent 호출] → 완료 보고
```

---

## STEP 2: ANALYSIS (분석)

**오케스트레이터가 ANALYSIS 워커를 디스패치한다.**

> **워커 디스패치**: 단계=ANALYSIS, 이전 산출물=TASK.md, 가이드=analysis-guide.md, 산출물=ANALYSIS.md

**상세 가이드**: `references/analysis-guide.md`를 읽고 따른다.

### ANALYSIS 단계 핵심

분석 대상 (작업 유형별 깊이 조절):

| 분석 영역 | 신규 | 개선 | 수정 | 오류 |
|----------|------|------|------|------|
| 기존 코드베이스 분석 | ● | ● | ● | ● |
| 외부 API/라이브러리 조사 | ● | ○ | - | - |
| 유사 구현 패턴 참조 | ● | ○ | - | - |
| 영향 범위 분석 | ● | ● | ● | ○ |
| 원인 분석 (Root Cause) | - | - | - | ● |

(● 필수 / ○ 선택 / - 불필요)

### 워커 디스패치 프롬프트

```
dev-task-pilot ANALYSIS 워커로서 아래 태스크를 수행하라.

**태스크**: {태스크 제목}
**단계**: ANALYSIS
**태스크 폴더**: {tasks/{NNN}-{name}/}

**이전 산출물**:
- {tasks/{NNN}-{name}/TASK.md}

**단계 가이드**:
- {skills/dev-task-pilot/references/analysis-guide.md 절대 경로}

**프로젝트 컨벤션**:
- {프로젝트 루트의 CLAUDE.md 절대 경로}

**추가 참조**:
- {~/.opal/references/skills.md} (기술 스택별 추천 스킬 섹션)
- {skills/dev-task-pilot/references/dev-tools-registry.md 절대 경로} (있으면)

**산출물 저장 경로**: {tasks/{NNN}-{name}/ANALYSIS.md}
```

### 워커 완료 시

워커가 ANALYSIS.md를 반환하면, **오케스트레이터가 dtp-qa-dev-agent를 호출**한다. QA 결과를 포함하여 사용자에게 보고.

---

## STEP 3: PLAN (구현 계획)

**오케스트레이터가 PLAN 워커를 디스패치한다.**

> **워커 디스패치**: 단계=PLAN, 이전 산출물=TASK.md+ANALYSIS.md, 가이드=plan-guide.md (Full Task 섹션), 산출물=PLAN.md
>
> **resume 가능 시**: ANALYSIS 워커를 이어서(resume) PLAN을 수행한다. 코드 분석 컨텍스트가 보존되어 설계 품질이 향상된다.

**상세 가이드**: `references/plan-guide.md`의 "Full Task PLAN" 섹션을 읽고 따른다.

### PLAN 단계 핵심

구현 계획에 반드시 포함되는 항목:

1. **구현 순서** — 파일별 작업을 순서대로 나열
2. **파일 목록** — 신규 생성/수정 대상 파일 전체 경로
3. **핵심 설계** — 클래스 구조, 함수 시그니처, 데이터 모델 등
4. **의존성** — 추가 패키지, 환경 설정 변경 사항
5. **테스트 전략** — 어떤 테스트를 작성할지, 성공 기준

### 워커 디스패치 프롬프트

```
dev-task-pilot PLAN 워커로서 아래 태스크를 수행하라.

**태스크**: {태스크 제목}
**단계**: PLAN
**태스크 폴더**: {tasks/{NNN}-{name}/}

**이전 산출물**:
- {tasks/{NNN}-{name}/TASK.md}
- {tasks/{NNN}-{name}/ANALYSIS.md}

**단계 가이드**:
- {skills/dev-task-pilot/references/plan-guide.md 절대 경로} (Full Task 섹션)

**프로젝트 컨벤션**:
- {프로젝트 루트의 CLAUDE.md 절대 경로}

**추가 입력**:
- {tasks/{NNN}-{name}/ANALYSIS.md}의 "6. 기술 컨텍스트" 섹션

**산출물 저장 경로**:
- {tasks/{NNN}-{name}/PLAN.md}
- {tasks/{NNN}-{name}/execution-plan.json} (FE/BE 작업 시)
```

### 워커 완료 시

워커가 PLAN.md (+ execution-plan.json)를 반환하면, **오케스트레이터가 dtp-qa-dev-agent를 호출**한다. QA 결과를 포함하여 사용자에게 보고.

---

## STEP 4: TODO (실행 체크리스트)

**오케스트레이터가 TODO 워커를 디스패치한다.**

> **워커 디스패치**: 단계=TODO, 이전 산출물=TASK.md+ANALYSIS.md+PLAN.md, 가이드=todo-guide.md, 산출물=TODO.md

**상세 가이드**: `references/todo-guide.md`를 읽고 따른다.

### TODO 단계 핵심

TODO.md는 실행 모드에 따라 2~3개 파트로 구성된다:

**Part A: 실행 체크리스트**
- PLAN의 각 구현 항목을 작업 단위로 분해
- 각 작업에 체크박스, 테스트 기준, 실행 방법(direct/sub-agent) 명시
- 작업 간 의존성 순서를 표시

**Part B: QA 체크리스트**
- 기능 테스트 항목
- 회귀 테스트 항목
- 코드 품질 체크

### 복잡도 판별

Part A 작성 후, 아래 기준으로 실행 모드를 결정한다:

| 기준 | 단순 모드 | 복잡 모드 |
|------|----------|----------|
| Step 수 | ≤5개 | 6개 이상 |
| 변경 파일 수 | ≤3개 | 4개 이상 |
| 모듈 범위 | 단일 모듈 | 다중 모듈/레이어 |
| 작업 유형 | 오류 수정, 단순 기능 수정 | 신규 개발, 대규모 개선 |
| 외부 의존성 | 없음 | 새 API, 새 패키지, 새 도구 필요 |

**하나라도 "복잡 모드" 기준에 해당하면 복잡 모드를 적용한다.**

### 모드별 분기

**단순 모드:**
1. Part A + Part B 작성
2. 사용자에게 **승인 요청** (QA 생략)

**복잡 모드:**
1. 워커가 Part A + Part B + 복잡도 판별 결과를 반환
2. **오케스트레이터가** 복잡 모드 판정 확인 → **dtp-action-plan-agent 호출** → Part C 생성
3. TODO.md (A+B+C) 완성
4. 사용자에게 **승인 요청** (QA 생략)

### 워커 디스패치 프롬프트

```
dev-task-pilot TODO 워커로서 아래 태스크를 수행하라.

**태스크**: {태스크 제목}
**단계**: TODO
**태스크 폴더**: {tasks/{NNN}-{name}/}

**이전 산출물**:
- {tasks/{NNN}-{name}/TASK.md}
- {tasks/{NNN}-{name}/ANALYSIS.md}
- {tasks/{NNN}-{name}/PLAN.md}

**단계 가이드**:
- {skills/dev-task-pilot/references/todo-guide.md 절대 경로}

**프로젝트 컨벤션**:
- {프로젝트 루트의 CLAUDE.md 절대 경로}

**산출물 저장 경로**: {tasks/{NNN}-{name}/TODO.md}
```

### 사용자 보고

```
📋 [TODO] 완료 보고

📎 산출물: tasks/{NNN}-{태스크명}/TODO.md
   실행 모드: {단순 / 복잡}
   Step 수: {N}개

승인하시면 TEST-SCENARIO 작성으로 넘어갑니다.
```

---

## STEP 4.5: TEST-SCENARIO (테스트 시나리오)

TODO.md가 사용자의 승인을 받으면, **오케스트레이터가 TEST-SCENARIO 워커를 디스패치한다.**

> **워커 디스패치**: 단계=TEST-SCENARIO, 이전 산출물=TASK.md+TODO.md, 가이드=test-scenario-guide.md, 산출물=TEST-SCENARIO.md

**상세 가이드**: `references/test-scenario-guide.md`를 읽고 따른다.

### 워커 디스패치 프롬프트

```
dev-task-pilot TEST-SCENARIO 워커로서 아래 태스크를 수행하라.

**태스크**: {태스크 제목}
**단계**: TEST-SCENARIO
**태스크 폴더**: {tasks/{NNN}-{name}/}

**이전 산출물**:
- {tasks/{NNN}-{name}/TASK.md}
- {tasks/{NNN}-{name}/TODO.md}

**단계 가이드**:
- {skills/dev-task-pilot/references/test-scenario-guide.md 절대 경로}

**프로젝트 컨벤션**:
- {프로젝트 루트의 CLAUDE.md 절대 경로}

**산출물 저장 경로**: {tasks/{NNN}-{name}/TEST-SCENARIO.md}
```

워커 완료 시 사용자에게 보고:

```
📋 [TEST-SCENARIO] 완료 보고

📎 산출물: tasks/{NNN}-{태스크명}/TEST-SCENARIO.md

승인하시면 EXECUTE를 시작합니다.
```

---

## STEP 5: EXECUTE (실행)

TEST-SCENARIO.md가 사용자의 승인을 받으면, **오케스트레이터가 EXECUTE 워커를 디스패치한다.**

> **워커 디스패치**: 단계=EXECUTE, 이전 산출물=TASK.md+TODO.md(+Part C), 가이드=execute-guide.md, 산출물=코드 변경

**상세 가이드**: `references/execute-guide.md`를 읽고 따른다.

### 체크리스트 갱신 규칙

워커가 각 Step 완료 시 TODO.md의 체크박스를 즉시 갱신한다:
- `- [ ] 완료` → `- [x] 완료`

**QA 체크리스트 갱신**: 모든 실행 Step 완료 후, test 에이전트 호출 전에 워커가 Part B QA 체크리스트의 각 항목을 실제 검증하고 체크박스를 갱신한다:
- 통과 항목: `- [ ]` → `- [x]`
- 미통과 항목: `- [ ]` 유지 + 사유를 인라인 주석으로 기록 (예: `- [ ] 항목 <!-- 사유: ... -->`)

### 단순 모드 실행

워커가 Step 순서대로 직접 실행한다:

1. Part A의 Step을 의존성 순서대로 하나씩 실행
2. 각 Step 완료 시: TODO.md 체크박스 갱신
3. 블로커 발생 시 즉시 오케스트레이터에 반환
4. 모든 Step 완료 후:
   - Part B QA 체크리스트를 검증하고 체크박스 갱신 (통과: `[x]`, 미통과: `[ ]` + 사유)
   - 결과 반환 → **오케스트레이터가**:
     - **dtp-dev-test-agent 호출** → TEST-SCENARIO.md에 결과 채움 + 판정
     - **DONE.md 생성** (완료 리포트 규칙 참조)
     - 사용자에게 완료 보고

### 복잡 모드 실행

워커가 Part C 토폴로지에 따라 내부 서브 에이전트를 배치하여 실행한다:

1. Part C-3 도구 요구사항 확인 — 미설치 도구 설치 (사용자 확인 후)
2. Part C-1 에이전트 토폴로지에 따라 배치(batch) 구성
3. 각 배치: 서브 에이전트를 **병렬로** Task 도구로 실행
4. 배치 완료마다 TODO.md 체크박스 갱신 + 진행 보고
5. 전체 에이전트 완료 후:
   - Part B QA 체크리스트를 검증하고 체크박스 갱신 (통과: `[x]`, 미통과: `[ ]` + 사유)
   - 결과 반환 → **오케스트레이터가**:
     - **dtp-dev-test-agent 호출** → TEST-SCENARIO.md에 결과 채움 + 판정
     - **DONE.md 생성** (완료 리포트 규칙 참조)
     - 사용자에게 완료 보고

> **복잡 모드 + 중첩 불가 시** (Cursor 등): 워커가 내부 서브 에이전트를 호출할 수 없는 플랫폼에서는, 오케스트레이터가 Part C 토폴로지에 따라 배치별 서브 에이전트를 직접 디스패치한다.

### execution-plan.json 기반 FE/BE 병렬 디스패치

execution-plan.json이 존재하고 frontend + backend 모두 포함된 경우, **오케스트레이터가** 아래 순서로 디스패치한다:

**Phase 1: Common 실행**
- `execution_order.sequence`의 phase 1 항목 (공통 타입, 설정 등)
- 단일 워커로 순차 실행

**Phase 2: FE + BE 병렬 디스패치**
- **FE 서브에이전트**: `frontend.screens` 배열을 전달
  - 각 screen에 대해 ui-designer plan-driven 모드 호출
  - 화면 간 독립적이면 내부 병렬 가능
- **BE 서브에이전트**: `backend.layers` 배열을 전달
  - layer 순서(model→dto→service→router)에 따라 순차 실행

**FE 서브에이전트 프롬프트**:

```
dev-task-pilot EXECUTE 워커(FE)로서 아래 화면을 구현하라.

**담당 영역**: Frontend
**태스크 폴더**: {tasks/{NNN}-{name}/}
**실행 계획**: {tasks/{NNN}-{name}/execution-plan.json}의 frontend.screens

**화면별 구현**:
- 각 screen 객체를 ui-designer plan-driven 모드의 입력으로 전달
- ui-designer 스킬 탐색: {프로젝트}/.opal/skills/ui-designer/SKILL.md → ~/.opal/skills/ui-designer/SKILL.md
- SKILL.md의 모드 판별 → modes/plan-driven.md Read → 프로세스 따름

**가이드**: {skills/dev-task-pilot/references/execute-guide.md 절대 경로}
**컨벤션**: {프로젝트 루트의 CLAUDE.md 절대 경로}
```

**BE 서브에이전트 프롬프트**:

```
dev-task-pilot EXECUTE 워커(BE)로서 아래 레이어를 구현하라.

**담당 영역**: Backend
**태스크 폴더**: {tasks/{NNN}-{name}/}
**실행 계획**: {tasks/{NNN}-{name}/execution-plan.json}의 backend.layers

**레이어 실행 순서**: depends_on에 따라 순차 (일반적으로 model→dto→service→router)
**가이드**: {skills/dev-task-pilot/references/execute-guide.md 절대 경로}
**컨벤션**: {프로젝트 루트의 CLAUDE.md 절대 경로}
```

**Phase 3: 완료**
- FE + BE 모두 완료 → **dtp-dev-test-agent 호출** → **DONE.md 생성** → 사용자 보고

**fallback**: execution-plan.json이 없거나 단일 영역(FE만/BE만)이면 → 기존 TODO.md 기반 순차 실행 (아래 프롬프트).

---

### 워커 디스패치 프롬프트 (기존 방식 — fallback)

```
dev-task-pilot EXECUTE 워커로서 아래 태스크를 수행하라.

**태스크**: {태스크 제목}
**단계**: EXECUTE
**태스크 폴더**: {tasks/{NNN}-{name}/}

**이전 산출물**:
- {tasks/{NNN}-{name}/TASK.md}
- {tasks/{NNN}-{name}/TODO.md}

**단계 가이드**:
- {skills/dev-task-pilot/references/execute-guide.md 절대 경로}

**프로젝트 컨벤션**:
- {프로젝트 루트의 CLAUDE.md 절대 경로}

**실행 규칙**:
1. TODO.md의 Part A 체크리스트를 순서대로 실행한다
2. 각 Step 완료 시 TODO.md 체크박스를 갱신한다
3. 모든 Step 완료 후 Part B QA 체크리스트를 검증한다
4. 완료 시 changed_files, summary, status를 반환한다
5. 블로커 발생 시 즉시 status: blocked로 반환한다
6. QA/Test 에이전트는 호출하지 않는다
```
