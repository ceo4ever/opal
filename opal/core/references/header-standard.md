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

> 위 표에 정의된 필드 외의 필드를 `@header`에 신설하지 않는다. 특히 **이력 전용 필드** — 변경 이력을 누적 기재하려는 목적의 필드 — 를 두지 않는다. 이름을 불문한다(예: `changelog`·`history`·`revisions`). 이력은 git과 `tasks/{NNN}-*/DONE.md`가 갖는다(§2.1). 다만 `task`·`scenarios`처럼 이력 필드가 아니라 다른 도구(예: 테스트 자산)가 참조하는 필드는 이 금지의 대상이 아니다.

---

### 2.1 이력 비기재 원칙

> `@header`의 어느 필드에도 **변경 이력을 기재하지 않는다**. 근거는 `opal-doc-standard.md:28` — "실행 지시문은 코드처럼 제자리에서 갱신되고 **변경 이력은 git이 갖는다**. 다만 **버전 번호**는 문서 안에 남는다". `@header`는 코드 파일의 실행 지시문이므로 같은 원칙이 적용된다.
> **이력의 소재는 2곳이다** — ① `git log --oneline --all -- <파일>`(커밋 메시지에 태스크 번호가 실린다) ② `tasks/{NNN}-*/DONE.md`(태스크별 변경 서술).
> `@header`는 **현재 시점의 사실만** 담는다. 필드를 갱신할 때는 이전 값 옆에 덧붙이지 않고 **제자리에서 교체**한다.
> 적용 범위: `@header` JSON 블록 전체. 특히 워커가 기입하는 `description`·`exports`·`depends`·`note`·`feature` 5필드가 그 예다. `@header` 블록 **밖**의 평문 주석 `변경이력:` 블록(예: `opal/tools/code-scan/tests/test-validate.js:39-48`)과 `.md` 문서의 `## 변경이력` 표는 이 원칙의 적용 대상이 **아니다**(별건).

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

## 4. 필드 작성 가이드

### 4.1 exports (layer별)

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

### 4.2 description·depends·note·feature

| 필드 | 담는 것 | 담지 않는 것 | 예시 |
|------|--------|------------|------|
| `description` | 이 파일이 **지금 무엇인가** — 역할 한 줄. 코드량이 늘어도 길이가 늘지 않는 축이다(코드량 축은 `exports`가 담당한다) | **변경 이력** — 서로 다른 태스크 번호(`[T061]`·`014:`·`TASK 077` 등 시점 표기)가 **2개 이상** 쌓이는 형태, 시점별 변경 단락의 append, 함수 목록(=`exports` 관할). 자산의 출신 태스크 1개를 단발로 인용하는 것은 이력이 아니므로 허용한다 | `"세션별 BrainSession 상태기계 — 대화 단위 인메모리 핸들 + 프라임 연결 풀"` |
| `depends` | 이 파일이 의존하는 **모듈 ID**(코드: kebab-case) 또는 **참조 문서명**(기획/설계) | 표준 라이브러리 나열, 버전 번호, 도입 시점·태스크 번호 | `["auth-service", "결제_정책서"]` |
| `note` | 코드를 읽어서는 알 수 없는 **현재 유효한 제약·계약**(순서 계약, fail-safe 이유, 의도적 예외) | **변경 이력**(`description`의 이력을 옮겨 담는 대체 저장소가 아니다 — 블록 총량이 그대로면 창문 재포화를 늦출 뿐이다) — 서로 다른 태스크 번호가 **2개 이상** 쌓이는 형태, TODO·미래 계획. 출신 태스크 1개의 단발 인용은 허용한다 | `"모드 게이트는 code-map 로딩보다 위에 놓인다 — 아래에 있으면 무출력 계약이 stderr 축에서 깨진다"` |
| `feature` | 기능축 조인 키 1개 — `code-scan feature <id>` 조회 키(§7) | 복수 값 나열, 태스크 번호, 화면/정책 축 값(`ia:{system}:{screen}`·`POL-{번호}`는 별개 축) | `"F-003"` |

> **임계값 근거**: `description`·`note` 모두 서로 다른 태스크 번호가 **2개 이상**(`TASK_TAG_THRESHOLD = 2`, `opal/tools/code-scan/code-scan.js:51`) 모이면 `code-scan validate`가 `header_history` 비차단 경고로 감지한다(같은 파일 `:3311-3321`). 1개는 규정과 도구 양쪽에서 허용된다 — 자산의 출신 태스크를 밝히는 단발 인용일 뿐 시간이 지나도 늘지 않기 때문이다.

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

1. **인라인** — §2·§3에서 규정한 소스 파일 내부 주석.
2. **외부 code-map** — `.opal/code-map/` 트리에 저장된 JSON 파일(`index.json` + 스코프별 패키지 매니페스트).

`code-scan.js`의 `resolveHeader()`가 두 소스를 단일 진입점에서 판정한다. 어느 소스를 볼지는 `config.headerSource`(`inline` / `manifest` **2택**, **미설정 시 전 명령 거부**)가 결정한다 — 두 소스는 모드에 의해 상호 배타이므로 경합·병합 규칙이 존재하지 않는다.

| 모드 | 해석 경로 | `_source` |
|------|----------|-----------|
| `inline` | tier① 인라인 **단독**. 매니페스트는 읽지 않는다 | 붙지 않음 (반환값이 `extractHeader()`와 완전히 동일) |
| `manifest` | tier② `files` → ③ `package` → ④ `layerRules` → ⑤ `domains` **4단 상속**. 인라인은 읽지 않는다 | §7.3의 4종 |

**전역 단일 키**: `headerSource`는 프로젝트당 전역 1개다. `index.json`의 `scopes.{name}`에도 `.opal/code-scan.json`의 `scopes.{name}`에도 모드 선언 키를 두지 않으며, 한 실행의 모드는 **실행당 1값**이다. 스코프별 모드 오버라이드 절은 존재하지 않는다 — 스코프에 이 키를 넣으면 무시되고 stderr 안내 1줄만 나온다. 우선순위는 CLI `--header-source` > 전역 `config.headerSource`의 **2층**이며, 어느 층에서도 값이 정해지지 않거나 2택 밖의 값이면 전 명령이 exit 1로 거부된다(`header_source_unset` \| `header_source_invalid` \| `code_scan_config_invalid`).

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
| `scopes[].include` | 선택 | string[] | `[]` | 스코프 root 기준 **포함** 글롭 패턴. 비어 있으면 root 전체가 대상. `/`를 포함한 패턴은 상대 경로에, 아니면 파일명에 매칭한다 |
| `scopes[].exclude` | 선택 | string[] | `[]` | 스코프 root 기준 **제외** 글롭 패턴. `include` 통과 후 평가되며, `exclude` 매칭이 최종 승리한다 |
| `scopes[].readonly` | — | — | — | **제거됨(Task 080)**. 이 키는 무시된다 — 값이 무엇이든 `manifest`로 해석되지 **않는다**. 기록 소스는 `.opal/code-scan.json`의 **전역 `headerSource`**로 설정한다 |
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
| `files` | 필수 | object\<basename, FileEntry\> | `{}` | 키=도구 / 값=워커 | 파일별 고유값(tier②). 키는 `dir`의 파일 중 **스코프 필터(`include`/`exclude`)와 `exclude`/`excludePatterns`를 통과한 부분집합**과 집합 일치. 매니페스트가 디렉토리 전체를 대표하지 않는 것이 정상이다 |
| `files[].description` | 선택 | string | `""` | 워커 | 파일 역할 한 줄 |
| `files[].exports` | 선택 | string[] | `[]` | 워커 | 노출 항목. `validate`가 텍스트 존재 대조 |
| `files[].depends` | 선택 | string[] | `[]` | 워커 | 의존 모듈 ID |
| `files[].note` | 선택 | string | - | 워커 | 메모 |
| `files[].feature` | 선택 | string | - | 워커 | 기능축 조인 키 (§2 `feature` 필드와 동일 의미) |
| `files[].module` | 선택 | string | basename stem 파생 | 도구 | 생략 권장. 존재 시 파생값과 일치해야 함(불일치 = `module_override` 위반) |
| `files[].draft` | 선택 | boolean | `description` 공란이면 `true` | 도구 | 골격 미기입 마커 |

- **`layer`·`domain`은 매니페스트에 기재하지 않는다** — 각각 tier④(`layerRules`)·tier⑤(`domains.paths`) 전용 필드다. 매니페스트에 이 키가 존재하는 것 자체가 위반(`layer_in_manifest`/`domain_in_manifest`)이다.
- **`module` 파생 규칙**: `stem = basename.slice(0, -path.extname(basename).length)` — 케이스 변환을 하지 않는다. 파일명 자체가 이미 §2 `module` 필드의 언어별 컨벤션을 만족하므로 stem 그대로가 정답이다. 다중 확장자(`auth.service.ts`)는 마지막 확장자만 제거해 `auth.service`가 된다.

### 7.3 `_source` 계약

`inline` 모드에서는 결과 객체에 `_source`·`_sources` 키가 **붙지 않는다** — 인라인 단독 반환값이 `extractHeader()`와 완전히 동일하기 때문이다.

`manifest` 모드에서만 아래 4종이 나타난다.

| 값 | tier | 의미 |
|----|------|------|
| `file` | ② | 매니페스트 `files[basename]` |
| `package` | ③ | 매니페스트 `package` |
| `rule` | ④ | `index.layerRules` 매칭 + `module` basename 파생 |
| `domain` | ⑤ | `index.domains.paths` 매칭 |

결과 객체는 `_source`(문자열, 최근접 기여 tier 1개)와 `_sources`(객체, 필드별 tier)를 함께 갖는다. 두 값의 도메인 모두 위 4종으로 닫힌다 — `module` 파생은 `rule`로 표기한다.

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

### 7.5 스코프 필터와 소속 판정 우선순위

**파일 집합 필터** — 한 스코프 안에서 어떤 파일이 관리 대상인지는 `include`/`exclude`가 결정한다. 순서는 고정이다.

1. `include`가 비어 있지 않은데 매칭되지 않으면 탈락 (화이트리스트 우선)
2. `exclude`에 매칭되면 탈락 (블랙리스트가 최종 승리)
3. 둘 다 통과하면 관리 대상

필터에서 탈락한 파일은 `target`이 `write_to: none` · `reason: out_of_scope`를 exit 0으로 돌려준다 — 오류가 아니라 "기록 위치 없음"이라는 정상 판정이다. 이 필터는 **모드 선언이 아니다** — 어느 소스에 쓰는지는 여전히 전역 `headerSource`가 정한다.

**소속 스코프 판정** — 한 파일이 여러 스코프 root에 걸치면 아래 순서로 1개를 확정한다.

1. root 매칭 스코프만 후보
2. 파일 집합 필터에서 탈락한 후보 제외
3. **최장 root** 승리
4. 동률이면 `include`로 좁혀진 후보 1개가 승리
5. 동률 후보 2개 이상이 각자의 `include`에 동시 매칭되면 오류(`scope_ambiguous`) — 한쪽 `include`를 좁혀 소속을 1개로 확정한다
6. 그 외 동률은 스코프 이름 사전순

---

## 변경이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-04-12 | 초기 작성 — 필드 정의 7개 + 언어별 예시 6개 + layer별 exports 가이드 + 삽입 위치 규칙 (109) |
| v1.1 | 2026-04-12 | 기획/설계 layer 5개 추가(`policy`/`ia`/`wireframe`/`erd`/`api-spec`) + `depends` 필드 설명 보강 + exports 가이드 확장 + Markdown 예시 갱신 (113) |
| v1.2 | 2026-04-17 | §2 `module` 필드 — kebab-case 단일 → 언어별 컨벤션(Python: snake_case, TS/JS: kebab-case, Kotlin/Swift: PascalCase). §3 Python 예시 module 값 수정 |
| v1.4 | 2026-08-02 14:47 | §7 전면 개정 — `headerSource` `inline`/`manifest` **2택 전역 단일 키**(미설정 시 전 명령 거부·CLI > 전역 2층 우선순위), 상속을 모드별로 재정의(`inline` tier① 단독 / `manifest` tier②~⑤ 4단), `scopes[].readonly` 제거 표기, `scopes[].include`/`exclude` 필드 행 신설, §7.2 `files` 집합 일치를 필터 통과 부분집합으로 재정의, §7.3 `_source`를 `manifest` 모드 4종으로 축소, §7.5 스코프 필터·소속 판정 우선순위 신설 (080) |
| v1.5 | 2026-09-06 13:34 | @header 4필드 작성 가이드(§4.2) 신설 + 이력 비기재 원칙(§2.1) 명문화 + §2 이력 전용 필드(`changelog`·`history`·`revisions` 등) 신설 금지 문단 추가 + §2.1 적용 범위를 5필드 한정에서 `@header` JSON 블록 전체로 확장 + §4.2 `description`·`note` 「담지 않는 것」의 「태스크 번호」 항목을 `code-scan` 임계값(`TASK_TAG_THRESHOLD = 2`)과 일치하도록 「서로 다른 태스크 번호 2개 이상」 기준으로 정밀화(출신 태스크 1개 단발 인용은 허용) (107) |
| v1.3 | 2026-07-28 15:33 | §2에 `feature`(선택, string) 필드 행 추가 + §7 "2소스 표현 — 인라인과 code-map" 절 신설 — `index.json` 필드 표·패키지 매니페스트 필드 표(각 필수/선택/타입/기본값 포함)·`_source` 5종 표·미러 경로 사상 예시(root→anchors→stripPrefix, 최장 일치 승리). code-scan.js v1.3.0 실제 구현(`resolveHeader`/`mirrorPathForDir`/`loadCodeMap` 등)과 대조 확인 완료 (077) |
