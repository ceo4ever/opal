# PLAN: 워커 에이전트 프로젝트 컨텍스트 자율 로딩

> 작성일: 2026-03-30
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `agents/opal-task-agent/AGENT.md` | 범용 워커 에이전트 — 단계 스킬 실행 | **수정** |
| `agents/opal-task-qa-agent/AGENT.md` | QA 워커 에이전트 — qa_skill로 QA 수행 | **수정** |
| `agents/op-dev-test-agent/AGENT.md` | 테스트 워커 에이전트 — 동적 검증 | **수정** |
| `docs/PROJECT.md` | 프로젝트 정의 SSOT + 문서 허브 테이블 | 참조 (수정 없음) |
| `docs/ARCHITECTURE.md` | 시스템 아키텍처 | 참조 (수정 없음) |
| `docs/CONVENTIONS.md` | 코드 및 문서 컨벤션 | 참조 (수정 없음) |
| `skills/opal-pilot-dev/SKILL.md` | Full Task 오케스트레이터 — 디스패치 프롬프트 참조 | 참조 (수정 없음) |
| `skills/opal-project-pilot/SKILL.md` | 범용 오케스트레이터 — 디스패치 프롬프트 참조 | 참조 (수정 없음) |

### 현재 상태

**opal-task-agent** (6단계 실행 프로세스):
1. 오케스트레이터 프롬프트에서 스킬 경로, 태스크 폴더, 이전 산출물 확인
2. 스킬 SKILL.md Read
3. 페르소나 Read
4. references 가이드 Read
5. 스킬 프로세스 따라 산출물 생성
6. 결과 반환

→ **프로젝트 컨텍스트(docs/) 로딩 단계가 없다.** 오케스트레이터가 디스패치 시 `**프로젝트 컨텍스트**` 필드로 전달해야만 워커가 인지한다. opal-pilot-dev는 이 필드를 전달하지만, opal-project-pilot은 전달하지 않는다.

**opal-task-qa-agent** (5단계 실행 프로세스):
1. 오케스트레이터 프롬프트에서 qa_skill, 검증 대상 경로, 단계명, TASK.md 경로 확인
2. qa_skill SKILL.md Read
3. 페르소나/가이드 Read
4. 검증 수행 + QA 리포트 생성
5. 결과 반환

→ 마찬가지로 **프로젝트 컨텍스트 로딩이 없다.** QA가 프로젝트 구조/컨벤션을 모른 채 검증한다.

**op-dev-test-agent** (8단계 실행 프로세스):
1. 오케스트레이터 프롬프트에서 TEST-SCENARIO.md 경로, changed_files, 모드 확인
2. TEST-SCENARIO.md Read
3-7. 시나리오 실행, 코드 품질, 보안, 회귀 테스트
8. 결과 반환

→ **프로젝트 컨텍스트 로딩이 없다.** 프로젝트 구조를 모른 채 테스트 실행.

**docs/ 문서 체계** (docs/PROJECT.md "프로젝트 문서" 테이블 기준):

| 문서 | 용도 | 참조 시점 |
|------|------|----------|
| `docs/PROJECT.md` | 프로젝트 정의 (SSOT) | 모든 작업 |
| `docs/ARCHITECTURE.md` | 시스템 아키텍처 | 개발 작업 |
| `docs/CONVENTIONS.md` | 코드/문서 컨벤션 | 개발 작업 |

→ PROJECT.md 자체가 문서 허브 역할. 이 파일을 먼저 읽으면 어떤 문서가 있는지 알 수 있다.

### 영향 범위

- **직접 수정**: 3개 에이전트 AGENT.md (opal-task-agent, opal-task-qa-agent, op-dev-test-agent)
- **간접 영향**: 이 에이전트들을 호출하는 모든 오케스트레이터 (opal-pilot-dev, opal-pilot-dev-short, opal-pilot-dev-wireframe, opal-project-pilot 등). 단, 오케스트레이터 수정은 불필요 — 워커가 자율적으로 docs/를 탐색하므로.
- **하위 호환**: docs/ 미존재 프로젝트에서는 컨텍스트 로딩을 스킵하므로 기존 동작 그대로.

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| (없음) | | |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `agents/opal-task-agent/AGENT.md` | 실행 프로세스 Step 2~3 사이에 "프로젝트 컨텍스트 로드" 단계 삽입 |
| 2 | `agents/opal-task-qa-agent/AGENT.md` | 실행 프로세스 Step 2~3 사이에 "프로젝트 컨텍스트 로드" 단계 삽입 |
| 3 | `agents/op-dev-test-agent/AGENT.md` | 실행 프로세스 Step 2~3 사이에 "프로젝트 컨텍스트 로드" 단계 삽입 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| (없음) | | |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | opal-task-agent 프로젝트 컨텍스트 로드 단계 추가 | `agents/opal-task-agent/AGENT.md` | 낮음 |
| 2 | opal-task-qa-agent 프로젝트 컨텍스트 로드 단계 추가 | `agents/opal-task-qa-agent/AGENT.md` | 낮음 |
| 3 | op-dev-test-agent 프로젝트 컨텍스트 로드 단계 추가 | `agents/op-dev-test-agent/AGENT.md` | 낮음 |

> 3개 파일은 독립적이므로 순서는 자유. 단, opal-task-agent를 먼저 작성하여 패턴을 확립하고, 나머지 2개에 적용하는 방식이 효율적이다.

### 핵심 설계

#### 공통 설계: "프로젝트 컨텍스트 로드" 단계

모든 에이전트에 공통으로 적용하는 프로젝트 컨텍스트 로딩 로직:

**삽입 위치**: 스킬/시나리오 Read 직후, 본격 작업 시작 직전.
- opal-task-agent: Step 2(스킬 Read) → **[새 Step]** → Step 3(페르소나 Read)
- opal-task-qa-agent: Step 2(qa_skill Read) → **[새 Step]** → Step 3(페르소나/가이드 Read)
- op-dev-test-agent: Step 2(TEST-SCENARIO Read) → **[새 Step]** → Step 3(시나리오 실행)

**로딩 로직**:

```
프로젝트 컨텍스트 로드:
1. 오케스트레이터가 전달한 프로젝트 루트(태스크 폴더의 상위)에서 docs/PROJECT.md를 탐색한다.
2. docs/PROJECT.md가 존재하면 Read한다.
   - "프로젝트 문서" 테이블에서 추가 문서 목록을 확인한다.
3. 스킬 유형에 따라 추가 문서를 Read한다:
   - 모든 스킬: docs/PROJECT.md (필수, 존재 시)
   - 코드 관련 스킬(op-dev-*): + docs/ARCHITECTURE.md, docs/CONVENTIONS.md
   - FE 도메인: + docs/FRONTEND.md (존재 시)
   - BE 도메인: + docs/BACKEND.md (존재 시)
4. docs/ 디렉토리 또는 개별 문서가 없으면 해당 항목을 스킵한다.
```

**스킬 유형 판별 기준**:
- 오케스트레이터가 전달한 **스킬 경로**의 접두사로 판별:
  - `op-dev-*` → 코드 관련 (ARCHITECTURE.md + CONVENTIONS.md 추가 로드)
  - `op-task-*` → 범용 (PROJECT.md만)
  - 기타 → 범용

**op-dev-test-agent 특화**:
- 이 에이전트는 스킬 경로를 받지 않고 TEST-SCENARIO.md와 mode를 받는다. mode 값(`full-simple`, `full-complex`, `short`)은 모두 코드 개발 컨텍스트이므로, 항상 코드 관련 문서(ARCHITECTURE.md, CONVENTIONS.md)도 로드한다.

#### 파일별 변경 명세

**1. `agents/opal-task-agent/AGENT.md`**

실행 프로세스를 6단계 → 7단계로 확장:

```
## 실행 프로세스

1. 오케스트레이터 프롬프트에서 스킬 경로, 태스크 폴더, 이전 산출물을 확인한다.
2. 스킬 SKILL.md를 Read한다.
3. [신규] 프로젝트 컨텍스트를 로드한다. ← 새 단계
4. 스킬의 personas/에서 지정된 페르소나를 Read한다.
5. 스킬의 references/에서 지정된 가이드를 Read한다.
6. 스킬의 프로세스를 따라 산출물을 생성한다.
7. 결과를 반환한다.
```

새 Step 3의 내용:

```
3. 프로젝트 컨텍스트를 로드한다.
   - 태스크 폴더의 프로젝트 루트에서 `docs/PROJECT.md`를 탐색한다.
   - 존재하면 Read하고, "프로젝트 문서" 테이블에서 추가 문서를 확인한다.
   - 스킬 유형에 따라 추가 문서를 Read한다:
     - `op-dev-*` 스킬: `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md` 추가
     - 해당 도메인 문서: `docs/FRONTEND.md`, `docs/BACKEND.md` (존재 시)
   - `docs/` 또는 개별 문서가 없으면 스킵한다.
```

**2. `agents/opal-task-qa-agent/AGENT.md`**

실행 프로세스를 5단계 → 6단계로 확장:

```
## 실행 프로세스

1. 오케스트레이터 프롬프트에서 qa_skill, 검증 대상 경로, 단계명, TASK.md 경로를 확인한다.
2. qa_skill SKILL.md를 Read한다.
3. [신규] 프로젝트 컨텍스트를 로드한다. ← 새 단계
4. 스킬 프로세스에 따라 페르소나/가이드를 Read한다.
5. 검증을 수행하고 QA 리포트를 생성한다.
6. 결과를 반환한다.
```

새 Step 3의 내용 (opal-task-agent와 동일 로직, qa_skill 경로로 스킬 유형 판별):

```
3. 프로젝트 컨텍스트를 로드한다.
   - 검증 대상 경로의 프로젝트 루트에서 `docs/PROJECT.md`를 탐색한다.
   - 존재하면 Read하고, "프로젝트 문서" 테이블에서 추가 문서를 확인한다.
   - qa_skill 유형에 따라 추가 문서를 Read한다:
     - `op-dev-qa`: `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md` 추가
     - `op-task-qa`: `docs/PROJECT.md`만
   - `docs/` 또는 개별 문서가 없으면 스킵한다.
```

**3. `agents/op-dev-test-agent/AGENT.md`**

실행 프로세스를 8단계 → 9단계로 확장:

```
## 실행 프로세스

1. 오케스트레이터 프롬프트에서 TEST-SCENARIO.md 경로, changed_files, 모드를 확인한다.
2. TEST-SCENARIO.md를 Read한다.
3. [신규] 프로젝트 컨텍스트를 로드한다. ← 새 단계
4~8. (기존 Step 3~7 번호 시프트)
9. 결과를 반환한다.
```

새 Step 3의 내용 (항상 코드 관련 문서 로드):

```
3. 프로젝트 컨텍스트를 로드한다.
   - TEST-SCENARIO.md 경로의 프로젝트 루트에서 `docs/PROJECT.md`를 탐색한다.
   - 존재하면 Read하고, "프로젝트 문서" 테이블에서 추가 문서를 확인한다.
   - 코드 테스트 에이전트이므로 `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`도 Read한다.
   - 해당 도메인 문서: `docs/FRONTEND.md`, `docs/BACKEND.md` (존재 시)
   - `docs/` 또는 개별 문서가 없으면 스킵한다.
```

#### 프로젝트 루트 탐색 방식

태스크 폴더(예: `tasks/049-agent-project-context/`)로부터 프로젝트 루트를 추론한다:
- 태스크 폴더는 항상 `{프로젝트 루트}/tasks/{NNN}-{name}/` 형식
- 프로젝트 루트 = 태스크 폴더의 2단계 상위 디렉토리
- 또는 오케스트레이터가 디스패치 시 프로젝트 루트를 별도로 전달한 경우 그것을 사용

실용적 접근: 워커는 태스크 폴더 경로에서 `tasks/` 부분을 제거하여 프로젝트 루트를 추론한다. 별도의 파라미터 추가 없이 기존 정보만으로 동작한다.

## 3. 실행 체크리스트

> 총 3개 Step

### Step 1: opal-task-agent 프로젝트 컨텍스트 로드 단계 추가
- [ ] 완료
- **파일**: `agents/opal-task-agent/AGENT.md`
- **작업 내용**:
  - 실행 프로세스 Step 2(스킬 Read)와 Step 3(페르소나 Read) 사이에 "프로젝트 컨텍스트 로드" 단계를 삽입
  - 이후 Step 번호를 +1 시프트 (기존 3→4, 4→5, 5→6, 6→7)
  - 스킬 유형 판별 기준(op-dev-* vs op-task-*), 로딩할 문서 목록, 스킵 조건을 명시
  - 프로젝트 루트 추론 방식 기술
- **완료 기준**: 실행 프로세스가 7단계이며, Step 3이 프로젝트 컨텍스트 로드 단계이다. docs/ 미존재 시 스킵 조건이 명시되어 있다.
- **테스트**: AGENT.md를 읽고 (1) Step 3에 컨텍스트 로드가 있는지 (2) 번호가 1~7 연속인지 (3) 스킵 조건이 명시되어 있는지 확인
- **의존**: 없음

### Step 2: opal-task-qa-agent 프로젝트 컨텍스트 로드 단계 추가
- [ ] 완료
- **파일**: `agents/opal-task-qa-agent/AGENT.md`
- **작업 내용**:
  - 실행 프로세스 Step 2(qa_skill Read)와 Step 3(페르소나/가이드 Read) 사이에 "프로젝트 컨텍스트 로드" 단계를 삽입
  - 이후 Step 번호를 +1 시프트 (기존 3→4, 4→5, 5→6)
  - qa_skill 유형 판별 기준(op-dev-qa vs op-task-qa), 로딩할 문서 목록, 스킵 조건을 명시
  - 프로젝트 루트 추론 방식 기술
- **완료 기준**: 실행 프로세스가 6단계이며, Step 3이 프로젝트 컨텍스트 로드 단계이다. docs/ 미존재 시 스킵 조건이 명시되어 있다.
- **테스트**: AGENT.md를 읽고 (1) Step 3에 컨텍스트 로드가 있는지 (2) 번호가 1~6 연속인지 (3) 스킵 조건이 명시되어 있는지 확인
- **의존**: Step 1 (패턴 참조)

### Step 3: op-dev-test-agent 프로젝트 컨텍스트 로드 단계 추가
- [ ] 완료
- **파일**: `agents/op-dev-test-agent/AGENT.md`
- **작업 내용**:
  - 실행 프로세스 Step 2(TEST-SCENARIO Read)와 Step 3(시나리오 실행) 사이에 "프로젝트 컨텍스트 로드" 단계를 삽입
  - 이후 Step 번호를 +1 시프트 (기존 3→4, 4→5, ..., 8→9)
  - 항상 코드 관련 문서 로드 (코드 테스트 전용 에이전트이므로)
  - 프로젝트 루트 추론 방식 기술
- **완료 기준**: 실행 프로세스가 9단계이며, Step 3이 프로젝트 컨텍스트 로드 단계이다. docs/ 미존재 시 스킵 조건이 명시되어 있다.
- **테스트**: AGENT.md를 읽고 (1) Step 3에 컨텍스트 로드가 있는지 (2) 번호가 1~9 연속인지 (3) 스킵 조건이 명시되어 있는지 확인
- **의존**: Step 1 (패턴 참조)

## 4. QA 체크리스트

### 기능 테스트
- [ ] opal-task-agent의 실행 프로세스에 "프로젝트 컨텍스트 로드" 단계가 존재한다
- [ ] opal-task-qa-agent의 실행 프로세스에 "프로젝트 컨텍스트 로드" 단계가 존재한다
- [ ] op-dev-test-agent의 실행 프로세스에 "프로젝트 컨텍스트 로드" 단계가 존재한다
- [ ] 스킬 유형별 로딩 문서 분기가 명확히 기술되어 있다 (op-dev-* vs op-task-*)
- [ ] docs/PROJECT.md는 모든 스킬에서 필수로 읽도록 되어 있다 (존재 시)
- [ ] docs/ARCHITECTURE.md, docs/CONVENTIONS.md는 코드 관련 스킬에서만 읽도록 되어 있다
- [ ] docs/FRONTEND.md, docs/BACKEND.md는 해당 도메인에서만 읽도록 되어 있다
- [ ] docs/ 미존재 시 스킵 조건이 명시되어 있다 (하위 호환)

### 일관성 테스트
- [ ] 3개 에이전트의 컨텍스트 로드 단계가 동일한 패턴을 따른다
- [ ] 기존 실행 프로세스의 순서가 유지된다 (삽입만, 기존 순서 변경 없음)
- [ ] Step 번호가 연속적이다 (빈 번호 없음)
- [ ] 결과 반환 형식, model override, 행동 규칙 등 기존 섹션이 변경 없이 유지된다
- [ ] 에이전트 AGENT.md만 수정하고 스킬 SKILL.md는 변경하지 않는다 (제약 조건)

### 문서 품질
- [ ] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [ ] kebab-case 파일/폴더 네이밍을 따르는가
- [ ] YAML frontmatter가 기존과 동일하게 유지되는가

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| 프로젝트 루트 추론 실패 (비표준 폴더 구조) | 컨텍스트 로드 실패 | docs/ 탐색 실패 시 스킵 — 기존 동작으로 폴백 |
| docs/PROJECT.md가 매우 큰 경우 컨텍스트 낭비 | 워커 컨텍스트 윈도우 소비 | PROJECT.md는 프로젝트 정의 SSOT이므로 크기가 제한적. 현재 체계에서는 문제 없음 |
| 오케스트레이터가 이미 프로젝트 컨텍스트를 전달한 경우 중복 로딩 | 불필요한 Read | 영향 미미 — Read는 멱등. 중복 읽기가 정보 누락보다 낫다 |
