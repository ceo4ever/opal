# OPAL MCP Registry

OPAL 에이전트가 사용할 수 있는 MCP(Model Context Protocol) 서버 목록.
MCP 서버가 등록되면 에이전트가 해당 도구를 인지하고 활용할 수 있다.

## 등록된 MCP 서버

현재 등록된 MCP 서버 없음.

## 등록 형식

새로운 MCP 서버 등록 시 아래 형식으로 추가:

```markdown
### {server-name}

- **설명**: {한줄 설명}
- **프로토콜**: stdio | sse | http
- **설정 경로**: {MCP 설정 파일 위치}
- **제공 도구**:
  - `{tool-name}`: {설명}
  - `{tool-name}`: {설명}
- **사용 예시**: {어떤 상황에서 이 MCP를 활용하는지}
```

### 예시

```markdown
### filesystem

- **설명**: 로컬 파일시스템 접근 MCP
- **프로토콜**: stdio
- **설정 경로**: ~/.claude/mcp.json
- **제공 도구**:
  - `read_file`: 파일 읽기
  - `write_file`: 파일 쓰기
  - `list_directory`: 디렉토리 목록
- **사용 예시**: 프로젝트 외부 파일에 접근해야 할 때
```
