# ANALYSIS: dev-task-pilot 모드별 스킬/에이전트 분리 리팩토링

> 작성일: 2026-03-21 | 참조: TASK.md

## 1. 기존 코드 분석

### 관련 파일 목록

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| skills/dev-task-pilot/SKILL.md | 단일 통합 SKILL, 모드별 분기 로직 포함 (1039줄) | 분리 대상 |
| skills/dev-task-pilot/references/*.md | 6개 가이드 (analysis, plan, execute, execute-plan, test-scenario, todo) | 신규 가이드 추가 |
| agents/claude/dtp-agent/AGENT.md | 모든 모드/단계 처리하는 워커 에이전트 | 제거 후 모드별 분리 |
| agents/claude/dtp-qa/AGENT.md | ANALYSIS/PLAN 단계 QA 담당 | 분리 필요 |
| agents/claude/dtp-planner/AGENT.md | TODO 복잡 모드 Part C 설계 | 리네임 대상 |
| agents/claude/dtp-test/AGENT.md | EXECUTE 후 테스트 검증 | 리네임 대상 |
| agents/cursor/dtp-*.md | Cursor 플랫폼 에이전트 (4개) | 분리 필요 |
| agents/antigravity/dtp-*/SKILL.md | Antigravity 플랫폼 에이전트 (4개) | 분리 필요 |
| opal/core/references/agents.md | 에이전트 레지스트리 | 갱신 필요 |
| CLAUDE.md | 프로젝트 설명서 | 갱신 필요 |

### 현재 구현 패턴

**단일 SKILL.md의 구조 (1039줄):**

```
SKILL.md
├── Metadata (name, description)
├── 구현 금지 원칙 (사전 규칙)
├── 워크플로우 개요 (오케스트레이터 모델)
├── 모드 판별 규칙
├── 오케스트레이터-워커 실행 모델
├── QA/Planner/Test 에이전트 호출 규칙 (공통)
├── 작업 유형 판별
├── 산출물 저장 구조 (Full/Short)
├── 사전 점검: Git 커밋
├── STEP 1: TASK (공통)
├── 분기: Full Task 경로
│   ├── STEP 2 (Full): ANALYSIS
│   ├── STEP 3 (Full): PLAN
│   ├── STEP 4 (Full): TODO
│   └── STEP 5 (Full): EXECUTE
├── 분기: Short Task 경로
│   ├── STEP 2 (Short): PLAN 통합
│   ├── STEP 3 (Short): TEST-SCENARIO
│   └── STEP 4 (Short): EXECUTE
└── 공통 규칙
    ├── 완료 리포트 (DONE.md)
    ├── STATE.md 체크포인트
    └── 오케스트레이터 보고 형식
```

**모드별 분기 로직:**
- 모드 판별 규칙에서 Full Task (예상 변경 파일 ≥10개, 다단계 기술 의사결정, 다중 모듈 연쇄 영향) vs Short Task 결정
- Full Task: 5단계 (TASK → ANALYSIS → PLAN → TODO → EXECUTE)
- Short Task: 3단계 (TASK → PLAN 통합 → TEST-SCENARIO → EXECUTE)
- Wireframe UI 모드: 아직 구현되지 않음

**워커 에이전트 구조:**
- `dtp-agent`: 모든 단계(ANALYSIS/PLAN/TODO/EXECUTE)를 처리하는 단일 워커
  - ANALYSIS: analysis-guide.md 따름
  - PLAN (Full): plan-guide.md의 Full Task 섹션
  - PLAN (Short): plan-guide.md의 Short Task 섹션
  - TODO: todo-guide.md 따름
  - EXECUTE: execute-guide.md 따름
- 3플랫폼 에이전트 (Claude/Cursor/Antigravity)에서 동일하게 처리

### 의존성 맵

**SKILL.md가 참조하는 파일:**
- 6개 references/*.md 가이드 파일
- 프로젝트 CLAUDE.md (코드 컨벤션)

**SKILL.md를 참조하는 파일:**
- dtp-agent AGENT.md: "dev-task-pilot 스킬에 따라 디스패치"
- 사용자 프롬프트: 직접 호출

**에이전트 간 의존성:**
- 오케스트레이터(알투): dtp-agent 디스패치 → dtp-qa/dtp-planner/dtp-test 호출
- 워커(dtp-agent): references/ 가이드 읽음 → 산출물 작성 → 오케스트레이터 반환
- QA(dtp-qa): ANALYSIS.md / PLAN.md 검증 (readonly=true)
- Planner(dtp-planner): TODO.md Part A+B 확인 → Part C 생성 (readonly=true)
- Test(dtp-test): 코드 실행 후 TEST-SCENARIO.md 채움 (readonly=true)

### 현재 정의된 에이전트

**Claude Code 플랫폼:**
- `agents/claude/dtp-agent/AGENT.md`: 워커 (모든 모드/단계)
- `agents/claude/dtp-qa/AGENT.md`: QA 검증 (ANALYSIS/PLAN)
- `agents/claude/dtp-planner/AGENT.md`: 아키텍처 설계 (TODO Part C)
- `agents/claude/dtp-test/AGENT.md`: 테스트 검증 (EXECUTE 후)

**Cursor 플랫폼:**
- `agents/cursor/dtp-agent.md`: 워커 (모든 모드/단계)
- `agents/cursor/dtp-qa.md`: QA 검증
- `agents/cursor/dtp-planner.md`: 아키텍처 설계
- `agents/cursor/dtp-test.md`: 테스트 검증

**Antigravity 플랫폼:**
- `agents/antigravity/dtp-agent/SKILL.md`: 워커
- `agents/antigravity/dtp-qa/SKILL.md`: QA 검증
- `agents/antigravity/dtp-planner/SKILL.md`: 아키텍처 설계
- `agents/antigravity/dtp-test/SKILL.md`: 테스트 검증

---

## 2. 리팩토링 목표와 현재 상태 분석

### 요구사항 재검토

**R1-R4: 스킬 분리** (핵심)
- SKILL.md는 모드별 디스패치 로직 + 공통 규칙만 남김 (라우터 역할)
- modes/dev-full.md: Full Task 파이프라인 (ANALYSIS → PLAN → TODO → EXECUTE)
- modes/dev-short.md: Short Task 파이프라인 (PLAN 통합 → TEST-SCENARIO → EXECUTE)
- modes/wireframe-ui.md: 신규 Wireframe UI 파이프라인 (TASK → WIREFRAME → EXECUTE → QA)

**R5-R8: 에이전트 분리** (영향도 높음)
- dtp-agent 제거 → 3개 워커 에이전트로 분리
  - dtp-dev-full-agent: Full Task 전용 (ANALYSIS/PLAN/TODO/EXECUTE)
  - dtp-dev-short-agent: Short Task 전용 (PLAN/TEST-SCENARIO/EXECUTE)
  - dtp-wireframe-ui-agent: Wireframe UI 전용 (TASK/WIREFRAME/EXECUTE)
- dtp-qa 분리 → 2개 QA 에이전트
  - dtp-qa-dev-agent: Full/Short Task QA (ANALYSIS/PLAN 검증)
  - dtp-qa-wireframe-agent: Wireframe UI QA (WIREFRAME 검증)
- dtp-planner → dtp-action-plan-agent (리네임)
- dtp-test → dtp-dev-test-agent (리네임)

**R9-R10: 신규 References**
- references/wireframe-task-guide.md: TASK 단계 (환경 검토, 입력물 분석)
- references/wireframe-qa-guide.md: QA 검증 (빌드/린트 + wireframe↔코드 대조)

**R11-R12: 레지스트리 갱신**
- opal/core/references/agents.md: 새 에이전트 목록 (7개 → 9개)
- CLAUDE.md: 프로젝트 설명서 (에이전트 구조 갱신)

### 영향 범위

**직접 영향 (변경 필수):**
1. 스킬 분리: SKILL.md (1 → 4개), references/ (6 → 8개 가이드)
2. 에이전트 분리: 3플랫폼 × 9개 에이전트 = 27개 파일
   - Claude: 7개 (기존 4개 + 신규 3개)
   - Cursor: 7개 (기존 4개 + 신규 3개)
   - Antigravity: 7개 (기존 4개 + 신규 3개)
3. 레지스트리: agents.md, CLAUDE.md

**간접 영향 (호출 변경):**
- 사용자 프롬프트: "dev-task-pilot" 호출 → 모드에 따라 올바른 워커 선택 (오케스트레이터가 처리)
- 오케스트레이터(SKILL.md의 STEP 1 로직): 모드 판별 후 올바른 워커/QA 에이전트 선택

**제약 조건 준수:**
- 기존 Full Task / Short Task 동작 영향 없음
  - 사용자 입장: 동일하게 "dev-task-pilot" 호출하면 자동으로 모드 선택
  - 오케스트레이터: 라우팅 로직만 개선
- 3플랫폼 에이전트 포맷 규칙 준수
  - Claude: AGENT.md (디렉토리 구조)
  - Cursor: .md 플랫 파일
  - Antigravity: SKILL.md 스킬 형식
- references/ 기존 가이드 수정 없음 (새 가이드만 추가)

---

## 3. 설계 결정: 파일 구조

### 안내 문제: 에이전트 탐색 경로

**현재 상황:**
- SKILL.md에서 에이전트를 탐색할 때 에이전트 이름을 지정 (예: "dtp-agent", "dtp-qa")
- 탐색 경로: 프로젝트 로컬 → 홈 디렉토리 (6개 경로)

**분리 후 문제:**
- 새 워커 3개 (dtp-dev-full-agent, dtp-dev-short-agent, dtp-wireframe-ui-agent)를 어떻게 선택?
  - STEP 1에서 모드 판별 후 상황에 맞는 워커를 디스패치해야 함
  - 오케스트레이터(SKILL.md)가 모드별로 올바른 에이전트 이름을 지정

**솔루션:**
1. SKILL.md (라우터)에서 모드 판별 후 워커 에이전트명 결정:
   ```
   Full Task 판별 → "dtp-dev-full-agent" 디스패치
   Short Task 판별 → "dtp-dev-short-agent" 디스패치
   Wireframe UI 판별 → "dtp-wireframe-ui-agent" 디스패치
   ```

2. 각 워커 에이전트 디렉토리는 기존 구조 유지:
   ```
   agents/claude/dtp-dev-full-agent/AGENT.md
   agents/claude/dtp-dev-short-agent/AGENT.md
   agents/claude/dtp-wireframe-ui-agent/AGENT.md
   agents/cursor/dtp-dev-full-agent.md
   agents/cursor/dtp-dev-short-agent.md
   agents/cursor/dtp-wireframe-ui-agent.md
   agents/antigravity/dtp-dev-full-agent/SKILL.md
   agents/antigravity/dtp-dev-short-agent/SKILL.md
   agents/antigravity/dtp-wireframe-ui-agent/SKILL.md
   ```

### 신규 스킬 구조

```
skills/dev-task-pilot/
├── SKILL.md                     ← 라우터 (모드 판별 + 공통 규칙)
├── modes/
│   ├── dev-full.md              ← Full Task 파이프라인
│   ├── dev-short.md             ← Short Task 파이프라인
│   └── wireframe-ui.md          ← Wireframe UI 파이프라인 (신규)
└── references/
    ├── analysis-guide.md        ← 기존 (수정 없음)
    ├── plan-guide.md            ← 기존 (수정 없음)
    ├── execute-guide.md         ← 기존 (수정 없음)
    ├── execute-plan-guide.md    ← 기존 (수정 없음)
    ├── test-scenario-guide.md   ← 기존 (수정 없음)
    ├── todo-guide.md            ← 기존 (수정 없음)
    ├── wireframe-task-guide.md  ← 신규
    └── wireframe-qa-guide.md    ← 신규
```

**각 파일의 역할:**
- **SKILL.md**: 오케스트레이터 핵심 로직 (모드 판별, 워커 디스패치, 공통 규칙)
- **modes/*.md**: 모드별 파이프라인 상세 정의
  - 각 모드의 STEP 시퀀스, 워커 디스패치 프롬프트, 보고 형식
  - 기존 SKILL.md의 "Full Task 경로" / "Short Task 경로" 섹션 추출
- **references/*.md**: 단계별 상세 가이드 (변경 없음)

---

## 4. 구현 복잡도와 리스크

### 파일 작업 규모

**신규 생성:**
- 스킬: SKILL.md (라우터 축약) + modes/dev-full.md + modes/dev-short.md + modes/wireframe-ui.md (4개)
- References: wireframe-task-guide.md + wireframe-qa-guide.md (2개)
- 에이전트: 3플랫폼 × (3 워커 + 1 QA-Wireframe + 2 리네임) = 18개
- 총 24개 신규 파일 + 기존 리팩토링

**수정 대상:**
- SKILL.md (1039줄): 약 500줄로 축약 (분기 로직 제거, 라우팅만 남김)
- CLAUDE.md: 에이전트 목록 업데이트
- opal/core/references/agents.md: 에이전트 레지스트리 갱신

**삭제 대상:**
- 없음 (기존 에이전트는 리네임 또는 분리, 직접 삭제 없음)

### 기술 리스크

**리스크 1: 오케스트레이터 라우팅 로직 오류**
- 위험: 잘못된 워커가 선택되면 전체 파이프라인 실패
- 완화: SKILL.md의 모드 판별 로직 재검증, 각 모드별 테스트

**리스크 2: 에이전트 파일 구조 불일치 (3플랫폼)**
- 위험: Claude/Cursor/Antigravity 포맷 차이로 인한 로드 오류
- 완화: 각 플랫폼별 가이드 준수, 필드명 표준화

**리스크 3: Wireframe UI 모드 미정의**
- 위험: wireframe-builder / ui-designer 스킬과의 연동 명확성 부족
- 영향: R13-R16 구현 시 상세화 필요
- 예상: 이번 ANALYSIS 단계에서는 구조만 정의, 상세 내용은 EXECUTE에서

**리스크 4: 기존 워커 컨텍스트 loss**
- 위험: 모드별 워커 분리로 코드 분석 컨텍스트 재사용성 감소
- 완화: 각 워커는 이전 산출물(.md)을 읽어서 컨텍스트 복원 가능 (resume 불필요)

---

## 5. 핵심 발견 사항

### 1. 모드별 분리는 아키텍처 개선 (기능 확장 아님)
- 기존 Full/Short Task 로직은 변경되지 않음
- 신규 Wireframe UI 모드 추가 시에도 기존 코드 영향 최소화

### 2. Wireframe UI 모드의 파이프라인은 기존과 다름
- 기존: ANALYSIS → PLAN → TODO → EXECUTE (개발 중심)
- 신규: TASK → WIREFRAME → EXECUTE → QA (설계 중심)
- wireframe-builder / ui-designer 스킬 연동 필요

### 3. 에이전트 분리의 핵심 이점
- **워커 전문화**: 각 워커가 특정 모드만 담당하여 프롬프트 최적화 가능
- **메모리 효율**: 큰 전체 AGENT.md 대신 모드별 소형 에이전트 로드
- **유지보수성**: 모드 추가/변경 시 새 에이전트만 추가, 기존 코드 수정 불필요

### 4. QA 에이전트 분리의 필요성
- 현재 dtp-qa: Full/Short Task 모두 처리 (ANALYSIS/PLAN 검증)
- 신규 dtp-qa-wireframe-agent: Wireframe 설계 산출물 검증 (WIREFRAME/QA)
- 검증 기준이 완전히 다르므로 분리 필수

### 5. 에이전트 이름 변경의 의미
- dtp-planner → dtp-action-plan-agent: 역할 명확화 (TODO Part C, 실행 아키텍처)
- dtp-test → dtp-dev-test-agent: 모드 명시 (개발 태스크 전용)

---

## 6. 구현 순서 제안

**Phase 1: 스킬 구조 정의** (이번 PLAN 단계)
1. modes/dev-full.md 작성 (기존 SKILL.md "Full Task 경로" 추출)
2. modes/dev-short.md 작성 (기존 SKILL.md "Short Task 경로" 추출)
3. modes/wireframe-ui.md 개요 작성 (상세는 EXECUTE에서)

**Phase 2: 에이전트 생성** (EXECUTE)
1. dtp-dev-full-agent (3플랫폼 × 1)
2. dtp-dev-short-agent (3플랫폼 × 1)
3. dtp-wireframe-ui-agent (3플랫폼 × 1)
4. dtp-qa-dev-agent (3플랫폼 × 1) - dtp-qa 복사/수정
5. dtp-qa-wireframe-agent (3플랫폼 × 1) - 신규
6. dtp-action-plan-agent (3플랫폼 × 1) - dtp-planner 리네임
7. dtp-dev-test-agent (3플랫폼 × 1) - dtp-test 리네임

**Phase 3: 가이드 추가** (EXECUTE)
- references/wireframe-task-guide.md
- references/wireframe-qa-guide.md

**Phase 4: SKILL.md 개선** (EXECUTE)
- 라우팅 로직 개선 (모드별 워커 선택)
- 기존 STEP 섹션을 modes/ 참조로 변경
- 크기 축약 (1039줄 → 500줄)

---

## 7. 제약과 주의사항

### 제약 조건
- [ ] 기존 Full Task / Short Task 사용자 경험 변경 금지
- [ ] 3플랫폼(Claude, Cursor, Antigravity) 포맷 규칙 준수
- [ ] references/ 기존 가이드 수정 금지 (신규만 추가)
- [ ] COMPONENT-CATALOG.md 생성 금지

### 구현 주의사항
1. **에이전트 탐색 경로**: 새 에이전트명으로 SKILL.md에서 올바르게 지정
2. **모드 판별 로직**: STEP 1에서 정확하게 판별 후 워커 선택
3. **Wireframe UI 상세화**: 이번 ANALYSIS에서는 구조만, 상세는 PLAN/EXECUTE에서
4. **테스트 범위**: 분리 후 각 모드별 엔드-투-엔드 테스트 필수

---

## 8. 다음 단계

**PLAN 단계:**
1. modes/ 구조 정의 (각 파일의 STEP 시퀀스, 워커 프롬프트)
2. 에이전트 목록 확정 (9개 에이전트 정확한 이름/역할)
3. Wireframe UI 모드 상세 설계 (TASK → WIREFRAME → EXECUTE → QA 파이프라인)
4. 레지스트리 갱신 계획 (agents.md, CLAUDE.md 변경 항목)

**EXECUTE 단계:**
1. 스킬 파일 생성/수정
2. 에이전트 파일 생성 (3플랫폼)
3. 레지스트리 갱신
4. 통합 테스트
