# OPAL MCP Registry

OPAL 에이전트가 사용할 수 있는 MCP(Model Context Protocol) 서버 목록.
MCP 서버가 등록되면 에이전트가 해당 도구를 인지하고 활용할 수 있다.

## 등록된 MCP 서버

### shadcn

- **설명**: shadcn/ui 컴포넌트 검색, 조회, 설치 MCP 서버
- **프로토콜**: stdio
- **설정 경로**: `~/.claude/mcp.json`, `~/.cursor/mcp.json`
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
