# @header 표준 — OPAL 코드 파일 메타블록

## 1. 목적

코드 파일 분석 시 파일 전체를 Read하는 토큰 낭비를 줄이기 위해, 각 파일 상단에 `@header` 메타블록을 정의한다. code-scan.js가 이 블록을 파싱하여 도메인/레이어/의존 관계를 빠르게 조회할 수 있게 한다.

파일 분석 시: code-scan으로 전체 구조를 먼저 파악 → 필요한 파일만 선택적으로 Read.

---

## 2. 필드 정의

| 필드 | 필수 여부 | 타입 | 설명 |
|------|---------|------|------|
| `module` | 필수 | string | 모듈 고유 식별자. 파일 네이밍 컨벤션을 따른다 — Python은 snake_case, TypeScript/JS는 kebab-case, Kotlin/Swift는 PascalCase. 프로젝트 내 unique를 권장한다. `code-scan depends` 명령이 module 필드를 키로 의존 관계를 추적하므로 중복 시 추적이 부정확해진다. |
| `layer` | 필수 | string | 아키텍처 레이어. 표준값은 아래 테이블 참조. |
| `domain` | 필수 | string | 비즈니스 도메인 (예: auth, user, payment) |
| `description` | 필수 | string | 파일의 역할 한 줄 요약 |
| `exports` | 필수 | string[] | 외부에 노출하는 항목 목록. layer에 따라 내용이 달라진다 (§4 참조). |
| `depends` | 선택 | string[] | 이 파일이 의존하는 모듈/외부 API 목록. 코드 파일: module ID(kebab-case), 기획/설계 문서: 참조 문서명 — 예: `["auth-service"]`, `["결제_정책서", "회원_ERD"]` |
| `note` | 선택 | string | 추가 메모 (작업 흔적, 특이사항) |

### layer 표준값

**코드 layer**:
`router` / `controller` / `service` / `repository` / `model` / `schema` / `middleware` / `util` / `config` / `page` / `component` / `composable` / `store` / `hook` / `api-client` / `test`

**문서 layer**:
`spec` / `analysis` / `report` / `skill` / `task` / `plan` / `reference`

**기획/설계 layer**:
`policy` / `ia` / `wireframe` / `erd` / `api-spec`

규칙: 표준값을 우선 사용하고, 프로젝트 도메인에 따라 추가 정의 가능.

---

## 3. 언어별 주석 포맷

### TypeScript / JavaScript (JSDoc)

```typescript
/**
 * @header {
 *   "module": "auth-service",
 *   "layer": "service",
 *   "domain": "auth",
 *   "description": "JWT 발급 및 검증 처리",
 *   "exports": ["issueToken", "verifyToken", "refreshToken"],
 *   "depends": ["user-repository", "redis-client"]
 * }
 */
```

### Python (docstring)

```python
"""
@header {
  "module": "auth_service",
  "layer": "service",
  "domain": "auth",
  "description": "JWT 발급 및 검증 처리",
  "exports": ["issue_token", "verify_token"],
  "depends": ["user_repository", "redis_client"]
}
"""
```

### Vue (HTML comment)

```html
<!--
@header {
  "module": "LoginPage",
  "layer": "page",
  "domain": "auth",
  "description": "로그인 화면",
  "exports": ["LoginPage"],
  "depends": ["auth-service", "useAuthStore"]
}
-->
```

### Kotlin

```kotlin
/**
 * @header {
 *   "module": "AuthService",
 *   "layer": "service",
 *   "domain": "auth",
 *   "description": "JWT 발급 및 검증 처리",
 *   "exports": ["issueToken", "verifyToken"],
 *   "depends": ["UserRepository", "RedisClient"]
 * }
 */
```

### Swift

```swift
/**
 * @header {
 *   "module": "AuthService",
 *   "layer": "service",
 *   "domain": "auth",
 *   "description": "JWT 발급 및 검증 처리",
 *   "exports": ["issueToken", "verifyToken"],
 *   "depends": ["UserRepository"]
 * }
 */
```

### Markdown (HTML comment)

```html
<!--
@header {
  "module": "payment-policy",
  "layer": "policy",
  "domain": "payment",
  "description": "결제 정책 체계 정의",
  "exports": ["환불 정책", "부분결제 기준", "PG 수수료 산정"],
  "depends": ["결제_ERD", "PG연동_API명세"]
}
-->
```

---

## 4. exports 작성 가이드 (layer별)

`exports`는 layer에 따라 담는 내용이 달라진다:

| layer | exports에 담는 내용 | 예시 |
|-------|-----------------|------|
| `router` | API 엔드포인트 경로 (HTTP 메서드 포함) | `["POST /auth/login", "DELETE /auth/logout"]` |
| `controller` | 핸들러 함수명 또는 API 엔드포인트 | `["login", "logout"]` 또는 `["POST /auth/login"]` |
| `service` | 공개 함수명 | `["issueToken", "verifyToken"]` |
| `util` | 공개 함수명 | `["formatDate", "parseJWT"]` |
| `page` | 페이지 컴포넌트명 | `["LoginPage"]` |
| `component` | 컴포넌트명 | `["AuthButton", "LoginForm"]` |
| `composable` / `hook` | 훅/컴포저블명 | `["useAuth", "useSession"]` |
| `store` | 스토어명 또는 주요 액션 | `["useAuthStore"]` |
| `repository` | 공개 메서드명 | `["findById", "save", "delete"]` |
| `model` / `schema` | 타입/클래스명 | `["User", "UserSchema"]` |
| `api-client` | 공개 함수명 또는 엔드포인트 | `["getUser", "createPost"]` |
| `spec` | 주요 기능/정책 목록 | `["로그인 플로우", "토큰 갱신 정책"]` |
| `analysis` | 분석 결과/핵심 발견 | `["병목 구간 3개", "개선 우선순위"]` |
| `report` | 보고 항목 | `["주간 배포 현황", "이슈 요약"]` |
| `skill` | 스킬이 수행하는 파이프라인/단계 | `["TASK→PLAN→EXECUTE"]` |
| `policy` | 정책/규칙 항목 | `["환불 정책", "부분결제 기준", "PG 수수료 산정"]` |
| `ia` | 주요 화면/메뉴 구조 | `["GNB 구조", "마이페이지 IA", "결제 플로우"]` |
| `wireframe` | 화면/컴포넌트명 | `["로그인 화면", "상품 목록", "결제 확인 팝업"]` |
| `erd` | 엔티티/테이블명 | `["User", "Order", "Payment"]` |
| `api-spec` | API 엔드포인트 또는 서비스명 | `["POST /payments", "PG 결제 승인 API"]` |

---

## 5. 삽입 위치 규칙

- shebang(`#!/...`)이 있으면: shebang 바로 다음 줄
- shebang이 없으면: 파일 첫 줄
- import/require 구문보다 반드시 위에 위치해야 한다
- **md 파일**: YAML frontmatter(`---`) 블록 다음에 삽입. frontmatter 없으면 파일 첫 줄.

---

## 6. 적용 대상 파일

code-scan.js의 기본 지원 확장자와 동일하다:

```
.py  .js  .ts  .jsx  .tsx  .vue  .svelte  .kt  .kts  .java  .swift
```

**선택 적용** (프로젝트 `.opal/code-scan.json`의 `extensions`에 추가):
- `.md` — 문서 파일에 @header를 적용하는 프로젝트

---

## 변경이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-04-12 | 초기 작성 — 필드 정의 7개 + 언어별 예시 6개 + layer별 exports 가이드 + 삽입 위치 규칙 (109) |
| v1.1 | 2026-04-12 | 기획/설계 layer 5개 추가(`policy`/`ia`/`wireframe`/`erd`/`api-spec`) + `depends` 필드 설명 보강 + exports 가이드 확장 + Markdown 예시 갱신 (113) |
| v1.2 | 2026-04-17 | §2 `module` 필드 — kebab-case 단일 → 언어별 컨벤션(Python: snake_case, TS/JS: kebab-case, Kotlin/Swift: PascalCase). §3 Python 예시 module 값 수정 |
