# OPAL MCP Registry

OPAL 에이전트가 사용할 수 있는 MCP(Model Context Protocol) 서버 목록.
MCP 서버가 등록되면 에이전트가 해당 도구를 인지하고 활용할 수 있다.

## 스킬 MCP 의존성

MCP 의존성이 있는 스킬 목록. 스킬 호출 전 해당 MCP가 등록되어 있는지 확인한다.

| 스킬명 | 필요 MCP | 용도 | 미등록 시 동작 |
|--------|----------|------|--------------|
| web-to-markdown (wtm) | `playwright` | browser 모드 / Phase 2 브라우저 렌더링 | Phase 1(WebFetch) 성공 시 정상 완료. Phase 2 진입 필요 시 등록 안내 후 중단 |

## 등록된 MCP 서버

### shadcn

- **설명**: shadcn/ui 컴포넌트 검색, 조회, 설치 MCP 서버
- **프로토콜**: stdio
- **설정 경로**: `~/.claude/mcp.json`, `~/.cursor/mcp.json`, `~/.gemini/settings.json`, `~/.gemini/antigravity/mcp_config.json`
- **설치 방식**: config_merge (install-mac.sh 자동)
- **제공 도구**:
  - `shadcn:get_project_registries`: 프로젝트 레지스트리 목록 조회
  - `shadcn:list_items_in_registries`: 레지스트리 컴포넌트 목록
  - `shadcn:search_items_in_registries`: 컴포넌트 퍼지 검색
  - `shadcn:view_items_in_registries`: 컴포넌트 상세 조회 (소스 코드 포함)
  - `shadcn:get_item_examples_from_registries`: 사용 예제/데모 검색
  - `shadcn:get_add_command_for_items`: CLI 설치 명령 생성
  - `shadcn:get_audit_checklist`: 컴포넌트 검증 체크리스트
- **사용 예시**: shadcn/ui 컴포넌트를 검색하고 프로젝트에 설치할 때

### sequential-thinking

- **설명**: 복잡한 문제를 단계별로 분해하고 추론 경로를 탐색하는 구조적 사고 MCP
- **프로토콜**: stdio
- **설정 경로**: `~/.claude/mcp.json`, `~/.cursor/mcp.json`, `~/.gemini/settings.json`, `~/.gemini/antigravity/mcp_config.json`
- **설치 방식**: config_merge (install-mac.sh 자동)
- **제공 도구**:
  - `sequential_thinking`: 단계적 사고 과정 촉진 — 현재 생각, 다음 단계 필요 여부, 총 추론 단계 수 입력
- **사용 예시**: 복잡한 아키텍처 설계, 다단계 문제 해결, 의사결정 시 추론 과정을 구조화할 때

### context7

- **설명**: 라이브러리 최신 공식 문서와 코드 예제를 실시간 조회하는 MCP
- **프로토콜**: stdio
- **설정 경로**: `~/.claude/mcp.json`, `~/.cursor/mcp.json`, `~/.gemini/settings.json`, `~/.gemini/antigravity/mcp_config.json`
- **설치 방식**: config_merge (install-mac.sh 자동)
- **제공 도구**:
  - `resolve-library-id`: 라이브러리 이름을 Context7 호환 ID로 변환
  - `get-library-docs`: 특정 주제의 최신 문서 조회
- **사용 예시**: 프로젝트 환경 설정 시 최신 API 문서 참조, deprecated 메서드 방지, "use context7"으로 자동 활성화

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

## 등록 형식

새로운 MCP 서버 등록 시 아래 형식으로 추가:

```markdown
### {server-name}

- **설명**: {한줄 설명}
- **프로토콜**: stdio | sse | http
- **설정 경로**: {MCP 설정 파일 위치}
- **설치 방식**: config_merge | cli_delegate | package_install
- **제공 도구**:
  - `{tool-name}`: {설명}
- **사용 예시**: {어떤 상황에서 이 MCP를 활용하는지}
```

소스 템플릿은 `opal/core/mcps/{server-name}.json`에 추가한다.
