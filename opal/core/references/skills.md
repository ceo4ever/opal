# OPAL Skills Registry

OPAL 에이전트가 사용할 수 있는 모든 스킬 목록.
사용자 요청에 매칭되는 스킬이 있으면 해당 SKILL.md를 Read로 읽어 실행한다.

## 프레임워크 스킬

플랫폼 네이티브 skills/ 디렉토리에 설치된 핵심 스킬.

| 스킬 | 트리거 | 설명 |
|------|--------|------|
| dev-task-pilot | "새 태스크", "개발 시작", "기능 개발", "오류 수정", "분석해줘", "계획 세워줘" | TASK→ANALYSIS→PLAN→TODO→EXECUTE 5단계 파이프라인 |
| api-analyzer | "API 분석해줘", "API 명세서", "API 검토", "외부 API 조사" | 외부 API 7단계 분석 및 명세서 생성 |
| doc-writer | "문서 작성해줘", "명세서 만들어줘", "보고서 작성" | 기술 문서 표준 템플릿 (모든 문서 스킬의 베이스) |
| interview | "검토해줘", "확인해줘", "궁금한 거 물어봐" | 구조화된 Q&A 요구사항 수집 |
| version-mgr | "업데이트해줘", "수정해줘", "버전 올려줘" | 산출물 v{Major}.{Minor} 버전 관리 |
| wireframe-builder | "와이어프레임", "화면 설계", "UI 설계", "화면 구조", "화면 도출" | UI 분석·설계 — 정책서/요구사항 → wireframe.md 생성 |
| ui-designer | "UI 구현", "UI 만들어줘", "화면 구현", "wireframe 구현", "프로토타입 만들어줘" | UI 구현 — wireframe.md → React + shadcn/ui 기반 UI |

탐색 경로 (우선순위):
1. `{프로젝트}/.opal/skills/{skill}/SKILL.md`
2. `~/.opal/skills/{skill}/SKILL.md`

## OPAL 전용 스킬

`~/.opal/skills/` 에 위치. OPAL 에이전트에서만 사용.

| 스킬 | 트리거 | 경로 |
|---------------|-----------------------------|------|
| opal-onboarding    | (자동: identity.md 없을 때)    | `~/.opal/skills/opal-onboarding/SKILL.md` |
| opal-project-init  | "프로젝트 초기 셋팅", "프로젝트 시작", "프로젝트 문서 만들어줘", "기존 프로젝트 문서화", "docs 생성" | `~/.opal/skills/opal-project-init/SKILL.md` |
| opal-orchestrator  | (자동: .opal/AGENT.md 있을 때) | `~/.opal/skills/opal-orchestrator/SKILL.md` |
| opal-skill-manager | "스킬 검색", "스킬 찾아줘", "스킬 설치해줘", "설치된 스킬", "스킬 삭제" | `~/.opal/skills/opal-skill-manager/SKILL.md` |

## 커뮤니티 스킬

`~/.opal/community-skills/` 에 위치. 기본 번들 31개.
추가 스킬은 `skill-manager`로 검색/설치 (`npx skills find` 또는 [skills.sh](https://skills.sh/)).

### Anthropic 공식 (18개)

| 스킬 | 트리거 | 경로 |
|------|--------|------|
| anthropics/docx | Word 문서, .docx 관련 작업 | `~/.opal/community-skills/anthropics/docx/SKILL.md` |
| anthropics/doc-coauthoring | 문서 공동 작성, 협업 편집 | `~/.opal/community-skills/anthropics/doc-coauthoring/SKILL.md` |
| anthropics/pptx | PowerPoint, .pptx, 프레젠테이션 | `~/.opal/community-skills/anthropics/pptx/SKILL.md` |
| anthropics/xlsx | Excel, 스프레드시트, .xlsx | `~/.opal/community-skills/anthropics/xlsx/SKILL.md` |
| anthropics/pdf | PDF 생성/편집/추출 | `~/.opal/community-skills/anthropics/pdf/SKILL.md` |
| anthropics/algorithmic-art | 제너러티브 아트, p5.js | `~/.opal/community-skills/anthropics/algorithmic-art/SKILL.md` |
| anthropics/canvas-design | 비주얼 디자인, PNG/PDF 아트 | `~/.opal/community-skills/anthropics/canvas-design/SKILL.md` |
| anthropics/frontend-design | 프론트엔드 UI/UX, 인터페이스 디자인 | `~/.opal/community-skills/anthropics/frontend-design/SKILL.md` |
| anthropics/slack-gif-creator | Slack GIF, 애니메이션 이미지 | `~/.opal/community-skills/anthropics/slack-gif-creator/SKILL.md` |
| anthropics/theme-factory | 테마, 스타일링, 슬라이드/문서 디자인 | `~/.opal/community-skills/anthropics/theme-factory/SKILL.md` |
| anthropics/web-artifacts-builder | HTML 아티팩트, React+Tailwind 웹 컴포넌트 | `~/.opal/community-skills/anthropics/web-artifacts-builder/SKILL.md` |
| anthropics/mcp-builder | MCP 서버 생성, Model Context Protocol | `~/.opal/community-skills/anthropics/mcp-builder/SKILL.md` |
| anthropics/webapp-testing | Playwright 테스트, 웹앱 테스트 | `~/.opal/community-skills/anthropics/webapp-testing/SKILL.md` |
| anthropics/brand-guidelines | 브랜드 컬러, 타이포그래피 적용 | `~/.opal/community-skills/anthropics/brand-guidelines/SKILL.md` |
| anthropics/internal-comms | 상태 보고서, 뉴스레터, FAQ | `~/.opal/community-skills/anthropics/internal-comms/SKILL.md` |
| anthropics/skill-creator | 스킬 작성 가이드, 스킬 만들기 | `~/.opal/community-skills/anthropics/skill-creator/SKILL.md` |
| anthropics/claude-api | Claude API, Anthropic SDK 연동 | `~/.opal/community-skills/anthropics/claude-api/SKILL.md` |
| anthropics/template | 스킬 기본 템플릿 | `~/.opal/community-skills/anthropics/template/SKILL.md` |

### Google Labs Stitch (5개)

| 스킬 | 트리거 | 경로 |
|------|--------|------|
| google-labs-code/design-md | DESIGN.md, 디자인 시스템 문서화 | `~/.opal/community-skills/google-labs-code/design-md/SKILL.md` |
| google-labs-code/enhance-prompt | 프롬프트 개선, UI 프롬프트 최적화 | `~/.opal/community-skills/google-labs-code/enhance-prompt/SKILL.md` |
| google-labs-code/react-components | Stitch→React 변환, 컴포넌트 생성 | `~/.opal/community-skills/google-labs-code/react-components/SKILL.md` |
| google-labs-code/remotion | 워크스루 영상, Remotion 비디오 | `~/.opal/community-skills/google-labs-code/remotion/SKILL.md` |
| google-labs-code/stitch-loop | 디자인→코드 반복, Stitch 자동화 | `~/.opal/community-skills/google-labs-code/stitch-loop/SKILL.md` |

### Vercel 개발 핵심 (5개)

| 스킬 | 트리거 | 경로 |
|------|--------|------|
| vercel-labs/react-best-practices | React 베스트 프랙티스, 성능 최적화 | `~/.opal/community-skills/vercel-labs/react-best-practices/SKILL.md` |
| vercel-labs/web-design-guidelines | 웹 디자인 가이드라인, UI 리뷰 | `~/.opal/community-skills/vercel-labs/web-design-guidelines/SKILL.md` |
| vercel-labs/composition-patterns | React 컴포지션 패턴, 재사용 컴포넌트 | `~/.opal/community-skills/vercel-labs/composition-patterns/SKILL.md` |
| vercel-labs/next-best-practices | Next.js 베스트 프랙티스, RSC, 데이터 패턴 | `~/.opal/community-skills/vercel-labs/next-best-practices/SKILL.md` |
| vercel-labs/shadcn | shadcn/ui 컴포넌트, UI 빌드, 프론트엔드 | `~/.opal/community-skills/vercel-labs/shadcn/SKILL.md` |

### 코드 품질 & 보안 (3개)

| 스킬 | 트리거 | 경로 |
|------|--------|------|
| trailofbits/modern-python | Python, uv, ruff, pytest, 모던 Python | `~/.opal/community-skills/trailofbits/modern-python/SKILL.md` |
| getsentry/code-review | 코드 리뷰, PR 리뷰 | `~/.opal/community-skills/getsentry/code-review/SKILL.md` |
| openai/security-best-practices | 보안 리뷰, 보안 취약점, 시큐리티 | `~/.opal/community-skills/openai/security-best-practices/SKILL.md` |

---

## 기술 스택별 추천 스킬

> dev-task-pilot의 ANALYSIS 단계에서 프로젝트 기술 스택을 식별한 후, 이 매핑을 참조하여 PLAN 단계에서 적용할 스킬/MCP를 결정한다.
> `(미등록)` 표시는 해당 스택 전용 커뮤니티 스킬이 아직 없음을 의미한다. context7 MCP로 최신 문서 조회는 가능.

### FE 기술 스택

| 기술 | 식별 조건 | 추천 스킬 | 추천 MCP |
|------|----------|----------|---------|
| React | package.json: `react` | vercel-labs/react-best-practices, vercel-labs/composition-patterns | context7 |
| Next.js | package.json: `next` | vercel-labs/next-best-practices + 위 React 스킬 | context7 |
| shadcn/ui | `components.json` 존재 또는 `components/ui/` 디렉토리 | vercel-labs/shadcn | shadcn MCP, context7 |
| Tailwind CSS | `tailwind.config.*` 존재 | (shadcn 스킬에 포함) | context7 |
| Vue | package.json: `vue` | (미등록) | context7 |
| Nuxt | package.json: `nuxt` | (미등록) | context7 |
| Angular | package.json: `@angular/core` | (미등록) | context7 |
| Svelte | package.json: `svelte` | (미등록) | context7 |

### BE 기술 스택

| 기술 | 식별 조건 | 추천 스킬 | 추천 MCP |
|------|----------|----------|---------|
| Python | `pyproject.toml` 또는 `requirements.txt` 존재 | trailofbits/modern-python | context7 |
| FastAPI | pyproject.toml/requirements.txt: `fastapi` | trailofbits/modern-python | context7 |
| Django | pyproject.toml/requirements.txt: `django` | trailofbits/modern-python | context7 |
| Flask | pyproject.toml/requirements.txt: `flask` | trailofbits/modern-python | context7 |
| Node.js/Express | package.json: `express` | (미등록) | context7 |
| NestJS | package.json: `@nestjs/core` | (미등록) | context7 |
| Java/Spring Boot | `pom.xml` 또는 `build.gradle`: `spring-boot` | (미등록) | context7 |
| Kotlin/Spring | `build.gradle.kts`: `spring-boot` | (미등록) | context7 |
| Go | `go.mod` 존재 | (미등록) | context7 |
| Go/Gin | go.mod: `gin-gonic/gin` | (미등록) | context7 |
| Go/Echo | go.mod: `labstack/echo` | (미등록) | context7 |
| Rust/Actix | `Cargo.toml`: `actix-web` | (미등록) | context7 |

### 공통 (모든 프로젝트)

| 용도 | 추천 스킬 | 적용 시점 |
|------|----------|----------|
| UI 구현 | ui-designer | EXECUTE 단계 (FE 화면 작업) |
| 코드 리뷰 | getsentry/code-review | TEST 단계 |
| 웹앱 테스트 | anthropics/webapp-testing | TEST 단계 (Playwright) |
| 프론트엔드 디자인 | anthropics/frontend-design | PLAN 단계 (UI/UX 설계 참조) |
