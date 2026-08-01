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
| `feature` | 선택 | string | 기능축 조인 키 — 화면/정책 축(`ia:{system}:{screen}`, `POL-{번호}` 등)과 별개로 기능 단위를 태깅한다. `code-scan feature <id>` 조회 키 (§7 참조) |

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

## 7. 2소스 표현 — 인라인과 code-map

`@header`는 두 소스 중 하나로 표현된다:

1. **인라인** — §2·§3에서 규정한 소스 파일 내부 주석. 존재하면 병합 없이 **단독 승리**한다.
2. **외부 code-map** — `.opal/code-map/` 트리에 저장된 JSON 파일(`index.json` + 스코프별 패키지 매니페스트). 인라인이 없는 파일에 한해 5단 상속으로 해석된다.

`code-scan.js`의 `resolveHeader()`가 두 소스를 단일 진입점에서 판정한다. `config.headerSource`(`auto`(기본) / `inline` / `manifest`)로 소스를 강제할 수 있으며, `.opal/code-map/index.json`이 없는 프로젝트는 인라인 전용으로 동작해 기존 동작이 그대로 유지된다(code-map 부재 시 반환값이 `extractHeader()`와 완전히 동일 — `_source` 키도 붙지 않는다).

### 7.1 `.opal/code-map/index.json` 필드

| 필드 | 필수 | 타입 | 기본값 | 설명 |
|------|------|------|--------|------|
| `version` | 필수 | integer | - | `1` 고정. 불일치 시 `unsupported_version` (exit 1) |
| `origin` | 선택 | `"discover"` \| `"manual"` | `"manual"` | 생성 주체 표기 |
| `status` | 선택 | `"draft"` \| `"reviewed"` | `"draft"` | 초안 상태 표시 (소유자 리뷰 후 `reviewed`) |
| `generatedAt` | 선택 | string(ISO8601) | - | `discover` 생성 시각 |
| `note` | 선택 | string | `""` | 소유자 메모 |
| `scopes` | 필수 | object\<string, Scope\> | - | 스코프 정의. 최소 1개. 키 = 스코프명 |
| `scopes[].root` | 필수 | string | - | 프로젝트 루트 상대 디렉토리 경로 (후행 `/` 허용, 정규화하여 저장) |
| `scopes[].anchors` | 선택 | string[] | `[]` | 스코프 루트 상대 모듈 디렉토리 목록. 비었으면 스코프 루트 전체가 단일 앵커 공간 |
| `scopes[].stripPrefix` | 선택 | string[] | `[]` | 앵커 내부에서 제거할 경로 접두 목록(소스 루트·패키지 상용구) |
| `scopes[].readonly` | 선택 | boolean | `false` | `true`면 `target`이 무조건 `manifest` 반환 |
| `domains` | 선택 | object\<string, {paths: string[]}\> | `{}` | 도메인 규칙(tier⑤). `paths` = 글롭 배열 |
| `layerRules` | 선택 | Array\<{match: string, layer: string}\> | `[]` | 레이어 규칙(tier④). `layer`는 §2 `layer 표준값` 권장 |
| `exclude` | 선택 | string[] | `[]` | code-map 연산 전용 추가 제외 디렉토리명. `config.exclude`와 합집합으로 사용하되 8커맨드 탐색에는 미적용 |

### 7.2 패키지 매니페스트 `.opal/code-map/{scope}/{mirrorRel}.json` 필드

| 필드 | 필수 | 타입 | 기본값 | 관할 | 설명 |
|------|------|------|--------|------|------|
| `version` | 필수 | integer | - | 도구 | `1` 고정 |
| `scope` | 필수 | string | - | 도구 | 소속 스코프명. 매니페스트 경로 첫 세그먼트와 일치해야 함 |
| `dir` | 필수 | string | - | 도구 | 미러 대상 소스 디렉토리 (프로젝트 루트 상대). **역매핑의 권위 소스** |
| `package` | 선택 | object | 없으면 키 생략 | 워커 | 이 디렉토리 공통값(tier③). 허용 키 = `description`/`exports`/`depends`/`note`/`feature` |
| `files` | 필수 | object\<basename, FileEntry\> | `{}` | 키=도구 / 값=워커 | 파일별 고유값(tier②). 키는 `dir` 실제 파일 목록과 집합 일치 |
| `files[].description` | 선택 | string | `""` | 워커 | 파일 역할 한 줄 |
| `files[].exports` | 선택 | string[] | `[]` | 워커 | 노출 항목. `validate`가 텍스트 존재 대조 |
| `files[].depends` | 선택 | string[] | `[]` | 워커 | 의존 모듈 ID |
| `files[].note` | 선택 | string | - | 워커 | 메모 |
| `files[].feature` | 선택 | string | - | 워커 | 기능축 조인 키 (§2 `feature` 필드와 동일 의미) |
| `files[].module` | 선택 | string | basename stem 파생 | 도구 | 생략 권장. 존재 시 파생값과 일치해야 함(불일치 = `module_override` 위반) |
| `files[].draft` | 선택 | boolean | `description` 공란이면 `true` | 도구 | 골격 미기입 마커 |

- **`layer`·`domain`은 매니페스트에 기재하지 않는다** — 각각 tier④(`layerRules`)·tier⑤(`domains.paths`) 전용 필드다. 매니페스트에 이 키가 존재하는 것 자체가 위반(`layer_in_manifest`/`domain_in_manifest`)이다.
- **`module` 파생 규칙**: `stem = basename.slice(0, -path.extname(basename).length)` — 케이스 변환을 하지 않는다. 파일명 자체가 이미 §2 `module` 필드의 언어별 컨벤션을 만족하므로 stem 그대로가 정답이다. 다중 확장자(`auth.service.ts`)는 마지막 확장자만 제거해 `auth.service`가 된다.

### 7.3 `_source` 계약 (5종)

| 값 | tier | 의미 |
|----|------|------|
| `inline` | ① | 소스 파일 인라인 `@header` (파일 단독 승리, 병합 없음) |
| `file` | ② | 매니페스트 `files[basename]` |
| `package` | ③ | 매니페스트 `package` |
| `rule` | ④ | `index.layerRules` 매칭 + `module` basename 파생 |
| `domain` | ⑤ | `index.domains.paths` 매칭 |

결과 객체는 `_source`(문자열, 최근접 기여 tier 1개)와 `_sources`(객체, 필드별 tier)를 함께 갖는다. 두 값의 도메인 모두 위 5종으로 닫힌다 — `module` 파생은 `rule`로 표기한다.

### 7.4 미러 경로 사상 예시

적용 순서는 **`root` → `anchors` → `stripPrefix`** 로 고정이며, 각 단계에서 최장 일치가 승리한다.

scope `svc` (`root: "svc/"`, `anchors: ["order-api","ship-api"]`, `stripPrefix: ["src/main/java/com/acme/","src/main/java/"]`)인 경우:

```
소스 디렉토리 : svc/order-api/src/main/java/com/acme/order/service
① root 절단   : order-api/src/main/java/com/acme/order/service
② anchor      : anchor="order-api", sub="src/main/java/com/acme/order/service"
③ stripPrefix : "src/main/java/com/acme/" (최장) 제거 → "order/service"
④ 조립        : mirrorRel = "order-api/order/service"
⑤ 매니페스트  : .opal/code-map/svc/order-api/order/service.json
```

서로 다른 두 소스 디렉토리가 동일 `mirrorRel`로 접히면 어느 쪽도 우선하지 않고 오류(`mirror_collision`)다 — `scaffold`는 exit 1로 거부하며 어떤 파일도 쓰지 않는다.

---

## 변경이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-04-12 | 초기 작성 — 필드 정의 7개 + 언어별 예시 6개 + layer별 exports 가이드 + 삽입 위치 규칙 (109) |
| v1.1 | 2026-04-12 | 기획/설계 layer 5개 추가(`policy`/`ia`/`wireframe`/`erd`/`api-spec`) + `depends` 필드 설명 보강 + exports 가이드 확장 + Markdown 예시 갱신 (113) |
| v1.2 | 2026-04-17 | §2 `module` 필드 — kebab-case 단일 → 언어별 컨벤션(Python: snake_case, TS/JS: kebab-case, Kotlin/Swift: PascalCase). §3 Python 예시 module 값 수정 |
| v1.3 | 2026-07-28 15:33 | §2에 `feature`(선택, string) 필드 행 추가 + §7 "2소스 표현 — 인라인과 code-map" 절 신설 — `index.json` 필드 표·패키지 매니페스트 필드 표(각 필수/선택/타입/기본값 포함)·`_source` 5종 표·미러 경로 사상 예시(root→anchors→stripPrefix, 최장 일치 승리). code-scan.js v1.3.0 실제 구현(`resolveHeader`/`mirrorPathForDir`/`loadCodeMap` 등)과 대조 확인 완료 (077) |
