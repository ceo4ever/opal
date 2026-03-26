# 기술 컨텍스트 가이드 — tech-context-guide.md

프로젝트의 기술 스택, 추천 스킬, MCP 서버를 식별하여 ANALYSIS.md "6. 기술 컨텍스트" 섹션에 기록하는 프로세스를 정의한다.

> **통합 가이드**: 이전에 dev-task-pilot의 여러 모드에 분산되어 있던 기술 컨텍스트 로딩 로직을 통합한 단일 참조 가이드이다.

## 1. 프로젝트 문서 확인

### docs/ 디렉토리가 있는 경우

다음 파일을 순서대로 Read한다 (존재하는 파일만):

```
docs/INDEX.md              ← 문서 전체 구조 파악
docs/server/README.md      ← 서버 아키텍처, API 구조
docs/client/README.md      ← 클라이언트 구조, 라우팅
docs/client/ARCHITECTURE.md ← 프론트엔드 아키텍처 상세
```

### .opal/AGENT.md 확인

프로젝트 루트의 `.opal/AGENT.md`가 있으면 Read한다:
- 프로젝트 개요, 기술 스택, 코딩 규약 섹션을 확인
- CLAUDE.md와 중복 시 .opal/AGENT.md 우선

### docs/가 없는 경우

프로젝트 문서가 부재하면 다음을 안내한다:
```
[참고] 프로젝트 문서(docs/)가 없습니다.
opal-project-init 스킬로 프로젝트 초기 문서를 생성하면 분석 품질이 향상됩니다.
```

문서 부재 시에도 분석을 계속 진행한다 (차선: 코드 직접 분석).

## 2. 기술 스택 식별

프로젝트 설정 파일에서 실제 사용 중인 기술 스택을 추출한다. **추측하지 말고 파일 내용을 근거로 기록한다.**

### 2.1 탐색 대상 파일

| 파일 | 추출 정보 |
|------|----------|
| `CLAUDE.md` | 기술 스택 섹션 (명시된 경우) |
| `package.json` | dependencies, devDependencies → 프레임워크, 라이브러리, 빌드 도구 |
| `pyproject.toml` | dependencies → Python 프레임워크, 라이브러리 |
| `go.mod` | require → Go 모듈 의존성 |
| `pom.xml` | dependencies → Java/Spring 의존성 |
| `build.gradle` / `build.gradle.kts` | dependencies → Gradle 프로젝트 의존성 |
| `Cargo.toml` | dependencies → Rust crate 의존성 |
| `components.json` | shadcn/ui 설정, CSS 프레임워크 |
| `tailwind.config.*` | Tailwind CSS 설정, 플러그인 |
| `tsconfig.json` | TypeScript 설정, 경로 별칭 |
| `.eslintrc.*` / `eslint.config.*` | 린트 규칙, 플러그인 |
| `docker-compose.yml` / `Dockerfile` | 인프라 스택 |

### 2.2 식별 항목

| 카테고리 | 예시 |
|----------|------|
| **언어** | TypeScript 5.x, Python 3.12, Go 1.22 |
| **프레임워크** | Next.js 15, FastAPI, Gin |
| **UI 라이브러리** | React 19, shadcn/ui, Tailwind CSS 4 |
| **상태 관리** | Zustand, Redux Toolkit, Jotai |
| **DB/ORM** | PostgreSQL + Prisma, MongoDB + Mongoose |
| **테스트** | Jest, Vitest, Pytest, Go test |
| **빌드/번들** | Vite, Turbopack, esbuild |
| **인프라** | Docker, Vercel, AWS |

## 3. 추천 스킬 매핑

```
Read ~/.opal/references/skills.md
```

`skills.md`의 "기술 스택별 추천 스킬" 섹션을 참조하여, 식별된 기술 스택에 맞는 스킬을 매핑한다.

**매핑 규칙**:
- 프레임워크 스킬: 해당 프레임워크 전용 스킬이 있으면 우선 추천
- 커뮤니티 스킬: 기술 스택과 관련된 커뮤니티 스킬 포함
- 범용 스킬: 특정 기술과 무관하게 항상 유용한 스킬 (version-mgr, doc-writer 등)

**기록 형식**:
```markdown
### 6.2 추천 스킬
| 스킬 | 용도 |
|------|------|
| anthropics/next-js | Next.js 15 App Router 개발 가이드 |
| anthropics/shadcn-ui | shadcn/ui 컴포넌트 활용 |
```

## 4. MCP 서버 매핑

```
Read ~/.opal/references/mcps.md
```

`mcps.md`를 참조하여, 태스크에 필요한 MCP 서버를 매핑한다.

**매핑 기준**:
- **context7**: 외부 라이브러리 문서 조회 필요 시 (거의 항상)
- **supabase**: Supabase 프로젝트인 경우
- **github**: GitHub 이슈/PR 연동 필요 시
- **figma**: 디자인 시안 참조 필요 시
- **sentry**: 에러 모니터링 데이터 참조 필요 시

**기록 형식**:
```markdown
### 6.3 추천 MCP
| MCP | 용도 |
|-----|------|
| context7 | React 19, Next.js 15 공식 문서 조회 |
| supabase | DB 스키마 조회 및 마이그레이션 |
```

## 5. 결과 기록

위 1~4단계의 결과를 ANALYSIS.md의 "6. 기술 컨텍스트" 섹션에 통합 기록한다:

```markdown
## 6. 기술 컨텍스트

### 6.1 기술 스택
| 카테고리 | 기술 | 버전 |
|----------|------|------|
| 언어 | TypeScript | 5.6 |
| 프레임워크 | Next.js | 15.1 |
| UI | shadcn/ui + Tailwind CSS | 4.0 |
| DB | PostgreSQL + Prisma | 6.2 |
| 테스트 | Vitest | 2.1 |

### 6.2 추천 스킬
| 스킬 | 용도 |
|------|------|
| anthropics/next-js | Next.js App Router 패턴 |
| anthropics/shadcn-ui | UI 컴포넌트 구현 |

### 6.3 추천 MCP
| MCP | 용도 |
|-----|------|
| context7 | 라이브러리 공식 문서 조회 |
```

**주의사항**:
- 버전은 설정 파일에서 확인된 실제 버전만 기록한다
- 추천 스킬/MCP는 태스크와 관련 있는 것만 선별한다 (전부 나열하지 않는다)
- skills.md나 mcps.md가 없으면 해당 섹션을 "참조 레지스트리 미설치"로 표기한다
