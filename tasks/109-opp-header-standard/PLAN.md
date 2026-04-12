# PLAN 109 — @header 표준 + code-scan 통합 워크플로우

**태스크**: TASK 109  
**작성일**: 2026-04-11  
**상태**: PLAN

---

## §1. 개요

8개 파일을 변경/신규 작성한다. 각 변경 대상의 구체적인 내용을 아래에 명시한다.

### 변경 대상 요약

| # | 대상 파일 | 유형 | 변경 내용 요약 |
|---|----------|------|--------------|
| 1 | `opal/core/references/header-standard.md` | 신규 | @header 포맷 표준 문서 전체 작성 |
| 2 | `opal/core/references/opal-harness.md` | 수정 | EXECUTE @header 규칙 섹션 추가 + code-scan 활용 가이드 (B안) 추가 |
| 3 | `opal/core/references/opal-pm.md` | 수정 | §3 디스패치 전 code-scan 활용 추가 + §4 PM 검토 게이트 체크 항목 추가 + §9 code-scan.json 관리 의무 섹션 추가 |
| 4 | `opal/core/references/tools.md` | 수정 | code-scan 섹션에 PM 관리 방안 서브섹션 추가 |
| 5 | `opal/skills/op-task-execute/SKILL.md` | 수정 | header-standard.md Read + @header 체크리스트 항목 추가 |
| 6 | `opal/skills/op-dev-execute/SKILL.md` | 수정 | 동일 |
| 7 | `opal/tools/code-scan/code-scan.js` | 수정 | `exports <keyword>` 커맨드 추가 — exports 필드 전용 검색 |
| 8 | `opal/core/AGENT.md` | 수정 | 알투(비서) code-scan 활용 규칙 추가 |

---

## §2. 변경 대상별 실행 계획

### 2-1. `opal/core/references/header-standard.md` (신규)

신규 파일로 작성한다. 전체 구조는 아래와 같다.

#### 문서 구조

```
# @header 표준 — OPAL 코드 파일 메타블록

## 1. 목적
## 2. 필드 정의
## 3. 언어별 주석 포맷
## 4. exports 작성 가이드 (layer별)
## 5. 삽입 위치 규칙
## 6. 적용 대상 파일
## 변경이력
```

#### 상세 내용

**§1. 목적**

코드 파일 분석 시 파일 전체를 Read하는 토큰 낭비를 줄이기 위해, 각 파일 상단에 `@header` 메타블록을 정의한다. code-scan.js가 이 블록을 파싱하여 도메인/레이어/의존 관계를 빠르게 조회할 수 있게 한다.

**§2. 필드 정의**

| 필드 | 필수 여부 | 타입 | 설명 |
|------|---------|------|------|
| `module` | 필수 | string | 모듈 고유 식별자 (kebab-case). 프로젝트 내 unique를 권장한다. `code-scan depends` 명령이 module 필드를 키로 의존 관계를 추적하므로 중복 시 추적이 부정확해진다. |
| `layer` | 필수 | string | 아키텍처 레이어 (예: router, controller, service, util, page, component). 표준값은 아래 테이블 참조. |
| `domain` | 필수 | string | 비즈니스 도메인 (예: auth, user, payment) |
| `description` | 필수 | string | 파일의 역할 한 줄 요약 |
| `exports` | 필수 | string[] | 외부에 노출하는 항목 목록 (layer에 따라 내용이 달라짐 — §4 참조) |
| `depends` | 선택 | string[] | 이 파일이 의존하는 모듈/외부 API 목록 |
| `note` | 선택 | string | 추가 메모 (작업 흔적, 특이사항) |

**layer 표준값**

코드 layer:
`router` / `controller` / `service` / `repository` / `model` / `schema` / `middleware` / `util` / `config` / `page` / `component` / `composable` / `store` / `hook` / `api-client` / `test`

문서 layer:
`spec` / `analysis` / `report` / `skill` / `task` / `plan` / `reference`

규칙: 표준값을 우선 사용하고, 프로젝트 도메인에 따라 추가 정의 가능.

**§3. 언어별 주석 포맷**

5개 언어별 전체 예시를 제공한다.

- **TypeScript/JavaScript (JSDoc)**

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

- **Python (docstring)**

```python
"""
@header {
  "module": "auth-service",
  "layer": "service",
  "domain": "auth",
  "description": "JWT 발급 및 검증 처리",
  "exports": ["issue_token", "verify_token"],
  "depends": ["user_repository", "redis_client"]
}
"""
```

- **Vue (HTML comment)**

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

- **Kotlin**

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

- **Swift**

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

- **md (HTML comment)**

```html
<!--
@header {
  "module": "auth-spec",
  "layer": "spec",
  "domain": "auth",
  "description": "인증 모듈 기능 명세",
  "exports": ["로그인 플로우", "토큰 갱신 정책", "세션 만료 처리"]
}
-->
```

**§4. exports 작성 가이드 (layer별)**

`exports`는 layer에 따라 담는 내용이 달라진다:

| layer | exports에 담는 내용 | 예시 |
|-------|-----------------|------|
| `router` | API 엔드포인트 경로 (HTTP 메서드 포함) | `["POST /auth/login", "DELETE /auth/logout"]` |
| `controller` | 핸들러 함수명 또는 API 엔드포인트 | `["login", "logout"]` 또는 `["POST /auth/login"]` |
| `service` | 공개 함수명 | `["issueToken", "verifyToken"]` |
| `util` | 공개 함수명 | `["formatDate", "parseJWT"]` |
| `page` | 페이지 컴포넌트명 | `["LoginPage"]` |
| `component` | 컴포넌트명 | `["AuthButton", "LoginForm"]` |
| `repository` | 공개 메서드명 | `["findById", "save", "delete"]` |
| `model` / `schema` | 타입/클래스명 | `["User", "UserSchema"]` |
| `spec` | 주요 기능/정책 목록 | `["로그인 플로우", "토큰 갱신 정책"]` |
| `analysis` | 분석 결과/핵심 발견 | `["병목 구간 3개", "개선 우선순위"]` |
| `report` | 보고 항목 | `["주간 배포 현황", "이슈 요약"]` |
| `skill` | 스킬이 수행하는 파이프라인/단계 | `["TASK→PLAN→EXECUTE"]` |

**§5. 삽입 위치 규칙**

- shebang(`#!/...`)이 있으면: shebang 바로 다음 줄
- shebang이 없으면: 파일 첫 줄
- import/require 구문보다 반드시 위에 위치해야 한다
- md 파일: YAML frontmatter(`---`) 다음에 삽입. frontmatter 없으면 파일 첫 줄.

**§6. 적용 대상 파일**

code-scan.js의 기본 지원 확장자와 동일하다:
`.py .js .ts .jsx .tsx .vue .svelte .kt .kts .java .swift`

선택(프로젝트 code-scan.json에 추가): `.md` 등

**변경이력**

v1.0 — 2026-04-11 — 초기 작성 (109)

---

### 2-2. `opal/core/references/opal-harness.md` — EXECUTE @header 규칙 추가

**현재 구조 확인**: opal-harness.md는 §1~§8 구조이며, §8이 "OPAL Tools" 섹션이다. EXECUTE 단계별 규칙은 서브 하네스(opal-harness-interactive.md, opal-harness-agentic.md)에서 정의되어 있다.

**삽입 위치**: §8 OPAL Tools 바로 앞에 새 섹션 `## 8. EXECUTE @header 규칙`을 삽입하고, 기존 §8을 `## 9. OPAL Tools`로 번호를 변경한다.

**추가할 내용** (`## 8. EXECUTE @header 규칙`):

```markdown
## 8. EXECUTE @header 규칙

> **트리거**: 코드 파일 생성/수정 시. code-scan 지원 확장자 파일에만 적용.
> **작성 주체**: 워커(LLM)가 직접 작성. 별도 도구 없음.

### 적용 대상 확장자

code-scan.js 기본 지원 확장자와 동일하다:
`.py .js .ts .jsx .tsx .vue .svelte .kt .kts .java .swift`

위 확장자 외 파일(예: `.json`, `.yaml`, `.md`, `.sh`)은 @header 작성 대상이 아니다.

### 파일 생성 시

@header가 없는 신규 파일을 생성할 때, 워커는 언어에 맞는 주석 문법으로 @header를 파일 최상단에 작성한다.

- 포맷 표준: `opal/core/references/header-standard.md` 참조
- 필수 필드: `module`, `layer`, `domain`, `description`, `exports`
- 선택 필드: `depends` (외부 의존 있을 때), `note` (특이사항 있을 때)

### 파일 수정 시

기존 파일에 @header가 있으면, 변경된 내용에 따라 해당 필드만 갱신한다.

| 변경 내용 | 갱신 대상 필드 |
|----------|-------------|
| 함수/엔드포인트 추가 | `exports` |
| 파일 역할 변경 | `description` |
| 새 의존 모듈 추가 | `depends` |
| 레이어/도메인 이동 | `layer`, `domain` |

기존 파일에 @header가 없으면, 파일 생성 규칙과 동일하게 신규 작성한다.

### 주석 문법

언어별 주석 포맷은 `opal/core/references/header-standard.md` §3을 따른다.
```

**Step 2 체크리스트 추가 항목**:

```
- [ ] opal/core/AGENT.md에서 harness §8 참조 여부 확인 → 있으면 §9로 갱신
```

**§ code-scan 활용 가이드 추가 (B안)**:

§8 신규 섹션 안에, @header 규칙 바로 뒤에 하위 섹션으로 추가한다.

```markdown
### code-scan 활용 가이드

PM·오케스트레이터·알투(비서)는 code-scan을 통해 프로젝트 구조를 파악한 뒤 필요한 파일만 선택적으로 Read한다.

#### 활용 시점

| 역할 | 활용 시점 | 권장 커맨드 |
|------|---------|-----------|
| 알투(비서) | 구조 파악 요청 / 파일 탐색 / 캡틴 질문 응답 | `scan`, `domain`, `layer`, `search`, `exports` |
| PM(오케스트레이터) | TASK/PLAN 수립 전 도메인 파악, 디스패치 전 범위 확인 | `scan`, `domain`, `depends` |
| PM Gate | EXECUTE 완료 후 @header 검증 | `scan <file> --json` |

#### 활용 절차

1. `.opal/code-scan.json` 존재 여부 확인 → 없으면 PM이 생성 (`opal-pm.md §9` 참조)
2. `code-scan scan <scope>` 로 전체 개요 파악
3. 필요 시 `code-scan domain <name>` / `code-scan layer <name>` 으로 범위 좁히기
4. 특정 기능 탐색: `code-scan exports <keyword>` (exports 필드 전용) 또는 `code-scan search <keyword>` (전체 필드)
5. 식별된 파일만 선택적으로 Read

#### 적용 조건

`.opal/code-scan.json`이 존재하는 프로젝트에서만 활용한다. 없으면 일반 파일 탐색(Glob/Grep)을 사용한다.
```

**변경이력 추가**:

```
| v3.6 | 2026-04-12 | §8 EXECUTE @header 규칙 추가 — 파일 생성/수정 시 워커 작성 의무 + 적용 대상 확장자 + md 파일 HTML comment 포맷 지원 + code-scan 활용 가이드 (B안) 추가 (109) |
```

---

### 2-3. `opal/core/references/opal-pm.md` — PM 관리 의무 추가

현재 opal-pm.md는 §1~§8 구조이며, §3이 "PM 디스패치 프로세스", §4가 "PM 검토 게이트"이다.

#### 수정 0: §3 PM 디스패치 프로세스 — code-scan 활용 항목 추가

PM이 워커에게 디스패치하기 전 code-scan으로 범위를 파악하는 절차를 추가한다.

**추가할 내용** (기존 §3 체크리스트에 "사전 범위 파악" 항목 추가):

```
- code-scan.json이 있는 프로젝트: `code-scan scan <scope>` 로 변경 대상 도메인/레이어 파악 후 디스패치
  - 변경 대상 파일의 domain/layer/depends 파악 → 워커 컨텍스트 주입에 활용
  - `code-scan.json` 없으면 일반 파일 탐색(Glob/Grep) 사용
```

#### 수정 1: §4 PM 검토 게이트 — 검토 절차 항목 추가

**현재 §4.검토 절차** (7개 항목):
1. 관련 참조 문서가 워커에게 전달되었는가
2. 기술 스택에 맞는 MCP/스킬이 활용되었는가
3. `.opal/AGENT.md`의 PM 검토 기준 체크리스트 평가
4. TASK.md 요구사항과 산출물의 정합성
5. 참조 문서 내용이 산출물에 반영되었는가
6. `docs/PROJECT.md`의 프로젝트 원칙/기준에 부합하는가
7. 금지사항 위반 여부

**추가할 항목** (8번으로 삽입):

```
8. EXECUTE 결과 changed_files 중 code-scan 대상 확장자 파일에 @header가 올바르게 작성되었는가
   확인 방법: code-scan scan <file> --json 실행
   - 결과 없음: @header 누락 → Fail
   - 결과 있음: module/layer/domain/description/exports 필드 존재 여부 확인 → 누락 시 Fail
   (EXECUTE 결과에 새 domain/scope 추가 시 code-scan.json 갱신 여부도 함께 확인)
```

#### 수정 2: §9 code-scan.json PM 관리 의무 (신규 섹션 추가)

**삽입 위치**: §8 워커 행동 규칙 다음에 신규 `## 9. code-scan.json PM 관리 의무` 섹션을 추가한다.

**추가할 내용**:

```markdown
## 9. code-scan.json PM 관리 의무

`{프로젝트}/.opal/code-scan.json`은 code-scan 도구의 프로젝트별 설정 파일이다.
PM이 이 파일의 생성과 갱신을 담당한다.

### 생성 시점

code-scan 도구를 처음 사용하려 할 때 `.opal/code-scan.json`이 없으면 PM이 직접 생성한다.

최소 구조:

```json
{
  "scopes": {},
  "extensions": [".py", ".js", ".ts", ".vue", ".jsx", ".tsx", ".svelte", ".kt", ".kts", ".java", ".swift"],
  "exclude": ["node_modules", "__pycache__", ".git", "dist", "build", ".venv"],
  "excludePatterns": []
}
```

`scopes`는 프로젝트의 BE/FE 디렉터리 구조에 맞게 정의한다.
예: `{ "be": "backend/src/", "fe": "frontend/src/" }`

### 갱신 트리거

다음 상황에서 PM이 code-scan.json을 검토하고 필요 시 갱신한다:

1. **신규 도메인/폴더 추가**: EXECUTE 결과로 새 도메인 또는 주요 폴더가 추가된 경우
2. **대규모 리팩토링**: 폴더 구조가 변경된 경우
3. **신규 기술 스택 추가**: 기존 extensions에 없는 확장자를 가진 언어가 도입된 경우

### PM Gate 확인 절차

PM Gate(§4 검토 절차 8번)에서 code-scan.json 갱신이 필요하다고 판단되면:
1. `.opal/code-scan.json`을 Read하여 현재 상태 확인
2. 갱신 필요 시 직접 수정한다 (이 경우는 PM이 직접 갱신 허용)
3. 갱신 내용을 소유자에게 보고한다
```

**변경이력 갱신**:

```
| v1.1 | 2026-04-11 | §4 검토 절차에 code-scan.json 갱신 확인 항목 추가 + §9 code-scan.json PM 관리 의무 신규 추가 (109) |
```

---

### 2-4. `opal/core/references/tools.md` — code-scan PM 관리 항목 보완

**현재 tools.md code-scan 섹션 구조**:
- 커맨드
- 주요 옵션
- 프로젝트 설정 (code-scan.json 예시 포함)
- 사용 예시

**추가할 서브섹션**: "프로젝트 설정" 바로 아래에 `### PM 관리 방안` 서브섹션을 추가한다.

**추가할 내용**:

```markdown
### PM 관리 방안

`{프로젝트}/.opal/code-scan.json`은 PM이 생성하고 관리한다.

- **생성 시점**: code-scan 도구를 처음 사용하려 할 때 파일이 없으면 PM이 생성
- **갱신 트리거**: 신규 도메인/폴더 추가, 대규모 리팩토링, 신규 언어 도입
- **PM Gate 확인**: EXECUTE 완료 후 PM Gate에서 신규 scope/domain 반영 여부 확인

상세 관리 절차: `opal-pm.md` §9 참조
```

**변경이력 갱신**:

```
| v1.2 | 2026-04-11 | code-scan 섹션에 PM 관리 방안 서브섹션 추가 (109) |
```

---

### 2-5. `opal/skills/op-task-execute/SKILL.md` — @header 작성 지시 추가

파일을 Read하여 실제 구조를 파악한 뒤, 파일 생성/수정 관련 섹션 또는 체크리스트에 아래 내용을 추가한다.

**추가할 내용**:

```markdown
### @header 작성 (code-scan 대상 확장자 파일)

파일을 생성하거나 수정할 때:
1. `~/.opal/references/header-standard.md` Read
2. 파일 언어에 맞는 주석 포맷으로 @header 작성/갱신
   - 생성: 필수 필드 모두 작성 (module, layer, domain, description, exports)
   - 수정: 변경된 내용에 해당하는 필드만 갱신
3. 삽입 위치: 파일 최상단 (shebang/frontmatter 다음, 없으면 첫 줄)

대상 확장자: `.py .js .ts .vue .jsx .tsx .svelte .kt .kts .java .swift`
+ 프로젝트 code-scan.json에 추가된 확장자
```

---

### 2-6. `opal/skills/op-dev-execute/SKILL.md` — @header 작성 지시 추가

op-task-execute와 동일한 내용 추가. 파일 구조 Read 후 적합한 위치에 삽입.

**추가할 내용**: §2-5와 동일.

---

### 2-7. `opal/tools/code-scan/code-scan.js` — exports 커맨드 추가

`exports` 통합 필드 도입에 따라, exports 필드만 대상으로 하는 전용 검색 커맨드를 추가한다.
기존 `search`는 전체 JSON을 검색하여 노이즈가 있으나, `exports`는 해당 필드만 정확히 매칭한다.

**추가할 커맨드**: `exports <keyword>`

**동작**:
1. 전체 파일 스캔 후 각 파일의 `header.exports` 배열을 확인
2. keyword가 exports 항목 중 하나에 포함되면 매칭
3. 출력 형식: 기존 `search`와 동일 (brief/full/json 지원)

**추가할 코드 위치**: `cmdSearch` 함수 다음에 `cmdExports` 함수 추가, `commands` 객체에 `exports: cmdExports` 등록, USAGE 문자열에 커맨드 설명 추가

**USAGE 추가 내용**:
```
  exports <keyword>     Search within exports field only
```

**함수 구현 계획**:
```js
function cmdExports(projectRoot, config, opts) {
  const keyword = opts.commandArg;
  if (!keyword) { console.error('Usage: code-scan exports <keyword>'); process.exit(1); }

  const all = scanHeaders(projectRoot, config, { ...opts, domain: null, layer: null });
  const kw = keyword.toLowerCase();
  const matches = all.filter(r => {
    if (!r.header.exports || !Array.isArray(r.header.exports)) return false;
    return r.header.exports.some(e => e.toLowerCase().includes(kw));
  });

  // Re-apply domain/layer filters
  const filtered = matches.filter(r => {
    if (opts.domain && r.header.domain !== opts.domain) return false;
    if (opts.layer && r.header.layer !== opts.layer) return false;
    return true;
  });
  output(filtered, opts);
}
```

**변경이력 추가**:
```
| v1.1 | 2026-04-12 | exports 커맨드 추가 — exports 필드 전용 검색 (109) |
```

---

### 2-8. `opal/core/AGENT.md` — 알투(비서) code-scan 활용 규칙 추가

알투(비서) 모드에서 code-scan을 활용하는 규칙을 AGENT.md에 추가한다.

**현재 구조 확인**: opal/core/AGENT.md는 에이전트 정의 및 부트스트랩 절차를 담고 있다. 비서 역할 섹션에 Lazy 트리거 테이블이 있으며 tools.md가 등록되어 있다.

**추가할 위치**: 비서 역할 섹션의 "프로젝트 탐색/분석" 관련 부분에 추가. 또는 Lazy 트리거 테이블 하단에 code-scan 활용 규칙을 별도 서브섹션으로 추가.

**추가할 내용**:

```markdown
### code-scan 활용 규칙 (비서 모드)

`.opal/code-scan.json`이 존재하는 프로젝트에서, 아래 상황에 code-scan을 우선 활용한다.

| 상황 | 활용 방법 |
|------|---------|
| 프로젝트 구조 파악 요청 | `code-scan scan <scope>` → 전체 개요 파악 후 필요 파일만 Read |
| 특정 기능/도메인 파일 탐색 | `code-scan domain <name>` 또는 `code-scan layer <name>` |
| 함수/API 위치 탐색 | `code-scan exports <keyword>` (exports 필드 전용) |
| 키워드 포함 파일 탐색 | `code-scan search <keyword>` (전체 @header 필드) |
| 의존 관계 파악 | `code-scan depends <module>` |

**원칙**: 전체 파일 Read 전에 code-scan으로 범위를 좁혀 토큰 낭비를 줄인다.  
`.opal/code-scan.json` 없으면 code-scan 사용 생략 → Glob/Grep으로 탐색한다.
```

**변경이력 추가**:
```
| vX.X | 2026-04-12 | 알투(비서) code-scan 활용 규칙 추가 (109) |
```

(실제 버전 번호는 EXECUTE 시 AGENT.md 현재 변경이력 확인 후 결정)

---

## §3. 실행 체크리스트

### Step 1 — header-standard.md 신규 작성

- [x] `opal/core/references/header-standard.md` 파일 생성
- [x] §1 목적 작성
- [x] §2 필드 정의 테이블 작성 (7개 필드: module/layer/domain/description/exports/depends/note)
- [x] §3 언어별 주석 포맷 예시 작성 (TypeScript, Python, Vue, Kotlin, Swift — 5개)
- [x] §4 exports 작성 가이드 (layer별 — 8가지 layer 유형)
- [x] §5 삽입 위치 규칙 작성 (shebang 유무 분기 포함)
- [x] §6 적용 대상 파일 목록 작성
- [x] 변경이력 작성 (v1.0 / 2026-04-12 / 초기 작성 / 109)

### Step 2 — opal-harness.md 수정

- [x] `opal/core/references/opal-harness.md` 현재 §8 OPAL Tools 섹션 앞에 신규 `## 8. EXECUTE @header 규칙` 삽입
- [x] §8 안에 `### code-scan 활용 가이드` 서브섹션 추가 (B안 — 역할별 활용 시점 + 절차 + 적용 조건)
- [x] 기존 `## 8. OPAL Tools` → `## 9. OPAL Tools` 번호 변경
- [x] 기존 §8 내부 자기 참조 번호 있으면 §9로 갱신 (내부 자기 참조 없음 — 확인됨)
- [x] 변경이력 v3.6 행 추가

### Step 3 — opal-pm.md 수정

- [x] `opal/core/references/opal-pm.md` §3 PM 디스패치 프로세스에 code-scan 사전 범위 파악 항목 추가
- [x] §4 검토 절차에 8번 항목(code-scan.json 갱신 확인) 추가
- [x] §8 워커 행동 규칙 다음에 신규 `## 9. code-scan.json PM 관리 의무` 섹션 추가
- [x] 변경이력 v1.1 행 추가

### Step 4 — tools.md 수정

- [x] `opal/core/references/tools.md` code-scan 섹션의 "프로젝트 설정" 아래에 `### PM 관리 방안` 서브섹션 추가
- [x] 변경이력 v1.2 행 추가

### Step 5 — op-task-execute/SKILL.md 수정

- [x] `opal/skills/op-task-execute/SKILL.md` Read하여 구조 파악
- [x] @header 작성 섹션 추가 (header-standard.md Read 지시 포함)
- [x] 대상 확장자 목록 포함

### Step 6 — op-dev-execute/SKILL.md 수정

- [x] `opal/skills/op-dev-execute/SKILL.md` Read하여 구조 파악
- [x] @header 작성 섹션 추가 (동일)

### Step 7 — code-scan.js 수정

- [x] `opal/tools/code-scan/code-scan.js` Read하여 구조 파악
- [x] USAGE 문자열에 `exports <keyword>` 설명 추가
- [x] `cmdExports` 함수 추가 (`cmdSearch` 다음 위치)
- [x] `commands` 객체에 `exports: cmdExports` 등록
- [x] 변경이력 v1.1 행 추가

### Step 8 — opal/core/AGENT.md 수정

- [x] `opal/core/AGENT.md` Read하여 비서 역할 섹션 및 Lazy 트리거 테이블 위치 파악
- [x] 비서 모드 `### code-scan 활용 규칙` 서브섹션 추가 (상황별 커맨드 표 + 적용 조건)
- [x] 변경이력 추가 (v1.8)

---

## §4. QA 체크리스트

### QA-1. header-standard.md 완결성

- [x] 7개 필드 모두 정의되었는가 (module / layer / domain / description / exports / depends / note)
- [x] exports 필드의 layer별 분기(최소 5개 layer 유형)가 명시되었는가
- [x] 5개 언어 모두 예시가 제공되었는가 (TypeScript, Python, Vue, Kotlin, Swift)
- [x] 삽입 위치 규칙에 shebang 예외가 명시되었는가
- [x] 적용 대상 확장자 목록이 code-scan.js `DEFAULT_CONFIG.extensions`와 일치하는가
- [x] layer 표준값 테이블이 포함되었는가 (코드 layer + 문서 layer 구분)
- [x] module unique 권장 규칙이 명시되었는가
- [x] md 파일 HTML comment 예시가 포함되었는가
- [x] md 삽입 위치(YAML frontmatter 이후) 규칙이 명시되었는가

### QA-2. opal-harness.md 수정 정합성

- [x] 새 §8이 §8 OPAL Tools 앞에 위치하는가
- [x] 기존 §8이 §9로 올바르게 번호 변경되었는가
- [x] 적용 대상 확장자 목록이 header-standard.md §6과 동일한가
- [x] 파일 생성/수정 시 분기가 명확히 구분되는가
- [x] `### code-scan 활용 가이드` 서브섹션이 §8 안에 포함되었는가 (역할별 활용 시점 표 + 절차 + 적용 조건)
- [x] 변경이력에 v3.6이 추가되었는가

### QA-3. opal-pm.md 수정 정합성

- [x] §3 PM 디스패치 프로세스에 code-scan 사전 범위 파악 항목이 추가되었는가
- [x] §4 검토 절차에 8번 항목이 추가되었는가
- [x] 8번 항목에 "EXECUTE 결과에 새 도메인 또는 폴더가 추가된 경우만 확인"이라는 범위 제한이 명시되었는가
- [x] §9가 §8 다음에 위치하는가
- [x] §9에 생성 시점, 갱신 트리거, PM Gate 확인 절차 3가지가 모두 포함되었는가
- [x] 변경이력에 v1.1이 추가되었는가

### QA-4. tools.md 수정 정합성

- [x] PM 관리 방안 서브섹션이 "프로젝트 설정" 바로 아래에 위치하는가
- [x] opal-pm.md §9 교차 참조가 포함되어 있는가
- [x] 변경이력에 v1.2가 추가되었는가

### QA-5. 문서 간 일관성

- [x] header-standard.md 적용 대상 확장자 ↔ opal-harness.md §8 적용 대상 확장자 일치
- [x] opal-pm.md §9 생성/갱신 규칙 ↔ tools.md PM 관리 방안 내용 일치
- [x] opal-pm.md §9 교차 참조(tools.md) ↔ tools.md 교차 참조(opal-pm.md §9) 쌍방 포함 여부
- [x] op-task/dev-execute의 대상 확장자 ↔ header-standard.md §6 일치
- [x] opal-pm.md §4 8번 확인 방법(code-scan scan --json) ↔ tools.md PM 관리 방안 일치
- [x] opal-harness.md §8 code-scan 활용 가이드 ↔ AGENT.md code-scan 활용 규칙 — 커맨드 목록 일치
- [x] opal-pm.md §3 code-scan 활용 절차 ↔ opal-harness.md §8 가이드 내용 정합성

### QA-6. op-task-execute/op-dev-execute SKILL.md 수정 정합성

- [x] header-standard.md Read 지시가 포함되었는가
- [x] 필수 필드 목록이 명시되었는가
- [x] 대상 확장자 목록이 header-standard.md §6과 동일한가
- [x] 삽입 위치 규칙이 포함되었는가

### QA-7. code-scan.js exports 커맨드

- [x] USAGE에 exports 커맨드 설명이 추가되었는가
- [x] cmdExports 함수가 exports 필드 배열을 대상으로 검색하는가 (전체 JSON 검색 아님)
- [x] domain/layer 필터(--domain, --layer)가 cmdExports에도 적용되는가
- [x] commands 객체에 exports가 등록되었는가
- [x] 변경이력 v1.1이 추가되었는가

### QA-8. AGENT.md 수정 정합성

- [x] 비서 모드 code-scan 활용 규칙이 추가되었는가
- [x] 상황별 커맨드 표에 scan/domain/layer/exports/search/depends가 포함되었는가
- [x] `.opal/code-scan.json` 없을 때 대체 수단(Glob/Grep)이 명시되었는가
- [x] 변경이력이 추가되었는가

---

## 부록. 코드 불일치 보고

| 항목 | 문서 내용 | 실제 코드 | 처리 방법 |
|------|---------|----------|---------|
| tools.md §8 현재 등록된 도구 테이블 | `xlsx-tool`만 등록됨 | code-scan이 tools.md에는 등록되어 있으나 opal-harness.md §8 "현재 등록된 도구" 테이블에는 미등록 | 이번 태스크 범위 외 (별도 opi 대상) |

> **판단**: opal-harness.md §8 "현재 등록된 도구" 테이블에 code-scan이 없는 것은 문서 불일치이나, TASK 109 범위는 @header 규칙 추가이므로 해당 테이블 갱신은 별도 처리한다. PM에게 보고한다.
