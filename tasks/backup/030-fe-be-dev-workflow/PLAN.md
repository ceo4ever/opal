# PLAN: FE/BE 개발 워크플로우 체계화

> 작성일: 2026-03-22 | 모드: Full Task | 참조: TASK.md, ANALYSIS.md
> 갱신: 2026-03-22 — 기존 문서 재활용 방향 반영

## 1. 구현 범위

### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `opal/core/references/skills.md` | 기술 스택 → 스킬 매핑 섹션 추가 (기존 스킬 목록에 확장) |
| 2 | `skills/dev-task-pilot/references/analysis-guide.md` | 0단계 신설 (docs/ + skills.md + mcps.md 참조) + context7 의무 + 실데이터 샘플링 |
| 3 | `skills/dev-task-pilot/references/plan-guide.md` | docs/ 참조 기반 설계 + execution-plan.json 생성 + 영역 태그 + ui-designer 참조 |
| 4 | `skills/dev-task-pilot/references/execute-guide.md` | 금지 행동 + 가드레일 + 보안 가드레일 + execution-plan.json 입력 |
| 5 | `skills/ui-designer/SKILL.md` | 모드 판별 라우터로 재구성 + 공통 규칙 유지 |
| 5a | `skills/ui-designer/modes/scaffold.md` (신규) | 기존 Phase 1~5 이동 |
| 5b | `skills/ui-designer/modes/plan-driven.md` (신규) | plan-driven 모드 신규 |
| 6 | `agents/dtp-dev-test-agent/AGENT.md` | 스모크 테스트 + code-review 연계 |
| 7 | `skills/dev-task-pilot/SKILL.md` | 산출물에 execution-plan.json 추가 |
| 8 | `skills/dev-task-pilot/modes/dev-full.md` | FE/BE 병렬 디스패치 + 워커 프롬프트 보강 |
| 9 | `skills/dev-task-pilot/modes/dev-short.md` | execution-plan.json 생성 + 병렬 조건 |

### 제거된 항목 (기존 문서 재활용)

| 제거 | 이유 | 대체 |
|------|------|------|
| ~~dev-tools-registry.md 신규~~ | `skills.md`에 이미 스킬 목록 있음 | skills.md에 기술 스택 매핑 섹션 추가 |
| ~~tech-context.json 매 태스크 생성~~ | opi가 만든 docs/에 기술 스택 이미 있음 | ANALYSIS에서 docs/ + skills.md + mcps.md를 Read만 |

### 영향 확인 (변경 없지만 정합성 확인 필요)

| # | 파일 경로 | 확인 사항 |
|---|----------|----------|
| - | `skills/dev-task-pilot/modes/wireframe-ui.md` | Wireframe UI 모드가 영향받지 않는지 |
| - | `agents/dtp-dev-agent/AGENT.md` | 워커 실행 프로세스와 충돌 없는지 |
| - | `agents/dtp-wireframe-ui-agent/AGENT.md` | 기존 ui-designer scaffold 호출 흐름 유지 |

## 2. 구현 순서

의존 관계: skills.md 매핑 → analysis-guide(참조 규칙) → plan-guide(execution-plan.json 스키마) → execute-guide + modes/(JSON 소비) → ui-designer + test-agent(최종 소비자)

| 순서 | 영역 | 작업 | 파일 |
|------|------|------|------|
| 1 | [공통] | skills.md에 기술 스택 매핑 섹션 추가 | opal/core/references/skills.md |
| 2 | [공통] | analysis-guide.md 수정 | references/analysis-guide.md |
| 3 | [공통] | plan-guide.md 수정 | references/plan-guide.md |
| 4 | [공통] | execute-guide.md 수정 | references/execute-guide.md |
| 5 | [공통] | SKILL.md 산출물 추가 | skills/dev-task-pilot/SKILL.md |
| 6 | [공통] | modes/dev-full.md FE/BE 병렬 디스패치 | modes/dev-full.md |
| 7 | [공통] | modes/dev-short.md 병렬 조건 | modes/dev-short.md |
| 8a | [FE] | ui-designer SKILL.md → 모드 라우터 재구성 | skills/ui-designer/SKILL.md |
| 8b | [FE] | ui-designer scaffold.md (Phase 1~5 이동) | skills/ui-designer/modes/scaffold.md |
| 8c | [FE] | ui-designer plan-driven.md (신규) | skills/ui-designer/modes/plan-driven.md |
| 9 | [공통] | dtp-dev-test-agent 스모크 + code-review | agents/dtp-dev-test-agent/AGENT.md |

## 3. 핵심 설계

### 3-1. 기존 문서 재활용 구조

```
프레임워크 레벨 (이미 존재, 1회 갱신):
  ~/.opal/references/skills.md  ← 기술 스택 매핑 섹션 추가
  ~/.opal/references/mcps.md    ← 그대로 활용
  ~/.opal/references/agents.md  ← 그대로 활용

프로젝트 레벨 (opi가 이미 생성):
  docs/server/README.md         ← BE 기술 스택, 구조, 실행 방법
  docs/client/README.md         ← FE 기술 스택, 구조
  docs/client/ARCHITECTURE.md   ← Routing/View 분리, 컴포넌트 구조
  docs/INDEX.md                 ← 문서 인덱스 + 개발 워크플로우
  .opal/AGENT.md                ← PM 프로필, 프로젝트 규칙

태스크 레벨 (매 태스크 생성):
  tasks/{NNN}/execution-plan.json  ← PLAN에서 생성, EXECUTE에서 소비
```

### 3-2. skills.md 기술 스택 매핑 (신규 섹션)

기존 skills.md 하단에 추가. ANALYSIS 워커가 프로젝트 기술 스택 식별 후 참조:

```markdown
## 기술 스택별 추천 스킬

### FE 기술 스택

| 기술 | 식별 조건 | 추천 스킬 | 추천 MCP |
|------|----------|----------|---------|
| React | package.json: "react" | vercel-labs/react-best-practices, vercel-labs/composition-patterns | context7 |
| Next.js | package.json: "next" | vercel-labs/next-best-practices + 위 React 스킬 | context7 |
| shadcn/ui | components.json 존재 | vercel-labs/shadcn | shadcn MCP |
| Vue/Nuxt | package.json: "vue" 또는 "nuxt" | (미등록) | context7 |

### BE 기술 스택

| 기술 | 식별 조건 | 추천 스킬 | 추천 MCP |
|------|----------|----------|---------|
| Python | pyproject.toml 존재 | trailofbits/modern-python | context7 |
| FastAPI | pyproject.toml: "fastapi" | trailofbits/modern-python | context7 |
| Django | pyproject.toml: "django" | trailofbits/modern-python | context7 |
| Java/Spring | pom.xml 또는 build.gradle | (미등록) | context7 |
| Kotlin | build.gradle.kts | (미등록) | context7 |
| Go | go.mod | (미등록) | context7 |
| Node.js/Express | package.json: "express" | (미등록) | context7 |

### 공통 (모든 프로젝트)

| 용도 | 추천 스킬 | 적용 시점 |
|------|----------|----------|
| 코드 리뷰 | getsentry/code-review | TEST 단계 |
| 웹앱 테스트 | anthropics/webapp-testing | TEST 단계 (Playwright) |
| UI 구현 | ui-designer | EXECUTE 단계 (FE 화면) |
```

### 3-3. analysis-guide.md 변경 상세

기존 5단계 유지 + 아래 추가:

- **0단계 (신설)**: 프로젝트 컨텍스트 로딩
  1. `docs/` 존재 확인 → 있으면 Read (서버/클라이언트 README, ARCHITECTURE 등)
  2. 없으면 opi 실행 제안
  3. `.opal/AGENT.md` 존재 시 Read (프로젝트 규칙/컨벤션)
  4. 기술 스택 식별 (package.json, pyproject.toml, CLAUDE.md 등)
  5. `~/.opal/references/skills.md`의 "기술 스택별 추천 스킬" 참조 → 적용할 스킬/MCP 파악
  6. `~/.opal/references/mcps.md` 참조 → 사용 가능한 MCP 파악
- **1단계 보강**: 데이터 파이프라인 작업 시 실데이터 첫 5행 샘플링
- **2단계 보강**: context7 MCP 의무 호출 + 커뮤니티 검색 (GitHub Issues, SO, Reddit)
- **3단계 보강**: 아키텍처 정합성 — docs/의 구조에 맞는 구현 방식 제안
- **출력 형식**: "6. 기술 컨텍스트" 섹션 추가 (식별된 스택 + 추천 스킬/MCP)
- **품질 체크리스트**: 3항목 추가

### 3-4. plan-guide.md 변경 상세

Full Task:
- **0단계 (신설)**: docs/ + ANALYSIS.md "기술 컨텍스트" 섹션 참조 → 추천 스킬 SKILL.md Read → 설계 반영 (의무)
- **2단계 뒤**: [FE]/[BE]/[공통] 영역 태그 규칙 + 테이블 예시
- **3단계 보강**: FE 설계 시 ui-designer 화면 유형별 패턴(Phase 4.2) 참조
- **5단계 뒤**: execution-plan.json 생성 규칙 (스키마 + BE layers 순서: model→dto→service→router)
- **출력 형식**: "7. 참조 도구" 섹션 + execution-plan.json 참조
- **품질 체크리스트**: 3항목 추가

Short Task:
- 0단계 동일 (docs/ + skills.md 참조)
- execution-plan.json (FE/BE 작업 시)
- 출력 형식에 기술 컨텍스트 섹션

#### execution-plan.json 스키마

```json
{
  "task_id": "NNN-태스크명",
  "common": {
    "items": [
      { "id": "C-1", "description": "...", "files": [...], "depends_on": [] }
    ]
  },
  "frontend": {
    "screens": [
      {
        "id": "FE-1",
        "name": "화면명",
        "type": "crud | dashboard | form | auth | detail | settings | report | monitor",
        "action": "new | modify",
        "route": "/path",
        "files": [...],
        "shadcn_components": [...],
        "depends_on": [...],
        "ui_work": { "description": "...", "components_to_create": [...], "components_to_modify": [...] },
        "api_work": { "endpoints": [...], "description": "..." }
      }
    ]
  },
  "backend": {
    "layers": [
      { "id": "BE-1", "layer": "model | dto | service | router", "description": "...", "files": [...], "depends_on": [...] }
    ]
  },
  "execution_order": {
    "strategy": "common-first-then-parallel",
    "sequence": [
      { "phase": 1, "items": ["C-*"], "note": "공통 먼저" },
      { "phase": 2, "parallel": ["frontend", "backend"], "note": "FE/BE 병렬" }
    ]
  }
}
```

### 3-5. execute-guide.md 변경 상세

기존 전체 유지 + 새 섹션 삽입 ("실행 모드별 동작" 앞):

- **금지 행동**: PLAN 밖 파일 변경 금지, 설계 임의 변경 금지, 영역 침범 금지, 미승인 패키지 설치 금지
- **가드레일 판단 기준**: 즉시 멈추고 보고 (구조 불일치, 보안, 연쇄 타입 에러) vs 진행 후 보고 (네이밍, 포맷, deprecated 경고)
- **보안 가드레일**: 하드코딩 시크릿, SQL injection, 민감 파일, 무제한 입력 → 즉시 중단
- **execution-plan.json 기반 실행**: 입력 우선순위 (JSON > TODO.md > PLAN.md), JSON 읽기 규칙, FE screen → ui-designer 연결

### 3-6. ui-designer 구조 개선 + plan-driven 모드

dtp와 동일한 모드 분리 구조로 개선:

```
skills/ui-designer/
├── SKILL.md              ← 모드 판별 + 공통 규칙 (라우터)
└── modes/
    ├── scaffold.md       ← wireframe.md → 새 프로젝트 (현재 Phase 1~5 이동)
    └── plan-driven.md    ← execution-plan.json screen → 기존 프로젝트 화면 구현 (신규)
```

#### SKILL.md (라우터) — 유지하는 것

- frontmatter (name, description 확장)
- 모드 판별 규칙 (신규)
- shadcn Critical Rules (공통 — 두 모드 모두 참조)
- 화면 유형별 구현 패턴 (공통 — Phase 4.2 dashboard, crud, form, auth 등)
- wireframe.md 입력 스키마 (공통 참조)

#### SKILL.md 모드 판별 규칙

| 모드 | 입력 | 파이프라인 파일 |
|------|------|--------------|
| scaffold | wireframe.md | modes/scaffold.md |
| plan-driven | execution-plan.json screen 객체 | modes/plan-driven.md |

판별:
- wireframe.md 입력 / "새 프로젝트", "프로토타입" → scaffold
- dtp EXECUTE에서 호출 / "기존 프로젝트", "화면 추가", "수정" → plan-driven

#### modes/scaffold.md — 기존 Phase 1~5 이동

현재 SKILL.md의 Phase 1(입력 파싱) ~ Phase 5(빌드/산출물) + 완료 보고를 이동.
SKILL.md의 공통 규칙(shadcn Critical Rules, 화면 유형별 패턴)은 "SKILL.md 참조"로 연결.

#### modes/plan-driven.md — 신규

- **입력**: execution-plan.json의 screen 객체 (id, name, type, action, route, files, shadcn_components, ui_work, api_work)
- **프로세스**:
  1. 프로젝트 구조 파악 (기존 디렉토리, 컴포넌트 패턴, shadcn 설치 여부, 라우팅 패턴)
  2. action별 실행 (new: SKILL.md 화면 유형별 패턴으로 생성 / modify: Read → 수정)
  3. shadcn 컴포넌트 확인 (미설치 시 `npx shadcn@latest add` + shadcn MCP 활용)
  4. 검증 (SKILL.md shadcn Critical Rules 참조 + 기존 패턴 일관성)
- **산출물**: 생성/수정된 파일 목록

### 3-7. modes/ FE/BE 병렬 디스패치

dev-full.md EXECUTE 단계:

```
execution-plan.json 존재 시:
  Phase 1: common 실행 (순차)
  Phase 2: [FE 서브에이전트 + BE 서브에이전트] 병렬
    FE: 화면별 ui-designer plan-driven 호출
    BE: layer 순서대로 순차 (model→dto→service→router)
  완료 → dtp-dev-test-agent

fallback (JSON 없음): 기존 TODO.md 기반 실행
```

dev-short.md: FE+BE 있으면 병렬, 단일 영역이면 기존 순차.

### 3-8. dtp-dev-test-agent 보강

- **Step 1.5 스모크 테스트**: docs/ 또는 프로젝트 설정에서 서버 기동 명령 파악 → 서버 기동 → health 체크 → Pass/Fail
- **Step 4 code-review 연계**: getsentry/code-review SKILL.md Read → N+1, Runtime errors, 성능 패턴 검사
- **판정**: 스모크 Fail = Critical Fail

## 4. 의존성 및 환경 변경

없음. 모든 변경은 마크다운 문서 수정이며, 패키지 설치나 환경 설정 변경 불필요.

## 5. 테스트 전략

### 구조 검증
- 기존 dtp 3모드(Full/Short/Wireframe UI) 파이프라인이 깨지지 않는지
- execution-plan.json 없을 때 fallback(기존 TODO.md/PLAN.md 기반)이 유지되는지

### 흐름 검증 (가상 시나리오)
- FE+BE 태스크: TASK → ANALYSIS(docs/ 참조) → PLAN(execution-plan.json) → EXECUTE(병렬) → TEST
- BE only 태스크: TASK → PLAN(frontend 없음) → EXECUTE(순차) → TEST
- Wireframe UI: 기존 흐름 영향 없음 확인

### 파일 간 정합성
- execution-plan.json 스키마: plan-guide ↔ execute-guide ↔ modes/ 일치
- ui-designer screen 입력: execution-plan.json frontend.screens 스키마 일치

## 6. 리스크 및 대응

| 리스크 | 대응 |
|--------|------|
| docs/ 없는 프로젝트 | opi 실행 제안 + 기본 분석은 package.json/pyproject.toml 기반 |
| execution-plan.json ↔ 기존 PLAN.md 공존 혼란 | JSON = 실행 계획, PLAN.md = 설계 설명 — 역할 분리 명시 |
| ui-designer scaffold P0 미해결 | plan-driven 모드 우선, scaffold은 별도 태스크 |
| FE/BE 병렬 시 공유 파일 충돌 | common 먼저 실행 후 병렬 |

## 7. 참조 도구

### 기존 재활용 (변경 없이 참조)
- `~/.opal/references/skills.md` — 스킬 목록 + 기술 스택 매핑 (이번에 추가)
- `~/.opal/references/mcps.md` — MCP 서버 목록
- `docs/` — opi 생성 프로젝트 문서 (기술 스택, 아키텍처, 구조)
- ui-designer SKILL.md Phase 4.2 화면 유형별 패턴
- ui-designer shadcn Critical Rules 인라인 요약
- dtp-dev-test-agent 기존 Step 1~6 프로세스
