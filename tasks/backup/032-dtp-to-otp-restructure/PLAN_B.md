# PLAN_B: dev-task-pilot 컴포지션 아키텍처 전환 (Skill Spec 기반 일괄 생성)

> 작성일: 2026-03-26 | 참조: TASK.md, ANALYSIS.md, PLAN.md
> 입력: TASK.md, ANALYSIS.md
> 출력: PLAN_B.md

## 변경 사유

PLAN.md는 "알투가 직접 작성"하는 실행 계획이었다. PLAN_B는 **opal-skill-creator를 활용하여 11개 스킬을 생성**하는 실행 계획이다. Skill Spec 사전 작성으로 Phase 1 대화 라운드를 최소화하면서 프레임워크 프로세스를 준수한다.

---

## 1. 실행 전략 개요

```
Phase A: Skill Spec 작성 (알투 직접)
    ↓
Phase B: 단계 스킬 8개 일괄 생성 (워커 × opal-skill-creator)
    ↓
Phase C: 오케스트레이터 3개 생성 (워커 × opal-skill-creator)
    ↓
Phase D: 에이전트 3개 작성 (알투 직접)
    ↓
Phase E: 레지스트리 + 프로젝트 문서 갱신 (알투 직접)
    ↓
Phase F: 오케스트레이터 테스트 + Description 최적화
```

---

## 2. Phase A: Skill Spec 작성

알투가 `tasks/032-dtp-to-otp-restructure/dtp-skill-specs.md`를 작성한다. 이 문서는 11개 스킬의 opal-skill-creator Phase 1 답변을 사전에 담는다.

### 각 스킬 Spec 항목

```markdown
## {skill-name}

### Capture Intent
- **목적**: {이 스킬이 뭘 하는가}
- **트리거**: {언제 호출되는가 — 오케스트레이터 디스패치 / 사용자 직접}
- **출력 형식**: {산출물 형식과 구조}

### Input/Output Contract
- **필수 입력**: {입력 파일/데이터}
- **선택 입력**: {있으면 품질 향상되는 입력}
- **보장 출력**: {항상 생성하는 산출물}

### Content Source
- **기존 파일**: {이관할 기존 dtp 파일 경로}
- **변경 사항**: {기존 대비 추가/수정/삭제 내용}

### Persona
- **페르소나**: {이름}
- **Principles**: {5-7개}
- **행동 규칙**: {3-5개}

### Dependencies
- **활용 스킬**: {커뮤니티/OPAL 스킬 목록}
- **활용 MCP**: {MCP 서버 목록}

### Edge Cases
- {엣지 케이스 1}
- {엣지 케이스 2}
```

### Spec 대상 (11개)

| # | 스킬 | 콘텐츠 소스 |
|---|------|-----------|
| 1 | dtp-task | SKILL.md §STEP 1 + wireframe-task-guide.md |
| 2 | dtp-analysis | analysis-guide.md + 기술 컨텍스트 3곳 통합 |
| 3 | dtp-plan | plan-guide.md (Full+Short 통합 → 입력 기반 분기) |
| 4 | dtp-todo | todo-guide.md + execute-plan-guide.md |
| 5 | dtp-test-scenario | test-scenario-guide.md |
| 6 | dtp-execute | execute-guide.md + checkpoint-guide.md |
| 7 | dtp-wireframe | wireframe-ui.md WIREFRAME 단계 |
| 8 | dtp-qa | dtp-qa-dev-agent + dtp-qa-wireframe-agent + wireframe-qa-guide.md |
| 9 | dtp-dev | SKILL.md 공통 규칙 + modes/dev-full.md 파이프라인 |
| 10 | dtp-dev-short | SKILL.md 공통 규칙 + modes/dev-short.md 파이프라인 |
| 11 | dtp-dev-wf | SKILL.md 공통 규칙 + modes/wireframe-ui.md 파이프라인 |

---

## 3. Phase B: 단계 스킬 8개 일괄 생성

각 단계 스킬에 대해 워커를 디스패치하여 opal-skill-creator 프로세스를 수행한다.

### 워커 디스패치 프롬프트

```
opal-skill-creator 스킬을 사용하여 아래 스킬을 생성하라.

**생성 모드**: 신규 생성
**스킬 유형**: 프레임워크 스킬

**Skill Spec** (Phase 1 사전 답변):
{dtp-skill-specs.md의 해당 스킬 섹션 전체}

**콘텐츠 소스** (기존 파일, Read하여 참조):
{기존 reference 파일 경로}

**OPAL 규칙 (Phase 1 컨텍스트)**:
- 한국어 본문, 영어 코드/필드명
- 명령형(imperative) 문체
- SKILL.md 500줄 이하
- 필요 시 references/ 하위에 상세 가이드 분리
- personas/ 하위에 페르소나 파일 배치

**Phase 1 진행**:
- Capture Intent: Spec에서 이미 답변됨 → 확인만 하고 진행
- Interview: Spec의 Edge Cases + Dependencies로 대체 → 추가 질문 있으면 Spec 보강
- Write SKILL.md: 콘텐츠 소스를 기반으로 새 구조에 맞게 재작성
- Test Cases: 입출력 검증 테스트 2개 작성 (Spec의 Input/Output Contract 기반)
- Running: (스킵 — Phase F에서 통합 테스트)
- Improving: (스킵 — Phase F에서 통합 개선)

**Phase 2 진행**:
- 디렉토리: skills/{skill-name}/ 하위에 배치
- frontmatter: name, description ("반드시 이 스킬을 사용해야 하는 상황:" 패턴 포함)
- 레지스트리: (스킵 — Phase E에서 일괄 등록)
- 버전 태깅: v1.0 + 변경이력 테이블
- 에이전트: (스킵 — Phase D에서 별도 생성)
```

### 실행 순서

단계 스킬 8개는 상호 독립이므로 **병렬 디스패치 가능**:

```
Batch 1 (병렬):
  워커 1 → dtp-task
  워커 2 → dtp-analysis
  워커 3 → dtp-plan
  워커 4 → dtp-todo
  워커 5 → dtp-test-scenario
  워커 6 → dtp-execute
  워커 7 → dtp-wireframe
  워커 8 → dtp-qa
```

> 플랫폼 제약으로 병렬이 불가하면 순차 실행. 순서 무관.

### 워커 완료 시 알투 확인

각 워커 완료 후 알투가 확인:
- [ ] SKILL.md <500줄인가
- [ ] references/ 파일이 생성되었는가
- [ ] personas/ 파일이 생성되었는가
- [ ] frontmatter "반드시 이 스킬을 사용해야 하는 상황:" 패턴 존재
- [ ] 버전 v1.0 + 변경이력 테이블 존재
- [ ] 입출력 검증 테스트 2개 작성됨

---

## 4. Phase C: 오케스트레이터 3개 생성

단계 스킬이 완성된 후, 오케스트레이터를 생성한다. 오케스트레이터는 단계 스킬의 **실제 경로**를 참조해야 하므로 Phase B 이후에 수행.

### 워커 디스패치 프롬프트

Phase B와 동일 구조. 추가 컨텍스트:

```
**추가 컨텍스트**:
- 단계 스킬 목록과 경로:
  - dtp-task: skills/dtp-task/SKILL.md
  - dtp-analysis: skills/dtp-analysis/SKILL.md
  - ...
- 각 단계 스킬의 입출력 계약 (Spec 참조)
- 파이프라인 정의 (PLAN.md §3.5 참조)
```

### 실행 순서

```
Batch 2 (순차 권장 — 파이프라인 참조 관계):
  워커 9  → dtp-dev (Full, 모든 단계 스킬 참조)
  워커 10 → dtp-dev-short (dtp-dev 기반, 단계 생략 차이)
  워커 11 → dtp-dev-wf (별도 파이프라인)
```

### 오케스트레이터 핵심 포함 사항

| 항목 | 내용 |
|------|------|
| 파이프라인 정의 | 단계 스킬 호출 순서 + 조건부 분기 |
| 디스패치 프롬프트 템플릿 | 각 단계별 워커 프롬프트 |
| 공통 규칙 | 구현 금지 원칙, Git 사전 점검 |
| 게이트 체크포인트 | 단계별 사용자 보고 + 승인 |
| STATE.md 관리 | 오케스트레이터 전용 갱신 규칙 |
| QA/Test 호출 규칙 | 어떤 단계 후 어떤 워커 호출 |
| 에스컬레이션 (dtp-dev-short) | Full 전환 조건 |

---

## 5. Phase D: 에이전트 3개 작성

알투가 직접 작성. opal-skill-creator는 에이전트 생성에 특화되지 않으므로 직접이 효율적.

| 에이전트 | 역할 | 기반 |
|---------|------|------|
| dtp-worker | 범용 워커: 단계 스킬 SKILL.md Read → 실행 | 기존 dtp-dev-agent 단순화 |
| dtp-qa-worker | QA 워커: dtp-qa 스킬 Read → 검증 | 기존 dtp-qa-dev-agent + dtp-qa-wireframe-agent 통합 |
| dtp-test-worker | Test 워커: TEST-SCENARIO.md 기반 동적 검증 | 기존 dtp-dev-test-agent 이관 |

---

## 6. Phase E: 레지스트리 + 프로젝트 문서 갱신

### 레지스트리

| 대상 | 추가 | 제거 |
|------|------|------|
| `opal/core/references/skills.md` | dtp 스킬 11개 | dev-task-pilot |
| `opal/core/references/agents.md` | dtp 에이전트 3개 | dtp-*-agent 6개 |
| `~/.opal/references/skills.md` | 동기화 | 동기화 |
| `~/.opal/references/agents.md` | 동기화 | 동기화 |

### 스킬 레지스트리 등록 형식

```markdown
| 스킬 | 트리거 | 설명 |
|------|--------|------|
| dtp-dev | "개발해줘", "Full Task", "/dtp-dev", 코드 변경 수반 작업 (대규모) | Full Task 오케스트레이터 |
| dtp-dev-short | "수정해줘", "Short", "/dtp-dev-short", 코드 변경 수반 작업 (소규모) | Short Task 오케스트레이터 |
| dtp-dev-wf | "와이어프레임", "/dtp-dev-wf" | Wireframe UI 오케스트레이터 |
| dtp-task | (오케스트레이터 디스패치) | TASK.md 작성 |
| dtp-analysis | (오케스트레이터 디스패치) | 코드베이스 분석 |
| dtp-plan | (오케스트레이터 디스패치) | 구현 계획 |
| dtp-todo | (오케스트레이터 디스패치) | 실행 체크리스트 확장 |
| dtp-test-scenario | (오케스트레이터 디스패치) | 테스트 시나리오 작성 |
| dtp-execute | (오케스트레이터 디스패치) | 코드 실행 |
| dtp-wireframe | (오케스트레이터 디스패치) | 와이어프레임 생성 |
| dtp-qa | (오케스트레이터 디스패치) | QA 검증 |
```

### 프로젝트 문서

- `CLAUDE.md`: 소스 구조에 dtp 컴포지션 아키텍처 반영
- `.opal/MEMORY.md`: 작업 히스토리 갱신

---

## 7. Phase F: 오케스트레이터 테스트 + Description 최적화

### 테스트 프롬프트

| 스킬 | 테스트 프롬프트 | 검증 범위 |
|------|---------------|----------|
| dtp-dev | "회원가입 기능 개발해줘" | TASK → ANALYSIS 단계까지 |
| dtp-dev-short | "버튼 색상 변경해줘" | TASK → PLAN 단계까지 |
| dtp-dev-wf | "대시보드 와이어프레임 만들어줘" | TASK → WIREFRAME 단계까지 |

### 검증 포인트

- [ ] 트리거: 프롬프트로 올바른 오케스트레이터가 활성화되는가
- [ ] 디스패치: 워커에게 올바른 단계 스킬 경로가 전달되는가
- [ ] 페르소나: 워커가 personas/ 파일을 Read하는가
- [ ] 가이드: 워커가 references/ 파일을 Read하는가
- [ ] 산출물: 통일 형식 + 입출력 계약이 헤더에 명시되는가
- [ ] 게이트: 단계 완료 후 사용자에게 보고하는가

### Description 최적화

오케스트레이터 3개에 대해 skill-creator의 Description Optimization 수행:
1. 트리거 eval 쿼리 20개 생성 (should-trigger 10 + should-not-trigger 10)
2. 사용자 검토
3. 최적화 루프 실행
4. 최적 description 적용

### 개선 반복

테스트 결과에서 문제 발견 시:
1. 해당 단계 스킬 또는 오케스트레이터 수정
2. 재테스트
3. 캡틴 확인 후 완료

---

## 8. 실행 체크리스트 (전체)

### Phase A: Skill Spec
- [ ] A-1: dtp-skill-specs.md 작성 (11개 스킬 전체 명세)
- [ ] A-2: 캡틴 검토 + 승인

### Phase B: 단계 스킬 (8개)
- [ ] B-1: dtp-task (opal-skill-creator)
- [ ] B-2: dtp-analysis (opal-skill-creator)
- [ ] B-3: dtp-plan (opal-skill-creator)
- [ ] B-4: dtp-todo (opal-skill-creator)
- [ ] B-5: dtp-test-scenario (opal-skill-creator)
- [ ] B-6: dtp-execute (opal-skill-creator)
- [ ] B-7: dtp-wireframe (opal-skill-creator)
- [ ] B-8: dtp-qa (opal-skill-creator)
- [ ] B-9: 알투 일괄 검증 (500줄, frontmatter, 버전, 자기완결)

### Phase C: 오케스트레이터 (3개)
- [ ] C-1: dtp-dev (opal-skill-creator)
- [ ] C-2: dtp-dev-short (opal-skill-creator)
- [ ] C-3: dtp-dev-wf (opal-skill-creator)
- [ ] C-4: 알투 일괄 검증

### Phase D: 에이전트 (3개)
- [ ] D-1: dtp-worker
- [ ] D-2: dtp-qa-worker
- [ ] D-3: dtp-test-worker

### Phase E: 레지스트리 + 문서
- [ ] E-1: opal/core/references/skills.md 갱신
- [ ] E-2: opal/core/references/agents.md 갱신
- [ ] E-3: ~/.opal/references/ 동기화
- [ ] E-4: CLAUDE.md 소스 구조 갱신
- [ ] E-5: .opal/MEMORY.md 갱신

### Phase F: 테스트 + 최적화
- [ ] F-1: dtp-dev 테스트 (TASK → ANALYSIS)
- [ ] F-2: dtp-dev-short 테스트 (TASK → PLAN)
- [ ] F-3: dtp-dev-wf 테스트 (TASK → WIREFRAME)
- [ ] F-4: Description 최적화 (오케스트레이터 3개)
- [ ] F-5: 개선 반복 (필요 시)
- [ ] F-6: 캡틴 최종 승인

---

## 9. QA 체크리스트

### 스킬 품질
- [ ] 각 SKILL.md <500줄
- [ ] 각 스킬 자기완결 (외부 스킬 references 참조 없음)
- [ ] YAML frontmatter 규격 준수 ("반드시 이 스킬을 사용해야 하는 상황:")
- [ ] 버전 v1.0 + 변경이력 테이블
- [ ] 한국어 본문 / 영어 코드 규칙

### 구조 정합성
- [ ] 11개 스킬 디렉토리 존재
- [ ] 3개 에이전트 디렉토리 존재
- [ ] 레지스트리 등록 완전 (11 스킬 + 3 에이전트)
- [ ] 기존 항목 제거 완전 (dev-task-pilot + dtp-*-agent)
- [ ] CLAUDE.md 소스 구조 일치

### 동적 검증
- [ ] 오케스트레이터 3개 파이프라인 정상 동작
- [ ] 트리거 정확성 (should-trigger / should-not-trigger)
- [ ] 페르소나 주입 확인
- [ ] 커뮤니티 스킬/MCP 참조 확인

---

## 10. 리스크 및 대응

| 리스크 | 대응 |
|--------|------|
| opal-skill-creator 워커가 Spec을 무시하고 자체 Interview 시작 | 프롬프트에 "Spec이 Phase 1 답변임" 명시 + "추가 질문 시 Spec 참조" 지시 |
| 병렬 워커 8개가 동시에 레지스트리 수정 시도 | Phase B에서 레지스트리 수정 스킵, Phase E에서 일괄 수행 |
| 오케스트레이터 디스패치 프롬프트가 잘못된 스킬 경로 참조 | Phase C에서 실제 생성된 경로 확인 후 작성, Phase F에서 검증 |
| 기존 dtp 호출 시 레지스트리에 없어서 실패 | Phase E를 마지막에 수행, 그 전까지는 기존 레지스트리 유지 |

---

## 11. PLAN.md 대비 변경점 요약

| 항목 | PLAN.md | PLAN_B.md |
|------|---------|-----------|
| 생성 방법 | 알투 직접 작성 | opal-skill-creator 활용 |
| Phase 1 | 미적용 | Skill Spec 기반 풀 적용 |
| Phase 2 | 일부만 (frontmatter, 디렉토리) | 전체 (+ 버전 태깅) |
| 테스트 | R7에 간략 | Phase F에서 상세 (Description 최적화 포함) |
| 실행 구조 | 16 Step 순차 | 6 Phase (병렬 가능) |
| 산출물 | 스킬 파일만 | 스킬 파일 + dtp-skill-specs.md + 테스트 결과 |
