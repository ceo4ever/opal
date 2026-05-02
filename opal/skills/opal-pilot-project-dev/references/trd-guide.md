# TRD 작성 가이드

> opal-pilot-project-dev Phase 1에서 TRD를 작성할 때 참조하는 구조/내용 지침.
> PRD 확정 후, 기능 요구사항을 기술적으로 어떻게 구현할지 정의한다.

---

## 작성 전 준비

### 문서 Read (필수)

- `docs/PRD.md` — 기능 요구사항, 우선순위 매트릭스
- `docs/PROJECT.md` — 프로젝트 원칙, 기준
- `docs/ARCHITECTURE.md` — 기존 아키텍처, 기술 스택
- `docs/CONVENTIONS.md` — 코드 컨벤션 (있으면)
- `.opal/AGENT.md` — PM 검토 기준

### MCP 활용 (기술 결정 시)

기술 스택 버전 확정, API 설계, 라이브러리 선택 시 최신 정보를 조회한다.

| MCP | 용도 | 사용 시점 |
|-----|------|----------|
| context7 | 라이브러리 최신 버전/API 문서 조회 | 기술 스택 버전 확정, 설정 방법 확인 |
| shadcn | UI 컴포넌트 존재 여부/사용법 확인 | FE 기술 결정 시 |
| 웹 검색 | 외부 API 문서, 가격, 제한사항 | 외부 연동 설계 시 |

```
사용 예:
  context7 → resolve-library-id("fastapi") → query-docs("latest version, configuration")
  context7 → resolve-library-id("next.js") → query-docs("app router, server components")
  shadcn → search_items("file upload") → 컴포넌트 존재 확인
  웹 검색 → "{라이브러리} deprecation 2026" → 지원 종료 예정 확인
```

### Deprecation / Breaking Change 체크 (필수)

기술 스택 버전 확정 시, 각 핵심 라이브러리에 대해 아래를 확인한다:

| 체크 항목 | 방법 |
|----------|------|
| 최신 안정 버전인가 | context7 또는 공식 문서 |
| deprecation 예정인가 | 웹 검색: "{라이브러리} deprecation" |
| 다음 메이저 버전 breaking change가 있는가 | 릴리즈 노트/마이그레이션 가이드 확인 |
| 의존하는 하위 패키지가 호환되는가 | 패키지 호환성 매트릭스 확인 |

확인 결과를 TRD의 "기술적 제약/트레이드오프" 섹션에 기록한다.

```
예:
| 결정 | 선택 | 대안 | 근거 |
|------|------|------|------|
| Gemini SDK | google-genai 1.x | google-generativeai (deprecated) | google-generativeai는 2026 Q2 지원 종료 예정 |
```

### 커뮤니티 스킬 참조 (기술 스택별)

ARCHITECTURE.md의 기술 스택에 따라 해당 스킬을 Read하여 베스트 프랙티스를 반영한다.

| 기술 스택 | 참조 스킬 | 경로 |
|----------|----------|------|
| React | `vercel-labs/react-best-practices` | `~/.opal/community-skills/vercel-labs/` |
| Next.js | `vercel-labs/next-best-practices` | `~/.opal/community-skills/vercel-labs/` |
| shadcn/ui | `vercel-labs/shadcn` | `~/.opal/community-skills/vercel-labs/` |
| Python | `trailofbits/modern-python` | `~/.opal/community-skills/trailofbits/` |
| Claude API | `anthropics/claude-api` | `~/.opal/community-skills/anthropics/` |

해당 기술 스택이 프로젝트에 포함되어 있으면 스킬을 Read하고, TRD의 기술 결정에 반영한다.

---

## TRD 구조

```markdown
# TRD: {프로젝트명}

> 작성일: YYYY-MM-DD | 상태: 초안 / PM 검수 완료 / 사용자 확정
> 기반: PRD vX.X (YYYY-MM-DD 확정)

## 1. 시스템 아키텍처 상세

### 컴포넌트 다이어그램

{전체 시스템의 컴포넌트와 관계를 텍스트 또는 다이어그램으로 표현}

### 데이터 흐름

{사용자 요청 → 처리 → 응답까지의 데이터 흐름}

## 2. API 설계

### 엔드포인트 목록

| 메서드 | 경로 | 설명 | 요청 | 응답 | PRD 매핑 |
|--------|------|------|------|------|----------|
| POST | /api/v1/{resource} | {설명} | {스키마} | {스키마} | F-001 |

### 공통 사항
- 인증: {방식}
- 에러 응답: {형식}
- 페이지네이션: {방식}

## 3. 데이터 모델

### ERD

{엔티티 관계를 텍스트로 표현}

### 테이블 스키마

| 테이블 | 컬럼 | 타입 | 설명 |
|--------|------|------|------|

## 4. 성능 요구사항

| 항목 | 목표 | 측정 방법 |
|------|------|----------|
| API 응답 시간 | {예: p95 < 500ms} | {예: APM 모니터링} |
| 동시 접속 | {예: 100명} | {예: 부하 테스트} |

## 5. 보안 요구사항

| 항목 | 구현 방법 | OWASP 매핑 |
|------|----------|-----------|
| 인증 | {예: JWT + refresh token} | A07 |
| 인가 | {예: RBAC} | A01 |
| 데이터 보호 | {예: AES-256 암호화} | A02 |

## 6. 외부 연동

| 서비스 | 용도 | 인증 방식 | 에러 처리 |
|--------|------|----------|----------|
| {예: Claude API} | {예: 텍스트 생성} | {예: API Key} | {예: 재시도 3회 + 폴백} |

## 7. 기술적 제약 / 트레이드오프

| 결정 | 선택 | 대안 | 근거 |
|------|------|------|------|
```

---

## PRD → TRD 매핑 규칙

- PRD의 모든 Must/Should 기능에 대해 API + 데이터 모델이 정의되어야 한다
- 각 API 엔드포인트의 `PRD 매핑` 컬럼에 기능 ID(F-XXX)를 명시
- Could 기능은 TRD에서 "향후 확장" 섹션으로 분리 가능
- Won't 기능은 TRD에 포함하지 않음

## 기술 스택 버전 관리 규칙

**ARCHITECTURE.md가 기술 스택 버전의 SSOT(단일 진실 원천)이다.**

TRD에서 기술 결정을 상세화할 때:
- TRD의 "기술적 제약/트레이드오프" 섹션에 **왜 이 기술/버전을 선택했는지** 근거를 기록
- TRD 자체에 기술 스택 버전을 중복 기재하지 않는다 — "상세는 ARCHITECTURE.md 참조"
- TRD 확정 후 **반드시 ARCHITECTURE.md를 업데이트**하여 확정된 버전을 반영

```
TRD 확정 후 기술 스택 반영 흐름:

TRD.md (기술 결정/근거)
  → ARCHITECTURE.md 업데이트 (버전 확정 — SSOT)
  → PROJECT.md는 기술명만 유지 (버전 없이)
  → BACKEND.md, FRONTEND.md는 "ARCHITECTURE.md 참조"
```

---

## PM 검수 체크리스트

TRD 작성 후 사용자에게 넘기기 전, 아래를 1:1 대조한다:

- [ ] PRD의 모든 Must 기능이 API + 데이터 모델로 커버되는가
- [ ] PRD의 모든 Should 기능이 커버되거나 "향후 확장"에 명시되는가
- [ ] API 설계가 일관적인가 (네이밍, HTTP 메서드, 에러 형식)
- [ ] 데이터 모델이 기능 요구사항을 충족하는가
- [ ] 보안 요구사항이 OWASP Top 10을 고려했는가
- [ ] 외부 연동의 인증 방식과 에러 처리가 명시되었는가
- [ ] 성능 목표가 구체적 수치로 정의되었는가
- [ ] 기술적 결정에 근거가 있는가 (트레이드오프 섹션)
- [ ] 핵심 라이브러리의 deprecation/breaking change를 확인했는가
- [ ] docs/ARCHITECTURE.md와 정합성이 맞는가

## 사용자 확정 후 후속 조치 체크

- [ ] docs/ARCHITECTURE.md를 업데이트했는가 (TRD에서 확정된 기술 스택 버전 반영)
- [ ] docs/PROJECT.md 문서 테이블에 TRD.md 등록했는가 (설명, 용도, 참조 시점)
- [ ] `state-tool` 호출로 갱신했는가 (2-TRD → 확정)
- [ ] .opal/MEMORY.md 작업 히스토리를 갱신했는가
