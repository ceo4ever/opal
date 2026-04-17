# OPAL Skills Registry

스킬 메타데이터는 JSON 레지스트리가 SSOT이다.

- 프레임워크 스킬: `~/.opal/references/opal-skills-registry.json`
- 커뮤니티 스킬: `~/.opal/references/community-skills-registry.json`

## 스킬 도구 사용법

```bash
# 사용자 입력에서 스킬 매칭 (// 위치 무관)
node ~/.opal/tools/skill-registry/skill-registry.js match "{사용자 입력}"

# 스킬 상세 조회
node ~/.opal/tools/skill-registry/skill-registry.js get {스킬명}

# 스킬 목록 (그룹/도메인 필터)
node ~/.opal/tools/skill-registry/skill-registry.js list
node ~/.opal/tools/skill-registry/skill-registry.js list --group=otp
node ~/.opal/tools/skill-registry/skill-registry.js list --group=community/anthropics
node ~/.opal/tools/skill-registry/skill-registry.js list --domain=dev

# 레지스트리 검증
node ~/.opal/tools/skill-registry/skill-registry.js validate
```

> Node.js 미설치 시: 이 파일의 기술 스택별 추천 섹션을 직접 참조한다.

---

## 기술 스택별 추천 스킬

> op-dev-analysis 단계에서 프로젝트 기술 스택을 식별한 후, 이 매핑을 참조하여 op-dev-plan 단계에서 적용할 스킬/MCP를 결정한다.
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
| Rust/Actix | `Cargo.toml`: `actix-web` | (미등록) | context7 |

### 공통 (모든 프로젝트)

| 용도 | 추천 스킬 | 적용 시점 |
|------|----------|----------|
| UI 구현 | ui-designer | EXECUTE 단계 (FE 화면 작업) |
| 코드 리뷰 | getsentry/code-review | TEST 단계 |
| 웹앱 테스트 | anthropics/webapp-testing | TEST 단계 (Playwright) |
| 프론트엔드 디자인 | anthropics/frontend-design | PLAN 단계 (UI/UX 설계 참조) |
| SDD 명세 주도 개발 | opal-pilot-sdd (opsdd) | 명세 기반 개발 전체 (SPEC→VERIFY→PLAN→TASKS) |
| 보안·컨벤션 체크 (커밋 전) | opal-pilot-gc (opgc / gc) | 수동 실행 (`//opgc`) |
