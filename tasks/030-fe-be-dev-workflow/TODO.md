# TODO: FE/BE 개발 워크플로우 체계화

> 작성일: 2026-03-22 | 참조: PLAN.md

## Part A: 실행 체크리스트

### Phase 1: skills.md 기술 스택 매핑

- [x] **Step 1** [공통] `opal/core/references/skills.md`에 "기술 스택별 추천 스킬" 섹션 추가
  - FE 매핑: React, Next.js, shadcn/ui, Vue/Nuxt (식별 조건 + 추천 스킬 + MCP)
  - BE 매핑: Python, FastAPI, Django, Java/Spring, Kotlin, Go, Node.js/Express (식별 조건 + 추천 스킬 + MCP)
  - 공통 매핑: code-review, webapp-testing, ui-designer
  - 파일: `opal/core/references/skills.md`

### Phase 2: analysis-guide.md 수정

- [x] **Step 2** [공통] `references/analysis-guide.md` 0단계 신설 + 기존 단계 보강
  - 0단계: docs/ 참조 (없으면 opi 제안) + .opal/AGENT.md + 기술 스택 식별 + skills.md/mcps.md 참조
  - 1단계: 실데이터 샘플링 (데이터 파이프라인 시 첫 5행) 추가
  - 2단계: context7 MCP 의무 호출 + 커뮤니티 검색 규칙 추가
  - 3단계: 아키텍처 정합성 (docs/ 기반) 추가
  - 출력 형식: "6. 기술 컨텍스트" 섹션 추가
  - 품질 체크리스트: 3항목 추가
  - 파일: `skills/dev-task-pilot/references/analysis-guide.md`

### Phase 3: plan-guide.md 수정

- [x] **Step 3** [공통] `references/plan-guide.md` Full Task + Short Task 보강
  - Full 0단계: docs/ + ANALYSIS "기술 컨텍스트" → 추천 스킬 Read → 설계 반영
  - Full 2단계 뒤: [FE]/[BE]/[공통] 영역 태그 규칙
  - Full 3단계: FE 설계 시 ui-designer 화면 유형별 패턴 참조
  - Full 5단계 뒤: execution-plan.json 생성 규칙 (스키마 정의)
  - Full 출력 형식: "7. 참조 도구" + execution-plan.json 참조
  - Full 품질 체크리스트: 3항목 추가
  - Short: 0단계 동일 + execution-plan.json (FE/BE 시)
  - 파일: `skills/dev-task-pilot/references/plan-guide.md`

### Phase 4: execute-guide.md 수정

- [x] **Step 4** [공통] `references/execute-guide.md` 금지 행동 + 가드레일 추가
  - 금지 행동 섹션: PLAN 밖 변경 금지, 설계 임의 변경 금지, 영역 침범 금지, 미승인 패키지 금지
  - 가드레일 판단 기준: 즉시 멈춤 vs 진행 후 보고
  - 보안 가드레일: 시크릿, SQL injection, 민감 파일, 무제한 입력
  - execution-plan.json 기반 실행 규칙: 입력 우선순위, JSON 읽기, FE screen → ui-designer 연결
  - 품질 체크리스트: 3항목 추가
  - 파일: `skills/dev-task-pilot/references/execute-guide.md`

### Phase 5: SKILL.md (dtp) 산출물 추가

- [x] **Step 5** [공통] `SKILL.md` (dev-task-pilot) 산출물 구조 갱신
  - Full/Short Task 산출물에 execution-plan.json 추가
  - 프로젝트 컨텍스트 로딩에 "기술 스택 사전 판별" 추가
  - 파일: `skills/dev-task-pilot/SKILL.md`

### Phase 6: modes/ FE/BE 병렬 디스패치

- [x] **Step 6** [공통] `modes/dev-full.md` FE/BE 병렬 디스패치
  - ANALYSIS 워커 프롬프트: skills.md 참조 추가
  - PLAN 워커 프롬프트: execution-plan.json 산출물 추가
  - EXECUTE 단계: execution-plan.json 기반 FE/BE 병렬 디스패치 규칙
  - FE/BE 서브에이전트 프롬프트 템플릿
  - fallback: JSON 없으면 기존 TODO.md 기반
  - 파일: `skills/dev-task-pilot/modes/dev-full.md`

- [x] **Step 7** [공통] `modes/dev-short.md` — Full과 동일 수준 적용
  - Short는 단계 축약이지 품질 축약이 아님 — Full과 동일한 업무 절차
  - PLAN 통합 프롬프트: skills.md/mcps.md 참조 + execution-plan.json 산출물 추가
  - EXECUTE: FE/BE 병렬 디스패치 규칙 (Full과 동일)
  - FE/BE 서브에이전트 프롬프트 (Full과 동일)
  - fallback: JSON 없으면 기존 PLAN.md 체크리스트 기반
  - 파일: `skills/dev-task-pilot/modes/dev-short.md`

### Phase 7: ui-designer 구조 개선

- [x] **Step 8** [FE] `ui-designer/SKILL.md` → 모드 라우터 재구성
  - 기존 Phase 1~5를 modes/scaffold.md로 이동 준비
  - SKILL.md: frontmatter 확장 + 모드 판별 규칙 + 공통 규칙 유지 (shadcn Critical Rules, 화면 유형별 패턴, wireframe.md 스키마)
  - 파일: `skills/ui-designer/SKILL.md`

- [x] **Step 9** [FE] `ui-designer/modes/scaffold.md` 신규 생성
  - 기존 SKILL.md의 Phase 1~5 + 완료 보고 + web-artifacts-builder 연계 이동
  - 공통 규칙은 "SKILL.md 참조"로 연결
  - 파일: `skills/ui-designer/modes/scaffold.md`

- [x] **Step 10** [FE] `ui-designer/modes/plan-driven.md` 신규 생성
  - 입력: execution-plan.json screen 객체
  - Step 1: 프로젝트 구조 파악
  - Step 2: action별 실행 (new/modify)
  - Step 3: shadcn 컴포넌트 확인 (MCP 활용)
  - Step 4: 검증 (SKILL.md shadcn Critical Rules + 패턴 일관성)
  - 파일: `skills/ui-designer/modes/plan-driven.md`

### Phase 8: dtp-dev-test-agent 보강

- [x] **Step 11** [공통] `dtp-dev-test-agent/AGENT.md` 스모크 테스트 + code-review
  - Step 1.5: 스모크 테스트 (서버 기동 → health 체크)
  - Step 4 보강: code-review 스킬 연계 (N+1, Runtime errors, 성능)
  - 판정 기준: 스모크 Fail = Critical Fail
  - 파일: `agents/dtp-dev-test-agent/AGENT.md`

---

## Part B: QA 체크리스트

### B-1: 기능 검증

- [ ] skills.md 기술 스택 매핑이 기존 스킬 목록과 정합한가?
- [ ] analysis-guide.md 0단계가 docs/ 없는 프로젝트에서도 동작하는가? (fallback)
- [ ] execution-plan.json 스키마가 plan-guide ↔ execute-guide ↔ modes/ 간 일치하는가?
- [ ] ui-designer plan-driven screen 입력이 execution-plan.json frontend.screens 스키마와 일치하는가?
- [ ] FE/BE 병렬 디스패치가 단일 영역(FE만/BE만) 시 순차 fallback 되는가?

### B-2: 회귀 검증

- [ ] 기존 dtp Full Task 파이프라인 (execution-plan.json 없이) 동작하는가?
- [ ] 기존 dtp Short Task 파이프라인 동작하는가?
- [ ] Wireframe UI 모드가 영향받지 않는가?
- [ ] ui-designer scaffold 모드 (modes/scaffold.md 이동 후) 동작하는가?
- [ ] dtp-dev-test-agent 기존 Step 1~6이 영향받지 않는가?

### B-3: 코드 품질

- [ ] 모든 파일 간 참조 경로가 정확한가?
- [ ] JSON 스키마 예시가 유효한 JSON인가?
- [ ] 마크다운 포맷팅이 일관되는가?

### B-4: 보안

- [ ] execute-guide.md 보안 가드레일이 명확한가?
- [ ] 시크릿 하드코딩 감지 패턴이 구체적인가?
