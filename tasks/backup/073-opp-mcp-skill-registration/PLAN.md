# PLAN: OPAL 스킬 MCP 사전 확인 메커니즘 추가

> 태스크: 073-opp-mcp-skill-registration
> 작성일: 2026-04-02
> 작성자: Worker (op-task-plan)

## 현황 분석

### 문제 원인
- `wtm browser http://...` 호출 시 Playwright MCP 미등록 상태에서 Phase 2 진입 시점에야 실패를 인지
- AGENT.md Lazy 트리거의 "MCP 사용 요청" 조건은 사용자가 MCP를 명시적으로 요청하는 상황에만 적용됨
- 스킬 SKILL.md에 `required_mcps` 선언이 없어 스킬 호출 전 사전 체크 불가
- mcps.md에 스킬↔MCP 매핑 정보 없음

### 수정 대상 파일 (소스 경로)
- `opal/core/references/mcps.md` — 스킬 MCP 의존성 테이블 + Playwright MCP 항목 + 등록 가이드
- `skills/web-to-markdown/SKILL.md` — `### 필수 MCP` 서브섹션 추가
- `opal/core/AGENT.md` — Lazy 트리거 "MCP 사용 요청" 조건 구체화

### 배포 경로 관계
- `opal/core/references/mcps.md` → 배포 시 `~/.opal/references/mcps.md`
- `opal/core/AGENT.md` → 배포 시 `~/.opal/AGENT.md`
- `skills/web-to-markdown/SKILL.md` → 배포 시 `~/.opal/skills/web-to-markdown/SKILL.md`

---

## T1. mcps.md — 스킬↔MCP 매핑 테이블 + Playwright MCP + 등록 가이드

**대상 파일**: `opal/core/references/mcps.md`

### 변경 내용

#### 1. Playwright MCP 항목 추가

`## 등록된 MCP 서버` 섹션 맨 아래(context7 항목 이후, `## 등록 형식` 이전)에 추가:

```markdown
### playwright

- **설명**: Chromium 기반 브라우저 자동화 MCP. JavaScript 렌더링이 필요한 페이지, SPA, localhost 접근에 사용
- **프로토콜**: stdio
- **설정 경로**: `~/.claude/settings.json` (Claude Code), `~/.cursor/mcp.json`, `~/.gemini/settings.json`
- **설치 방식**: npx 자동 (별도 설치 불필요)
- **제공 도구**:
  - `browser_navigate`: URL로 브라우저 이동
  - `browser_snapshot`: Accessibility Tree 스냅샷 반환
  - `browser_click`: 요소 클릭
  - `browser_type`: 텍스트 입력
- **사용 예시**: SPA/동적 페이지 렌더링 후 콘텐츠 추출, localhost 페이지 접근, wtm browser 모드
```

#### 2. 스킬 MCP 의존성 테이블 추가

`## 등록된 MCP 서버` 섹션 바로 위(파일 첫 번째 `##` 섹션 앞)에 신규 섹션으로 추가:

```markdown
## 스킬 MCP 의존성

MCP 의존성이 있는 스킬 목록. 스킬 호출 전 해당 MCP가 등록되어 있는지 확인한다.

| 스킬명 | 필요 MCP | 용도 | 미등록 시 동작 |
|--------|----------|------|--------------|
| web-to-markdown (wtm) | `playwright` | browser 모드 / Phase 2 브라우저 렌더링 | Phase 1(WebFetch) 성공 시 정상 완료. Phase 2 진입 필요 시 등록 안내 후 중단 |
```

#### 3. MCP 등록 방법 가이드 추가

`## 등록 형식` 섹션 위에 신규 섹션으로 추가:

```markdown
## MCP 등록 방법

### Claude Code (settings.json)

`~/.claude/settings.json`에 `mcpServers` 키를 추가한다:

```json
{
  "mcpServers": {
    "{server-name}": {
      "command": "npx",
      "args": ["{package-name}@latest"]
    }
  }
}
```

**Playwright MCP 등록 예시:**

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

> npx가 패키지를 자동으로 가져오므로 별도 설치 불필요. Claude Code 재시작 후 적용.

### 설정 동기화

`install-mac.sh`의 `config_merge` 방식을 사용하는 MCP는 자동 배포된다.
수동 등록 MCP(`playwright` 등)는 위 방법으로 직접 추가해야 한다.
```

---

## T2. web-to-markdown/SKILL.md — `### 필수 MCP` 서브섹션 추가

**대상 파일**: `skills/web-to-markdown/SKILL.md`

### 변경 내용

`## 의존성` 섹션의 기존 테이블 **앞**에 `### 필수 MCP` 서브섹션을 추가한다.

**삽입 위치**: `## 의존성` 헤더 직후, 기존 의존성 테이블 직전

```markdown
### 필수 MCP

| MCP | 필요 시점 | 미등록 시 동작 |
|-----|----------|--------------|
| `playwright` | browser 모드 진입 시, 또는 Phase 1 실패 후 Phase 2 진입 시 | 등록 안내 메시지 출력 후 즉시 중단 |

**사전 확인 규칙**: browser 모드가 명시되거나 localhost/127.0.0.1/[::1] URL이 감지된 경우, Phase 진입 전에 `playwright` MCP 도구(`browser_navigate`) 가용 여부를 ToolSearch 또는 세션 컨텍스트에서 확인한다. 미등록 확인 시 아래 "Playwright MCP 미등록 시" 안내를 즉시 출력하고 실행을 중단한다.

> Phase 1(WebFetch) 경로에서는 MCP 사전 확인을 수행하지 않는다. Phase 1 성공 시 Playwright MCP 없이 완료 가능하므로 불필요한 확인을 방지한다.
```

**기존 "Playwright MCP 미등록 시" 안내 블록과의 통합**: Phase 2 섹션의 기존 안내 블록은 유지한다. 위 서브섹션은 "browser 모드 사전 확인"을 다루고, Phase 2 내 안내는 "Phase 1 실패 후 런타임 확인"을 다루므로 중복이 아닌 계층 구조다.

---

## T3. AGENT.md — Lazy 트리거 "MCP 사용 요청" 조건 구체화

**대상 파일**: `opal/core/AGENT.md`

### 현황

현재 Lazy 트리거 테이블:

| 트리거 조건 | 로드 대상 |
|------------|----------|
| MCP 사용 요청 | `mcps.md` |

### 변경 방향

변경 최소화 원칙에 따라 기존 행을 **수정**하되, 조건을 구체화한다.

**변경 전:**
```
| MCP 사용 요청 | `mcps.md` | - | **금지** | 로드 중단, 트리거 발생 시 재로드 |
```

**변경 후:**
```
| MCP 사용 요청 또는 MCP 의존 스킬 호출 | `mcps.md` | - | **금지** | 로드 중단, 트리거 발생 시 재로드 |
```

### 판단 근거

- "MCP 의존 스킬 호출"은 "MCP 사용 요청"과 동일한 흐름의 확장이므로, 새 행 추가보다 기존 조건 구체화가 더 적합
- mcps.md에 스킬 MCP 의존성 테이블이 추가되므로, 스킬 호출 시 mcps.md를 로드하면 해당 스킬의 필요 MCP를 즉시 확인 가능
- 하네스나 다른 참조 문서 변경 없이 AGENT.md 1줄 수정으로 처리 — 범위 최소화 달성

---

## 실행 순서

1. `opal/core/references/mcps.md` 수정 (T1)
2. `skills/web-to-markdown/SKILL.md` 수정 (T2)
3. `opal/core/AGENT.md` 수정 (T3)
4. `~/.opal/references/mcps.md` (배포 경로) 동일하게 수정
5. `~/.opal/skills/web-to-markdown/SKILL.md` (배포 경로) 동일하게 수정
6. `~/.opal/AGENT.md` (배포 경로) 동일하게 수정

> 소스(`opal/core/`)와 배포 경로(`~/.opal/`)를 함께 수정해야 현재 세션에 즉시 적용된다.

---

## 검증 기준

- [x] mcps.md에 `### playwright` 항목이 등록됨
- [x] mcps.md에 "스킬 MCP 의존성" 테이블이 존재하고 `wtm` 스킬이 포함됨
- [x] mcps.md에 "MCP 등록 방법" 섹션과 Playwright settings.json 예시가 포함됨
- [x] web-to-markdown/SKILL.md의 `## 의존성` 섹션 상단에 `### 필수 MCP` 서브섹션이 존재함
- [x] browser 모드 사전 확인 규칙이 Phase 진입 전 조건으로 명시됨
- [x] AGENT.md Lazy 트리거 테이블의 해당 행 조건이 "MCP 사용 요청 또는 MCP 의존 스킬 호출"로 변경됨
- [ ] 소스 경로와 배포 경로가 동기화됨
