# OPAL MCP 설정 템플릿

`install-mac.sh`가 이 디렉토리의 `*.json` 파일을 읽어 각 플랫폼의 `mcp.json`에 머지한다.

## 템플릿 스키마

```json
{
  "name": "server-name",
  "description": "한줄 설명",
  "install_type": "config_merge | cli_delegate | package_install",
  "config": {
    "command": "npx",
    "args": ["-y", "@package/server-name"],
    "env": {}
  },
  "platforms": ["claude", "cursor", "gemini", "antigravity"]
}
```

### 필드 설명

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `name` | string | ✅ | `mcpServers` 객체의 키. 소문자 kebab-case |
| `description` | string | ✅ | `references/mcps.md` 등록용 설명 |
| `install_type` | string | ✅ | 설치 패턴 (아래 참조) |
| `config` | object | ✅ | `mcpServers.{name}` 아래에 들어갈 설정 |
| `platforms` | string[] | ✅ | 설치 대상: `claude`, `cursor`, `gemini`, `antigravity` |

### install_type

| 타입 | install-mac.sh 동작 | 런타임 동작 |
|------|---------------------|------------|
| `config_merge` | 플랫폼별 mcp.json에 자동 머지 | 즉시 사용 가능 |
| `cli_delegate` | 안내 메시지 출력 (수동) | `npx {tool} mcp init` 실행 필요 |
| `package_install` | 안내 메시지 출력 (수동) | `npm install` + 설정 머지 필요 |

### config 객체 구조

**stdio 로컬 서버:**
```json
{
  "command": "npx",
  "args": ["-y", "@package/server-name", ...],
  "env": { "API_KEY": "${ENV_VAR_NAME}" }
}
```

**원격 URL 서버:**
```json
{
  "url": "https://mcp.example.com/v1",
  "headers": { "Authorization": "Bearer ${TOKEN}" }
}
```

### 플랫폼별 설정 경로

| 플랫폼 | 설정 방식 | 비고 |
|--------|----------|------|
| `claude` | `claude mcp add --scope user` | `.claude.json`에 등록 |
| `gemini` | `gemini mcp add -s user` | `~/.gemini/settings.json`에 등록 (CLI 없으면 config_merge 폴백) |
| `cursor` | config_merge | `~/.cursor/mcp.json` 수동 머지 (CLI 미지원) |
| `antigravity` | config_merge | `~/.gemini/antigravity/mcp_config.json` 수동 머지 (CLI 미지원) |

> **Note**: Claude Code와 Gemini CLI는 자체 `mcp add` CLI 명령어로 등록해야 한다. `mcp.json` 직접 편집은 무시될 수 있다.

## 새 MCP 추가 방법

1. 이 디렉토리에 `{server-name}.json` 파일 생성
2. 위 스키마에 맞게 작성
3. `opal/core/references/mcps.md`에 서버 항목 등록
4. `install-mac.sh` 재실행 시 자동 반영
